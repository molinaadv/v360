# =====================================================================
# V360 MOLINA — COLABORADORES  (dark)
# =====================================================================
import plotly.express as px
import streamlit as st

import theme as t


def render(df_colabs):
    t.titulo("👥 COLABORADORES", "Metas e produtividade por colaborador.")
    if df_colabs is None or df_colabs.empty:
        st.info("Sem dados de colaboradores.")
        return

    c1, c2 = st.columns(2)
    with c1:
        top_meta = df_colabs.sort_values("meta_mes_atual", ascending=False).head(20)
        fig = px.bar(top_meta, x="meta_mes_atual", y="colaborador", orientation="h",
                     text="meta_mes_atual")
        fig.update_traces(marker_color=t.NEUTRO, textfont_color=t.CORES["ink"])
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(t.layout(fig, 520, "Top — Metas no mês"), use_container_width=True)
    with c2:
        top_prod = df_colabs.sort_values("total_produtividade", ascending=False).head(20)
        fig = px.bar(top_prod, x="total_produtividade", y="colaborador", orientation="h",
                     text="total_produtividade")
        fig.update_traces(marker_color=t.CORES["roxo"], textfont_color=t.CORES["ink"])
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(t.layout(fig, 520, "Top — Produtividade total"), use_container_width=True)

    cols = [c for c in ["colaborador", "unidade_nome", "total_tarefas", "cumprido",
                        "pendente", "total_meta", "meta_mes_atual"] if c in df_colabs.columns]
    st.dataframe(df_colabs[cols].sort_values(cols[-1], ascending=False),
                 use_container_width=True, hide_index=True)
