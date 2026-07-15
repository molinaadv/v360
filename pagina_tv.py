# =====================================================================
# V360 MOLINA — TV OPERACIONAL  (console: abre todas as TVs num lugar só)
# =====================================================================
# Junta num único menu:
#  1) os painéis de TV que já existem em /pages (cada um abre em tela cheia);
#  2) o Painel Operacional ADM por unidade (via painel_tv_operacional.py).
# =====================================================================
import streamlit as st

import theme as t

try:
    import painel_tv_operacional as tvop
except Exception:
    tvop = None

# Painéis-página (arquivos em /pages). label = como aparece no card.
TVS = [
    {"arq": "pages/painel_tv_michelle.py",    "nome": "Gerência (Michelle)",   "desc": "Confecção → Protocolo · Benefícios · Alvará", "ic": "📄"},
    {"arq": "pages/painel_tv_rodrigo.py",     "nome": "Rodrigo",               "desc": "Painel do núcleo do Rodrigo",                 "ic": "📄"},
    {"arq": "pages/painel_tv_analise.py",     "nome": "Análise",               "desc": "Núcleo de Análise",                           "ic": "🔎"},
    {"arq": "pages/painel_tv_aparecida.py",   "nome": "Aparecida",             "desc": "Unidade Aparecida",                           "ic": "🏢"},
    {"arq": "pages/painel_tv_compensa.py",    "nome": "Compensa",              "desc": "Unidade Compensa",                            "ic": "🏢"},
    {"arq": "pages/painel_tv_iranduba.py",    "nome": "Iranduba",              "desc": "Unidade Iranduba",                            "ic": "🏢"},
    {"arq": "pages/painel_tv_itacoatiara.py", "nome": "Itacoatiara",           "desc": "Unidade Itacoatiara",                         "ic": "🏢"},
    {"arq": "pages/painel_tv_manacapuru.py",  "nome": "Manacapuru",            "desc": "Unidade Manacapuru",                          "ic": "🏢"},
    {"arq": "pages/painel_tv_portovelho1.py", "nome": "Porto Velho 1",         "desc": "Unidade Porto Velho - Unid 1",                "ic": "🏢"},
    {"arq": "pages/painel_tv.py",             "nome": "Painel TV (geral)",     "desc": "Painel rotativo geral / modelo",              "ic": "📺"},
]


def _card(nome, desc, ic, extra_html=""):
    st.markdown(
        f"""<div style="background:linear-gradient(160deg,{t.CORES['panel']},{t.CORES['panel2']});
             border:1px solid {t.CORES['line']};border-radius:16px;padding:16px 16px 12px;
             min-height:120px;box-shadow:0 10px 30px rgba(0,0,0,.25);margin-bottom:6px;">
            <div style="font-weight:800;color:{t.CORES['ink']};font-size:15px;">{ic} {nome}</div>
            <div style="color:{t.CORES['muted']};font-size:12.5px;margin-top:6px;">{desc}</div>
            {extra_html}
        </div>""",
        unsafe_allow_html=True,
    )


def render(df_tasks, df_colabs=None, df_metas=None):
    t.titulo("📺 TV OPERACIONAL",
             "Abra qualquer painel na TV a partir daqui. Na TV, aperte F para tela cheia — "
             "sincroniza sozinho a cada 5 min.",
             pills=[t.pill("painéis por núcleo / unidade", t.NEUTRO), t.pill("ao vivo", live=True)])

    # ---- 1) Painéis-página ----
    t.secao("Painéis por núcleo e unidade")
    cols = st.columns(3)
    for i, tv in enumerate(TVS):
        with cols[i % 3]:
            _card(tv["nome"], tv["desc"], tv["ic"])
            try:
                st.page_link(tv["arq"], label="▶  Abrir na TV", use_container_width=True)
            except Exception:
                # fallback se page_link não resolver o caminho
                url = "/" + tv["arq"].split("/")[-1].replace(".py", "")
                st.link_button("▶  Abrir na TV", url, use_container_width=True)

    # ---- 2) Painel Operacional ADM por unidade ----
    if tvop is None:
        return
    t.secao("Painel Operacional ADM (por unidade)")
    if "unidade_nome" not in df_tasks.columns:
        return
    unidades = sorted(df_tasks["unidade_nome"].dropna().astype(str).unique())
    if not unidades:
        return
    unidade = st.selectbox("Unidade", unidades)
    setores = tvop.UNIDADE_SETORES.get(unidade, list(tvop.SETORES.keys()))

    cols = st.columns(3)
    for i, chave in enumerate(setores):
        cfg = tvop.SETORES.get(chave)
        if not cfg:
            continue
        try:
            dados = tvop.montar_dados(df_tasks, df_colabs, df_metas, unidade, chave)
            areas = dados["setor"]["areas"]
            tot_pend = sum(a["atrasados"] + a["pendDia"] + a["pendFut"] for a in areas)
            tot_cump = sum(a["cumpridoMes"] for a in areas)
        except Exception:
            tot_pend = tot_cump = 0
        link = f"?setor={chave}&unidade={unidade}"
        with cols[i % 3]:
            extra = (f'<div style="margin-top:10px;color:{t.CORES["muted"]};font-size:12.5px;">'
                     f'Pendências: <b style="color:{t.ABERTO};">{tot_pend}</b> · '
                     f'Cumpridos/mês: <b style="color:{t.CUMPRIDO};">{tot_cump}</b></div>')
            _card(cfg["titulo"], f"Unidade: {unidade}", "🖥️", extra)
            st.link_button("▶  Abrir na TV", link, use_container_width=True)
            st.code(link, language=None)
