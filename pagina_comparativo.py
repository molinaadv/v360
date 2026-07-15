# =====================================================================
# V360 MOLINA — COMPARATIVO ANALÍTICO  (ao vivo do Supabase)
# =====================================================================
# Reproduz o "Relatório Analítico Comparativo" lendo vw_tasks_completa.
# Compara volume por período/escritório/subtipo/responsável, com base na
# Data de Cadastro (creation_date) ou de Cumprimento (data_conclusao).
# =====================================================================
import pandas as pd
import plotly.express as px
import streamlit as st

import theme as t
import regras as r
from export import botao_export

MESES_ABREV = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
               7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}
MESES_NOME = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
              7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}

# rótulo amigável -> coluna real da view
GRUPOS = {
    "Escritório": "unidade_nome",
    "Subtipo": "subtipo_nome",
    "Responsável": "responsavel_nome",
    "Status": "status_nome",
    "Cumprido por": "usuario_executor",
    "Cadastrou": "usuario_criador",
    "Área / Setor": "setor_meta",
}


def _opcoes(df, col):
    if col not in df.columns:
        return ["Todos"]
    vals = sorted(v for v in df[col].dropna().astype(str).unique() if v and v != "nan")
    return ["Todos"] + vals


def _filtra(df, col, sel):
    if col not in df.columns or not sel or "Todos" in sel:
        return df
    return df[df[col].astype(str).isin(sel)]


def render(df_f, df_metas_f, ano: int, mes: int):
    t.titulo("🔀 COMPARATIVO ANALÍTICO",
             "Compare volume por período, escritório, subtipo e responsável — "
             "escolhendo a data-base e os recortes.",
             pills=[t.pill("análise histórica", t.CORES["roxo"])])

    if df_f is None or df_f.empty:
        st.warning("Sem tarefas para o recorte selecionado.")
        return

    # ---- controles ----
    c1, c2, c3, c4 = st.columns([1.3, 1, 1, 1])
    with c1:
        base_data = st.radio("Usar qual data?", ["Data de Cadastro", "Data de Cumprimento"],
                             horizontal=True)
    col_data = "creation_date" if base_data == "Data de Cadastro" else "data_conclusao"

    d = df_f.copy()
    d[col_data] = pd.to_datetime(d.get(col_data), errors="coerce")
    d = d[d[col_data].notna()]
    if d.empty:
        st.warning(f"Não há datas válidas em {base_data}.")
        return

    dmin, dmax = d[col_data].dt.date.min(), d[col_data].dt.date.max()
    with c2:
        di = st.date_input("Data inicial", value=dmin, min_value=dmin, max_value=dmax)
    with c3:
        dfim = st.date_input("Data final", value=dmax, min_value=dmin, max_value=dmax)
    with c4:
        anos = sorted(d[col_data].dt.year.dropna().astype(int).unique(), reverse=True)
        ano_comp = st.selectbox("Ano comparativo", anos)

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        sub_sel = st.multiselect("Subtipo", _opcoes(d, "subtipo_nome"), default=["Todos"])
    with f2:
        esc_sel = st.multiselect("Escritório", _opcoes(d, "unidade_nome"), default=["Todos"])
    with f3:
        resp_sel = st.multiselect("Responsável", _opcoes(d, "responsavel_nome"), default=["Todos"])
    with f4:
        st_sel = st.multiselect("Status", _opcoes(d, "status_nome"), default=["Todos"])

    g1, g2 = st.columns([1, 1])
    with g1:
        area_sel = st.multiselect("Área / Setor", _opcoes(d, "setor_meta"), default=["Todos"])
    with g2:
        grupo_lbl = st.selectbox("Agrupar por", list(GRUPOS.keys()))
    grupo_col = GRUPOS[grupo_lbl]

    # ---- aplica filtros ----
    d = d[(d[col_data].dt.date >= di) & (d[col_data].dt.date <= dfim)]
    d = _filtra(d, "subtipo_nome", sub_sel)
    d = _filtra(d, "unidade_nome", esc_sel)
    d = _filtra(d, "responsavel_nome", resp_sel)
    d = _filtra(d, "status_nome", st_sel)
    d = _filtra(d, "setor_meta", area_sel)

    if d.empty:
        st.warning("Nenhum registro com os filtros selecionados.")
        return

    d["Ano"] = d[col_data].dt.year
    d["MesN"] = d[col_data].dt.month
    d["Mes"] = d[col_data].dt.strftime("%m/%Y")

    # ---- KPIs ----
    t.secao("Resumo executivo")
    total = len(d)
    cumpr = int(d["status_nome"].astype(str).str.contains("Cumprido", case=False, na=False).sum())
    pend = int(d["status_nome"].isin(r.STATUS_ABERTO).sum())
    n_sub = d["subtipo_nome"].nunique()
    ult = d[d["Ano"] == ano_comp].groupby("MesN").size().sort_index()
    v_atual = int(ult.iloc[-1]) if len(ult) else 0
    v_ant = int(ult.iloc[-2]) if len(ult) > 1 else None
    delta = f"{(v_atual-v_ant)/v_ant*100:+.0f}% vs mês anterior" if v_ant else ""
    k = st.columns(5)
    with k[0]:
        t.kpi("Total filtrado", t.fmt(total), base_data, t.NEUTRO, "📁")
    with k[1]:
        t.kpi("Cumpridos", t.fmt(cumpr), "no recorte", t.CUMPRIDO, "✅")
    with k[2]:
        t.kpi("Em aberto", t.fmt(pend), "pendente/iniciado", t.ABERTO, "⚠️")
    with k[3]:
        t.kpi("Subtipos", t.fmt(n_sub), "distintos", t.CORES["azul"], "📌")
    with k[4]:
        t.kpi(f"Último mês de {ano_comp}", t.fmt(v_atual), delta or "sem base anterior", t.CORES["roxo"], "📅")

    # ---- abas ----
    t.secao("Comparativo mensal")
    a1, a2, a3, a4 = st.tabs(["Evolução do ano", "Ano x Ano", f"Por {grupo_lbl}", "Analítico"])

    with a1:
        dy = d[d["Ano"] == ano_comp]
        mensal = (dy.groupby(["MesN", "Mes"]).size().reset_index(name="Qtd").sort_values("MesN"))
        if mensal.empty:
            st.info("Sem dados para o ano comparativo.")
        else:
            fig = px.line(mensal, x="Mes", y="Qtd", markers=True, text="Qtd")
            fig.update_traces(line_color=t.NEUTRO, textposition="top center",
                              textfont_color=t.CORES["muted"])
            st.plotly_chart(t.layout(fig, 420, f"Evolução mensal · {base_data} · {ano_comp}"),
                            use_container_width=True)
            st.dataframe(mensal[["Mes", "Qtd"]], use_container_width=True, hide_index=True)

    with a2:
        anos_sel = st.multiselect("Anos para comparar", anos,
                                  default=anos[:2] if len(anos) >= 2 else anos)
        da = d[d["Ano"].isin(anos_sel)]
        comp = (da.groupby(["Ano", "MesN"]).size().reset_index(name="Qtd").sort_values(["Ano", "MesN"]))
        comp["Mes"] = comp["MesN"].map(MESES_ABREV)
        if comp.empty:
            st.info("Selecione ao menos um ano.")
        else:
            fig = px.line(comp, x="Mes", y="Qtd", color="Ano", markers=True,
                          category_orders={"Mes": list(MESES_ABREV.values())})
            st.plotly_chart(t.layout(fig, 460, "Comparativo Ano x Ano"), use_container_width=True)
            piv = comp.pivot_table(index="Mes", columns="Ano", values="Qtd", aggfunc="sum",
                                   fill_value=0).reindex(list(MESES_ABREV.values())).reset_index()
            piv.columns = [str(c) for c in piv.columns]
            st.dataframe(piv, use_container_width=True, hide_index=True)

    with a3:
        if grupo_col not in d.columns:
            st.info(f"A coluna de '{grupo_lbl}' não está disponível nos dados.")
        else:
            top_n = st.slider("Quantos grupos no gráfico", 3, 20, 10)
            tops = d[grupo_col].value_counts().head(top_n).index.tolist()
            dt = d[d[grupo_col].isin(tops)].copy()
            cg = (dt.groupby([grupo_col, "Ano", "MesN"]).size().reset_index(name="Qtd"))
            cg["Periodo"] = cg["MesN"].map(MESES_ABREV) + "/" + cg["Ano"].astype(str)
            fig = px.bar(cg, x="Periodo", y="Qtd", color=grupo_col, barmode="group")
            st.plotly_chart(t.layout(fig, 520, f"Comparativo mensal por {grupo_lbl}"),
                            use_container_width=True)
            tab = cg.pivot_table(index=grupo_col, columns="Periodo", values="Qtd",
                                 aggfunc="sum", fill_value=0)
            tab["Total"] = tab.sum(axis=1)
            tab = tab.sort_values("Total", ascending=False).reset_index()
            tab.columns = [str(c) for c in tab.columns]
            st.dataframe(tab, use_container_width=True, hide_index=True)

    with a4:
        resumo = (d.groupby(grupo_col).size().reset_index(name="Qtd")
                  .sort_values("Qtd", ascending=False)) if grupo_col in d.columns else pd.DataFrame()
        st.markdown(f"**Tabela agrupada por {grupo_lbl}**")
        st.dataframe(resumo, use_container_width=True, hide_index=True)
        cols = [c for c in ["creation_date", "data_conclusao", "unidade_nome", "subtipo_nome",
                            "status_nome", "responsavel_nome", "usuario_executor",
                            "usuario_criador", "setor_meta"] if c in d.columns]
        st.markdown("**Base detalhada**")
        st.dataframe(d[cols].sort_values(col_data, ascending=False).head(500),
                     use_container_width=True, hide_index=True)
        botao_export({"Comparativo": d[cols], "Agrupado": resumo}, nome="comparativo_v360")

    # ---- insights ----
    t.secao("Insights automáticos")
    mt = d.groupby(["Ano", "MesN"]).size().reset_index(name="Qtd")
    if not mt.empty:
        mel = mt.sort_values("Qtd", ascending=False).iloc[0]
        pio = mt.sort_values("Qtd").iloc[0]
        melhor = f"{MESES_NOME[int(mel['MesN'])]}/{int(mel['Ano'])} ({int(mel['Qtd'])})"
        pior = f"{MESES_NOME[int(pio['MesN'])]}/{int(pio['Ano'])} ({int(pio['Qtd'])})"
    else:
        melhor = pior = "—"
    m_sub = d["subtipo_nome"].value_counts().idxmax() if d["subtipo_nome"].notna().any() else "—"
    m_esc = d["unidade_nome"].value_counts().idxmax() if d["unidade_nome"].notna().any() else "—"
    m_resp = d["responsavel_nome"].value_counts().idxmax() if "responsavel_nome" in d and d["responsavel_nome"].notna().any() else "—"
    t.nota(f"<b>Melhor mês:</b> {melhor} &nbsp;·&nbsp; <b>Pior mês:</b> {pior}", "ok", "📈")
    t.nota(f"<b>Maior subtipo:</b> {m_sub} &nbsp;·&nbsp; <b>Maior escritório:</b> {m_esc} "
           f"&nbsp;·&nbsp; <b>Maior responsável:</b> {m_resp}", "info", "💡")
