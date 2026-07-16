# -*- coding: utf-8 -*-
"""
V360 — camada de funções fechadas para o Assistente.

REGRA CENTRAL: a IA não escreve SQL. Ela escolhe uma função daqui e passa
argumentos. Quem consulta o banco é este arquivo. Consequências:

  - o número vem sempre do Postgres (a IA não pode inventar);
  - `notes` / `description` nunca são selecionados (CPF, NB, senha do INSS);
  - o recorte de unidade do usuário logado é aplicado em TODAS as funções.

Lê apenas as views (vw_tasks_completa, vw_compromissos_completa,
vw_v360_metas_vs_meta) — herda a regra de negócio já validada.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from supabase import create_client

TZ = ZoneInfo("America/Manaus")

VIEW_TASKS = "vw_tasks_completa"
VIEW_COMPROMISSOS = "vw_compromissos_completa"
VIEW_METAS = "vw_v360_metas_vs_meta"

EM_ABERTO = ["Pendente", "Não cumprido", "Iniciado"]

# Colunas que o assistente PODE ler. Qualquer coluna fora desta lista não sai
# do banco. `notes` e `description` estão fora de propósito — não remover.
COLUNAS_PERMITIDAS = {
    "id", "subtipo_nome", "status_nome", "unidade_nome",
    "usuario_executor", "usuario_criador", "responsavel_nome",
    "data_conclusao", "mes_conclusao", "end_datetime", "creation_date",
    "cliente_nome", "setor_meta",
}

MAX_LINHAS = 20_000  # trava de segurança: acima disso a função recusa e sugere filtrar


# ─────────────────────────────────────────────────────────────────────────────
# infra
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource
def _sb():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def _checar_colunas(cols: list[str]) -> str:
    proibidas = set(cols) - COLUNAS_PERMITIDAS
    if proibidas:
        raise ValueError(f"coluna fora do escopo do assistente: {sorted(proibidas)}")
    return ",".join(cols)


def _aplicar_recorte(q, unidades: list[str] | str):
    """unidades == '*' → sem filtro. Senão, restringe às unidades do usuário."""
    if unidades != "*":
        q = q.in_("unidade_nome", unidades)
    return q


def _contar(view: str, unidades, filtros: dict, in_filtros: dict | None = None) -> int:
    """COUNT do lado do Postgres. Não puxa linha (o cap de 1000 do PostgREST
    não afeta count exato)."""
    q = _sb().table(view).select("id", count="exact")
    q = _aplicar_recorte(q, unidades)
    for col, val in filtros.items():
        q = q.eq(col, val)
    for col, vals in (in_filtros or {}).items():
        q = q.in_(col, vals)
    return q.limit(1).execute().count or 0


def _puxar(view: str, unidades, cols: list[str], montar) -> pd.DataFrame:
    """Leitura paginada (cap de 1000 do PostgREST)."""
    sel = _checar_colunas(cols)
    linhas, ini = [], 0
    while True:
        q = _sb().table(view).select(sel)
        q = _aplicar_recorte(q, unidades)
        q = montar(q)
        lote = q.range(ini, ini + 999).execute().data or []
        linhas.extend(lote)
        if len(lote) < 1000:
            break
        ini += 1000
        if ini > MAX_LINHAS:
            raise ValueError("consulta ampla demais — filtre por subtipo, unidade ou período")
    return pd.DataFrame(linhas)


def _mes_ref(mes: str | None) -> str:
    return mes or datetime.now(TZ).strftime("%Y-%m")


def _semana_atual() -> tuple[datetime, datetime]:
    hoje = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    ini = hoje - timedelta(days=hoje.weekday())          # segunda
    return ini, ini + timedelta(days=7)


def _janela(periodo: str) -> tuple[datetime, datetime, str]:
    agora = datetime.now(TZ)
    hoje = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    if periodo == "hoje":
        return hoje, hoje + timedelta(days=1), "hoje"
    if periodo == "semana":
        ini, fim = _semana_atual()
        return ini, fim, f"semana de {ini:%d/%m}"
    ini = hoje.replace(day=1)
    fim = (ini + timedelta(days=32)).replace(day=1)
    return ini, fim, f"{ini:%m/%Y}"


# ─────────────────────────────────────────────────────────────────────────────
# funções expostas à IA
# ─────────────────────────────────────────────────────────────────────────────

def contar_em_aberto(unidades, subtipo: str, unidade: str | None = None) -> dict:
    """Em aberto (Pendente/Não cumprido/Iniciado) + cumpridos no mês corrente."""
    esc = [unidade] if unidade and unidades != "*" and unidade in unidades else (
        [unidade] if unidade and unidades == "*" else unidades
    )
    mes = _mes_ref(None)

    aberto = _contar(VIEW_TASKS, esc, {"subtipo_nome": subtipo},
                     {"status_nome": EM_ABERTO})
    cumprido = _contar(VIEW_TASKS, esc, {"subtipo_nome": subtipo,
                                         "status_nome": "Cumprido",
                                         "mes_conclusao": mes})

    # quebra por status (revela "Iniciado" fantasma) e por unidade
    df = _puxar(VIEW_TASKS, esc, ["status_nome", "unidade_nome"],
                lambda q: q.eq("subtipo_nome", subtipo).in_("status_nome", EM_ABERTO))

    por_status = df["status_nome"].value_counts().to_dict() if not df.empty else {}
    por_unidade = (df["unidade_nome"].value_counts().head(5).to_dict()
                   if not df.empty else {})

    total = aberto + cumprido
    return {
        "subtipo": subtipo,
        "mes": mes,
        "em_aberto": aberto,
        "cumpridos_no_mes": cumprido,
        "total": total,
        "pct_concluido": round(100 * cumprido / total) if total else 0,
        "por_status": por_status,
        "por_unidade": por_unidade,
        "fonte": {"view": VIEW_TASKS, "regra": f"mes_conclusao = {mes}"},
    }


def ranking_executor(unidades, subtipo: str | None = None,
                     periodo: str = "semana") -> dict:
    """Quem CONCLUIU (usuario_executor = finished_by). Não é responsavel_nome."""
    ini, fim, rotulo = _janela(periodo)

    def montar(q):
        q = (q.eq("status_nome", "Cumprido")
              .gte("data_conclusao", ini.isoformat())
              .lt("data_conclusao", fim.isoformat()))
        return q.eq("subtipo_nome", subtipo) if subtipo else q

    df = _puxar(VIEW_TASKS, unidades, ["usuario_executor", "subtipo_nome"], montar)
    if df.empty:
        return {"periodo": rotulo, "subtipo": subtipo, "ranking": [], "total": 0}

    r = (df["usuario_executor"].fillna("— sem nome").value_counts()
         .head(10).reset_index().values.tolist())
    return {
        "periodo": rotulo,
        "subtipo": subtipo or "todos os assuntos",
        "ranking": [{"pessoa": p, "concluidas": int(n)} for p, n in r],
        "total": int(len(df)),
        "fonte": {"view": VIEW_TASKS,
                  "regra": "crédito por usuario_executor · data_conclusao em America/Manaus"},
    }


def agenda_semana(unidades, unidade: str | None = None) -> dict:
    """Perícias JUD e audiências da semana (compromissos)."""
    ini, fim = _semana_atual()
    esc = [unidade] if unidade else unidades

    df = _puxar(VIEW_COMPROMISSOS, esc,
                ["end_datetime", "subtipo_nome", "cliente_nome",
                 "status_nome", "unidade_nome"],
                lambda q: (q.gte("end_datetime", ini.isoformat())
                            .lt("end_datetime", fim.isoformat())))
    if df.empty:
        return {"semana": f"{ini:%d/%m} a {(fim - timedelta(days=1)):%d/%m}",
                "total": 0, "eventos": []}

    df["quando"] = (pd.to_datetime(df["end_datetime"])
                      .dt.tz_convert("America/Manaus")
                      .dt.strftime("%a %d/%m %H:%M"))
    df = df.sort_values("end_datetime")

    return {
        "semana": f"{ini:%d/%m} a {(fim - timedelta(days=1)):%d/%m}",
        "total": int(len(df)),
        "realizados": int((df["status_nome"] == "Cumprido").sum()),
        "eventos": df.head(40)[["quando", "subtipo_nome", "cliente_nome",
                                "unidade_nome", "status_nome"]].to_dict("records"),
        "fonte": {"view": VIEW_COMPROMISSOS, "regra": "end_datetime · America/Manaus"},
    }


def meta_vs_realizado(unidades, mes: str | None = None) -> dict:
    """Meta de pastas abertas/enviadas por unidade."""
    mes = _mes_ref(mes)
    q = _sb().table(VIEW_METAS).select(
        "unidade_principal,mes_referencia,meta_abertas,abertas_realizadas,"
        "meta_enviadas,enviadas_realizadas").eq("mes_referencia", mes)
    if unidades != "*":
        q = q.in_("unidade_principal", unidades)
    linhas = q.execute().data or []

    if not linhas:
        return {"mes": mes, "unidades": [],
                "aviso": "sem meta cadastrada para o período (v360_metas_unidades)"}

    def pct(r, m):
        return round(100 * (r or 0) / m) if m else None

    return {
        "mes": mes,
        "unidades": [{
            "unidade": l["unidade_principal"],
            "abertas": f"{l.get('abertas_realizadas') or 0} de {l.get('meta_abertas') or 0}",
            "pct_abertas": pct(l.get("abertas_realizadas"), l.get("meta_abertas")),
            "enviadas": f"{l.get('enviadas_realizadas') or 0} de {l.get('meta_enviadas') or 0}",
            "pct_enviadas": pct(l.get("enviadas_realizadas"), l.get("meta_enviadas")),
        } for l in linhas],
        "fonte": {"view": VIEW_METAS},
    }


def listar_subtipos(unidades, contem: str = "") -> dict:
    """Subtipos batem letra por letra. A IA usa isto antes de contar quando não
    tem certeza do nome exato (evita devolver 0 por causa de um acento)."""
    df = _puxar(VIEW_TASKS, unidades, ["subtipo_nome"],
                lambda q: q.ilike("subtipo_nome", f"%{contem}%") if contem else q)
    nomes = sorted(df["subtipo_nome"].dropna().unique().tolist()) if not df.empty else []
    return {"busca": contem or "(todos)", "encontrados": nomes[:40],
            "total": len(nomes)}


# ─────────────────────────────────────────────────────────────────────────────
# registro (nome → função) + schema para a API
# ─────────────────────────────────────────────────────────────────────────────

REGISTRO = {
    "contar_em_aberto": contar_em_aberto,
    "ranking_executor": ranking_executor,
    "agenda_semana": agenda_semana,
    "meta_vs_realizado": meta_vs_realizado,
    "listar_subtipos": listar_subtipos,
}

SCHEMA = [
    {
        "name": "contar_em_aberto",
        "description": ("Conta tarefas EM ABERTO (Pendente/Não cumprido/Iniciado) e "
                        "CUMPRIDAS no mês corrente para um assunto (subtipo). "
                        "Devolve também a quebra por status e as 5 unidades com mais casos."),
        "input_schema": {
            "type": "object",
            "properties": {
                "subtipo": {"type": "string",
                            "description": "Nome exato do subtipo, ex.: 'Enviado ao Banco (Levantamento)'"},
                "unidade": {"type": "string",
                            "description": "Opcional. Restringe a uma unidade, ex.: 'MANACAPURU'"},
            },
            "required": ["subtipo"],
        },
    },
    {
        "name": "ranking_executor",
        "description": ("Ranking de quem CONCLUIU tarefas no período. O crédito é de "
                        "quem concluiu (usuario_executor), não do responsável."),
        "input_schema": {
            "type": "object",
            "properties": {
                "subtipo": {"type": "string", "description": "Opcional. Filtra por assunto."},
                "periodo": {"type": "string", "enum": ["hoje", "semana", "mes"],
                            "description": "Padrão: semana."},
            },
        },
    },
    {
        "name": "agenda_semana",
        "description": "Perícias JUD e audiências agendadas para a semana corrente, com cliente e horário local.",
        "input_schema": {
            "type": "object",
            "properties": {"unidade": {"type": "string", "description": "Opcional."}},
        },
    },
    {
        "name": "meta_vs_realizado",
        "description": "Meta de pastas abertas e enviadas vs. realizado, por unidade, no mês.",
        "input_schema": {
            "type": "object",
            "properties": {"mes": {"type": "string", "description": "AAAA-MM. Padrão: mês corrente."}},
        },
    },
    {
        "name": "listar_subtipos",
        "description": ("Lista os nomes exatos de subtipos que contêm um texto. Use SEMPRE "
                        "antes de contar quando não tiver certeza do nome — os subtipos batem "
                        "letra por letra (acento, hífen, espaço)."),
        "input_schema": {
            "type": "object",
            "properties": {"contem": {"type": "string", "description": "Ex.: 'alvará', 'deferido'"}},
            "required": ["contem"],
        },
    },
]


def executar(nome: str, args: dict, unidades) -> dict:
    """Ponto único de execução. O recorte entra aqui — a IA não controla."""
    fn = REGISTRO.get(nome)
    if not fn:
        return {"erro": f"função desconhecida: {nome}"}
    try:
        return fn(unidades, **args)
    except Exception as e:
        return {"erro": str(e)}
