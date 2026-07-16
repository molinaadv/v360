# =====================================================================
# V360 MOLINA — AUDIÊNCIAS E PERÍCIAS  (agrupado por ADM / JUD / AVS)
# =====================================================================
# O agrupamento é pelo ASSUNTO (subtipo), que já traz o marcador:
#   ADM = Perícia ADM · JUD = Perícia JUD / Audiência · AVS = Avaliação Social
# Fontes: vw_tasks_completa (ADM/AVS) + vw_compromissos_completa (JUD).
# Data do evento = end_datetime. Situação: aberto/cumprido/cancelado;
# atraso = aberto com evento já vencido (hoje em Manaus).
# =====================================================================
import unicodedata

import pandas as pd
import plotly.express as px
import streamlit as st

import data
import theme as t
import regras as r
from export import botao_export

COL_EVENTO = "end_datetime"
STATUS_TODOS = ["Pendente", "Não cumprido", "Iniciado", "Cumprido", "Cancelado", "Recusado"]
STATUS_ID_MAP = {0: "Pendente", 1: "Cumprido", 2: "Não cumprido",
                 3: "Cancelado", 4: "Iniciado", 5: "Recusado"}
CORES_SIT = {"Em aberto": t.ABERTO, "Cumprido": t.CUMPRIDO,
             "Atraso": t.ATRASADO, "Cancelado": t.CORES["muted"]}
CORES_GRUPO = {"ADM": t.NEUTRO, "JUD": t.CORES["roxo"], "AVS": t.CORES["azul"]}


def _norm(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii").upper()


def _grupo(sub):
    """Grupo do assunto: ADM, JUD ou AVS (None se não for audiência/perícia)."""
    s = _norm(sub)
    if "AVALIACAO SOCIAL" in s or "AVS" in s:
        return "AVS"
    if "JUD" in s or "AUDIENCIA" in s:
        return "JUD"
    if "ADM" in s or "PERICIA" in s:
        return "ADM"
    return None


def _col(df, *names):
    low = {c.lower(): c for c in df.columns}
    for n in names:
        if n.lower() in low:
            return low[n.lower()]
    return None


def _situacao(row, hoje):
    stt = row["Status"]
    if stt == "Cumprido":
        return "Cumprido"
    if stt == "Cancelado":
        return "Cancelado"
    if stt in r.STATUS_ABERTO:
        ev = row["_evento"]
        return "Atraso" if (pd.notna(ev) and ev.date() < hoje) else "Em aberto"
    return "Outro"


def _fonte_tarefas(df_f):
    if df_f is None or df_f.empty:
        return pd.DataFrame()
    base = df_f.copy()
    base["_grupo"] = base["subtipo_nome"].map(_grupo)
    base = base[base["_grupo"].notna()]
    if base.empty:
        return pd.DataFrame()
    return pd.DataFrame({
        "Unidade": base["unidade_nome"], "Subtipo": base["subtipo_nome"],
        "Status": base["status_nome"], "_grupo": base["_grupo"],
        "_evento": pd.to_datetime(base.get(COL_EVENTO), errors="coerce"),
        "Responsável": base.get("responsavel_nome"),
    })


def _fonte_compromissos(df_comp):
    if df_comp is None or df_comp.empty:
        return pd.DataFrame(), {}
    cu = _col(df_comp, "unidade_nome", "unidade_principal", "unidade", "escritorio")
    cs = _col(df_comp, "subtipo_nome", "subtipo", "tipo_nome", "tipo")
    cst = _col(df_comp, "status_nome", "status")
    cid = _col(df_comp, "status_id", "statusid")
    cev = _col(df_comp, COL_EVENTO, "data_evento", "data_final", "start_datetime")
    ccli = _col(df_comp, "cliente_nome", "responsavel_nome", "contact_name")
    diag = {"unidade": cu, "subtipo": cs, "status": cst or cid, "evento": cev, "cliente": ccli}

    out = pd.DataFrame(index=df_comp.index)
    out["Unidade"] = df_comp[cu] if cu else "—"
    out["Subtipo"] = df_comp[cs] if cs else "Compromisso JUD"
    if cst:
        out["Status"] = df_comp[cst]
    elif cid:
        out["Status"] = pd.to_numeric(df_comp[cid], errors="coerce").map(STATUS_ID_MAP)
    else:
        out["Status"] = "Pendente"
    out["_grupo"] = out["Subtipo"].map(lambda s: _grupo(s) or "JUD")   # compromisso = JUD
    out["_evento"] = pd.to_datetime(df_comp[cev], errors="coerce") if cev else pd.NaT
    out["Responsável"] = df_comp[ccli] if ccli else None
    return out.reset_index(drop=True), diag


def render(df_f, df_comp, ano: int, mes: int):
    ini, fim = data.periodo_mes(ano, mes)
    hoje = data.hoje()
    t.titulo("⚖️ AUDIÊNCIAS E PERÍCIAS",
             "Agrupado por assunto: ADM · JUD · AVS (avaliação social) — por unidade.",
             pills=[t.pill(f"Competência · {mes:02d}/{ano}", t.CORES["roxo"]), t.pill("ao vivo", live=True)])

    tarefas = _fonte_tarefas(df_f)
    comp, diag = _fonte_compromissos(df_comp)
    base = pd.concat([x for x in (tarefas, comp) if not x.empty], ignore_index=True)
    if base.empty:
        t.nota("Não encontrei audiências/perícias no recorte.", "todo", "🔎")
        _diagnostico(df_comp, diag)
        return

    # ---- controles ----
    c1, c2, c3 = st.columns([1.1, 1.2, 1.4])
    with c1:
        recorte = st.radio("Data do evento", ["Mês selecionado", "Todas as datas"])
    with c2:
        grupos = sorted(base["_grupo"].dropna().unique())
        g_sel = st.multiselect("Assunto (grupo)", grupos, default=grupos)
    with c3:
        st_op = [s for s in STATUS_TODOS if s in base["Status"].unique()]
        st_sel = st.multiselect("Status (LegalOne)", st_op, default=st_op)

    d = base[base["_grupo"].isin(g_sel) & base["Status"].isin(st_sel)].copy()
    if recorte == "Mês selecionado":
        d = d[d["_evento"].notna() & (d["_evento"].dt.date >= ini) & (d["_evento"].dt.date <= fim)]
    if d.empty:
        t.nota("Nenhum registro para os filtros selecionados.", "todo", "📐")
        _diagnostico(df_comp, diag)
        return
    d["Situação"] = d.apply(lambda row: _situacao(row, hoje), axis=1)

    # ---- KPIs situação ----
    t.secao("Situação")
    ns = lambda s: int((d["Situação"] == s).sum())
    k = st.columns(5)
    with k[0]:
        t.kpi("Total", t.fmt(len(d)), "audiências + perícias", t.NEUTRO, "⚖️")
    with k[1]:
        t.kpi("Em aberto", t.fmt(ns("Em aberto")), "aguardando", t.ABERTO, "🟠")
    with k[2]:
        t.kpi("Cumprido", t.fmt(ns("Cumprido")), "realizados", t.CUMPRIDO, "✅")
    with k[3]:
        t.kpi("Atraso", t.fmt(ns("Atraso")), "evento vencido e em aberto", t.ATRASADO, "🔴")
    with k[4]:
        t.kpi("Cancelado", t.fmt(ns("Cancelado")), "cancelados", t.CORES["muted"], "⚪")

    # ---- KPIs por grupo ----
    t.secao("Por assunto (ADM · JUD · AVS)")
    ng = lambda g: int((d["_grupo"] == g).sum())
    kg = st.columns(3)
    for i, (g, ic) in enumerate([("ADM", "🏛️"), ("JUD", "⚖️"), ("AVS", "🧑‍⚕️")]):
        with kg[i]:
            t.kpi(g, t.fmt(ng(g)),
                  {"ADM": "Perícia ADM", "JUD": "Perícia JUD + Audiência",
                   "AVS": "Avaliação Social"}[g], CORES_GRUPO[g], ic)

    # ---- composição ----
    c1, c2 = st.columns([1, 1.4])
    with c1:
        t.secao("Distribuição por assunto")
        vc = d["_grupo"].value_counts()
        st.plotly_chart(t.donut(vc.index, vc.values, "ADM · JUD · AVS", CORES_GRUPO),
                        use_container_width=True)
    with c2:
        t.secao("Por unidade (situação)")
        g = d.groupby(["Unidade", "Situação"]).size().reset_index(name="Qtd")
        if not g.empty:
            fig = px.bar(g, x="Unidade", y="Qtd", color="Situação", barmode="stack",
                         color_discrete_map=CORES_SIT,
                         category_orders={"Situação": ["Em aberto", "Atraso", "Cumprido", "Cancelado"]})
            st.plotly_chart(t.layout(fig, 460), use_container_width=True)

    # ---- tabela por unidade (grupo + situação) ----
    t.secao("Todos os dados por unidade")
    pg = d.pivot_table(index="Unidade", columns="_grupo", values="Status", aggfunc="count", fill_value=0)
    for g in ["ADM", "JUD", "AVS"]:
        if g not in pg.columns:
            pg[g] = 0
    ps = d.pivot_table(index="Unidade", columns="Situação", values="Status", aggfunc="count", fill_value=0)
    for s in ["Em aberto", "Atraso", "Cumprido", "Cancelado"]:
        if s not in ps.columns:
            ps[s] = 0
    tab = pd.concat([pg[["ADM", "JUD", "AVS"]], ps[["Em aberto", "Atraso", "Cumprido", "Cancelado"]]], axis=1)
    tab.insert(0, "Total", tab[["ADM", "JUD", "AVS"]].sum(axis=1))
    tab = tab.sort_values("Total", ascending=False).reset_index()
    st.dataframe(tab, use_container_width=True, hide_index=True)

    # ---- detalhado + export ----
    t.secao("Detalhado e exportação")
    det = d[["_evento", "Unidade", "_grupo", "Subtipo", "Status", "Situação", "Responsável"]].rename(
        columns={"_evento": "Evento", "_grupo": "Grupo"})
    st.dataframe(det.sort_values("Evento", ascending=False).head(1000),
                 use_container_width=True, hide_index=True)
    botao_export({"Por_unidade": tab, "Detalhado": det}, nome=f"audiencias_pericias_{ano}_{mes:02d}")
    _diagnostico(df_comp, diag)


def _diagnostico(df_comp, diag):
    with st.expander("🔎 Diagnóstico da view de compromissos (JUD)"):
        if df_comp is None or df_comp.empty:
            st.warning("A view `vw_compromissos_completa` veio vazia ou não existe. "
                       "As audiências/perícias JUD só entram quando ela estiver acessível.")
            return
        st.markdown("**Colunas detectadas:**")
        st.json({k: (v or "❌ não encontrada") for k, v in diag.items()})
        st.markdown("**Todas as colunas da view:**")
        st.write(sorted(df_comp.columns.tolist()))
