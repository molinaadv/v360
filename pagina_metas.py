# =====================================================================
# V360 MOLINA — METAS  (atingimento por unidade, dark)
# =====================================================================
import pandas as pd
import plotly.express as px
import streamlit as st

import data
import theme as t
import regras as r
from export import botao_export

MAPA_STATUS = {"Meta batida": t.CUMPRIDO, "Perto da meta": t.ABERTO, "Longe da meta": t.ATRASADO}


def render(df_f, df_metas_f, ano: int, mes: int):
    ini, fim = data.periodo_mes(ano, mes)
    t.titulo("🎯 METAS",
             "Meta batida = unidade atingiu Pastas Abertas e Pastas Enviadas.",
             pills=[t.pill(f"Competência · {mes:02d}/{ano}", t.CORES['roxo'])])

    if df_metas_f is None or df_metas_f.empty:
        st.warning("Nenhuma meta encontrada para o período selecionado.")
        return

    rk = df_metas_f.groupby("unidade_principal").agg(
        meta_abertas=("meta_abertas", "sum"), abertas=("abertas_realizadas", "sum"),
        meta_enviadas=("meta_enviadas", "sum"), enviadas=("enviadas_realizadas", "sum"),
    ).reset_index()

    # Deferidas (Benefício ADM - Deferido criadas no mês) somam às enviadas
    defs = r.entre(df_f[df_f.get("subtipo_nome") == "Benefício ADM - Deferido"],
                   "creation_date", ini, fim).groupby("unidade_principal").size()
    rk["deferidas"] = rk["unidade_principal"].map(defs).fillna(0).astype(int)
    rk["enviadas_conf"] = rk["enviadas"]
    rk["enviadas"] = rk["enviadas"] + rk["deferidas"]

    rk["meta_total"] = rk["meta_abertas"] + rk["meta_enviadas"]
    rk["real_total"] = rk["abertas"] + rk["enviadas"]
    rk["pct_ab"] = (rk["abertas"] / rk["meta_abertas"].replace(0, pd.NA) * 100).fillna(0)
    rk["pct_en"] = (rk["enviadas"] / rk["meta_enviadas"].replace(0, pd.NA) * 100).fillna(0)
    rk["pct_geral"] = (rk["real_total"] / rk["meta_total"].replace(0, pd.NA) * 100).fillna(0)

    def faixa(row):
        if row["pct_ab"] >= 100 and row["pct_en"] >= 100:
            return "Meta batida"
        return "Perto da meta" if row["pct_geral"] >= 70 else "Longe da meta"

    rk["status_meta"] = rk.apply(faixa, axis=1)
    rk["unidade"] = rk["unidade_principal"]
    rk = rk.sort_values(["status_meta", "pct_geral"], ascending=[True, False])

    meta_ab, real_ab = int(rk["meta_abertas"].sum()), int(rk["abertas"].sum())
    meta_en, real_en = int(rk["meta_enviadas"].sum()), int(rk["enviadas"].sum())
    pct_ab = real_ab / meta_ab * 100 if meta_ab else 0
    pct_en = real_en / meta_en * 100 if meta_en else 0
    pct_tot = (real_ab + real_en) / (meta_ab + meta_en) * 100 if (meta_ab + meta_en) else 0
    bateram = int((rk["status_meta"] == "Meta batida").sum())
    longe = int((rk["status_meta"] == "Longe da meta").sum())
    tot_u = len(rk)

    t.secao("Resumo")
    k = st.columns(5)
    with k[0]:
        t.kpi("Pastas Abertas", f"{t.fmt(real_ab)}/{t.fmt(meta_ab)}", f"{pct_ab:.0f}% da meta", t.NEUTRO, "📁")
    with k[1]:
        t.kpi("Pastas Enviadas", f"{t.fmt(real_en)}/{t.fmt(meta_en)}", f"{pct_en:.0f}% da meta", t.NEUTRO, "📤")
    with k[2]:
        t.kpi("Atingimento geral", f"{pct_tot:.0f}%", "abertas + enviadas", t.CORES["roxo"], "📈")
    with k[3]:
        t.kpi("Bateram meta", f"{bateram}/{tot_u}", "abertas e enviadas", t.CUMPRIDO, "🏅")
    with k[4]:
        t.kpi("Abaixo / longe", f"{longe}/{tot_u}", "abaixo de 70%", t.ATRASADO, "❌")

    t.secao("Ranking geral de atingimento")
    fig = px.bar(rk.sort_values("pct_geral", ascending=False), x="unidade", y="pct_geral",
                 text=rk.sort_values("pct_geral", ascending=False)["pct_geral"].round(0).astype(int).astype(str) + "%",
                 color="status_meta", color_discrete_map=MAPA_STATUS)
    fig.add_hline(y=100, line_dash="dash", line_color=t.CORES["muted"])
    fig.update_traces(textposition="outside", cliponaxis=False, textfont_color=t.CORES["ink"])
    fig.update_yaxes(title="% da meta")
    st.plotly_chart(t.layout(fig, 460), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        t.secao("Pastas Abertas")
        f = px.bar(rk.sort_values("abertas", ascending=False), x="unidade", y="abertas",
                   text="abertas", color="status_meta", color_discrete_map=MAPA_STATUS)
        f.update_traces(textposition="outside", cliponaxis=False, textfont_color=t.CORES["ink"])
        st.plotly_chart(t.layout(f, 420), use_container_width=True)
    with c2:
        t.secao("Pastas Enviadas")
        f = px.bar(rk.sort_values("enviadas", ascending=False), x="unidade", y="enviadas",
                   text="enviadas", color="status_meta", color_discrete_map=MAPA_STATUS)
        f.update_traces(textposition="outside", cliponaxis=False, textfont_color=t.CORES["ink"])
        st.plotly_chart(t.layout(f, 420), use_container_width=True)

    t.secao("Detalhamento por unidade")
    st.caption("Enviadas = Confecção + Deferido (Benefício ADM - Deferido criado no mês).")
    tab = rk[["unidade", "meta_abertas", "abertas", "pct_ab", "meta_enviadas",
              "enviadas_conf", "deferidas", "enviadas", "pct_en", "meta_total",
              "real_total", "pct_geral", "status_meta"]].copy()
    for c in ("pct_ab", "pct_en", "pct_geral"):
        tab[c] = tab[c].round(1).astype(str) + "%"
    tab.columns = ["Unidade", "Meta Abertas", "Abertas", "% Abertas", "Meta Enviadas",
                   "Confecção", "Deferidas", "Enviadas (total)", "% Enviadas",
                   "Meta Total", "Realizado", "% Geral", "Status"]
    st.dataframe(tab, use_container_width=True, hide_index=True)

    t.secao("Exportar")
    botao_export({"Metas": tab}, nome=f"metas_{ano}_{mes:02d}")
