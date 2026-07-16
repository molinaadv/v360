# =====================================================================
# V360 MOLINA — CAMADA DE DADOS  (Supabase / LegalOne)
# =====================================================================
# Foco: VELOCIDADE. Duas mudanças grandes vs. o app antigo:
#   1) Não usa mais select("*"). Cada view puxa só as colunas usadas.
#      Isso corta o payload (e nunca traz `notes`/`description`, que são
#      pesados e sensíveis — CPF/NB/senha do INSS).
#   2) Fuso America/Manaus centralizado aqui (seção 3 da base). Toda
#      derivação de dia/mês/semana passa por estas funções — nunca
#      date.today()/datetime.now() puros (no Streamlit Cloud isso é UTC).
#
# Ler pelas VIEWS, nunca pelas tabelas cruas.
# =====================================================================
from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from supabase import create_client

TZ = ZoneInfo("America/Manaus")          # UTC-4 fixo, sem horário de verão

# ---------------------------------------------------------------------
# COLUNAS POR VIEW  (allowlist — só o que as páginas realmente usam)
# Ajuste aqui se uma página nova precisar de outra coluna.
# ---------------------------------------------------------------------
COLUNAS: dict[str, list[str]] = {
    "vw_tasks_completa": [
        "id", "subtipo_nome", "status_nome", "status_id", "cumprida",
        "creation_date", "end_datetime", "effective_end_datetime",
        "data_conclusao", "mes_conclusao", "deadline",
        "usuario_executor", "usuario_criador", "responsavel_nome",
        "unidade_nome", "unidade_principal",
        "entra_meta", "indicador_meta", "setor_meta",
        # NUNCA incluir: notes, description  (sensíveis)
    ],
    "vw_v360_metas_vs_meta": [
        "unidade_principal", "mes_referencia",
        "meta_abertas", "abertas_realizadas",
        "meta_enviadas", "enviadas_realizadas",
    ],
    "vw_v360_colaboradores": [
        "colaborador", "unidade_nome", "total_tarefas", "cumprido",
        "pendente", "total_meta", "meta_mes_atual", "total_produtividade",
    ],
    # dashboard/unidades: colunas variam — deixo "*" como fallback seguro
    "vw_v360_dashboard": None,
    "vw_v360_unidades": None,
}

# Colunas timestamptz (UTC) que representam MOMENTO → convertem p/ Manaus.
# `deadline` fica de fora de propósito: é data de calendário (vencimento).
COLS_TIMESTAMP = [
    "creation_date", "end_datetime", "effective_end_datetime",
    "data_conclusao", "publish_date", "start_datetime",
]


# ---------------------------------------------------------------------
# CONEXÃO
# ---------------------------------------------------------------------
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


# ---------------------------------------------------------------------
# LEITURA PAGINADA  (cap de 1000 do PostgREST → loop com .range)
# ---------------------------------------------------------------------
def _select_cols(view: str) -> str:
    cols = COLUNAS.get(view)
    return "*" if not cols else ",".join(cols)


@st.cache_data(ttl=300, show_spinner=False)
def carregar_view(view: str, lote: int = 1000) -> pd.DataFrame:
    sb = get_supabase()
    sel = _select_cols(view)
    registros, inicio = [], 0
    while True:
        resp = sb.table(view).select(sel).range(inicio, inicio + lote - 1).execute()
        dados = resp.data or []
        if not dados:
            break
        registros.extend(dados)
        if len(dados) < lote:
            break
        inicio += lote
    df = pd.DataFrame(registros)
    return _normalizar(df)


def _normalizar(df: pd.DataFrame) -> pd.DataFrame:
    """Converte colunas de momento para datetime em horário de Manaus
    (tz-naive, já convertido), uma única vez no carregamento."""
    if df.empty:
        return df
    for col in COLS_TIMESTAMP:
        if col in df.columns:
            df[col] = para_manaus(df[col])
    return df


@st.cache_data(ttl=300, show_spinner="Carregando dados do LegalOne…")
def carregar_tudo():
    tasks = carregar_view("vw_tasks_completa")
    metas = carregar_view("vw_v360_metas_vs_meta")
    colabs = carregar_view("vw_v360_colaboradores")
    return tasks, metas, colabs


@st.cache_data(ttl=300, show_spinner=False)
def carregar_compromissos():
    """Audiências/perícias JUD. View pequena → select *; remove campos sensíveis.
    Retorna DataFrame vazio se a view não existir/der erro."""
    try:
        df = carregar_view("vw_compromissos_completa")
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df
    sens = {"notes", "description", "notas", "descricao", "observacao", "observacoes"}
    return df.drop(columns=[c for c in df.columns if c.lower() in sens], errors="ignore")


# ---------------------------------------------------------------------
# FUSO — America/Manaus  (seção 3 da base de conhecimento)
# ---------------------------------------------------------------------
def agora() -> datetime:
    """'Agora' correto em Manaus (nunca datetime.now() puro)."""
    return datetime.now(TZ)


def hoje() -> date:
    """'Hoje' correto em Manaus (nunca date.today() puro)."""
    return datetime.now(TZ).date()


def para_manaus(serie) -> pd.Series:
    """Coluna timestamptz (UTC) → datetime local de Manaus, tz-naive.
    Robusto a valores naive (assume UTC) e a lixo (vira NaT)."""
    s = pd.to_datetime(serie, errors="coerce", utc=True)
    return s.dt.tz_convert(TZ).dt.tz_localize(None)


def data_manaus(serie) -> pd.Series:
    """Só a data (normalizada) em Manaus — bom para comparar por dia."""
    return para_manaus(serie).dt.normalize()


def periodo_mes(ano: int, mes: int) -> tuple[date, date]:
    """Primeiro e último dia do mês (datas de calendário)."""
    ini = date(ano, mes, 1)
    prox = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
    return ini, prox - timedelta(days=1)
