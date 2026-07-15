# =====================================================================
# V360 MOLINA — GRÁFICOS REUTILIZÁVEIS  (todos no tema dark)
# =====================================================================
# Barras por unidade/coluna, barra horizontal e barras agrupadas
# (pendente x cumprido). Todos passam por theme.layout, então saem
# com a mesma cara dark dos painéis.
# =====================================================================
import pandas as pd
import plotly.express as px

import theme as t


def _contagem(df: pd.DataFrame, col: str, limite: int) -> pd.DataFrame:
    if df.empty or col not in df.columns:
        return pd.DataFrame(columns=[col, "total"])
    return (df[df[col].notna()].groupby(col).size()
            .reset_index(name="total").sort_values("total", ascending=False).head(limite))


def barras(df, col, cor=t.NEUTRO, limite=30, altura=420, titulo=""):
    """Barras verticais por `col` (ex.: unidade_nome)."""
    g = _contagem(df, col, limite)
    if g.empty:
        return None
    tit = titulo or f"TOTAL {t.fmt(g['total'].sum())}"
    fig = px.bar(g, x=col, y="total", text="total")
    fig.update_traces(marker_color=cor, textposition="outside", cliponaxis=False,
                      textfont_color=t.CORES["ink"])
    return t.layout(fig, altura, tit)


def barras_h(df, col, cor=t.NEUTRO, limite=15, altura=420, titulo=""):
    """Barras horizontais por `col` (ex.: subtipo_nome, usuario_executor)."""
    g = _contagem(df, col, limite)
    if g.empty:
        return None
    tit = titulo or f"TOTAL {t.fmt(g['total'].sum())}"
    fig = px.bar(g, x="total", y=col, orientation="h", text="total")
    fig.update_traces(marker_color=cor, textposition="outside", cliponaxis=False,
                      textfont_color=t.CORES["ink"])
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return t.layout(fig, altura, tit)


def pendente_cumprido(pend, cump, col="unidade_nome", limite=25, altura=460):
    """Barras agrupadas Pendente(laranja) x Cumprido(verde) por unidade."""
    g = (pd.concat([
            pend.groupby(col).size().rename("Pendente"),
            cump.groupby(col).size().rename("Cumprido"),
         ], axis=1).fillna(0).reset_index())
    if g.empty:
        return None
    g = g.sort_values("Pendente", ascending=False).head(limite)
    longo = g.melt(id_vars=col, var_name="Situação", value_name="Qtd")
    tit = f"Pendente: {t.fmt(g['Pendente'].sum())}  ·  Cumprido: {t.fmt(g['Cumprido'].sum())}"
    fig = px.bar(longo, x=col, y="Qtd", color="Situação", text="Qtd", barmode="group",
                 color_discrete_map={"Pendente": t.ABERTO, "Cumprido": t.CUMPRIDO})
    fig.update_traces(textposition="outside", cliponaxis=False, textfont_color=t.CORES["ink"])
    return t.layout(fig, altura, tit)
