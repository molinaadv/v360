# =====================================================================
# V360 MOLINA — INSIGHTS V360  (inteligência operacional, dark)
# =====================================================================
# Performance · Gargalos · Eficiência · Estratégico. Lê os números do
# mês e aponta destaque, gargalo e ações — no mesmo visual dark.
# =====================================================================
import pandas as pd
import streamlit as st

import data
import theme as t
import graficos as g
import regras as r

VOL_MINIMO = 5
TOP_N = 15


def _taxa_conclusao(conc, pend, col="unidade_nome"):
    a = conc.groupby(col).size().rename("conc")
    b = pend.groupby(col).size().rename("pend")
    tx = pd.concat([a, b], axis=1).fillna(0)
    tx["recebidas"] = tx["conc"] + tx["pend"]
    tx = tx[tx["recebidas"] >= VOL_MINIMO]
    if tx.empty:
        return tx
    tx["taxa"] = tx["conc"] / tx["recebidas"] * 100
    return tx.sort_values("taxa", ascending=False)


def _tempo_medio(conc):
    if conc.empty:
        return pd.DataFrame(columns=["subtipo_nome", "dias"])
    c = conc.copy()
    ini = pd.to_datetime(c.get("creation_date"), errors="coerce")
    fim = pd.to_datetime(c.get("data_conclusao"), errors="coerce")
    c["dias"] = (fim - ini).dt.total_seconds() / 86400
    c = c[(c["dias"].notna()) & (c["dias"] >= 0) & (c["subtipo_nome"].notna())]
    if c.empty:
        return pd.DataFrame(columns=["subtipo_nome", "dias"])
    return (c.groupby("subtipo_nome")["dias"].mean().reset_index()
            .sort_values("dias", ascending=False))


def render(df_f, df_metas_f, ano: int, mes: int):
    ini, fim = data.periodo_mes(ano, mes)
    t.titulo("💡 INSIGHTS V360",
             f"Período: {ini.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}",
             pills=[t.pill("inteligência operacional", t.CORES["roxo"])])

    if df_f is None or df_f.empty:
        st.warning("Sem tarefas para o recorte selecionado.")
        return

    abertas_mes = r.entre(r.abertas(df_f), "data_conclusao", ini, fim)
    concl_mes = r.entre(r.cumpridas(df_f), "data_conclusao", ini, fim)
    pend = r.em_aberto(df_f)
    taxa = _taxa_conclusao(concl_mes, pend)

    # ---- Performance ----
    t.secao("Performance")
    u_ab, q_ab, p_ab = r.top(abertas_mes, "unidade_nome")
    u_co, q_co, _ = r.top(concl_mes, "unidade_nome")
    r_pr, q_pr, _ = r.top(concl_mes, "usuario_executor")
    c = st.columns(3)
    with c[0]:
        t.kpi("🏆 Melhor unidade do mês", u_ab or "—",
              f"{t.fmt(q_ab)} abertas · {p_ab:.0f}%" if u_ab else "sem dados", t.NEUTRO)
    with c[1]:
        t.kpi("📈 Melhor em conclusão", u_co or "—",
              f"{t.fmt(q_co)} concluídas" if u_co else "sem dados", t.CUMPRIDO)
    with c[2]:
        t.kpi("👤 Colaborador mais produtivo", r_pr or "—",
              f"{t.fmt(q_pr)} concluídas" if r_pr else "sem dados", t.CORES["azul"])

    # ---- Gargalos ----
    t.secao("Gargalos")
    u_pe, q_pe, _ = r.top(pend, "unidade_nome")
    tp, q_tp, _ = r.top(pend, "subtipo_nome")
    rf, q_rf, _ = r.top(pend, "usuario_executor")
    c = st.columns(3)
    with c[0]:
        t.kpi("⚠️ Mais pendências", u_pe or "—",
              f"{t.fmt(q_pe)} em aberto" if u_pe else "sem pendências", t.ABERTO)
    with c[1]:
        t.kpi("🧩 Tarefa mais travada", tp or "—",
              f"{t.fmt(q_tp)} paradas" if tp else "—", t.CORES["roxo"])
    with c[2]:
        t.kpi("📉 Maior fila (responsável)", rf or "—",
              f"{t.fmt(q_rf)} na fila" if rf else "—", t.NEUTRO)
    fig = g.barras_h(pend, "unidade_nome", t.ABERTO, limite=TOP_N, altura=460,
                     titulo="Pendências em aberto por unidade")
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    # ---- Eficiência ----
    t.secao("Eficiência")
    c = st.columns(2)
    with c[0]:
        if not taxa.empty:
            top_un = taxa.iloc[0]
            t.kpi("✅ Melhor taxa de conclusão", str(top_un.name),
                  f"{top_un['taxa']:.0f}% · {int(top_un['conc'])}/{int(top_un['recebidas'])}", t.CUMPRIDO)
        else:
            t.kpi("✅ Melhor taxa de conclusão", "—", "volume insuficiente", t.CORES["muted"])
    with c[1]:
        r_ab, q_rab, _ = r.top(abertas_mes, "usuario_executor")
        t.kpi("🚀 Mais abriu no período", r_ab or "—",
              f"{t.fmt(q_rab)} pastas" if r_ab else "—", t.NEUTRO)
    # tempo médio usa valor real (média de dias), não contagem — gráfico próprio
    tm = _tempo_medio(concl_mes).head(TOP_N)
    if not tm.empty:
        import plotly.express as px
        fig = px.bar(tm, x="dias", y="subtipo_nome", orientation="h", text=tm["dias"].round(1))
        fig.update_traces(marker_color=t.CORES["azul"], textposition="outside",
                          cliponaxis=False, textfont_color=t.CORES["ink"])
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(t.layout(fig, 460, "Tempo médio para concluir por tipo (dias)"),
                        use_container_width=True)

    # ---- Estratégico ----
    t.secao("Estratégico — onde agir nesta semana")
    if u_pe:
        t_un, q_un, _ = r.top(pend[pend["unidade_nome"] == u_pe], "subtipo_nome")
        if t_un:
            t.nota(f"<b>Oportunidade:</b> {u_pe} acumula <b>{t.fmt(q_pe)}</b> pendências, "
                   f"concentradas em <b>{t_un}</b> ({t.fmt(q_un)}). Reforçar essa frente destrava a unidade.",
                   "ok", "💡")
    if not taxa.empty:
        pior = taxa.iloc[-1]
        t.nota(f"<b>Alerta:</b> {pior.name} está com <b>{pior['taxa']:.0f}%</b> de conclusão "
               f"({int(pior['conc'])}/{int(pior['recebidas'])}) — pior do período.", "alerta", "🚨")
    if rf:
        t.nota(f"<b>Ação recomendada:</b> {rf} está com a maior fila (<b>{t.fmt(q_rf)}</b> tarefas). "
               f"Vale redistribuir parte da carga.", "info", "🛠")
