# =====================================================================
# V360 MOLINA — EXPORT EXCEL  (com mascaramento de dados sensíveis)
# =====================================================================
# Gera um .xlsx com uma aba por recorte. Defesa em profundidade: mesmo
# que alguma coluna sensível vaze pra cá, ela é removida/mascarada antes
# de escrever (CPF/NB/senha do INSS nunca saem no export — seção 7).
# =====================================================================
import io
import re

import pandas as pd
import streamlit as st

COLS_SENSIVEIS = {"notes", "description", "notas", "descricao", "observacao", "observacoes"}


def _mascarar(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.drop(columns=[c for c in df.columns if c.lower() in COLS_SENSIVEIS],
                  errors="ignore").copy()
    # varre colunas de texto restantes e mascara CPF / possíveis segredos
    for col in out.select_dtypes(include="object").columns:
        out[col] = out[col].astype(str).map(_limpar_texto)
    return out


def _limpar_texto(v: str) -> str:
    if not isinstance(v, str) or v == "nan":
        return "" if v == "nan" else v
    # CPF (000.000.000-00 ou 11 dígitos) → mascara
    v = re.sub(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", "***.***.***-**", v)
    # sequências longas de dígitos (NB/benefício) → mascara o miolo
    v = re.sub(r"\b\d{9,}\b", lambda m: m.group()[:2] + "…" + m.group()[-2:], v)
    return v


@st.cache_data(show_spinner=False)
def _montar_xlsx(abas: dict) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        vazio = True
        for nome, df in abas.items():
            limpo = _mascarar(df)
            if limpo.empty:
                continue
            limpo.to_excel(w, sheet_name=nome[:31], index=False)
            vazio = False
        if vazio:  # openpyxl exige ao menos uma aba
            pd.DataFrame({"info": ["Sem dados no recorte selecionado."]}).to_excel(
                w, sheet_name="Vazio", index=False)
    return buf.getvalue()


def botao_export(abas: dict, nome: str = "relatorio_v360"):
    """Renderiza o botão de download do Excel. `abas` = {nome_aba: DataFrame}."""
    try:
        conteudo = _montar_xlsx(abas)
    except Exception as e:
        st.warning(f"Não consegui gerar o Excel agora: {e}")
        return
    st.download_button(
        "⬇️  Baixar Excel", data=conteudo, file_name=f"{nome}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=False,
    )
