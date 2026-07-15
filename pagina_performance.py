# =====================================================================
# V360 MOLINA — PERFORMANCE  (ex-Colaboradores, ao vivo do Supabase)
# =====================================================================
# Reproduz o app "V360 Performance" lendo vw_tasks_completa em vez de
# planilha. PRODUÇÃO = tarefas Cumpridas no período, creditadas a
# `usuario_executor` (quem concluiu — regra da base de conhecimento).
# "Andamentos" não vive na view de tarefas → seção avisa em vez de inventar.
# =====================================================================
import pandas as pd
import plotly.express as px
import streamlit as st

import data
import theme as t
import graficos as g
import regras as r
from export import botao_export


def render(df_f, df_metas_f, ano: int, mes: int):
    ini, fim = data.periodo_mes(ano, mes)
    comp = f"{['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'][mes-1]}/{ano}"
    t.titulo("👥 PERFORMANCE",
             f"Produção do período: {ini.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')} · "
             "crédito de quem concluiu a tarefa.",
             pills=[t.pill(f"Competência · {comp}", t.CORES['roxo']), t.pill("ao vivo", live=True)])

    if df_f is None or df_f.empty:
        st.warning("Sem tarefas para o recorte selecionado.")
        return

    # PRODUÇÃO = cumpridas no mês (por data de conclusão)
    prod = r.entre(r.cumpridas(df_f), "data_conclusao", ini, fim)

    # ---- KPIs ----
    t.secao("Resumo de produção")
    n_prod = len(prod)
    n_colab = prod["usuario_executor"].nunique() if not prod.empty else 0
    media = (n_prod / n_colab) if n_colab else 0
    top_c, top_q, top_p = r.top(prod, "usuario_executor")
    k = st.columns(4)
    with k[0]:
        t.kpi("Produção total", t.fmt(n_prod), "tarefas concluídas no mês", t.CUMPRIDO, "✅")
    with k[1]:
        t.kpi("Colaboradores ativos", t.fmt(n_colab), "concluíram algo no mês", t.NEUTRO, "👤")
    with k[2]:
        t.kpi("Média por colaborador", t.fmt(round(media)), "tarefas / pessoa", t.CORES["azul"], "📊")
    with k[3]:
        t.kpi("Colaborador destaque", top_c or "—",
              f"{t.fmt(top_q)} concluídas · {top_p:.0f}%" if top_c else "sem dados", t.CORES["roxo"], "🥇")

    if prod.empty:
        t.nota("Nenhuma conclusão no mês selecionado para montar os rankings.", "todo", "📐")
        return

    # ---- Ranking de produção por colaborador ----
    t.secao("Ranking de produção — colaboradores")
    fig = g.barras_h(prod, "usuario_executor", t.CUMPRIDO, limite=20, altura=560,
                     titulo="Concluídas por colaborador")
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    # ---- Por unidade + por subtipo ----
    c1, c2 = st.columns(2)
    with c1:
        t.secao("Produção por unidade")
        fig = g.barras(prod, "unidade_nome", t.NEUTRO, altura=440, titulo="")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        t.secao("Produção por subtipo")
        fig = g.barras_h(prod, "subtipo_nome", t.CORES["roxo"], limite=15, altura=440, titulo="")
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    # ---- Evolução mensal (12m) ----
    t.secao("Evolução mensal da produção")
    hist = r.cumpridas(df_f)
    if "mes_conclusao" in hist.columns and hist["mes_conclusao"].notna().any():
        serie = (hist[hist["mes_conclusao"].notna()].groupby("mes_conclusao").size()
                 .reset_index(name="total").sort_values("mes_conclusao").tail(12))
        fig = px.line(serie, x="mes_conclusao", y="total", markers=True, text="total")
        fig.update_traces(line_color=t.CUMPRIDO, textposition="top center",
                          textfont_color=t.CORES["muted"])
        st.plotly_chart(t.layout(fig, 360, "Concluídas por mês"), use_container_width=True)
    else:
        t.nota("Sem histórico de conclusão suficiente para a evolução.", "todo", "📈")

    # ---- Andamentos (não disponível ao vivo) ----
    t.secao("Andamentos no processo")
    t.nota("Os <b>andamentos</b> vêm de outra exportação do LegalOne (movimentações do "
           "processo) e não estão na view de tarefas. Se você tiver uma view de andamentos "
           "no Supabase, me diga o nome que eu ligo este ranking aqui do mesmo jeito.",
           "todo", "🧩")

    # ---- Detalhado + export ----
    t.secao("Dados detalhados e exportação")
    cols = [c for c in ["data_conclusao", "usuario_executor", "unidade_nome", "subtipo_nome",
                        "status_nome", "responsavel_nome"] if c in prod.columns]
    st.dataframe(prod[cols].sort_values("data_conclusao", ascending=False).head(500),
                 use_container_width=True, hide_index=True)
    botao_export({"Producao": prod[cols],
                  "Ranking_colaborador": prod.groupby("usuario_executor").size()
                  .reset_index(name="concluidas").sort_values("concluidas", ascending=False)},
                 nome=f"performance_{ano}_{mes:02d}")
