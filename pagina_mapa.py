# =====================================================================
# V360 MOLINA — MAPA OPERACIONAL  (cartões por unidade, dark)
# =====================================================================
import pandas as pd
import streamlit as st

import data
import theme as t
import regras as r


def _status(pend: int):
    if pend > 200:
        return "Crítico", t.ATRASADO, "🔴"
    if pend >= 80:
        return "Atenção", t.ABERTO, "🟡"
    return "Normal", t.CUMPRIDO, "🟢"


def render(df_f, df_metas_f, ano: int, mes: int):
    ini, fim = data.periodo_mes(ano, mes)
    t.titulo("🗺️ MAPA OPERACIONAL",
             "Verde = normal · amarelo = atenção · vermelho = crítico (por volume de pendências).")

    abertas = r.entre(r.abertas(df_f), "data_conclusao", ini, fim)
    enviadas = r.entre(r.enviadas(df_f), "creation_date", ini, fim)
    pendencias = r.pendencias_analise(df_f)
    protocoladas = r.entre(
        r.cumpridas(df_f[df_f.get("subtipo_nome").isin(r.SUB_PROTOCOLO)]),
        "data_conclusao", ini, fim)

    def conta(base):
        return {} if base.empty else base.groupby("unidade_nome").size().to_dict()

    q_ab, q_en = conta(abertas), conta(enviadas)
    q_pe, q_pr = conta(pendencias), conta(protocoladas)
    unidades = sorted(set(list(q_ab) + list(q_en) + list(q_pe) + list(q_pr)))

    if not unidades:
        st.warning("Nenhuma unidade encontrada para montar o mapa.")
        return

    linhas = []
    for un in unidades:
        pe = int(q_pe.get(un, 0))
        lbl, cor, dot = _status(pe)
        linhas.append({"unidade": un, "ab": int(q_ab.get(un, 0)), "en": int(q_en.get(un, 0)),
                       "pe": pe, "pr": int(q_pr.get(un, 0)), "st": lbl, "cor": cor, "dot": dot})
    dfm = pd.DataFrame(linhas)
    ordem = {"Crítico": 0, "Atenção": 1, "Normal": 2}
    dfm["ordem"] = dfm["st"].map(ordem)
    dfm = dfm.sort_values(["ordem", "pe"], ascending=[True, False])

    normais = int((dfm["st"] == "Normal").sum())
    atencao = int((dfm["st"] == "Atenção").sum())
    criticas = int((dfm["st"] == "Crítico").sum())

    t.secao("Panorama")
    k = st.columns(4)
    with k[0]:
        t.kpi("Unidades", t.fmt(len(dfm)), "total monitorado", t.NEUTRO, "🏢")
    with k[1]:
        t.kpi("Normais", t.fmt(normais), "situação tranquila", t.CUMPRIDO, "🟢")
    with k[2]:
        t.kpi("Atenção", t.fmt(atencao), "acompanhar", t.ABERTO, "🟡")
    with k[3]:
        t.kpi("Críticas", t.fmt(criticas), "prioridade", t.ATRASADO, "🔴")

    t.secao("Unidades")
    por_linha = 4
    for i in range(0, len(dfm), por_linha):
        cols = st.columns(por_linha)
        for col, (_, row) in zip(cols, dfm.iloc[i:i + por_linha].iterrows()):
            col.markdown(
                f"""
                <div style="background:linear-gradient(160deg,{t.CORES['panel']},{t.CORES['panel2']});
                     border:1px solid {t.CORES['line']};border-left:4px solid {row['cor']};
                     border-radius:16px;padding:16px;min-height:210px;margin-bottom:14px;
                     box-shadow:0 10px 30px rgba(0,0,0,.25);">
                    <div style="display:flex;justify-content:space-between;align-items:center;
                         font-weight:900;color:{t.CORES['ink']};font-size:15px;margin-bottom:12px;">
                        <span>{row['dot']} {row['unidade']}</span>
                        <span style="background:{row['cor']};color:#0b1220;border-radius:8px;
                              padding:3px 9px;font-size:11px;font-weight:800;">{row['st']}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;border-bottom:1px solid {t.CORES['line']};padding:6px 0;color:{t.CORES['muted']};font-size:13px;">
                        <span>📁 Abertas</span><b style="color:{row['cor']};font-size:17px;">{row['ab']}</b></div>
                    <div style="display:flex;justify-content:space-between;border-bottom:1px solid {t.CORES['line']};padding:6px 0;color:{t.CORES['muted']};font-size:13px;">
                        <span>📤 Enviadas</span><b style="color:{row['cor']};font-size:17px;">{row['en']}</b></div>
                    <div style="display:flex;justify-content:space-between;border-bottom:1px solid {t.CORES['line']};padding:6px 0;color:{t.CORES['muted']};font-size:13px;">
                        <span>⚠️ Pendências</span><b style="color:{row['cor']};font-size:17px;">{row['pe']}</b></div>
                    <div style="display:flex;justify-content:space-between;padding:6px 0;color:{t.CORES['muted']};font-size:13px;">
                        <span>📄 Protocoladas</span><b style="color:{row['cor']};font-size:17px;">{row['pr']}</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
