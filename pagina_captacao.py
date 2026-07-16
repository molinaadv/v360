# =====================================================================
# V360 MOLINA — V360 CLIENTES  (Dashboard Executivo + Insights)
# =====================================================================
# Traz o relatório do sistema v360 Clientes (tabela captacao_leads) para
# dentro do app de Relatório, no tema dark. Um único menu "V360 Clientes"
# com duas visões, escolhidas por uma sub-navegação no topo:
#   📊 Dashboard Executivo  — cards, funil, evolução, ranking, bairros…
#   💡 Insights             — inteligência comercial, oportunidades, alertas
# Fonte: data.carregar_leads() (nunca traz cpf/telefone/nome do cliente).
# =====================================================================
from datetime import timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data
import theme as t

STATUS_LEAD = ["Novo", "Em atendimento", "Agendado", "Convertido", "Perdido"]
COR_STATUS = {
    "Novo": t.CORES["accent"], "Em atendimento": t.CORES["azul"],
    "Agendado": t.CORES["roxo"], "Convertido": t.CORES["ok"],
    "Perdido": t.CORES["crit"],
}
DIAS_MAP = {0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira",
            3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"}


# ---------------------------------------------------------------------
# helpers de apresentação
# ---------------------------------------------------------------------
def _card(titulo: str, valor, sub: str = "", cor: str = t.NEUTRO):
    valor = "—" if valor in (None, "", "Sem dados") else valor
    st.markdown(
        f'<div class="kpi" style="--accent:{cor};min-height:118px;">'
        f'<div class="lbl">{titulo}</div>'
        f'<div class="val" style="font-size:clamp(20px,2.2vw,26px);">{valor}</div>'
        f'<div class="sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def _grade(cards, por_linha=3):
    for i in range(0, len(cards), por_linha):
        linha = cards[i:i + por_linha]
        cols = st.columns(por_linha)
        for c, item in zip(cols, linha):
            with c:
                _card(item["titulo"], item["valor"], item.get("sub", ""),
                      item.get("cor", t.NEUTRO))


def _barra_h(df_plot, x, y, titulo, cor=None, key=None, pct=False, altura=430):
    """Barra horizontal dark (maior no topo)."""
    fig = px.bar(df_plot, x=x, y=y, orientation="h",
                 text=[f"{v:.0f}%" if pct else t.fmt(v) for v in df_plot[x]])
    fig.update_traces(marker_color=cor or t.CORES["accent"],
                      textposition="outside", cliponaxis=False)
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(t.layout(fig, altura, titulo), use_container_width=True, key=key)


# ---------------------------------------------------------------------
# preparação + filtros (compartilhados pelas duas visões)
# ---------------------------------------------------------------------
def _preparar(df_leads: pd.DataFrame) -> pd.DataFrame:
    df = df_leads.copy()
    for col in ["status_lead", "captador_nome", "bairro", "tipo_beneficio",
                "motivo_perda", "local_captacao", "unidade"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)
    df["status_lead"] = df["status_lead"].replace("", "Novo")
    df["captador_nome"] = df["captador_nome"].replace("", "Não informado")
    df["bairro"] = df["bairro"].replace("", "Não informado")
    df["tipo_beneficio"] = df["tipo_beneficio"].replace("", "Não informado")
    df["local_captacao"] = df["local_captacao"].replace("", "Não informado")
    df["unidade"] = df["unidade"].replace("", "Não informado")
    if "data_captacao" not in df.columns:
        df["data_captacao"] = pd.NaT
    df["data_captacao"] = pd.to_datetime(df["data_captacao"], errors="coerce")
    return df


def _filtros(df: pd.DataFrame, prefixo: str, com_unidade: bool):
    """Renderiza os filtros e devolve o DataFrame filtrado."""
    hoje = data.hoje()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        periodo = st.selectbox("Período", ["Últimos 7 dias", "Últimos 30 dias",
                               "Mês atual", "Todos", "Personalizado"], index=1,
                               key=f"{prefixo}_periodo")
    with c2:
        d_ini = st.date_input("Data inicial", hoje - timedelta(days=30),
                              key=f"{prefixo}_ini")
    with c3:
        d_fim = st.date_input("Data final", hoje, key=f"{prefixo}_fim")
    with c4:
        status_filtro = st.multiselect("Status", STATUS_LEAD, default=STATUS_LEAD,
                                       key=f"{prefixo}_status")

    dv = df["data_captacao"].dropna()
    dmin = dv.dt.date.min() if not dv.empty else hoje
    dmax = dv.dt.date.max() if not dv.empty else hoje
    if periodo == "Últimos 7 dias":
        data_ini, data_fim = hoje - timedelta(days=7), hoje
    elif periodo == "Últimos 30 dias":
        data_ini, data_fim = hoje - timedelta(days=30), hoje
    elif periodo == "Mês atual":
        data_ini, data_fim = hoje.replace(day=1), hoje
    elif periodo == "Todos":
        data_ini, data_fim = dmin, dmax
    else:
        data_ini, data_fim = d_ini, d_fim

    if com_unidade:
        colf = st.columns(5)
        with colf[0]:
            uni_f = st.multiselect("Unidade", sorted(df["unidade"].unique()),
                                   key=f"{prefixo}_uni")
        cols_rest = colf[1:]
    else:
        uni_f = []
        cols_rest = st.columns(4)
    with cols_rest[0]:
        atend_f = st.multiselect("Atendente", sorted(df["captador_nome"].unique()),
                                 key=f"{prefixo}_atend")
    with cols_rest[1]:
        bairro_f = st.multiselect("Bairro", sorted(df["bairro"].unique()),
                                  key=f"{prefixo}_bairro")
    with cols_rest[2]:
        benef_f = st.multiselect("Benefício", sorted(df["tipo_beneficio"].unique()),
                                 key=f"{prefixo}_benef")
    with cols_rest[3]:
        local_f = st.multiselect("Local", sorted(df["local_captacao"].unique()),
                                 key=f"{prefixo}_local")

    dc = df["data_captacao"].dt.date
    out = df[dc.notna() & (dc >= data_ini) & (dc <= data_fim)]
    if status_filtro:
        out = out[out["status_lead"].isin(status_filtro)]
    if uni_f:
        out = out[out["unidade"].isin(uni_f)]
    if atend_f:
        out = out[out["captador_nome"].isin(atend_f)]
    if bairro_f:
        out = out[out["bairro"].isin(bairro_f)]
    if benef_f:
        out = out[out["tipo_beneficio"].isin(benef_f)]
    if local_f:
        out = out[out["local_captacao"].isin(local_f)]
    return out


def _agg(df, campo, total):
    base = df.groupby(campo).agg(
        clientes=("id", "count"),
        convertidos=("status_lead", lambda s: (s == "Convertido").sum()),
        perdidos=("status_lead", lambda s: (s == "Perdido").sum()),
    ).reset_index()
    if not base.empty:
        base["conversao_%"] = (base["convertidos"] / base["clientes"] * 100).round(1)
    return base


# =====================================================================
# VISÃO 1 — DASHBOARD EXECUTIVO
# =====================================================================
def _dashboard(df_prep: pd.DataFrame):
    t.secao("🔎 Filtros Executivos")
    df = _filtros(df_prep, "dash", com_unidade=True)
    if df.empty:
        t.nota("Nenhum cliente encontrado com os filtros selecionados.", "alerta", "⚠️")
        return

    total = len(df)
    novos = int((df["status_lead"] == "Novo").sum())
    atend = int((df["status_lead"] == "Em atendimento").sum())
    agend = int((df["status_lead"] == "Agendado").sum())
    conv = int((df["status_lead"] == "Convertido").sum())
    perd = int((df["status_lead"] == "Perdido").sum())
    convp = conv / total * 100 if total else 0
    perdp = perd / total * 100 if total else 0

    # 1 — Cards executivos
    t.secao("1. Cards Executivos")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        t.kpi("Clientes", t.fmt(total), "clientes no período", t.NEUTRO, "📍")
    with c2:
        t.kpi("Em atendimento", t.fmt(atend), f"{novos} novos aguardando", t.ABERTO, "📞")
    with c3:
        t.kpi("Convertidos", t.fmt(conv), f"{convp:.1f}% de conversão", t.CUMPRIDO, "✅")
    with c4:
        t.kpi("Perdidos", t.fmt(perd), f"{perdp:.1f}% de perda", t.ATRASADO, "❌")
    with c5:
        t.kpi("Conversão", f"{convp:.1f}%", f"{conv}/{total} clientes", t.TOTAL, "📈")

    ranking = _agg(df, "captador_nome", total).sort_values(
        ["convertidos", "clientes"], ascending=False)
    ranking["em_atendimento"] = [int((df[df.captador_nome == a].status_lead == "Em atendimento").sum())
                                 for a in ranking["captador_nome"]]
    bairros = _agg(df, "bairro", total).sort_values("clientes", ascending=False)
    locais = _agg(df, "local_captacao", total).sort_values("clientes", ascending=False)

    # 2 e 3 — Funil + Evolução
    col1, col2 = st.columns(2)
    with col1:
        t.secao("2. Funil de Conversão")
        funil = pd.DataFrame({
            "Etapa": ["Clientes", "Novos", "Em atendimento", "Convertidos", "Perdidos"],
            "Quantidade": [total, novos, atend, conv, perd]})
        fig = px.funnel(funil, x="Quantidade", y="Etapa", text="Quantidade")
        fig.update_traces(marker_color=t.CORES["accent"])
        st.plotly_chart(t.layout(fig, 390), use_container_width=True, key="gr_dash_funil")
    with col2:
        t.secao("3. Evolução Diária")
        dd = df.copy()
        dd["dia"] = dd["data_captacao"].dt.date
        diario = dd.groupby("dia").size().reset_index(name="Clientes")
        figl = px.line(diario, x="dia", y="Clientes", markers=True)
        figl.update_traces(line_color=t.CORES["azul"], marker_color=t.CORES["azul"])
        st.plotly_chart(t.layout(figl, 390), use_container_width=True, key="gr_dash_evol")

    # 4 — Ranking de atendentes
    t.secao("4. Ranking de Atendentes")
    col3, col4 = st.columns([1.15, 0.85])
    with col3:
        _barra_h(ranking.head(10), "clientes", "captador_nome",
                 "Ranking por volume de clientes", t.CORES["roxo"], "gr_dash_rank")
    with col4:
        st.dataframe(ranking.rename(columns={
            "captador_nome": "Atendente", "clientes": "Clientes",
            "convertidos": "Convertidos", "em_atendimento": "Em atend.",
            "perdidos": "Perdidos", "conversao_%": "Conv. %"})[
            ["Atendente", "Clientes", "Convertidos", "Em atend.", "Perdidos", "Conv. %"]],
            use_container_width=True, hide_index=True)

    # 5 — Benefícios
    t.secao("5. Benefícios com Mais Clientes")
    bdf = df["tipo_beneficio"].value_counts().reset_index().head(12)
    bdf.columns = ["Benefício", "Quantidade"]
    _barra_h(bdf, "Quantidade", "Benefício", "", t.CORES["azul"], "gr_dash_benef")

    # 6 e 7 — Bairros
    col5, col6 = st.columns(2)
    with col5:
        t.secao("6. Bairros com Mais Clientes")
        _barra_h(bairros.head(15), "clientes", "bairro", "", t.CORES["accent"], "gr_dash_bairro_vol")
    with col6:
        t.secao("7. Bairros com Maior Conversão")
        bc = bairros[bairros["clientes"] >= 3].copy()
        if bc.empty:
            t.nota("Ainda não há volume suficiente por bairro (mínimo: 3 clientes).", "todo", "ℹ️")
        else:
            bc = bc.sort_values(["conversao_%", "convertidos", "clientes"], ascending=False).head(15)
            _barra_h(bc, "conversao_%", "bairro", "", t.CORES["ok"], "gr_dash_bairro_conv", pct=True)

    # 8 — Locais
    t.secao("8. Locais de Clientes")
    col7, col8 = st.columns(2)
    with col7:
        _barra_h(locais.head(15), "clientes", "local_captacao",
                 "Locais com mais clientes", t.CORES["accent"], "gr_dash_local_vol")
    with col8:
        lc = locais[locais["clientes"] >= 3].copy()
        if lc.empty:
            t.nota("Ainda não há volume suficiente por local (mínimo: 3 clientes).", "todo", "ℹ️")
        else:
            lc = lc.sort_values(["conversao_%", "convertidos", "clientes"], ascending=False).head(15)
            st.dataframe(lc.rename(columns={
                "local_captacao": "Local", "clientes": "Clientes",
                "convertidos": "Convertidos", "perdidos": "Perdidos",
                "conversao_%": "Conv. %"})[
                ["Local", "Clientes", "Convertidos", "Perdidos", "Conv. %"]],
                use_container_width=True, hide_index=True)

    # 9 — Motivos de perda
    t.secao("9. Motivos de Perda")
    perdas = df[df["status_lead"] == "Perdido"]
    if perdas.empty:
        t.nota("Nenhum cliente perdido no período selecionado.", "ok", "✅")
    else:
        pdf = perdas["motivo_perda"].replace("", "Não informado").value_counts().reset_index()
        pdf.columns = ["Motivo", "Quantidade"]
        _barra_h(pdf, "Quantidade", "Motivo", "", t.CORES["crit"], "gr_dash_motivos", altura=390)

    # 10 — Base (só colunas seguras; cpf/telefone/nome nunca vêm da fonte)
    t.secao("10. Base do Período")
    cols_base = [c for c in ["data_captacao", "unidade", "cidade", "bairro",
                 "local_captacao", "tipo_beneficio", "status_lead", "captador_nome",
                 "motivo_perda"] if c in df.columns]
    st.dataframe(df[cols_base].sort_values("data_captacao", ascending=False),
                 use_container_width=True, hide_index=True)
    csv = df[cols_base].to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Baixar base filtrada", csv,
                       "v360_clientes_executivo.csv", "text/csv")


# =====================================================================
# VISÃO 2 — INSIGHTS
# =====================================================================
def _insights(df_prep: pd.DataFrame):
    t.secao("🔎 Filtros dos Insights")
    df = _filtros(df_prep, "ins", com_unidade=False)
    if df.empty:
        t.nota("Nenhum cliente encontrado com os filtros selecionados.", "alerta", "⚠️")
        return

    total = len(df)
    conv = int((df["status_lead"] == "Convertido").sum())
    perd = int((df["status_lead"] == "Perdido").sum())
    convp = conv / total * 100 if total else 0
    perdp = perd / total * 100 if total else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        t.kpi("Leads no período", t.fmt(total), "total captado", t.NEUTRO, "👥")
    with k2:
        t.kpi("Convertidos", t.fmt(conv), f"{convp:.1f}% de conversão", t.CUMPRIDO, "✅")
    with k3:
        pend = int(df["status_lead"].isin(["Novo", "Em atendimento", "Agendado"]).sum())
        t.kpi("Em andamento", t.fmt(pend), "novos + atend. + agendados", t.ABERTO, "⏳")
    with k4:
        t.kpi("Perdidos", t.fmt(perd), f"{perdp:.1f}% de perda", t.ATRASADO, "❌")

    def top_valor(col):
        vc = df[col].replace("", "Não informado").value_counts()
        if vc.empty:
            return "Sem dados", 0, 0.0
        return str(vc.index[0]), int(vc.iloc[0]), (vc.iloc[0] / total * 100 if total else 0.0)

    def agg_conv(campo, minimo=3):
        base = _agg(df, campo, total)
        if base.empty:
            return base
        base = base[base["clientes"] >= minimo]
        return base.sort_values(["conversao_%", "convertidos", "clientes"], ascending=False)

    def top_conv(base, campo):
        if base.empty:
            return "Sem dados", "Volume mínimo: 3 leads"
        l = base.iloc[0]
        return str(l[campo]), f"{l['conversao_%']:.1f}% • {int(l['convertidos'])}/{int(l['clientes'])} convertidos"

    # Resumo Executivo
    t.secao("📌 Resumo Executivo")
    tb, tb_q, tb_p = top_valor("bairro")
    ta, ta_q, ta_p = top_valor("captador_nome")
    tbe, tbe_q, tbe_p = top_valor("tipo_beneficio")
    tl, tl_q, tl_p = top_valor("local_captacao")
    perdas = df[df["status_lead"] == "Perdido"]
    if perdas.empty:
        tm, tm_q, tm_p = "Sem perdas", 0, 0.0
    else:
        mvc = perdas["motivo_perda"].replace("", "Não informado").value_counts()
        tm, tm_q = str(mvc.index[0]), int(mvc.iloc[0])
        tm_p = (tm_q / len(perdas) * 100) if len(perdas) else 0.0

    _grade([
        {"titulo": "🏆 Bairro líder em leads", "valor": tb,
         "sub": f"{tb_q} leads • {tb_p:.1f}% do período", "cor": t.NEUTRO},
        {"titulo": "🥇 Atendente destaque", "valor": ta,
         "sub": f"{ta_q} leads • {ta_p:.1f}% do período", "cor": t.TOTAL},
        {"titulo": "📋 Benefício mais procurado", "valor": tbe,
         "sub": f"{tbe_q} leads • {tbe_p:.1f}% do período", "cor": t.CORES["azul"]},
        {"titulo": "🏪 Local mais produtivo", "valor": tl,
         "sub": f"{tl_q} leads • {tl_p:.1f}% do período", "cor": t.CUMPRIDO},
        {"titulo": "⚠️ Principal motivo de perda", "valor": tm,
         "sub": f"{tm_q} ocorrências • {tm_p:.1f}% das perdas", "cor": t.ATRASADO},
    ], por_linha=3)

    # Visão geral
    t.secao("📊 Visão geral")
    g1, g2 = st.columns([1, 1.3])
    with g1:
        vc = df["status_lead"].value_counts().reindex(STATUS_LEAD).dropna()
        st.plotly_chart(t.donut(vc.index, vc.values, "Leads por status", COR_STATUS),
                        use_container_width=True, key="gr_ins_donut")
    with g2:
        top_b = df["bairro"].value_counts().head(8).reset_index()
        top_b.columns = ["bairro", "n"]
        _barra_h(top_b, "n", "bairro", "Top bairros por volume de leads",
                 t.CORES["accent"], "gr_ins_bar_bairro", altura=360)

    capt_conv = agg_conv("captador_nome")
    if not capt_conv.empty:
        cc = capt_conv.head(10)
        _barra_h(cc, "conversao_%", "captador_nome",
                 "Taxa de conversão por atendente (≥3 leads)", t.CORES["ok"],
                 "gr_ins_bar_conv", pct=True, altura=360)

    # Inteligência Comercial
    t.secao("📈 Inteligência Comercial")

    def melhor_bairro_beneficio(texto):
        sub = df[df["tipo_beneficio"].str.contains(texto, case=False, na=False)]
        if sub.empty:
            return "Sem dados", "Nenhum lead encontrado"
        cv = sub[sub["status_lead"] == "Convertido"]
        base = cv if not cv.empty else sub
        vc = base["bairro"].value_counts()
        rot = "contratos" if not cv.empty else "leads"
        return str(vc.index[0]), f"{int(vc.iloc[0])} {rot} de {texto}"

    b_loas, s_loas = melhor_bairro_beneficio("LOAS")
    b_aux, s_aux = melhor_bairro_beneficio("Auxílio")

    dsem = df.copy()
    dsem["dia"] = dsem["data_captacao"].dt.weekday.map(DIAS_MAP)
    dvc = dsem["dia"].value_counts()
    melhor_dia = str(dvc.index[0]) if not dvc.empty else "Sem dados"
    melhor_dia_q = int(dvc.iloc[0]) if not dvc.empty else 0

    mes_ini = data.hoje().replace(day=1)
    dmes = df_prep.copy()
    dmes = dmes[dmes["data_captacao"].dt.date >= mes_ini]
    conv_mes = dmes[dmes["status_lead"] == "Convertido"] if not dmes.empty else pd.DataFrame()
    if conv_mes.empty:
        cap_mes, cap_mes_sub = "Sem conversões", "Nenhum contrato no mês atual"
    else:
        vc = conv_mes["captador_nome"].replace("", "Não informado").value_counts()
        cap_mes, cap_mes_sub = str(vc.index[0]), f"{int(vc.iloc[0])} conversões no mês"

    local_tx, local_tx_s = top_conv(agg_conv("local_captacao"), "local_captacao")
    bairro_tx, bairro_tx_s = top_conv(agg_conv("bairro"), "bairro")
    benef_tx, benef_tx_s = top_conv(agg_conv("tipo_beneficio"), "tipo_beneficio")
    atend_tx, atend_tx_s = top_conv(capt_conv, "captador_nome")

    _grade([
        {"titulo": "📈 Melhor bairro p/ LOAS", "valor": b_loas, "sub": s_loas},
        {"titulo": "📈 Melhor bairro p/ Auxílio", "valor": b_aux, "sub": s_aux},
        {"titulo": "📅 Melhor dia da semana", "valor": melhor_dia,
         "sub": f"{melhor_dia_q} leads no período", "cor": t.CORES["azul"]},
        {"titulo": "🥇 Melhor atendente do mês", "valor": cap_mes,
         "sub": cap_mes_sub, "cor": t.TOTAL},
        {"titulo": "🏪 Local c/ maior conversão", "valor": local_tx,
         "sub": local_tx_s, "cor": t.CUMPRIDO},
        {"titulo": "🏆 Bairro c/ maior conversão", "valor": bairro_tx,
         "sub": bairro_tx_s, "cor": t.CUMPRIDO},
        {"titulo": "📋 Benefício c/ maior conversão", "valor": benef_tx,
         "sub": benef_tx_s, "cor": t.CUMPRIDO},
        {"titulo": "👤 Atendente c/ maior conversão", "valor": atend_tx,
         "sub": atend_tx_s, "cor": t.CUMPRIDO},
    ], por_linha=4)

    # Oportunidades
    t.secao("🎯 Oportunidades")
    bairros_conv = agg_conv("bairro")
    locais_conv = agg_conv("local_captacao")
    benef_conv = agg_conv("tipo_beneficio")
    ops = []
    if not bairros_conv.empty:
        vol = df.groupby("bairro").size().reset_index(name="n").sort_values("n", ascending=False)
        topv = vol.iloc[0]
        linha = bairros_conv[bairros_conv["bairro"] == topv["bairro"]]
        if not linha.empty and float(linha.iloc[0]["conversao_%"]) < convp:
            ops.append(f"<b>{topv['bairro']}</b> tem alto volume de leads, mas conversão "
                       "abaixo da média. Vale revisar abordagem e acompanhamento.")
    if not locais_conv.empty:
        l = locais_conv.iloc[0]
        ops.append(f"<b>{l['local_captacao']}</b> tem a maior taxa de conversão "
                   f"({l['conversao_%']:.1f}%). Priorize novas ações nesse local.")
    if not benef_conv.empty:
        l = benef_conv.iloc[0]
        ops.append(f"<b>{l['tipo_beneficio']}</b> é o benefício com melhor conversão "
                   f"({l['conversao_%']:.1f}%). Pode ser prioridade em campanhas.")
    if not ops:
        ops.append("Ainda não há volume suficiente para oportunidades avançadas. "
                   "Continue cadastrando leads para o V360 identificar padrões.")
    for o in ops:
        t.nota(o, "ok", "🎯")

    # Alertas
    t.secao("🚨 Alertas")
    alertas = []
    if perdp >= 30:
        alertas.append((f"Taxa de perda em <b>{perdp:.1f}%</b> no período. "
                        "Verificar motivos e velocidade de atendimento.", "crit"))
    pendentes = int(df["status_lead"].isin(["Novo", "Em atendimento"]).sum())
    if pendentes >= max(5, int(total * 0.4)):
        alertas.append((f"Existem <b>{pendentes}</b> leads sem conclusão. "
                        "Pode haver gargalo no atendimento posterior.", "alerta"))
    if total < 10:
        alertas.append(("Volume de dados ainda baixo. Alguns insights podem mudar "
                        "bastante com novos cadastros.", "alerta"))
    if not alertas:
        alertas.append(("Nenhum alerta crítico identificado no período filtrado.", "ok"))
    for msg, tipo in alertas:
        t.nota(msg, tipo, "🚨" if tipo != "ok" else "✅")


# =====================================================================
# ENTRADA
# =====================================================================
def render(df_leads: pd.DataFrame | None = None):
    t.titulo("💼 V360 Clientes",
             "Relatório da captação — dashboard executivo e inteligência comercial",
             pills=[t.pill("Fonte: captacao_leads", t.CORES["azul"])])

    if df_leads is None:
        df_leads = data.carregar_leads()

    if df_leads is None or df_leads.empty:
        t.nota("Nenhum lead encontrado na tabela <b>captacao_leads</b>. "
               "Confirme se o sistema V360 Clientes está no mesmo projeto Supabase "
               "(ou configure <code>CAPTACAO_SUPABASE_URL</code> / "
               "<code>CAPTACAO_SUPABASE_KEY</code> nos Secrets).", "todo", "ℹ️")
        return

    df_prep = _preparar(df_leads)

    aba = st.radio("Visão", ["📊 Dashboard Executivo", "💡 Insights"],
                   horizontal=True, label_visibility="collapsed", key="capt_aba")
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    if aba.startswith("📊"):
        _dashboard(df_prep)
    else:
        _insights(df_prep)
