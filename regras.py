# =====================================================================
# V360 MOLINA — REGRAS DE NEGÓCIO  (fonte única)
# =====================================================================
# Centraliza o que a diretoria já validou no LegalOne, pra as páginas
# não repetirem string solta. Datas já vêm convertidas p/ Manaus na
# camada data.py, então aqui é só comparar por dia.
# =====================================================================
import pandas as pd

STATUS_ABERTO = ["Pendente", "Não cumprido", "Iniciado"]
STATUS_CUMPRIDO = "Cumprido"

INDICADOR_ABERTAS = "Pastas abertas"
INDICADOR_ENVIADAS = "Pastas enviadas"

# 3 subtipos reais (atenção ao hífen colado em "Análise- Cível")
SUB_PENDENCIA_ANALISE = [
    "Pendência na Análise", "Pendência na Análise - ADM", "Pendência na Análise- Cível",
]
SUB_PROTOCOLO = ["Inicial enviada ao protocolo", "Inicial enviada ao protocolo - Cível"]

# etapas do funil (rótulo -> subtipo_nome)
ETAPAS = [
    ("Análise",     ["Enviado p/ Análise", "Enviado p/ Análise ADM"]),
    ("Confecção",   ["Enviada p/ Confecção"]),
    ("Revisão",     ["Revisão"]),
    ("Protocolo",   ["Protocolo"]),
    ("Agendamento", ["Enviado p/ Agendamento"]),
]


def entre(df: pd.DataFrame, col: str, ini, fim) -> pd.DataFrame:
    """Linhas cujo `col` (datetime Manaus) cai no intervalo [ini, fim] por dia."""
    if col not in df.columns:
        return df.iloc[0:0]
    # compara com Timestamp (não .dt.date): robusto a série vazia (datetime64[s])
    s = pd.to_datetime(df[col], errors="coerce")
    return df[s.notna() & (s >= pd.Timestamp(ini)) & (s < pd.Timestamp(fim) + pd.Timedelta(days=1))]


def abertas(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df.get("entra_meta") == True) &
              (df.get("indicador_meta") == INDICADOR_ABERTAS) &
              (df.get("status_nome") == STATUS_CUMPRIDO)]


def enviadas(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df.get("entra_meta") == True) &
             (df.get("indicador_meta") == INDICADOR_ENVIADAS)]


def em_aberto(df: pd.DataFrame) -> pd.DataFrame:
    return df[df.get("status_nome").isin(STATUS_ABERTO)]


def cumpridas(df: pd.DataFrame) -> pd.DataFrame:
    return df[df.get("status_nome") == STATUS_CUMPRIDO]


def pendencias_analise(df: pd.DataFrame) -> pd.DataFrame:
    return df[df.get("subtipo_nome").isin(SUB_PENDENCIA_ANALISE) &
             df.get("status_nome").isin(STATUS_ABERTO)]


def top(df: pd.DataFrame, col: str):
    """(rótulo, qtd, %do total) do item mais frequente, ou (None, 0, 0)."""
    if df.empty or col not in df.columns:
        return None, 0, 0.0
    vc = df[df[col].notna()][col].value_counts()
    if vc.empty:
        return None, 0, 0.0
    total = int(vc.sum())
    return str(vc.index[0]), int(vc.iloc[0]), (vc.iloc[0] / total * 100 if total else 0.0)
