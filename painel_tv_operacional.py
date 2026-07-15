# -*- coding: utf-8 -*-
"""
PAINEL TV OPERACIONAL · V360 — Molina Advogados
Chamado pelo app.py:
  1) intercept()      -> ?setor=adm&unidade=ATRIUM abre o painel em TELA CHEIA (link de cada TV)
  2) render_console() -> tela "TV Operacional" do menu (gestor escolhe unidade e gera os links)

Números da Tela 1: vw_tasks_completa (status + data_meta + data_conclusao).
Tela 2 (hall): vw_v360_colaboradores. Não precisa de view nova.

Casamento de subtipos por NOME-BASE: sufixo de unidade em MAIÚSCULO
— ex: "(ATRIUM)", "(PORTO VELHO - UNID 1)" — é ignorado; parênteses com texto
normal — ex: "(Urbano e Rural)" — são preservados.
"""

import json
import re
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

MINUTOS_SYNC = 5
ALTURA_TV    = 1040
STATUS_PEND  = ["Pendente", "Não cumprido", "Iniciado"]

# ======================================================================
# SETORES  (setor -> sub-áreas -> subtipos-base do LegalOne)
# ícone: calendar | folder | shield | megaphone
# Subtipos vieram da planilha TV_ADM (sem o sufixo de unidade).
# ======================================================================
SETORES = {
    "adm": {
        "titulo": "Painel Operacional ADM",
        "subareas": [
            {"nome": "Agendamento", "icone": "calendar", "subtipos": [
                "Enviado p/ Agendamento",
                "Solicitar Prorrogação",
            ]},
            {"nome": "Agendamento Administrativo", "icone": "folder", "subtipos": [
                "Perícia ADM",
                "Agendar Perícia ADM",
                "Perícia ADM / Avaliação Social ADM",
                "Perícia ADM / Informar Cliente - Avaliação Social ADM",
                "Informar Cliente - Perícia ADM",
                "Perícia ADM Ausente no Municipio",
                "Perícia ADM Não Realizada",
            ]},
            {"nome": "Acompanhamento ADM", "icone": "shield", "subtipos": [
                "Agendar AVS ADM - Exigência",
                "Agendar Perícia ADM - Exigência",
                "Avaliação Social ADM Exigência",
                "Cumprimento de Exigência",
                "Inss Ausente no Municipio - Exigência",
                "Exigência / Perícia ADM",
                "Perícia ADM Exigência",
                "Solicitações de Documentos",
                "Acompanhamento de Reabilitação",
            ]},
            {"nome": "Denúncia", "icone": "megaphone", "subtipos": [
                "Denúncia Realizada",
                "Fazer Denúncia",
                "Fazer Denúncia - Acréscimo 25%",
                "Fazer Denúncia - Aposentadorias",
                "Fazer Denúncia - Aux Acidente 50%",
                "Fazer Denúncia - Aux por Incapacidade (Urbano e Rural)",
                "Fazer Denúncia - BPC Idoso ou Deficiente",
                "Fazer Denúncia - Cadastro de Rep. Legal",
                "Fazer Denúncia - PAB ou Reativação",
                "Fazer Denúncia - Pensão por Morte (Urbana e Rural)",
                "Fazer Denúncia - Salário Maternidade",
                "Fazer Denúncia - Seguro Defeso",
            ]},
        ],
    },
}

UNIDADE_SETORES = {
    # "ATRIUM": ["adm", ...],
}


# ======================================================================
# NORMALIZAÇÃO DE SUBTIPO (ignora sufixo de unidade em MAIÚSCULO)
# ======================================================================
def _norm_subtipo(s) -> str:
    s = str(s).strip()
    s = re.sub(r"\s*-\s*[Aa]justar\s*$", "", s).strip()      # anotação "- ajustar"
    m = re.search(r"\(([^)]*)\)\s*$", s)                     # parênteses no fim
    if m and not any(ch.islower() for ch in m.group(1)):     # corta só se MAIÚSCULO (= unidade)
        s = s[:m.start()].strip()
    return s


# ======================================================================
# RESOLUÇÃO DE COLUNAS DE DATA (nomes variam entre views)
# ======================================================================
# "data conclusão prevista" (prazo/vencimento) — usada p/ ATRASADO
# CONFIRMADO na vw_tasks_completa: a coluna é end_datetime.
COL_PRAZO = ["end_datetime", "data_meta", "data_conclusao_prevista", "deadline"]
# data de conclusão efetiva — usada p/ CUMPRIDO
COL_CONCLUSAO = ["data_conclusao", "effective_end_datetime"]


def _achar_col(df, candidatos):
    for c in candidatos:
        if c in getattr(df, "columns", []):
            return c
    return None


def _serie_dt(d, candidatos):
    """Retorna sempre uma Series datetime SEM fuso, alinhada ao índice de d
    (NaT quando a coluna não existe). Remove o timezone preservando a data
    (não converte de fuso, pra não deslocar datas armazenadas à meia-noite)."""
    c = _achar_col(d, candidatos)
    if c is None:
        return pd.Series(pd.NaT, index=d.index)
    s = pd.to_datetime(d[c], errors="coerce")
    try:
        if getattr(s.dt, "tz", None) is not None:
            s = s.dt.tz_localize(None)
    except Exception:
        pass
    return s


# ======================================================================
# MÉTRICAS (Tela 1)
# ======================================================================
def _metricas(df: pd.DataFrame, norm_sub: pd.Series, bases: set) -> dict:
    hoje = pd.Timestamp.now().normalize()
    d = df[norm_sub.isin(bases)]
    if d.empty:
        return {"atrasados": 0, "pendDia": 0, "pendFut": 0, "cumpridoDia": 0, "cumpridoMes": 0}
    dm = _serie_dt(d, COL_PRAZO)
    dc = _serie_dt(d, COL_CONCLUSAO)
    dmd, dcd = dm.dt.normalize(), dc.dt.normalize()
    stt  = d["status_nome"]
    pend = stt.isin(STATUS_PEND)
    cump = (stt == "Cumprido")
    return {
        "atrasados":   int((pend & dm.notna() & (dmd < hoje)).sum()),
        "pendDia":     int((pend & (dmd == hoje)).sum()),
        "pendFut":     int((pend & (dm.isna() | (dmd > hoje))).sum()),
        "cumpridoDia": int((cump & (dcd == hoje)).sum()),
        "cumpridoMes": int((cump & (dc.dt.year == hoje.year) & (dc.dt.month == hoje.month)).sum()),
    }


def _areas_reais(dfu: pd.DataFrame, cfg: dict) -> list:
    norm_sub = dfu["subtipo_nome"].map(_norm_subtipo) if "subtipo_nome" in dfu else pd.Series([], dtype=str)
    areas = []
    for sa in cfg["subareas"]:
        bases = {_norm_subtipo(x) for x in sa["subtipos"]}
        m = _metricas(dfu, norm_sub, bases) if bases else {
            "atrasados": 0, "pendDia": 0, "pendFut": 0, "cumpridoDia": 0, "cumpridoMes": 0}
        areas.append({"nome": sa["nome"], "icone": sa["icone"], **m})
    return areas


def _campeoes(df_colabs: pd.DataFrame, unidade: str) -> list:
    if df_colabs is None or df_colabs.empty or "colaborador" not in df_colabs:
        return _EXEMPLO["campeoes"]
    d = df_colabs.copy()
    if unidade and "unidade_nome" in d:
        d = d[d["unidade_nome"] == unidade]
    metrica = "cumprido" if "cumprido" in d else ("total_produtividade" if "total_produtividade" in d else None)
    if metrica is None or d.empty:
        return _EXEMPLO["campeoes"]
    d = d.sort_values(metrica, ascending=False).head(9)
    return [{"nome": str(r["colaborador"]), "area": "", "pontos": int(r[metrica] or 0)}
            for _, r in d.iterrows()]


def _meta_escritorio(df_tasks: pd.DataFrame, df_metas: pd.DataFrame, unidade: str) -> dict:
    out = {"metaUnidade": dict(_EXEMPLO["metaUnidade"]), "outras": list(_EXEMPLO["outrasUnidades"])}
    try:
        hoje = pd.Timestamp.now().normalize()
        t = df_tasks
        if "entra_meta" not in t.columns or "indicador_meta" not in t.columns:
            return out
        dc = _serie_dt(t, COL_CONCLUSAO)
        cond = (t.get("entra_meta") == True) & (t.get("indicador_meta") == "Pastas abertas") \
               & (t["status_nome"] == "Cumprido") & (dc.dt.year == hoje.year) & (dc.dt.month == hoje.month)
        realizado_por_un = t[cond].groupby("unidade_nome").size()
        realizado = int(realizado_por_un.get(unidade, 0))
        meta = _EXEMPLO["metaUnidade"]["meta"]
        if df_metas is not None and not df_metas.empty and "unidade_nome" in df_metas:
            linha = df_metas[df_metas["unidade_nome"] == unidade]
            for col in ("meta_total", "meta", "meta_mes"):
                if col in df_metas and not linha.empty:
                    meta = int(pd.to_numeric(linha[col], errors="coerce").fillna(0).sum()); break
        out["metaUnidade"] = {"meta": max(meta, 1), "realizado": realizado}
        outras = [{"nome": u, "meta": meta, "realizado": int(v)}
                  for u, v in realizado_por_un.sort_values(ascending=False).head(4).items() if u != unidade]
        if outras:
            out["outras"] = outras[:3]
    except Exception:
        pass
    return out


# ======================================================================
# MONTA O DADOS
# ======================================================================
def montar_dados(df_tasks, df_colabs, df_metas, unidade: str, setor_key: str) -> dict:
    cfg = SETORES.get(setor_key)
    if cfg is None:
        return None
    dfu = df_tasks
    if unidade and "unidade_nome" in df_tasks:
        dfu = df_tasks[df_tasks["unidade_nome"] == unidade]
    usar_exemplo = all(not sa["subtipos"] for sa in cfg["subareas"])
    areas = _EXEMPLO["setor"]["areas"] if usar_exemplo else _areas_reais(dfu, cfg)
    meta = _meta_escritorio(df_tasks, df_metas, unidade)
    return {
        "setor": {"nome": setor_key.upper(),
                  "titulo": cfg["titulo"] + (f" · {unidade}" if unidade else ""),
                  "areas": areas},
        "campeoes": _campeoes(df_colabs, unidade),
        "campeoesMetrica": "cumpridos no mês",
        "unidade": unidade or "Escritório",
        "metaUnidade": meta["metaUnidade"],
        "outrasUnidades": meta["outras"],
        "segundosPorTela": 16,
        "minutosAtualizacao": MINUTOS_SYNC,
        "fonteDados": "Legal One API",
        "atualizarSupabaseMin": 0,
    }


# ======================================================================
# RENDER — tela cheia
# ======================================================================
def _template() -> str:
    for p in (Path(__file__).with_name("painel_template.html"),
              Path(__file__).with_name("pages") / "painel_template.html"):
        if p.exists():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError("painel_template.html não encontrado (deixe-o na mesma pasta do app.py).")


def render_tela(df_tasks, df_colabs, df_metas, unidade: str, setor_key: str):
    st_autorefresh(interval=MINUTOS_SYNC * 60 * 1000, key=f"tv_{setor_key}_{unidade}")
    st.markdown("""
    <style>
      #MainMenu, header, footer {visibility:hidden;}
      [data-testid="stSidebar"], [data-testid="collapsedControl"] {display:none !important;}
      .block-container {padding:0 !important; max-width:100% !important;}
      [data-testid="stAppViewContainer"], .stApp {background:#060b14 !important;}
      iframe {border:none !important;}
    </style>""", unsafe_allow_html=True)
    dados = montar_dados(df_tasks, df_colabs, df_metas, unidade, setor_key)
    if dados is None:
        st.error(f"Setor '{setor_key}' não existe em SETORES.")
        return
    html = _template().replace("/*__DADOS__*/", "const DADOS = " + json.dumps(dados, ensure_ascii=False) + ";")
    components.html(html, height=ALTURA_TV, scrolling=False)


def intercept(df_tasks, df_colabs=None, df_metas=None):
    qp = st.query_params
    if "setor" in qp:
        render_tela(df_tasks, df_colabs, df_metas, qp.get("unidade", ""), qp.get("setor"))
        st.stop()


# ======================================================================
# DIAGNÓSTICO — subtipos configurados que NÃO existem na base
# ======================================================================
def _diagnostico(df_tasks):
    existentes = set(df_tasks["subtipo_nome"].dropna().map(_norm_subtipo)) if "subtipo_nome" in df_tasks else set()
    faltando = {}
    for chave, cfg in SETORES.items():
        for sa in cfg["subareas"]:
            miss = [x for x in sa["subtipos"] if _norm_subtipo(x) not in existentes]
            if miss:
                faltando[f"{chave} · {sa['nome']}"] = miss
    return faltando


# ======================================================================
# RENDER — console
# ======================================================================
def render_console(df_tasks, df_colabs=None, df_metas=None):
    st.markdown('<div class="v360-title">📺 TV OPERACIONAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="v360-subtitle">Escolha a unidade e abra o painel de cada setor na TV.</div>',
                unsafe_allow_html=True)

    unidades = sorted(df_tasks["unidade_nome"].dropna().astype(str).unique().tolist()) \
        if "unidade_nome" in df_tasks else []
    if not unidades:
        st.info("Sem unidades nos dados.")
        return

    unidade = st.selectbox("Unidade", unidades)
    setores = UNIDADE_SETORES.get(unidade, list(SETORES.keys()))
    if not setores:
        st.warning("Nenhum setor configurado para esta unidade (edite UNIDADE_SETORES).")
        return

    st.caption("Em cada TV, abra o link do setor e aperte **F** para tela cheia. "
               "Sincroniza sozinho a cada 5 minutos.")

    cols = st.columns(3)
    for i, chave in enumerate(setores):
        cfg = SETORES.get(chave)
        if not cfg:
            continue
        dados = montar_dados(df_tasks, df_colabs, df_metas, unidade, chave)
        tot_pend = sum(a["atrasados"] + a["pendDia"] + a["pendFut"] for a in dados["setor"]["areas"])
        tot_cump = sum(a["cumpridoMes"] for a in dados["setor"]["areas"])
        link = f"?setor={chave}&unidade={unidade}"
        with cols[i % 3]:
            st.markdown(
                f"""<div class="metric-card" style="min-height:auto;">
                    <div class="metric-label">📺 {cfg['titulo']}</div>
                    <div class="metric-sub" style="margin-top:6px;">
                        Pendências: <b>{tot_pend}</b> &nbsp;·&nbsp; Cumpridos/mês: <b>{tot_cump}</b>
                    </div></div>""",
                unsafe_allow_html=True,
            )
            st.link_button("▶ Abrir na TV", link, use_container_width=True)
            st.code(link, language=None)

    faltando = _diagnostico(df_tasks)
    col_prazo = _achar_col(df_tasks, COL_PRAZO)
    col_concl = _achar_col(df_tasks, COL_CONCLUSAO)
    with st.expander("🔎 Diagnóstico (colunas e subtipos)"):
        st.markdown(f"**Coluna de prazo (atrasado):** `{col_prazo or '❌ NÃO ENCONTRADA'}`  ·  "
                    f"**Coluna de conclusão:** `{col_concl or '❌ NÃO ENCONTRADA'}`")
        if not col_prazo:
            st.warning("Sem coluna de prazo, 'Atrasados' fica 0 e tudo pendente vira 'Futuras'. "
                       "Me diga qual coluna abaixo é a Data conclusão prevista.")
        st.markdown("**Colunas disponíveis na vw_tasks_completa:**")
        st.write(sorted(df_tasks.columns.tolist()))
        if faltando:
            st.markdown("**Subtipos configurados que NÃO aparecem na base:**")
            for grupo, itens in faltando.items():
                st.markdown(f"*{grupo}*")
                for it in itens:
                    st.write("• ", it)


# ======================================================================
# EXEMPLO (fallback)
# ======================================================================
_EXEMPLO = {
    "setor": {"areas": [
        {"nome": "Agendamento",                "icone": "calendar",  "atrasados": 12, "pendDia": 8,  "pendFut": 35, "cumpridoDia": 7,  "cumpridoMes": 132},
        {"nome": "Agendamento Administrativo", "icone": "folder",    "atrasados": 18, "pendDia": 10, "pendFut": 42, "cumpridoDia": 9,  "cumpridoMes": 145},
        {"nome": "Acompanhamento ADM",         "icone": "shield",    "atrasados": 27, "pendDia": 14, "pendFut": 61, "cumpridoDia": 12, "cumpridoMes": 198},
        {"nome": "Denúncia",                   "icone": "megaphone", "atrasados": 5,  "pendDia": 3,  "pendFut": 12, "cumpridoDia": 2,  "cumpridoMes": 37},
    ]},
    "campeoes": [
        {"nome": "Mariana Lopes", "area": "", "pontos": 198},
        {"nome": "Rafael Souza",  "area": "", "pontos": 145},
        {"nome": "Carla Mendes",  "area": "", "pontos": 132},
        {"nome": "João Pereira",  "area": "", "pontos": 94},
        {"nome": "Beatriz Alves", "area": "", "pontos": 81},
        {"nome": "Diego Ramos",   "area": "", "pontos": 69},
    ],
    "metaUnidade": {"meta": 780, "realizado": 703},
    "outrasUnidades": [
        {"nome": "Manaus",     "meta": 1200, "realizado": 1044},
        {"nome": "Parintins",  "meta": 540,  "realizado": 498},
        {"nome": "Manacapuru", "meta": 420,  "realizado": 301},
    ],
}
