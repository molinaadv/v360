# =====================================================================
# V360 MOLINA — PERFORMANCE  (ex-Colaboradores) — ao vivo do Supabase
# =====================================================================
# Reproduz o app "V360 Performance": comparar colaboradores selecionados,
# com resumo comparativo e as abas Comparação / Evolução mensal / Ranking /
# Unidades / Subtipos / Base detalhada.
#
# PRODUÇÃO = tarefas Cumpridas, creditadas a `usuario_executor` (quem
# concluiu). "Andamentos" é outra exportação do LegalOne (não está na view
# de tarefas) → aparece como 0 com aviso, sem inventar.
# =====================================================================
import pandas as pd
import plotly.express as px
import streamlit as st

import data
import theme as t
import regras as r
from export import botao_export

MAX_COLAB = 5


def _competencia(df):
    """Coluna 'competencia' (YYYY-MM) em Manaus, a partir de mes_conclusao ou data_conclusao."""
    if "mes_conclusao" in df.columns and df["mes_conclusao"].notna().any():
        return df["mes_conclusao"].astype(str)
    return pd.to_datetime(df.get("data_conclusao"), errors="coerce").dt.strftime("%Y-%m")


def _bar(df, x, y, titulo, cor=t.CUMPRIDO, altura=420):
    if df.empty:
        st.info("Sem dados para este gráfico.")
        return
    fig = px.bar(df, x=x, y=y, text=y)
    fig.update_traces(marker_color=cor, textposition="outside", cliponaxis=False,
                      textfont_color=t.CORES["ink"])
    st.plotly_chart(t.layout(fig, altura, titulo), use_container_width=True)


def render(df_f, df_metas_f, ano: int, mes: int):
    ini, fim = data.periodo_mes(ano, mes)
    t.titulo("👥 PERFORMANCE",
             "Compare a produção de colaboradores — crédito de quem concluiu a tarefa.",
             pills=[t.pill("comparativo de produção", t.CORES["roxo"]), t.pill("ao vivo", live=True)])

    if df_f is None or df_f.empty:
        st.warning("Sem tarefas para o recorte selecionado.")
        return

    # PRODUÇÃO = cumpridas, com executor e data de conclusão
    prod = r.cumpridas(df_f).copy()
    prod = prod[prod.get("usuario_executor").notna() & prod.get("data_conclusao").notna()]
    if prod.empty:
        t.nota("Nenhuma conclusão nos dados do recorte.", "todo", "📐")
        return
    prod["competencia"] = _competencia(prod)

    # período: por padrão usa todo o histórico (melhor pra comparar/evoluir);
    # opção de restringir ao mês selecionado no topo.
    restringe = st.checkbox(f"Restringir ao mês selecionado ({mes:02d}/{ano})", value=False)
    if restringe:
        prod = r.entre(prod, "data_conclusao", ini, fim)
        if prod.empty:
            t.nota("Sem conclusões no mês selecionado.", "todo", "📐")
            return

    colaboradores = sorted(c for c in prod["usuario_executor"].dropna().astype(str).unique() if c)
    ranking = (prod.groupby("usuario_executor").size().reset_index(name="Total produção")
               .sort_values("Total produção", ascending=False).reset_index(drop=True))
    ranking["ranking"] = range(1, len(ranking) + 1)

    st.success(f"Colaboradores encontrados: {len(colaboradores)}  ·  "
               f"Produção total no recorte: {t.fmt(len(prod))}")

    # top 5 como default (mais útil que 1 pra comparar)
    padrao = ranking["usuario_executor"].head(2).tolist()
    selecionados = st.multiselect("Escolha até 5 colaboradores para comparar",
                                  colaboradores, default=padrao, max_selections=MAX_COLAB)
    if not selecionados:
        st.info("Selecione pelo menos um colaborador.")
        return

    prod_sel = prod[prod["usuario_executor"].isin(selecionados)]

    # ---- Resumo comparativo ----
    resumo = []
    for nome in selecionados:
        pnome = prod_sel[prod_sel["usuario_executor"] == nome]
        total_prod = int(len(pnome))
        n_meses = pnome["competencia"].nunique() or 1
        media_mensal = round(total_prod / n_meses, 1)
        rk = ranking[ranking["usuario_executor"] == nome]["ranking"]
        resumo.append({
            "Colaborador": nome, "Total geral": total_prod,
            "Produção concluída": total_prod, "Andamentos cadastrados": 0,
            "Média mensal produção": media_mensal,
            "Ranking produção": int(rk.iloc[0]) if not rk.empty else "-",
        })
    resumo_df = pd.DataFrame(resumo).sort_values("Total geral", ascending=False).reset_index(drop=True)
    media_grupo = round(resumo_df["Total geral"].mean(), 1) if not resumo_df.empty else 0
    resumo_df["Diferença vs média"] = resumo_df["Total geral"].apply(lambda x: round(x - media_grupo, 1))

    t.secao("Resumo comparativo")
    cols = st.columns(len(resumo_df))
    for i, row in resumo_df.iterrows():
        with cols[i]:
            t.kpi(row["Colaborador"], t.fmt(row["Total geral"]),
                  f"{row['Diferença vs média']:+g} vs média · rank {row['Ranking produção']}",
                  t.CUMPRIDO if row["Diferença vs média"] >= 0 else t.ABERTO, "👤")
    st.dataframe(resumo_df, use_container_width=True, hide_index=True)

    a1, a2, a3, a4, a5, a6 = st.tabs(["📊 Comparação", "📈 Evolução mensal", "🏆 Ranking",
                                      "🏢 Unidades", "📂 Subtipos", "📋 Base detalhada"])

    # ---- Comparação ----
    with a1:
        _bar(resumo_df, "Colaborador", "Total geral", "Total geral por colaborador")

    # ---- Evolução mensal ----
    with a2:
        mensal = (prod_sel.groupby(["competencia", "usuario_executor"]).size()
                  .reset_index(name="Total").rename(columns={"competencia": "Mês",
                                                             "usuario_executor": "Colaborador"})
                  .sort_values("Mês"))
        if mensal.empty:
            st.info("Sem dados mensais para os selecionados.")
        else:
            fig = px.line(mensal, x="Mês", y="Total", color="Colaborador", markers=True)
            st.plotly_chart(t.layout(fig, 420, "Evolução mensal da produção"),
                            use_container_width=True)
            st.dataframe(mensal, use_container_width=True, hide_index=True)
            meses = sorted(mensal["Mês"].dropna().unique())
            if meses:
                mes_sel = st.selectbox("Comparativo por mês", meses, index=len(meses) - 1)
                mf = mensal[mensal["Mês"] == mes_sel]
                _bar(mf, "Colaborador", "Total", f"Produção no mês {mes_sel}")

    # ---- Ranking ----
    with a3:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Ranking de Produção**")
            st.dataframe(ranking.rename(columns={"usuario_executor": "Colaborador"})
                         [["ranking", "Colaborador", "Total produção"]].head(30),
                         use_container_width=True, hide_index=True)
        with c2:
            st.markdown("**Ranking de Andamentos**")
            t.nota("Andamentos vêm de outra exportação do LegalOne e não estão na view "
                   "de tarefas. Se houver uma view de andamentos no Supabase, eu ligo aqui.",
                   "todo", "🧩")

    # ---- Unidades ----
    with a4:
        uni = (prod_sel.groupby(["usuario_executor", "unidade_nome"]).size()
               .reset_index(name="Total").rename(columns={"usuario_executor": "Colaborador",
                                                          "unidade_nome": "Unidade"})
               .sort_values("Total", ascending=False))
        if uni.empty:
            st.info("Sem dados por unidade.")
        else:
            st.dataframe(uni, use_container_width=True, hide_index=True)
            top = (uni.groupby("Unidade")["Total"].sum().reset_index()
                   .sort_values("Total", ascending=False).head(15))
            _bar(top, "Unidade", "Total", "Top unidades no grupo selecionado", t.NEUTRO)

    # ---- Subtipos ----
    with a5:
        base = prod_sel[["usuario_executor", "subtipo_nome", "competencia"]].copy()
        base["subtipo_nome"] = base["subtipo_nome"].fillna("NÃO INFORMADO").astype(str)
        subs = sorted(base["subtipo_nome"].dropna().unique())
        escolhidos = st.multiselect("Filtrar subtipos", subs, default=subs[:3] if subs else [])
        bf = base[base["subtipo_nome"].isin(escolhidos)] if escolhidos else base
        mensal_sub = (bf.groupby(["competencia", "usuario_executor"]).size()
                      .reset_index(name="Total").rename(columns={"competencia": "Mês",
                                                                 "usuario_executor": "Colaborador"})
                      .sort_values("Mês"))
        if not mensal_sub.empty:
            fig = px.line(mensal_sub, x="Mês", y="Total", color="Colaborador", markers=True)
            st.plotly_chart(t.layout(fig, 400, "Evolução por subtipo (filtro)"),
                            use_container_width=True)
        top_sub = (bf.groupby("subtipo_nome").size().reset_index(name="Total")
                   .rename(columns={"subtipo_nome": "Subtipo"})
                   .sort_values("Total", ascending=False).head(15))
        _bar(top_sub, "Subtipo", "Total", "Top subtipos no filtro", t.CORES["roxo"])

    # ---- Base detalhada + export ----
    with a6:
        cols_ = [c for c in ["data_conclusao", "usuario_executor", "unidade_nome",
                            "subtipo_nome", "status_nome", "competencia"] if c in prod_sel.columns]
        st.dataframe(prod_sel[cols_].sort_values("data_conclusao", ascending=False).head(1000),
                     use_container_width=True, hide_index=True)
        botao_export({"Resumo": resumo_df,
                      "Ranking_producao": ranking.rename(columns={"usuario_executor": "Colaborador"}),
                      "Producao_selecionados": prod_sel[cols_]},
                     nome=f"performance_{ano}_{mes:02d}")
