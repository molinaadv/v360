# =====================================================================
# V360 MOLINA — TV OPERACIONAL  (console: abre todas as TVs num lugar só)
# =====================================================================
# Cada painel é um CARD CLICÁVEL (o card inteiro é o botão "Abrir na TV").
# Sem widget separado, sem caixa branca. Abre em nova aba.
#  1) painéis-página de /pages (URL = nome do arquivo);
#  2) Painel Operacional ADM por unidade (?setor=adm&unidade=…).
# =====================================================================
from urllib.parse import quote

import streamlit as st

import theme as t

try:
    import painel_tv_operacional as tvop
except Exception:
    tvop = None

# arq = caminho em /pages · slug = URL da página (nome do arquivo sem .py)
TVS = [
    {"arq": "painel_tv_michelle",    "nome": "Gerência (Michelle)", "desc": "Confecção → Protocolo · Benefícios · Alvará", "ic": "📄"},
    {"arq": "painel_tv_rodrigo",     "nome": "Rodrigo",             "desc": "Painel do núcleo do Rodrigo",                 "ic": "📄"},
    {"arq": "painel_tv_analise",     "nome": "Análise",             "desc": "Núcleo de Análise",                           "ic": "🔎"},
    {"arq": "painel_tv_aparecida",   "nome": "Aparecida",           "desc": "Unidade Aparecida",                           "ic": "🏢"},
    {"arq": "painel_tv_compensa",    "nome": "Compensa",            "desc": "Unidade Compensa",                            "ic": "🏢"},
    {"arq": "painel_tv_iranduba",    "nome": "Iranduba",            "desc": "Unidade Iranduba",                            "ic": "🏢"},
    {"arq": "painel_tv_itacoatiara", "nome": "Itacoatiara",         "desc": "Unidade Itacoatiara",                         "ic": "🏢"},
    {"arq": "painel_tv_manacapuru",  "nome": "Manacapuru",          "desc": "Unidade Manacapuru",                          "ic": "🏢"},
    {"arq": "painel_tv_portovelho1", "nome": "Porto Velho 1",       "desc": "Unidade Porto Velho - Unid 1",                "ic": "🏢"},
    {"arq": "painel_tv",             "nome": "Painel TV (geral)",   "desc": "Painel rotativo geral / modelo",              "ic": "📺"},
]


def _card_link(href, nome, desc, ic, extra_html=""):
    """Card inteiro clicável (é o próprio botão 'Abrir na TV'). Abre em nova aba.
    HTML numa linha só de propósito: indentação faz o Streamlit tratar como
    bloco de código e vazar '</div></a>' na tela."""
    titulo = (f'<div style="font-weight:900;color:{t.CORES["ink"]};'
              f'font-size:clamp(18px,1.5vw,22px);text-align:center;">{ic} {nome}</div>')
    sub = (f'<div style="color:{t.CORES["muted"]};font-size:13px;margin-top:6px;'
           f'text-align:center;">{desc}</div>')
    btn = '<div class="tvbtn">▶&nbsp; Abrir na TV</div>'
    return (f'<a href="{href}" target="_blank" class="tvcard-link">'
            f'<div class="tvcard">{titulo}{sub}{extra_html}{btn}</div></a>')


def render(df_tasks, df_colabs=None, df_metas=None):
    t.titulo("📺 TV OPERACIONAL",
             "Clique no painel para abrir na TV (nova aba). Na TV, aperte F para tela cheia — "
             "sincroniza sozinho a cada 5 min.",
             pills=[t.pill("painéis por núcleo / unidade", t.NEUTRO), t.pill("ao vivo", live=True)])

    # ---- 1) Painéis-página ----
    t.secao("Painéis por núcleo e unidade")
    cols = st.columns(3)
    for i, tv in enumerate(TVS):
        # URL relativa à raiz do app (a página vive em /pages, servida em /<slug>)
        cols[i % 3].markdown(_card_link(tv["arq"], tv["nome"], tv["desc"], tv["ic"]),
                             unsafe_allow_html=True)

    # ---- 2) Painel PADRÃO por unidade (perícias & audiências, todas as telas) ----
    t.secao("Painel padrão por unidade")
    st.caption("Um modelo único (perícias, audiências, pendências, pastas e meta) que abre "
               "para a unidade que você escolher — sem precisar de um arquivo por unidade.")
    if "unidade_nome" in df_tasks.columns:
        uni_lst = sorted(df_tasks["unidade_nome"].dropna().astype(str).unique())
        if uni_lst:
            u_pad = st.selectbox("Escolha a unidade", uni_lst, key="tvpadrao_uni")
            href = f"painel_tv_padrao?unidade={quote(str(u_pad))}"
            colp = st.columns(3)
            colp[0].markdown(
                _card_link(href, u_pad, "Painel padrão · todas as telas", "🖥️"),
                unsafe_allow_html=True)

    # ---- 3) Painel Operacional ADM por unidade ----
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
        extra = (f'<div style="margin-top:10px;color:{t.CORES["muted"]};font-size:12.5px;">'
                 f'Pendências: <b style="color:{t.ABERTO};">{tot_pend}</b> · '
                 f'Cumpridos/mês: <b style="color:{t.CUMPRIDO};">{tot_cump}</b></div>')
        href = f"?setor={chave}&unidade={unidade}"
        cols[i % 3].markdown(_card_link(href, cfg["titulo"], f"Unidade: {unidade}", "🖥️", extra),
                             unsafe_allow_html=True)
