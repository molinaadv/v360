# -*- coding: utf-8 -*-
"""
PAINEL TV · ANÁLISE (setor de Pendência) — V360 Molina
TV corporativa do setor de Análise, com DADOS REAIS do Supabase.
Mesma estrutura visual do painel_template.html; cada um dos 6 subtipos
de pendência vira um cartão com Atrasados / Do dia / Futuras / Total /
Cumpridos do dia / Cumpridos do mês.

Colocar este arquivo em /pages (ao lado de painel_template.html).
Requer 'streamlit-autorefresh' no requirements.txt.
"""
import json
import datetime as dt
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from supabase import create_client

MINUTOS_SYNC = 5
ALTURA_TV    = 1040
UNIDADE_META = "ATRIUM"          # meta exibida na tela 3 (quando ligarmos)
UNIDADES_TELA2 = ["ATRIUM", "ONLINE"]   # pendências por unidade (tela 2) — nomes exatos da view
UNIDADES_META  = ["ATRIUM", "ONLINE"]   # tela 4 (velocímetros de meta) — nomes exatos da view

# 6 subtipos (SÓ o subtipo, sem o prefixo do tipo) — ordem dos cartões
SUBTIPOS = [
    "Pendência na Análise",
    "Pendência na Análise - ADM",
    "Pendência na Análise- Cível",
    "Pendência Agendamento",
    "Pendência na Confecção",
    "Pendência Resolvida",
]
ICONE = {
    "Pendência na Análise": "shield", "Pendência na Análise - ADM": "shield",
    "Pendência na Análise- Cível": "shield",
    "Pendência Agendamento": "calendar", "Pendência na Confecção": "folder",
    "Pendência Resolvida": "shield",
}
STATUS_ABERTO = ["Pendente", "Não cumprido", "Iniciado"]

st.set_page_config(page_title="TV Análise · V360", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=MINUTOS_SYNC * 60 * 1000, key="tv_analise_sync")
st.markdown("""
<style>
  #MainMenu, header, footer {visibility:hidden;}
  [data-testid="stSidebar"], [data-testid="collapsedControl"] {display:none;}
  .block-container {padding:0 !important; max-width:100% !important;}
  [data-testid="stAppViewContainer"] {background:#060b14;}
  iframe {border:none !important;}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# CÁLCULO DAS MÉTRICAS (funções puras — testáveis sem banco)
# ----------------------------------------------------------------------
def _dias(df: pd.DataFrame, col: str):
    """Série de datas normalizadas (meia-noite, sem fuso) — compatível com
    qualquer resolução/fuso do pandas. Coluna ausente vira tudo NaT."""
    if col not in df.columns:
        return pd.to_datetime(pd.Series([pd.NaT] * len(df), index=df.index))
    x = pd.to_datetime(df[col], errors="coerce")
    if getattr(x.dt, "tz", None) is not None:
        x = x.dt.tz_localize(None)
    return x.dt.normalize()


def _metricas_de(sub: pd.DataFrame, hoje: date, H, M):
    """Calcula os 6 números de um recorte (um subtipo OU uma unidade)."""
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
            "cumpridoDia": cump_dia, "cumpridoMes": cump_mes}


def _metricas(df: pd.DataFrame, hoje: date):
    H = pd.Timestamp(hoje); M = pd.Timestamp(date(hoje.year, hoje.month, 1))
    areas = []
    for nome in SUBTIPOS:
        m = _metricas_de(df[df["subtipo_nome"] == nome], hoje, H, M)
        areas.append({"nome": nome, "icone": ICONE.get(nome, "folder"), **m})
    return areas


def _pend_por_unidade(df: pd.DataFrame, hoje: date, unidades):
    """Tela 2 — pendências dos 5 subtipos, somadas por unidade."""
    H = pd.Timestamp(hoje); M = pd.Timestamp(date(hoje.year, hoje.month, 1))
    areas = []
    for u in unidades:
        m = _metricas_de(df[df["unidade_nome"] == u], hoje, H, M)
        areas.append({"nome": u, "icone": "building", **m})
    return areas


def _campeoes(df: pd.DataFrame, hoje: date):
    """Quem mais cumpriu nos 6 subtipos no mês vigente."""
    H = pd.Timestamp(hoje)
    M = pd.Timestamp(date(hoje.year, hoje.month, 1))
    cump = df[df["status_nome"] == "Cumprido"].copy()
    if cump.empty or "usuario_executor" not in cump.columns:
        return []
    dc = _dias(cump, "data_conclusao")
    cump = cump[(dc >= M) & (dc <= H)]
    cump = cump[cump["usuario_executor"].notna()]
    if cump.empty:
        return []
    g = cump.groupby("usuario_executor").size().sort_values(ascending=False)
    return [{"nome": n, "area": "Análise", "pontos": int(q)} for n, q in g.items()]


def _meta(df_metas: pd.DataFrame, unidade: str, hoje: date):
    """Meta da unidade (soma abertas+enviadas) + outras unidades."""
    base = {"unidade": unidade, "metaUnidade": {"meta": 0, "realizado": 0}, "outras": []}
    if df_metas is None or df_metas.empty:
        return base
    m = df_metas.groupby("unidade_principal").agg(
        meta=("meta_abertas", "sum"), real_ab=("abertas_realizadas", "sum"),
        meta_env=("meta_enviadas", "sum"), real_env=("enviadas_realizadas", "sum")).reset_index()
    m["meta_tot"] = m["meta"] + m["meta_env"]
    m["real_tot"] = m["real_ab"] + m["real_env"]
    linha = m[m["unidade_principal"] == unidade]
    if not linha.empty:
        r = linha.iloc[0]
        base["metaUnidade"] = {"meta": int(r["meta_tot"]), "realizado": int(r["real_tot"])}
    outras = m[m["unidade_principal"] != unidade].sort_values("real_tot", ascending=False).head(4)
    base["outras"] = [{"nome": r["unidade_principal"], "meta": int(r["meta_tot"]),
                       "realizado": int(r["real_tot"])} for _, r in outras.iterrows()]
    return base


def _metas_velocimetros(df_metas: pd.DataFrame, unidades):
    """Tela 4 — para cada unidade, 2 velocímetros: Abertas e Enviadas.
    Cada gauge tem meta, realizado e pct (pode passar de 100%)."""
    saida = []
    if df_metas is None or df_metas.empty:
        # devolve estrutura zerada para a tela não quebrar
        for u in unidades:
            saida.append({"unidade": u,
                          "abertas":  {"meta": 0, "realizado": 0, "pct": 0},
                          "enviadas": {"meta": 0, "realizado": 0, "pct": 0}})
        return saida

    m = df_metas.groupby("unidade_principal").agg(
        meta_ab=("meta_abertas", "sum"),  real_ab=("abertas_realizadas", "sum"),
        meta_en=("meta_enviadas", "sum"), real_en=("enviadas_realizadas", "sum"),
    ).reset_index()

    def _pct(real, meta):
        return int(round(real / meta * 100)) if meta and meta > 0 else 0

    for u in unidades:
        linha = m[m["unidade_principal"] == u]
        if linha.empty:
            saida.append({"unidade": u,
                          "abertas":  {"meta": 0, "realizado": 0, "pct": 0},
                          "enviadas": {"meta": 0, "realizado": 0, "pct": 0}})
            continue
        r = linha.iloc[0]
        ma, ra = int(r["meta_ab"]), int(r["real_ab"])
        me, re_ = int(r["meta_en"]), int(r["real_en"])
        saida.append({
            "unidade": u,
            "abertas":  {"meta": ma, "realizado": ra, "pct": _pct(ra, ma)},
            "enviadas": {"meta": me, "realizado": re_, "pct": _pct(re_, me)},
        })
    return saida


def _campeoes_por_subtipo(df: pd.DataFrame, hoje: date):
    """Opção B — por subtipo, campeão da semana (seg→hoje) e do mês."""
    ini_sem = hoje - dt.timedelta(days=hoje.weekday())        # segunda-feira
    S = pd.Timestamp(ini_sem)
    M = pd.Timestamp(date(hoje.year, hoje.month, 1))
    H = pd.Timestamp(hoje)
    cump = df[(df["status_nome"] == "Cumprido") & df["usuario_executor"].notna()]

    def _top(sub, ini):
        if sub.empty:
            return {"nome": "—", "qtd": 0}
        dc = _dias(sub, "data_conclusao")
        janela = sub[(dc >= ini) & (dc <= H)]
        if janela.empty:
            return {"nome": "—", "qtd": 0}
        g = janela.groupby("usuario_executor").size().sort_values(ascending=False)
        return {"nome": str(g.index[0]), "qtd": int(g.iloc[0])}

    out = []
    for nome in SUBTIPOS:
        sub = cump[cump["subtipo_nome"] == nome]
        out.append({"subtipo": nome, "semana": _top(sub, S), "mes": _top(sub, M)})
    return out


def _montar_dados(df_tasks, df_metas, hoje):
    areas = _metricas(df_tasks, hoje)
    areas_uni = _pend_por_unidade(df_tasks, hoje, UNIDADES_TELA2)
    camp_sub = _campeoes_por_subtipo(df_tasks, hoje)
    meta = _meta(df_metas, UNIDADE_META, hoje)
    metas_gauges = _metas_velocimetros(df_metas, UNIDADES_META)
    return {
        "setor": {"nome": "Análise", "titulo": "Painel Operacional · Análise", "areas": areas},
        "setor2": {"titulo": "Pendências por Unidade", "areas": areas_uni},
        "campeoesSubtipo": camp_sub,
        "metasUnidades": metas_gauges,     # tela 4 (velocímetros)
        "unidade": meta["unidade"],
        "metaUnidade": meta["metaUnidade"],
        "outrasUnidades": meta["outras"],
        "segundosPorTela": [30, 15, 25, 25],   # tela1=30s · tela2=15s · tela3=25s · tela4=25s
        "minutosAtualizacao": MINUTOS_SYNC,
        "fonteDados": "Legal One API", "atualizarSupabaseMin": 0,
    }


# ----------------------------------------------------------------------
# CARGA DO SUPABASE
# ----------------------------------------------------------------------
@st.cache_resource
def _sb():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


@st.cache_data(ttl=MINUTOS_SYNC * 60, show_spinner=False)
def carregar_dados() -> dict:
    sb = _sb()
    # só as tarefas dos 6 subtipos (subconjunto pequeno)
    registros, ini = [], 0
    while True:
        resp = sb.table("vw_tasks_completa").select("*").in_("subtipo_nome", SUBTIPOS)\
                 .range(ini, ini + 999).execute()
        dados = resp.data or []
        registros.extend(dados)
        if len(dados) < 1000:
            break
        ini += 1000
    df = pd.DataFrame(registros)
    metas = pd.DataFrame(sb.table("vw_v360_metas_vs_meta").select("*").execute().data or [])
    if not metas.empty and "mes_referencia" in metas.columns:
        hoje = date.today()
        mref = pd.to_datetime(metas["mes_referencia"], errors="coerce")
        metas = metas[(mref.dt.year == hoje.year) & (mref.dt.month == hoje.month)]
    if df.empty:
        df = pd.DataFrame(columns=["subtipo_nome", "status_nome", "deadline",
                                   "data_conclusao", "usuario_executor"])
    return _montar_dados(df, metas, date.today())


# ----------------------------------------------------------------------
# RENDER
# ----------------------------------------------------------------------
try:
    dados = carregar_dados()
except Exception as e:
    st.error("Falha ao carregar dados do Supabase para a TV de Análise.")
    st.exception(e)
    st.stop()

template = Path(__file__).with_name("painel_template.html").read_text(encoding="utf-8")
html = template.replace("/*__DADOS__*/", "const DADOS = " + json.dumps(dados, ensure_ascii=False) + ";")
components.html(html, height=ALTURA_TV, scrolling=False)
