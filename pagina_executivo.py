# =====================================================================
# V360 MOLINA — EXECUTIVO  (relatório mensal p/ diretoria, dark)
# =====================================================================
import pandas as pd
import plotly.express as px
import streamlit as st

import data
import theme as t
import graficos as g
import regras as r
from export import botao_export


def _delta(atual: int, anterior: int) -> str:
    if not anterior:
        return '<span style="color:#6b7a99;font-size:12px;">sem base do mês anterior</span>'
    pct = (atual - anterior) / anterior * 100
    if pct > 0:
        cor, seta = t.CUMPRIDO, "▲"
    elif pct < 0:
        cor, seta = t.ATRASADO, "▼"
    else:
        cor, seta = t.CORES["muted"], "■"
    return f'<span style="color:{cor};font-weight:800;font-size:12px;">{seta} {abs(pct):.0f}% vs mês anterior</span>'


def _mes_anterior(ano, mes):
    return (ano - 1, 12) if mes == 1 else (ano, mes - 1)


def render(df_f: pd.DataFrame, df_metas_f: pd.DataFrame, ano: int, mes: int):
    ini, fim = data.periodo_mes(ano, mes)
    a_ini, a_fim = data.periodo_mes(*_mes_anterior(ano, mes))
    comp = f"{['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'][mes-1]} / {ano}"

    t.titulo("🏠 EXECUTIVO",
             f"Período: {ini.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}",
             pills=[t.pill("todas as unidades", t.NEUTRO),
                    t.pill(f"Competência · {comp}", t.CORES["roxo"]),
                    t.pill("ao vivo", live=True)])

    if df_f is None or df_f.empty:
        st.warning("Sem tarefas para o recorte selecionado.")
        return

    # ---- recortes principais ----
    abertas = r.abertas(df_f)
    abertas_mes = r.entre(abertas, "data_conclusao", ini, fim)
    abertas_ant = r.entre(abertas, "data_conclusao", a_ini, a_fim)
    enviadas_mes = r.entre(r.enviadas(df_f), "creation_date", ini, fim)
    enviadas_ant = r.entre(r.enviadas(df_f), "creation_date", a_ini, a_fim)
    concl = r.cumpridas(df_f)
    concl_mes = r.entre(concl, "data_conclusao", ini, fim)
    concl_ant = r.entre(concl, "data_conclusao", a_ini, a_fim)
    pend_analise = r.pendencias_analise(df_f)

    # ---- KPIs ----
    t.secao("Visão do mês")
    k = st.columns(5)
    with k[0]:
        t.kpi("Pastas Abertas", t.fmt(len(abertas_mes)),
              _delta(len(abertas_mes), len(abertas_ant)), t.NEUTRO, "📁")
    with k[1]:
        t.kpi("Pastas Enviadas", t.fmt(len(enviadas_mes)),
              _delta(len(enviadas_mes), len(enviadas_ant)), t.NEUTRO, "📤")
    with k[2]:
        t.kpi("Concluídas", t.fmt(len(concl_mes)),
              _delta(len(concl_mes), len(concl_ant)), t.CUMPRIDO, "✅")
    with k[3]:
        t.kpi("Pendências de Análise", t.fmt(len(pend_analise)),
              "3 subtipos · em aberto", t.ABERTO, "⚠️")
    with k[4]:
        n_un = abertas_mes["unidade_nome"].nunique() if not abertas_mes.empty else 0
        t.kpi("Escritórios ativos", t.fmt(n_un), "abriram pasta no mês", t.CORES["roxo"], "🏢")

    # ---- Destaques ----
    t.secao("Destaques do período")
    un, qun, pun = r.top(abertas_mes, "unidade_nome")
    col_p, qcol, _ = r.top(concl_mes, "usuario_executor")
    ass, qass, pass_ = r.top(r.em_aberto(df_f), "subtipo_nome")
    d = st.columns(3)
    with d[0]:
        t.kpi("🏆 Escritório líder em captação", un or "—",
              f"{t.fmt(qun)} pastas · {pun:.0f}% do mês" if un else "sem abertura", t.NEUTRO)
    with d[1]:
        t.kpi("🥇 Colaborador destaque", col_p or "—",
              f"{t.fmt(qcol)} concluídas no mês" if col_p else "sem conclusões", t.CUMPRIDO)
    with d[2]:
        t.kpi("📋 Tarefa em aberto mais comum", ass or "—",
              f"{t.fmt(qass)} casos · {pass_:.0f}% do backlog" if ass else "sem backlog", t.CORES["roxo"])

    # ---- Pendências de Análise ----
    t.secao("Pendências de Análise")
    if pend_analise.empty:
        t.nota("Sem pendências de análise no recorte selecionado.", "ok", "✅")
    else:
        c1, c2 = st.columns(2)
        fig = g.barras(pend_analise, "unidade_nome", t.ABERTO, titulo="Por escritório")
        if fig:
            c1.plotly_chart(fig, use_container_width=True)
        fig = g.barras_h(pend_analise, "subtipo_nome", t.ABERTO, titulo="Por subtipo")
        if fig:
            c2.plotly_chart(fig, use_container_width=True)

    # ---- Funil operacional ----
    t.secao("Funil operacional")
    df_mes = r.entre(df_f, "creation_date", ini, fim)
    linhas = []
    for rot, subs in r.ETAPAS:
        base = df_mes[df_mes.get("subtipo_nome").isin(subs)]
        linhas.append({
            "Etapa": rot,
            "Concluídas": int((base["status_nome"] == r.STATUS_CUMPRIDO).sum()),
            "Em andamento": int((base["status_nome"] == "Iniciado").sum()),
            "Aguardando": int(base["status_nome"].isin(["Pendente", "Não cumprido"]).sum()),
        })
    funil = pd.DataFrame(linhas)
    if funil[["Concluídas", "Em andamento", "Aguardando"]].to_numpy().sum() == 0:
        t.nota("Sem movimento nas etapas configuradas para este mês/recorte.", "todo", "📐")
    else:
        longo = funil.melt(id_vars="Etapa", var_name="Situação", value_name="Qtd")
        fig = px.bar(longo, x="Etapa", y="Qtd", color="Situação", text="Qtd", barmode="group",
                     color_discrete_map={"Concluídas": t.CUMPRIDO, "Em andamento": t.NEUTRO,
                                         "Aguardando": t.ABERTO})
        fig.update_traces(textposition="outside", cliponaxis=False, textfont_color=t.CORES["ink"])
        st.plotly_chart(t.layout(fig, 440), use_container_width=True)

    # ---- Composição + Tendência ----
    t.secao("Composição e tendência")
    c1, c2 = st.columns(2)
    with c1:
        base = r.entre(df_f, "creation_date", ini, fim)
        if base.empty:
            t.nota("Sem tarefas no mês.", "todo", "📐")
        else:
            vc = base["status_nome"].value_counts()
            mapa = {"Cumprido": t.CUMPRIDO, "Pendente": t.ABERTO, "Não cumprido": t.ATRASADO,
                    "Iniciado": t.NEUTRO, "Cancelado": t.CORES["muted"], "Recusado": t.CORES["roxo"]}
            st.plotly_chart(t.donut(vc.index, vc.values, "Status das tarefas do mês", mapa),
                            use_container_width=True)
    with c2:
        ab = abertas.copy()
        if ab.empty or "mes_conclusao" not in ab.columns:
            t.nota("Sem histórico suficiente para a tendência.", "todo", "📈")
        else:
            serie = (ab[ab["mes_conclusao"].notna()].groupby("mes_conclusao").size()
                     .reset_index(name="total").sort_values("mes_conclusao").tail(12))
            fig = px.line(serie, x="mes_conclusao", y="total", markers=True, text="total")
            fig.update_traces(line_color=t.NEUTRO, textposition="top center",
                              textfont_color=t.CORES["muted"])
            st.plotly_chart(t.layout(fig, 360, "Pastas abertas por mês (12m)"),
                            use_container_width=True)

    # ---- Rankings ----
    t.secao("Quem produziu no mês")
    c1, c2 = st.columns(2)
    fig = g.barras(abertas_mes, "unidade_nome", t.NEUTRO, titulo="Pastas abertas por escritório")
    if fig:
        c1.plotly_chart(fig, use_container_width=True)
    else:
        c1.info("Sem pastas abertas no mês.")
    fig = g.barras_h(concl_mes, "usuario_executor", t.CORES["azul"], titulo="Concluídas por colaborador")
    if fig:
        c2.plotly_chart(fig, use_container_width=True)
    else:
        c2.info("Sem conclusões no mês.")

    # ---- Export ----
    t.secao("Exportar")
    botao_export({
        "Abertas_mes": abertas_mes, "Enviadas_mes": enviadas_mes,
        "Concluidas_mes": concl_mes, "Pendencias_analise": pend_analise,
    }, nome=f"executivo_{ano}_{mes:02d}")
