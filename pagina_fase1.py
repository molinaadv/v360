# =====================================================================
# V360 MOLINA — EXECUTIVO FASE 1  (dark, dirigido pelo indicadores_fase1.csv)
# =====================================================================
# Port do relatorio_fase1.py para o app novo: mesmos 21 indicadores e a
# mesma leitura do CSV (você ajusta subtipos/área na planilha), mas dark e
# organizado em ABAS por grupo (menos rolagem). Fuso Manaus via data.hoje().
# =====================================================================
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data
import theme as t
import regras as r

# ---- Benefícios & Acordos (Michelle · Tela 2) ----
G_INDEFERIDO = ["Benefício ADM - Indeferido"]
G_DEFERIDOS = ["Benefício ADM - Deferido", "Benefício ADM - Deferido REENVIO",
               "Prorrogação de Benefício ADM - Deferido", "Benefício ADM - Deferido Temporariamente",
               "Prorrogação de Benefício ADM", "PAB Concedido", "Benefício Implantado",
               "Benefício ADM - Deferido em Perícia Revisional"]
LABELS_DEF = {"Benefício ADM - Deferido": "Deferido", "Benefício ADM - Deferido REENVIO": "Deferido REENVIO",
              "Prorrogação de Benefício ADM - Deferido": "Prorrog. Deferido",
              "Benefício ADM - Deferido Temporariamente": "Deferido Temporário",
              "Prorrogação de Benefício ADM": "Prorrogação ADM", "PAB Concedido": "PAB Concedido",
              "Benefício Implantado": "Implantado", "Benefício ADM - Deferido em Perícia Revisional": "Deferido Perícia Rev."}
G_PRE_ACORDO = ["Pré-Acordo"]
G_ACORDO_AGENDADO = ["Acordo Agendado"]
G_ACORDO_REALIZADO = ["Acordo Realizado"]

# ---- Alvará & Levantamento (Michelle · Tela 3) ----
G_ALVARA = ["Precatório Disponível p/ Saque", "Precatório Expedido", "RPV Disponível p/ Saque",
            "RPV Expedido", "Aguardando Levantamento do Alvará"]
LABELS_ALV = {"Precatório Disponível p/ Saque": "Precatório Disp. Saque", "Precatório Expedido": "Precatório Expedido",
              "RPV Disponível p/ Saque": "RPV Disp. Saque", "RPV Expedido": "RPV Expedido",
              "Aguardando Levantamento do Alvará": "Aguard. Levant. Alvará"}
SINGLES_ALV = [("Acompanhamento de Cliente ao Banco", "Acomp. Cliente ao Banco", t.CORES["azul"]),
               ("Enviado ao Banco (Levantamento)", "Enviado ao Banco", t.CORES["roxo"]),
               ("Alvará Levantado", "Alvará Levantado", t.CUMPRIDO),
               ("Agendamento Recibo - RPV/Alvará", "Agend. Recibo RPV/Alvará", t.CORES["azul"]),
               ("Agendamento Receber Ofício - RPV", "Agend. Ofício RPV", t.CORES["civel"]),
               ("Pagar cliente", "Pagar Cliente", t.CORES["azul"])]

CSV_PADRAO = "indicadores_fase1.csv"
STATUS_ABERTO = ["Pendente", "Não cumprido", "Iniciado"]
STATUS_CUMPRIDO = "Cumprido"

AMBAR, VERDE, AZUL, VERM, ROXO = t.ABERTO, t.CUMPRIDO, t.NEUTRO, t.ATRASADO, t.CORES["roxo"]

ABERTAS = ["Pastas Abertas Previdenciarias e Meta", "Pastas Abertas Cível", "Pastas Abertas Trabalhista"]
PEND_ANALISE = ["Pendencia de pastas abertas", "Pendencia de pastas abertas - Iniciadas"]

SECOES = [
    {"titulo": "Atendimento Novo — Pendentes", "indicadores": ["Colaborador que abriu mais pastas ( destaque da meta )"], "subtipos": ["Atendimento Novo"], "modo": "pendente", "dim": "unidade", "cor": AMBAR},
    {"titulo": "Organização da Pasta — Pendentes", "indicadores": ["Organização de Pastas"], "modo": "pendente", "dim": "unidade", "cor": AMBAR},
    {"titulo": "Pastas Abertas (todas as unidades)", "indicadores": ABERTAS, "modo": "cumprido_mes", "dim": "unidade", "cor": AZUL},
    {"titulo": "Pastas Abertas por Área", "indicadores": ABERTAS, "modo": "cumprido_mes", "dim": "area", "chart": "pizza"},
    {"titulo": "Pastas Abertas Previdenciária", "indicadores": ["Pastas Abertas Previdenciarias e Meta"], "modo": "cumprido_mes", "dim": "unidade", "cor": AZUL},
    {"titulo": "Pastas Abertas Cíveis", "indicadores": ["Pastas Abertas Cível"], "modo": "cumprido_mes", "dim": "unidade", "cor": AZUL},
    {"titulo": "Pastas Abertas Trabalhistas", "indicadores": ["Pastas Abertas Trabalhista"], "modo": "cumprido_mes", "dim": "unidade", "cor": AZUL},
    {"titulo": "Pendências Geral", "indicadores": PEND_ANALISE, "modo": "pendente", "dim": "unidade", "cor": AMBAR},
    {"titulo": "Tipo de Pendência", "indicadores": PEND_ANALISE, "modo": "pendente", "dim": "subtipo", "cor": AMBAR},
    {"titulo": "Pastas Pendentes de Análise", "indicadores": ["Pastas a serem analisadas"], "modo": "pendente", "dim": "unidade", "cor": AMBAR},
    {"titulo": "Pastas Pendentes de Agendamento", "indicadores": ["Agendamento Administrativo"], "subtipos": ["Enviado p/ Agendamento"], "modo": "pendente", "dim": "unidade", "cor": AMBAR},
    {"titulo": "Agendamento Administrativo — Pendentes", "indicadores": ["Agendamento Administrativo"], "excluir_subtipos": ["Enviado p/ Agendamento", "Solicitar Prorrogação"], "modo": "pendente", "dim": "unidade", "cor": AMBAR},
    {"titulo": "Acompanhamento ADM — Pendentes", "indicadores": ["Acompanhamento ADM"], "modo": "pendente", "dim": "unidade", "cor": AMBAR},
    {"titulo": "Denúncias — Total e Atrasadas", "indicadores": ["Denúncia"],
     "subtipos": ["Denúncia Realizada", "Fazer Denúncia", "Fazer Denúncia - Acréscimo 25%",
                  "Fazer Denúncia - Aposentadorias", "Fazer Denúncia - Aux Acidente 50%",
                  "Fazer Denúncia - Aux por Incapacidade (Urbano e Rural)",
                  "Fazer Denúncia - BPC Idoso ou Deficiente", "Fazer Denúncia - Cadastro de Rep. Legal",
                  "Fazer Denúncia - PAB ou Reativação", "Fazer Denúncia - Pensão por Morte (Urbana e Rural)",
                  "Fazer Denúncia - Salário Maternidade", "Fazer Denúncia - Seguro Defeso"],
     "modo": "pendente_atrasado", "dim": "unidade"},
    {"titulo": "Benefício ADM - Deferido (criado no mês)", "indicadores": ["Benefício ADM - Deferido"], "subtipos": ["Benefício ADM - Deferido"], "modo": "criado_mes", "dim": "unidade", "cor": VERDE},
    {"titulo": "Benefício ADM - Indeferido (criado no mês)", "indicadores": ["Benefício ADM - Indeferido"], "modo": "criado_mes", "dim": "unidade", "cor": VERM},
    {"titulo": "Pré-Acordo — Pendente e Cumprido", "indicadores": ["Pré-Acordo"], "modo": "pendente_cumprido", "dim": "unidade"},
    {"titulo": "Acordo Agendado — Pendente e Cumprido", "indicadores": ["Acordo Agendado"], "modo": "pendente_cumprido", "dim": "unidade"},
    {"titulo": "Análise Final — Pendentes", "indicadores": ["Análise Final Previdenciária", "Análise Final Cível"], "subtipos": ["Análise Final"], "modo": "pendente", "dim": "unidade", "cor": ROXO},
    {"titulo": "Enviada p/ Confecção — Pendentes e Cumpridos", "indicadores": ["Pastas a serem distribuidas"], "modo": "pendente_cumprido", "dim": "unidade"},
    {"titulo": "Inicial enviada para Confecção — Pendentes e Cumpridos", "indicadores": ["Inicial na Confecção"], "modo": "pendente_cumprido", "dim": "unidade"},
    {"titulo": "Inicial enviada para Revisão — Pendentes e Cumpridos", "indicadores": ["Inicial na Revisão"], "modo": "pendente_cumprido", "dim": "unidade"},
    {"titulo": "Inicial enviada ao Protocolo (e Cível) — Pendentes e Cumpridos", "indicadores": ["Inicial enviada ao protocolo", "Inicial enviada ao protocolo - Cível"], "modo": "pendente_cumprido", "dim": "unidade"},
]

# abas: (rótulo, tipo, payload)
#   tipo "secoes" → lista de índices em SECOES
#   tipo "beneficios"/"alvara" → telas de desfecho no estilo dos painéis da Michelle
GRUPOS = [
    ("📂 Abertura & Pastas", "secoes", list(range(0, 7))),
    ("⚠️ Pendências & Análise", "secoes", [7, 8, 9, 18]),  # + Análise Final
    ("📅 Agendamento & ADM", "secoes", list(range(10, 13))),
    ("📢 Denúncias", "secoes", [13]),
    ("🏛️ Benefícios & Acordos", "beneficios", None),
    ("💵 Alvará & Levantamento", "alvara", None),
    ("📝 Confecção & Protocolo", "secoes", list(range(19, 23))),
]


# ---------- leitura do CSV ----------
def _split_subtipos(cel):
    if not isinstance(cel, str):
        return []
    partes = []
    for linha in cel.split("\n"):
        for p in linha.split(","):
            p = p.strip()
            if not p:
                continue
            if "(" in p:
                partes.append(p)
            else:
                for q in p.split(" e "):
                    q = q.strip()
                    if q:
                        partes.append(q)
    return partes


@st.cache_data(ttl=600, show_spinner=False)
def carregar_indicadores(caminho=CSV_PADRAO):
    p = Path(caminho)
    if not p.exists():
        return {}
    df = pd.read_csv(p)
    mapa = {}
    for _, row in df.iterrows():
        ind = str(row.get("INDICADOR", "")).strip()
        if not ind:
            continue
        e = mapa.setdefault(ind, {"area": str(row.get("AREA", "")).strip(), "subtipos": set()})
        for s in _split_subtipos(row.get("SUBTIPO", "")):
            e["subtipos"].add(s)
    return mapa


def _subtipos_da_secao(spec, mapa):
    if spec.get("subtipos"):
        return list(spec["subtipos"])
    subs = set()
    for ind in spec["indicadores"]:
        subs |= mapa.get(ind, {}).get("subtipos", set())
    excluir = set(spec.get("excluir_subtipos", []))
    return [s for s in subs if s not in excluir]


def _area_do_subtipo(mapa):
    out = {}
    for _, e in mapa.items():
        for s in e["subtipos"]:
            out[s] = e["area"] or "Não classificado"
    return out


# ---------- contagem ----------
def _entre(serie, ini, fim):
    # compara com Timestamp (não .dt.date): robusto a série vazia, que em
    # pandas 2 vira datetime64[s] e quebra a comparação com date.
    s = pd.to_datetime(serie, errors="coerce")
    return s.notna() & (s >= pd.Timestamp(ini)) & (s < pd.Timestamp(fim) + pd.Timedelta(days=1))


def _aplica_modo(df, subtipos, modo, ini, fim):
    base = df[df["subtipo_nome"].isin(subtipos)]
    if modo == "cumprido_mes":
        return base[(base["status_nome"] == STATUS_CUMPRIDO) & _entre(base["data_conclusao"], ini, fim)]
    if modo == "criado_mes":
        return base[_entre(base["creation_date"], ini, fim)]
    if modo == "pendente":
        return base[base["status_nome"].isin(STATUS_ABERTO)]
    return base


def _bar_unidade(dados, cor, key, vazio="Sem dados para este recorte."):
    g = (dados[dados["unidade_nome"].notna()].groupby("unidade_nome").size()
         .reset_index(name="total").sort_values("total", ascending=False).head(30))
    if g.empty:
        st.info(vazio)
        return
    fig = px.bar(g, x="unidade_nome", y="total", text="total")
    fig.update_traces(marker_color=cor, textposition="outside", cliponaxis=False, textfont_color=t.CORES["ink"])
    st.plotly_chart(t.layout(fig, 420, f"TOTAL {t.fmt(g['total'].sum())}"), use_container_width=True, key=key)


def _render_secao(num, spec, df, mapa, area_map, ini, fim, hoje):
    st.markdown(f'<div class="v360-section">{num}. {spec["titulo"]}</div>', unsafe_allow_html=True)
    subtipos = _subtipos_da_secao(spec, mapa)
    if not subtipos:
        st.info("Indicador não encontrado na planilha. Confira o nome no indicadores_fase1.csv.")
        return
    modo, dim = spec["modo"], spec.get("dim", "unidade")

    if modo == "pendente_cumprido":
        base = df[df["subtipo_nome"].isin(subtipos)]
        pend = base[base["status_nome"].isin(STATUS_ABERTO)]
        cump = base[(base["status_nome"] == STATUS_CUMPRIDO) & _entre(base["data_conclusao"], ini, fim)]
        g = pd.concat([pend.groupby("unidade_nome").size().rename("Pendente"),
                       cump.groupby("unidade_nome").size().rename("Cumprido")], axis=1).fillna(0).reset_index()
        if g.empty:
            st.info("Sem dados para este recorte.")
            return
        g = g.sort_values("Pendente", ascending=False)
        longo = g.melt(id_vars="unidade_nome", var_name="Situação", value_name="Qtd")
        fig = px.bar(longo, x="unidade_nome", y="Qtd", color="Situação", text="Qtd", barmode="group",
                     color_discrete_map={"Pendente": AMBAR, "Cumprido": VERDE})
        fig.update_traces(textposition="outside", cliponaxis=False, textfont_color=t.CORES["ink"])
        st.plotly_chart(t.layout(fig, 440, f"Pendente: {t.fmt(g['Pendente'].sum())} · Cumprido: {t.fmt(g['Cumprido'].sum())}"),
                        use_container_width=True, key=f"fs_{num}_pc")
        return

    if modo == "pendente_atrasado":
        base = df[df["subtipo_nome"].isin(subtipos)]
        pend = base[base["status_nome"].isin(STATUS_ABERTO)]
        if "end_datetime" in pend.columns:
            dm = pd.to_datetime(pend["end_datetime"], errors="coerce")
            atras = pend[dm.notna() & (dm < pd.Timestamp(hoje))]
        else:
            atras = pend.iloc[0:0]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Total pendentes**")
            _bar_unidade(pend, AMBAR, key=f"fs_{num}_pend")
        with c2:
            st.markdown("**Atrasadas — prazo vencido**")
            _bar_unidade(atras, VERM, key=f"fs_{num}_atr", vazio="Nenhuma atrasada (ou sem prazo preenchido).")
        return

    dados = _aplica_modo(df, subtipos, modo, ini, fim)
    if dados.empty:
        st.info("Sem dados para este recorte.")
        return

    if dim == "area":
        d = dados.copy()
        d["_area"] = d["subtipo_nome"].map(area_map).fillna("Não classificado")
        g = d.groupby("_area").size().reset_index(name="total").sort_values("total", ascending=False)
        st.plotly_chart(t.donut(g["_area"], g["total"], f"TOTAL {t.fmt(g['total'].sum())}"),
                        use_container_width=True, key=f"fs_{num}_area")
        return

    col = "subtipo_nome" if dim == "subtipo" else "unidade_nome"
    g = (dados[dados[col].notna()].groupby(col).size().reset_index(name="total")
         .sort_values("total", ascending=False).head(30))
    if g.empty:
        st.info("Sem dados para este recorte.")
        return
    cor = spec.get("cor", AZUL)
    tit = f"TOTAL {t.fmt(g['total'].sum())}"
    if dim == "subtipo":
        fig = px.bar(g, x="total", y=col, orientation="h", text="total")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
    else:
        fig = px.bar(g, x=col, y="total", text="total")
    fig.update_traces(marker_color=cor, textposition="outside", cliponaxis=False, textfont_color=t.CORES["ink"])
    st.plotly_chart(t.layout(fig, 430, tit), use_container_width=True, key=f"fs_{num}_bar")


def _diagnostico(df, mapa):
    with st.expander("🔧 Diagnóstico de nomes (subtipos que não casaram)"):
        nos_dados = set(df["subtipo_nome"].dropna().unique())
        achou = False
        for num, spec in enumerate(SECOES, 1):
            faltando = [s for s in _subtipos_da_secao(spec, mapa) if s not in nos_dados]
            if faltando:
                achou = True
                st.markdown(f"**{num}. {spec['titulo']}** — {len(faltando)} sem correspondência:")
                st.write(faltando)
        if not achou:
            st.success("Todos os subtipos da planilha casaram com os dados. 🎉")


# ---------- telas de desfecho (estilo painel Michelle) ----------
def _ab_cump(df, subtipos, ini, fim):
    base = df[df["subtipo_nome"].isin(subtipos)]
    aberto = int(base["status_nome"].isin(STATUS_ABERTO).sum())
    cump = int(((base["status_nome"] == STATUS_CUMPRIDO) & _entre(base["data_conclusao"], ini, fim)).sum())
    return aberto, cump


def _card_desfecho(nome, aberto, cumprido, cor):
    tot = (aberto + cumprido) or 1
    return (f'<div style="background:linear-gradient(160deg,{t.CORES["panel"]},{t.CORES["panel2"]});'
            f'border:1px solid {t.CORES["line"]};border-radius:16px;padding:16px 18px;margin-bottom:14px;'
            f'box-shadow:0 10px 30px rgba(0,0,0,.25);">'
            f'<div style="font-weight:800;color:{t.CORES["ink"]};font-size:14px;"><span style="color:{cor};">●</span> {nome}</div>'
            f'<div style="display:flex;gap:48px;margin-top:12px;">'
            f'<div><div style="font-size:34px;font-weight:900;color:{t.ABERTO};line-height:1;">{aberto}</div>'
            f'<div style="color:{t.CORES["muted"]};font-size:12px;margin-top:4px;">Em aberto</div></div>'
            f'<div><div style="font-size:34px;font-weight:900;color:{t.CUMPRIDO};line-height:1;">{cumprido}</div>'
            f'<div style="color:{t.CORES["muted"]};font-size:12px;margin-top:4px;">Cumpr./mês</div></div></div>'
            f'<div style="display:flex;height:8px;border-radius:4px;overflow:hidden;margin-top:14px;background:{t.CORES["panel2"]};">'
            f'<div style="width:{aberto / tot * 100:.1f}%;background:{t.ABERTO};"></div>'
            f'<div style="width:{cumprido / tot * 100:.1f}%;background:{t.CUMPRIDO};"></div></div></div>')


def _donut_pct(aberto, cumprido, key):
    tot = aberto + cumprido
    pct = round(cumprido / tot * 100) if tot else 0
    fig = go.Figure(go.Pie(values=[aberto or 0, cumprido or 0], labels=["Em aberto", "Cumprido"], hole=0.72,
                           sort=False, marker=dict(colors=[t.ABERTO, t.CUMPRIDO], line=dict(color=t.CORES["bg"], width=2)),
                           textinfo="none", hoverinfo="label+value"))
    fig.add_annotation(text=f"<b>{pct}%</b><br>CUMPRIDO", showarrow=False,
                       font=dict(color=t.CORES["ink"], size=20))
    fig.update_layout(showlegend=False)
    st.plotly_chart(t.layout(fig, 260), use_container_width=True, key=key)


def _linha_sub(label, aberto, cumprido, mx):
    mx = mx or 1
    return (f'<div style="margin:7px 0;">'
            f'<div style="display:flex;justify-content:space-between;color:{t.CORES["muted"]};font-size:12.5px;">'
            f'<span>{label}</span><span><b style="color:{t.ABERTO};">{aberto}</b> &nbsp;<b style="color:{t.CUMPRIDO};">{cumprido}</b></span></div>'
            f'<div style="display:flex;height:7px;border-radius:4px;overflow:hidden;margin-top:3px;background:{t.CORES["panel2"]};">'
            f'<div style="width:{aberto / mx * 100:.1f}%;background:{t.ABERTO};"></div>'
            f'<div style="width:{cumprido / mx * 100:.1f}%;background:{t.CUMPRIDO};"></div></div></div>')


def _consolidado(df, subtipos, labels, ini, fim, titulo, key):
    t.secao(titulo)
    dados = [(labels.get(s, s), *_ab_cump(df, [s], ini, fim)) for s in subtipos]
    tot_ab = sum(a for _, a, _ in dados)
    tot_cu = sum(c for _, _, c in dados)
    mx = max([a + c for _, a, c in dados] + [1])
    c1, c2 = st.columns([1, 1.5])
    with c1:
        _donut_pct(tot_ab, tot_cu, key=f"{key}_donut")
        st.markdown(
            f'<div style="display:flex;gap:28px;justify-content:center;">'
            f'<div style="text-align:center;"><div style="font-size:26px;font-weight:900;color:{t.ABERTO};">{tot_ab}</div>'
            f'<div style="color:{t.CORES["muted"]};font-size:12px;">Em aberto</div></div>'
            f'<div style="text-align:center;"><div style="font-size:26px;font-weight:900;color:{t.CUMPRIDO};">{tot_cu}</div>'
            f'<div style="color:{t.CORES["muted"]};font-size:12px;">Cumpr./mês</div></div></div>'
            f'<div style="text-align:center;color:{t.CORES["dim"]};font-size:12px;margin-top:8px;">'
            f'Total no mês: <b>{tot_ab + tot_cu}</b> ({len(subtipos)} subtipos)</div>',
            unsafe_allow_html=True)
    with c2:
        st.markdown("".join(_linha_sub(n, a, c, mx) for n, a, c in dados), unsafe_allow_html=True)


def _por_unidade_ac(df, subtipos, titulo, ini, fim, key):
    """Barras por unidade: Em aberto (laranja) + Cumprido no mês (verde) —
    mesmo formato das outras seções, só que para os desfechos."""
    t.secao(titulo)
    base = df[df["subtipo_nome"].isin(subtipos)]
    pend = base[base["status_nome"].isin(STATUS_ABERTO)]
    cump = base[(base["status_nome"] == STATUS_CUMPRIDO) & _entre(base["data_conclusao"], ini, fim)]
    g = pd.concat([pend.groupby("unidade_nome").size().rename("Em aberto"),
                   cump.groupby("unidade_nome").size().rename("Cumprido")], axis=1).fillna(0).reset_index()
    if g.empty or g[["Em aberto", "Cumprido"]].to_numpy().sum() == 0:
        st.info("Sem dados para este recorte.")
        return
    g["_tot"] = g["Em aberto"] + g["Cumprido"]
    g = g.sort_values("_tot", ascending=False).head(30)
    longo = g.melt(id_vars="unidade_nome", value_vars=["Em aberto", "Cumprido"],
                   var_name="Situação", value_name="Qtd")
    fig = px.bar(longo, x="unidade_nome", y="Qtd", color="Situação", text="Qtd", barmode="group",
                 color_discrete_map={"Em aberto": t.ABERTO, "Cumprido": t.CUMPRIDO})
    fig.update_traces(textposition="outside", cliponaxis=False, textfont_color=t.CORES["ink"])
    st.plotly_chart(t.layout(fig, 430, f"Em aberto: {t.fmt(g['Em aberto'].sum())} · Cumprido: {t.fmt(g['Cumprido'].sum())}"),
                    use_container_width=True, key=key)


def _tab_beneficios(df, ini, fim):
    _por_unidade_ac(df, G_INDEFERIDO, "Indeferido — por unidade", ini, fim, "b_ind")
    _por_unidade_ac(df, G_DEFERIDOS, "Deferidos (consolidado) — por unidade", ini, fim, "b_def")
    _por_unidade_ac(df, G_PRE_ACORDO, "Pré-Acordo — por unidade", ini, fim, "b_pre")
    _por_unidade_ac(df, G_ACORDO_AGENDADO, "Acordo Agendado — por unidade", ini, fim, "b_aga")
    _por_unidade_ac(df, G_ACORDO_REALIZADO, "Acordo Realizado — por unidade", ini, fim, "b_are")


def _tab_alvara(df, ini, fim):
    _por_unidade_ac(df, G_ALVARA, "Alvará (consolidado) — por unidade", ini, fim, "a_alv")
    for i, (sub, label, cor) in enumerate(SINGLES_ALV):
        _por_unidade_ac(df, [sub], f"{label} — por unidade", ini, fim, f"a_sing{i}")


def render(df_f, df_metas_f, ano, mes):
    ini, fim = data.periodo_mes(ano, mes)
    hoje = data.hoje()
    t.titulo("🏠 EXECUTIVO",
             f"Período: {ini.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')} · "
             "indicadores definidos na planilha indicadores_fase1.csv.",
             pills=[t.pill(f"Competência · {mes:02d}/{ano}", ROXO), t.pill("ao vivo", live=True)])

    if df_f is None or df_f.empty:
        st.warning("Sem tarefas para o recorte selecionado.")
        return

    mapa = carregar_indicadores()
    if not mapa:
        t.nota("Não encontrei <b>indicadores_fase1.csv</b> na raiz do app. Suba o arquivo ao lado do app.py.",
               "crit", "❌")
        return
    area_map = _area_do_subtipo(mapa)

    # ---- resumo rápido no topo ----
    abertas = r.entre(r.abertas(df_f), "data_conclusao", ini, fim)
    pend_an = r.pendencias_analise(df_f)
    concl = r.entre(r.cumpridas(df_f), "data_conclusao", ini, fim)
    k = st.columns(3)
    with k[0]:
        t.kpi("Pastas Abertas (mês)", t.fmt(len(abertas)), "cumpridas no mês", AZUL, "📁")
    with k[1]:
        t.kpi("Pendências de Análise", t.fmt(len(pend_an)), "em aberto", AMBAR, "⚠️")
    with k[2]:
        t.kpi("Concluídas (mês)", t.fmt(len(concl)), "todas as etapas", VERDE, "✅")

    _diagnostico(df_f, mapa)

    # ---- abas por grupo ----
    abas = st.tabs([g[0] for g in GRUPOS])
    for aba, (label, kind, payload) in zip(abas, GRUPOS):
        with aba:
            if kind == "beneficios":
                _tab_beneficios(df_f, ini, fim)
            elif kind == "alvara":
                _tab_alvara(df_f, ini, fim)
            else:
                for i in payload:
                    try:
                        _render_secao(i + 1, SECOES[i], df_f, mapa, area_map, ini, fim, hoje)
                    except Exception as e:
                        st.error(f"Seção {i + 1} ({SECOES[i]['titulo']}) falhou.")
                        st.exception(e)
