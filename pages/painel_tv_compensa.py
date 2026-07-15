# -*- coding: utf-8 -*-
"""
PAINEL TV · PERÍCIAS & AUDIÊNCIAS — Núcleo Compensa (V360 Molina)
================================================================
Unidades: COMPENSA, AÇÃO COMPENSA.
Dados reais do Supabase (vw_tasks_completa).

4 telas rotativas:
  Tela 1 · GERAL        — agendadas abertas (qualquer data) + realizadas no mês
  Tela 2 · ESTA SEMANA  — eventos agendados nesta semana (seg→dom)
  Tela 3 · ESTE MÊS     — eventos agendados neste mês
  Tela 4 · REALIZAÇÃO   — velocímetro por unidade (realizadas ÷ agendadas do mês)

A unidade é lida do PRÓPRIO subtipo (parênteses), não do unidade_nome —
mais robusto. Ex.: "Perícia ADM (COMPENSA)".

Colocar este arquivo em /pages, ao lado de painel_template_compensa.html.
Requer 'streamlit-autorefresh' no requirements.txt.
"""
import re
import json
import datetime as dt
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from supabase import create_client

# ======================================================================
# CONFIG  — o que você mais provavelmente vai querer editar fica aqui
# ======================================================================
MINUTOS_SYNC = 5
ALTURA_TV    = 1040
NUCLEO_LABEL = "Compensa"      # nome do núcleo exibido nas telas

# >>> COLUNA DA DATA DO EVENTO = CONCLUSÃO PREVISTA <<<
# É a data que a Justiça informa para a audiência/perícia — no LegalOne é a
# "Data final", que no banco é `end_datetime`. É por ela que se contabiliza:
#  - Compromissos (Audiência/Perícia JUD): início == final == dia do evento.
#  - Tarefas (Perícia ADM): o início pode ser meses antes; o que vale é o final.
# A HORA exibida no calendário continua vindo do início (coluna "Hora início").
COL_EVENTO = "end_datetime"

# Unidades do núcleo (nomes EXATOS como aparecem entre parênteses no subtipo)
# <<< CONFERIR estes nomes EXATOS na coluna vw_tasks_completa.unidade_nome
UNIDADES = [
    "COMPENSA",
    "AÇÃO COMPENSA",
]

# Nome curto para caber na TV
UNI_CURTO = {
    "COMPENSA": "COMPENSA",
    "AÇÃO COMPENSA": "AÇÃO COMPENSA",
}

# ---------------------------------------------------------------------
# ESCOPOS POR SEÇÃO (podem diferir) — CONFERIR nomes exatos na view
#   Perícias (telas 1-4) ....... UNIDADES (as 5 acima)
#   Pendências + Pastas (5,6,7) . UNIDADES_PEND
#   Meta (tela 8) .............. UNIDADES_META
# ---------------------------------------------------------------------
UNIDADES_PEND = ["COMPENSA", "AÇÃO COMPENSA"]   # <<< CONFERIR nomes exatos
UNIDADES_META = ["COMPENSA"]                        # <<< meta só Compensa

# "Exigência" (Perícia ADM Exigência, Avaliação Social ADM Exigência, ...) é
# um PRAZO (start == end no fim do dia), NÃO um evento agendado. Por padrão
# TODA exigência fica de fora. Ponha True p/ contá-las nas suas categorias.
INCLUIR_EXIGENCIA = False

# Exigências que DEVEM entrar no dashboard, mesmo com INCLUIR_EXIGENCIA=False
# (exceção à regra "exigência = prazo"). Contadas na categoria do seu prefixo.
EXIGENCIA_OK = ["Avaliação Social ADM Exigência"]

# Categorias de EVENTO (o que o painel conta), por prefixo do subtipo.
# Ordem = mais específico primeiro (ex.: "Avaliação Social ADM" antes de
# "Avaliação Social"). Uma linha "Exigência" é filtrada à parte (acima).
_BASE = [
    ("Avaliação Social ADM", "avaliacao"),
    ("Avaliação Social",     "avaliacao"),
    ("Perícia JUD",          "pericia"),
    ("Perícia ADM",          "pericia"),
    ("Audiência",            "audiencia"),
]

STATUS_ABERTO = ["Pendente", "Não cumprido", "Iniciado"]

# Subtipos consultados no banco = base × unidades (+ variantes " Exigência"
# só quando ligado). Lista explícita p/ o .in_() — 100% confiável.
SUBTIPOS = []
for _pref, _cat in _BASE:
    for _u in UNIDADES:
        SUBTIPOS.append(f"{_pref} ({_u})")
        if INCLUIR_EXIGENCIA:
            SUBTIPOS.append(f"{_pref} Exigência ({_u})")
# Exigências específicas permitidas (mesmo com INCLUIR_EXIGENCIA=False)
for _pref in EXIGENCIA_OK:
    for _u in UNIDADES:
        SUBTIPOS.append(f"{_pref} ({_u})")

# ======================================================================
# PENDÊNCIAS + PASTAS ABERTAS (Telas 5, 6, 7) — CONFERIR NOMES LETRA-A-LETRA
# Estes subtipos batem EXATAMENTE com a coluna vw_tasks_completa.subtipo_nome
# (acento, hífen e espaços importam). Filtro de unidade usa `unidade_nome`.
# ======================================================================
SUB_PENDENCIAS = [
    "Pendência na Análise",
    "Pendência na Análise - ADM",
    "Pendência na Análise- Cível",           # <- hífen colado em "Análise-"
    "Pendência Agendamento",
    "Pendência na Confecção",
    "URGENTE - Solicitação de Documentos",   # <<< CONFERIR texto exato no LegalOne
]
_EMJ_PEND = {
    "Pendência na Análise": "🛡️",
    "Pendência na Análise - ADM": "🛡️",
    "Pendência na Análise- Cível": "🛡️",
    "Pendência Agendamento": "📅",
    "Pendência na Confecção": "📁",
    "URGENTE - Solicitação de Documentos": "🚨",
}
# Pastas abertas = subtipos "Enviado p/ Análise*" CUMPRIDOS, por data_conclusao.
SUB_PASTAS = [
    "Enviado p/ Análise ADM",
    "Enviado p/ Análise",
    "Enviado p/ Análise Cível",
]

_UNIT_RE = re.compile(r"\(([^)]+)\)")


# ======================================================================
# PÁGINA
# ======================================================================
st.set_page_config(page_title="Painel Compensa", layout="wide",
                   initial_sidebar_state="collapsed")
st_autorefresh(interval=MINUTOS_SYNC * 60 * 1000, key="tv_compensa_sync")
st.markdown("""
<style>
  #MainMenu, header, footer {visibility:hidden;}
  [data-testid="stSidebar"], [data-testid="collapsedControl"] {display:none;}
  /* --- esconder a barra/badge do Streamlit Cloud (foto + selo "coroa") --- */
  [data-testid="stToolbar"], [data-testid="stStatusWidget"], [data-testid="stDecoration"] {display:none !important;}
  [data-testid="stAppViewBadge"], [data-testid="manage-app-button"] {display:none !important;}
  [class*="viewerBadge"], [class*="_profileContainer"], [class*="_profileImage"], [class*="_link_"] {display:none !important;}
  a[href*="streamlit.io"], a[href*="share.streamlit.io"] {display:none !important;}
  .block-container {padding:0 !important; max-width:100% !important;}
  [data-testid="stAppViewContainer"] {background:#060b14;}
  iframe {border:none !important;}
</style>
""", unsafe_allow_html=True)


# ======================================================================
# CÁLCULO DAS MÉTRICAS (funções puras)
# ======================================================================
# Manaus é UTC-4 o ano todo (sem horário de verão). Converter garante que a
# hora e o DIA do evento saiam corretos (o banco guarda em UTC/+00).
_TZ = dt.timezone(dt.timedelta(hours=-4))


def _local(serie):
    """Converte uma série datetime (UTC/tz-aware) para hora local de Manaus,
    devolvendo tz-naive. Séries já sem fuso passam direto."""
    x = pd.to_datetime(serie, errors="coerce")
    if getattr(x.dt, "tz", None) is not None:
        x = x.dt.tz_convert(_TZ).dt.tz_localize(None)
    return x


def _dias(df: pd.DataFrame, col: str):
    """Série de datas locais normalizadas (meia-noite). Coluna ausente -> NaT."""
    if col not in df.columns:
        return pd.to_datetime(pd.Series([pd.NaT] * len(df), index=df.index))
    return _local(df[col]).dt.normalize()


def _classifica(subtipo):
    """(unidade, categoria) a partir do nome do subtipo. Ex.:
       'Perícia ADM (COMPENSA)' -> ('COMPENSA', 'pericia')."""
    if not isinstance(subtipo, str):
        return (None, None)
    m = _UNIT_RE.search(subtipo)
    unidade = m.group(1).strip() if m else None
    if unidade not in UNIDADES:
        return (None, None)
    if ("Exigência" in subtipo) and not INCLUIR_EXIGENCIA \
            and not any(subtipo.startswith(pp) for pp in EXIGENCIA_OK):
        return (unidade, None)          # exigência = prazo, não evento
    for pref, cat in _BASE:
        if subtipo.startswith(pref):
            return (unidade, cat)
    return (unidade, None)


def _janelas(hoje: date):
    ini_sem = hoje - dt.timedelta(days=hoje.weekday())          # segunda
    fim_sem = ini_sem + dt.timedelta(days=6)                    # domingo
    ini_mes = date(hoje.year, hoje.month, 1)
    if hoje.month == 12:
        fim_mes = date(hoje.year, 12, 31)
    else:
        fim_mes = date(hoje.year, hoje.month + 1, 1) - dt.timedelta(days=1)
    return {k: pd.Timestamp(v) for k, v in dict(
        H=hoje, IS=ini_sem, FS=fim_sem, IM=ini_mes, FM=fim_mes).items()}


def _montar_areas(df: pd.DataFrame, hoje: date, escopo: str):
    """escopo ∈ {'geral','semana','mes'}. Um card por unidade."""
    J = _janelas(hoje)
    ev  = _dias(df, COL_EVENTO)
    dc  = _dias(df, "data_conclusao")
    ab  = df["status_nome"].isin(STATUS_ABERTO)
    cmp = df["status_nome"] == "Cumprido"

    if escopo == "semana":
        jan_agenda = (ev >= J["IS"]) & (ev <= J["FS"])
        jan_real   = (dc >= J["IS"]) & (dc <= J["FS"])
    elif escopo == "mes":
        jan_agenda = (ev >= J["IM"]) & (ev <= J["FM"])
        jan_real   = (dc >= J["IM"]) & (dc <= J["FM"])
    else:  # geral
        jan_agenda = pd.Series(True, index=df.index)
        jan_real   = (dc >= J["IM"]) & (dc <= J["FM"])

    areas = []
    for u in UNIDADES:
        mu = df["unidade_calc"] == u
        agendadas = df[mu & ab & jan_agenda]
        cat = agendadas["categoria"]
        areas.append({
            "nome": UNI_CURTO.get(u, u), "icone": "building",
            "pericia":    int((cat == "pericia").sum()),
            "audiencia":  int((cat == "audiencia").sum()),
            "avaliacao":  int((cat == "avaliacao").sum()),
            "realizadas": int((mu & cmp & jan_real).sum()),
            "atrasadas":  int((mu & ab & (ev < J["H"])).sum()),
        })
    return areas


def _produtividade(df: pd.DataFrame, hoje: date):
    """Tela 4 — perícias/audiências CONCLUÍDAS no mês (por data_conclusao),
    por unidade, com quebra por categoria."""
    J = _janelas(hoje)
    dc  = _dias(df, "data_conclusao")
    cmp = df["status_nome"] == "Cumprido"
    base = cmp & (dc >= J["IM"]) & (dc <= J["FM"])
    out = []
    for u in UNIDADES:
        sel = df[(df["unidade_calc"] == u) & base]
        cat = sel["categoria"]
        out.append({
            "unidade":   UNI_CURTO.get(u, u),
            "pericia":   int((cat == "pericia").sum()),
            "audiencia": int((cat == "audiencia").sum()),
            "avaliacao": int((cat == "avaliacao").sum()),
            "total":     int(len(sel)),
        })
    return out


def _tipo_evento(subtipo: str) -> str:
    """Rótulo curto do evento a partir do subtipo (JUD/ADM/etc.)."""
    if subtipo.startswith("Perícia JUD"):
        return "Perícia JUD"
    if subtipo.startswith("Perícia ADM"):
        return "Perícia ADM"
    if subtipo.startswith("Audiência"):
        return "Audiência"
    if subtipo.startswith("Avaliação"):
        return "Aval. Social"
    return "Evento"


def _nome_curto(nome) -> str:
    """Nome do cliente enxuto p/ a TV: primeiro + último (title case).
    Qualquer coisa que não seja string (None, NaN) vira ''."""
    if not isinstance(nome, str):
        return ""
    partes = [w for w in nome.strip().split() if w]
    if not partes:
        return ""
    curto = partes[0] if len(partes) == 1 else f"{partes[0]} {partes[-1]}"
    return curto.title()


def _eventos(df: pd.DataFrame, hoje: date, escopo: str):
    """Lista de eventos (dicts) no escopo (semana|mes), ordenados por data/hora.
    Dia = conclusão prevista (COL_EVENTO / end_datetime); hora exibida = início
    (Hora início). Cada dict alimenta o calendário no HTML."""
    if df.empty:
        return []
    J = _janelas(hoje)
    prev_dia = _dias(df, COL_EVENTO)          # dia da conclusão prevista (bucket)
    prev_dt  = _local(df[COL_EVENTO])          # datetime da conclusão prevista
    ini_dt   = _local(df["start_datetime"]) if "start_datetime" in df.columns \
               else prev_dt                    # datetime do início (p/ a hora)
    if escopo == "semana":
        mask = (prev_dia >= J["IS"]) & (prev_dia <= J["FS"])
    else:
        mask = (prev_dia >= J["IM"]) & (prev_dia <= J["FM"])

    sub = df[mask]
    if sub.empty:
        return []
    H = pd.Timestamp(hoje)

    eventos = []
    for idx, row in sub.iterrows():
        d = prev_dia.loc[idx]                  # dia (meia-noite) da conclusão prevista
        if pd.isna(d):
            continue
        h = ini_dt.loc[idx]                    # hora vem do início
        if pd.isna(h):
            h = prev_dt.loc[idx]               # sem início? usa a da conclusão prevista
        st = row["status_nome"]
        if st == "Cumprido":
            status = "feito"
        elif d < H:
            status = "atrasado"
        else:
            status = "pendente"
        eventos.append({
            "data": d.strftime("%Y-%m-%d"),
            "hora": h.strftime("%H:%M") if pd.notna(h) else "",
            "tipo": _tipo_evento(row["subtipo_nome"]),
            "cat":  row["categoria"],
            "unidade": UNI_CURTO.get(row["unidade_calc"], row["unidade_calc"]),
            "cliente": _nome_curto(row.get("cliente")),
            "status": status,
        })
    eventos.sort(key=lambda e: (e["data"], e["hora"]))
    return eventos


def _iso(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def _metas_pastas(df_metas):
    """Tela 5 — meta de pastas Abertas/Enviadas por unidade (mês vigente/último)."""
    def _pct(real, meta):
        return int(round(real / meta * 100)) if meta and meta > 0 else 0

    vazio = lambda: {"meta": 0, "real": 0, "pct": 0, "tem": False}
    saida = []
    grupo = None
    if df_metas is not None and not df_metas.empty \
            and "unidade_principal" in df_metas.columns:
        grupo = df_metas.groupby("unidade_principal").agg(
            ma=("meta_abertas", "sum"),  ra=("abertas_realizadas", "sum"),
            me=("meta_enviadas", "sum"), rn=("enviadas_realizadas", "sum"),
        ).reset_index()

    for u in UNIDADES_META:
        item = {"unidade": UNI_CURTO.get(u, u),
                "abertas": vazio(), "enviadas": vazio()}
        if grupo is not None:
            linha = grupo[grupo["unidade_principal"] == u]
            if not linha.empty:
                r = linha.iloc[0]
                ma, ra = int(r["ma"]), int(r["ra"])
                me, rn = int(r["me"]), int(r["rn"])
                item["abertas"]  = {"meta": ma, "real": ra, "pct": _pct(ra, ma), "tem": ma > 0}
                item["enviadas"] = {"meta": me, "real": rn, "pct": _pct(rn, me), "tem": me > 0}
        saida.append(item)
    return saida


def _pend_numeros(sub: pd.DataFrame, hoje: date) -> dict:
    """Os 6 números de um recorte de pendências (por subtipo OU por unidade)."""
    H = pd.Timestamp(hoje)
    M = pd.Timestamp(date(hoje.year, hoje.month, 1))
    aberto = sub[sub["status_nome"].isin(STATUS_ABERTO)]
    dl = _dias(aberto, "deadline")
    atrasados = int((dl < H).sum())
    pend_dia  = int((dl == H).sum())
    pend_fut  = int(len(aberto) - atrasados - pend_dia)
    cump = sub[sub["status_nome"] == "Cumprido"]
    dc = _dias(cump, "data_conclusao")
    cump_dia = int((dc == H).sum())
    cump_mes = int(((dc >= M) & (dc <= H)).sum())
    return {"atrasados": atrasados, "pendDia": pend_dia, "pendFut": pend_fut,
            "total": int(len(aberto)), "cumpridoDia": cump_dia, "cumpridoMes": cump_mes}


def _pend_por_subtipo(dfp: pd.DataFrame, hoje: date):
    """Tela 5 — um card por subtipo de pendência (os 6 tipos)."""
    out = []
    for s in SUB_PENDENCIAS:
        m = _pend_numeros(dfp[dfp["subtipo_nome"] == s], hoje)
        out.append({"nome": s, "emj": _EMJ_PEND.get(s, "🛡️"),
                    "urgente": s.startswith("URGENTE"), **m})
    return out


def _pend_por_unidade_nome(dfp: pd.DataFrame, hoje: date):
    """Tela 6 — um card por unidade (soma dos 6 subtipos naquela unidade)."""
    out = []
    for u in UNIDADES_PEND:
        m = _pend_numeros(dfp[dfp["unidade_nome"] == u], hoje)
        out.append({"nome": UNI_CURTO.get(u, u), "emj": "🏢", **m})
    return out


def _pastas_abertas(dfp: pd.DataFrame, hoje: date) -> dict:
    """Tela 7 — pastas abertas (Enviado p/ Análise* cumpridas) por unidade,
    contadas por data_conclusao: Semana (segunda→hoje) e Mês (1º→hoje)."""
    H = pd.Timestamp(hoje)
    ini_sem = hoje - dt.timedelta(days=hoje.weekday())      # segunda
    S = pd.Timestamp(ini_sem)
    M = pd.Timestamp(date(hoje.year, hoje.month, 1))
    base = dfp[(dfp["subtipo_nome"].isin(SUB_PASTAS)) &
               (dfp["status_nome"] == "Cumprido")]
    dc = _dias(base, "data_conclusao")
    areas, tot_s, tot_m = [], 0, 0
    for u in UNIDADES_PEND:
        mu = (base["unidade_nome"] == u)
        sem = int(((dc >= S) & (dc <= H) & mu).sum())
        mes = int(((dc >= M) & (dc <= H) & mu).sum())
        tot_s += sem
        tot_m += mes
        areas.append({"nome": UNI_CURTO.get(u, u), "semana": sem, "mes": mes})
    return {"titulo": "Pastas Abertas", "areas": areas,
            "totalSemana": tot_s, "totalMes": tot_m}


def _campeoes_por_subtipo(dfp: pd.DataFrame, hoje: date):
    """Tela · DESTAQUE POR ASSUNTO — por subtipo de pendência, o executor que
    mais cumpriu na SEMANA (seg→hoje) e no MÊS (1º→hoje). Se a coluna
    usuario_executor não existir na view, devolve tudo "—"/0 (não quebra)."""
    ini_sem = hoje - dt.timedelta(days=hoje.weekday())      # segunda
    S = pd.Timestamp(ini_sem)
    M = pd.Timestamp(date(hoje.year, hoje.month, 1))
    H = pd.Timestamp(hoje)
    vazio = {"nome": "—", "qtd": 0}
    if dfp is None or dfp.empty or "usuario_executor" not in dfp.columns:
        return [{"subtipo": s, "emj": _EMJ_PEND.get(s, "🛡️"),
                 "semana": dict(vazio), "mes": dict(vazio)} for s in SUB_PENDENCIAS]
    cump = dfp[(dfp["status_nome"] == "Cumprido") & dfp["usuario_executor"].notna()]

    def _top(sub, ini):
        if sub.empty:
            return dict(vazio)
        dc = _dias(sub, "data_conclusao")
        janela = sub[(dc >= ini) & (dc <= H)]
        if janela.empty:
            return dict(vazio)
        g = janela.groupby("usuario_executor").size().sort_values(ascending=False)
        return {"nome": str(g.index[0]), "qtd": int(g.iloc[0])}

    out = []
    for nome in SUB_PENDENCIAS:
        sub = cump[cump["subtipo_nome"] == nome]
        out.append({"subtipo": nome, "emj": _EMJ_PEND.get(nome, "🛡️"),
                    "semana": _top(sub, S), "mes": _top(sub, M)})
    return out


def _montar_dados(df: pd.DataFrame, hoje: date,
                  df_metas=None, mes_meta: str = "", df_pend=None) -> dict:
    if df_pend is None:
        df_pend = pd.DataFrame(columns=["subtipo_nome", "unidade_nome",
                                        "status_nome", "deadline", "data_conclusao"])
    ini_sem = hoje - dt.timedelta(days=hoje.weekday())   # segunda
    return {
        # Tela 1 — números gerais (cards)
        "setor":  {"titulo": "Perícias & Audiências · Geral",
                   "areas": _montar_areas(df, hoje, "geral")},
        # Telas 2 e 3 — CALENDÁRIO
        "setor2": {"titulo": "Agenda da Semana"},
        "setor3": {"titulo": f"Agenda de {['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'][hoje.month-1]}"},
        "eventosSemana": _eventos(df, hoje, "semana"),
        "eventosMes":    _eventos(df, hoje, "mes"),
        "hojeISO":         _iso(hoje),
        "semanaInicioISO": _iso(ini_sem),
        "mesRef":          f"{hoje.year:04d}-{hoje.month:02d}",
        # Tela 4 — produtividade (concluídas no mês)
        "produtividadeUnidades": _produtividade(df, hoje),
        # Telas 5/6/7 — pendências (subtipo/unidade) + pastas abertas
        "pendSubtipo":  {"titulo": "Pendências por Subtipo",
                         "areas": _pend_por_subtipo(df_pend, hoje)},
        "pendUnidade":  {"titulo": "Pendências por Unidade",
                         "areas": _pend_por_unidade_nome(df_pend, hoje)},
        "pastasAbertas": _pastas_abertas(df_pend, hoje),
        # Tela · DESTAQUE POR ASSUNTO — campeões por subtipo (semana/mês)
        "campeoesSubtipo": _campeoes_por_subtipo(df_pend, hoje),
        # Tela — meta de pastas Abertas/Enviadas
        "metasPastas":  _metas_pastas(df_metas),
        "mesMetaLabel": mes_meta,
        "segundosPorTela": [25, 30, 30, 22, 22, 22, 25],
        "minutosAtualizacao": MINUTOS_SYNC,
        "nucleo": NUCLEO_LABEL,
        "fonteDados": "Legal One API", "atualizarSupabaseMin": 0,
    }


# ======================================================================
# CARGA DO SUPABASE
# ======================================================================
@st.cache_resource
def _sb():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def _clientes_map(sb, df) -> dict:
    """{lawsuit_id: contact_name} do cliente (Customer + is_main) para os
    processos das tarefas carregadas. Busca em lotes p/ não estourar a URL."""
    if df.empty or "lawsuit_id" not in df.columns:
        return {}
    ids = sorted({int(x) for x in df["lawsuit_id"].dropna().unique()})
    mapa = {}
    for i in range(0, len(ids), 300):
        lote = ids[i:i + 300]
        try:
            resp = (sb.table("legalone_participants")
                      .select("lawsuit_id,contact_name")
                      .in_("lawsuit_id", lote)
                      .eq("participant_type", "Customer")
                      .eq("is_main", True).execute())
        except Exception:
            continue
        for r in (resp.data or []):
            lid = r.get("lawsuit_id")
            if lid is not None and lid not in mapa:
                mapa[lid] = r.get("contact_name")
    return mapa


@st.cache_data(ttl=MINUTOS_SYNC * 60, show_spinner=False)
def carregar_dados(scope_key) -> dict:
    sb = _sb()
    registros, ini = [], 0
    while True:
        resp = (sb.table("vw_tasks_completa").select("*")
                  .in_("subtipo_nome", SUBTIPOS)
                  .range(ini, ini + 999).execute())
        dados = resp.data or []
        registros.extend(dados)
        if len(dados) < 1000:
            break
        ini += 1000

    df = pd.DataFrame(registros)
    if df.empty:
        df = pd.DataFrame(columns=["subtipo_nome", "status_nome",
                                   COL_EVENTO, "data_conclusao", "lawsuit_id"])
        df["unidade_calc"] = pd.Series(dtype=object)
        df["categoria"]    = pd.Series(dtype=object)
        df["cliente"]      = pd.Series(dtype=object)
    else:
        cls = df["subtipo_nome"].apply(_classifica)
        df["unidade_calc"] = cls.apply(lambda t: t[0])
        df["categoria"]    = cls.apply(lambda t: t[1])
        df = df[df["categoria"].notna()]     # só eventos das unidades configuradas
        _cli = _clientes_map(sb, df)
        if "lawsuit_id" in df.columns:
            df["cliente"] = df["lawsuit_id"].map(
                lambda x: _cli.get(int(x)) if pd.notna(x) else None)
        else:
            df["cliente"] = None

    # --- Tela 5: meta de pastas Abertas/Enviadas das 5 unidades ---
    metas = pd.DataFrame(
        sb.table("vw_v360_metas_vs_meta").select("*")
          .in_("unidade_principal", UNIDADES_META).execute().data or [])
    mes_meta = date.today().strftime("%m/%Y")
    if not metas.empty and "mes_referencia" in metas.columns:
        mref = pd.to_datetime(metas["mes_referencia"], errors="coerce")
        h = date.today()
        metas = metas[(mref.dt.year == h.year) & (mref.dt.month == h.month)]

    # --- Telas 5/6/7: pendências (6 subtipos) + pastas (Enviado p/ Análise*) ---
    # Filtro por subtipo_nome (plano) + unidade_nome (as 5 unidades do hub).
    sub_extra = SUB_PENDENCIAS + SUB_PASTAS
    reg2, ini2 = [], 0
    while True:
        r2 = (sb.table("vw_tasks_completa").select("*")
                .in_("subtipo_nome", sub_extra)
                .in_("unidade_nome", UNIDADES_PEND)
                .range(ini2, ini2 + 999).execute())
        d2 = r2.data or []
        reg2.extend(d2)
        if len(d2) < 1000:
            break
        ini2 += 1000
    df_pend = pd.DataFrame(reg2)
    if df_pend.empty:
        df_pend = pd.DataFrame(columns=["subtipo_nome", "unidade_nome",
                                        "status_nome", "deadline", "data_conclusao"])

    return _montar_dados(df, date.today(), metas, mes_meta, df_pend)


# ======================================================================
# RENDER
# ======================================================================
try:
    dados = carregar_dados(tuple(UNIDADES))
except Exception as e:
    st.error("Falha ao carregar dados do Supabase para a TV de Perícias & Audiências.")
    st.exception(e)
    st.stop()

template = Path(__file__).with_name("painel_template_compensa.html").read_text(encoding="utf-8")
html = template.replace("/*__DADOS__*/",
                        "const DADOS = " + json.dumps(dados, ensure_ascii=False) + ";")
components.html(html, height=ALTURA_TV, scrolling=False)
