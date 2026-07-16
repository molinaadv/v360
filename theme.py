# =====================================================================
# V360 MOLINA — DESIGN SYSTEM DARK  (tokens do painel de TV)
# =====================================================================
# Tema dark dos painéis de TV (seção 4 da base de conhecimento), agora
# no app de Relatório. Semântica de cor consistente em tudo:
#   laranja = em aberto · verde = cumprido · vermelho = atrasado/pendência
#   azul = futuras/neutro · roxo = total/destaque
# Todos os componentes (cards, pills, donut, barra segmentada) e o layout
# dos gráficos Plotly vivem aqui — as páginas só consomem.
# =====================================================================
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------
# TOKENS
# ---------------------------------------------------------------------
CORES = {
    "bg":     "#0b1220",
    "panel":  "#141d2e",
    "panel2": "#1b2740",
    "line":   "#26324d",
    "ink":    "#f2f6ff",
    "muted":  "#93a1bd",
    "dim":    "#6b7a99",
    "accent": "#5b8cff",   # azul/neutro
    "warn":   "#f5a524",   # laranja  → EM ABERTO
    "ok":     "#2fce8f",   # verde    → CUMPRIDO
    "crit":   "#ef7a7a",   # vermelho → atrasado/pendência
    "roxo":   "#8b7bff",   # total/destaque
    "civel":  "#f38ba8",
    "azul":   "#4fb0e8",
}

# apelidos semânticos (usar estes nas páginas p/ manter consistência)
ABERTO   = CORES["warn"]
CUMPRIDO = CORES["ok"]
ATRASADO = CORES["crit"]
NEUTRO   = CORES["accent"]
TOTAL    = CORES["roxo"]

# sequência categórica para gráficos com muitas séries
SEQUENCIA = [CORES["accent"], CORES["ok"], CORES["warn"], CORES["roxo"],
             CORES["azul"], CORES["civel"], CORES["crit"], CORES["muted"]]

FONTE = '-apple-system, "Segoe UI", Roboto, Inter, Arial, sans-serif'


# ---------------------------------------------------------------------
# CSS GLOBAL
# ---------------------------------------------------------------------
def injetar_css():
    # SEMPRE injeta: o Streamlit reconstrói o DOM a cada rerun, então um guard
    # em session_state faria o estilo sumir depois do login (bug que deixava o
    # app claro e trazia de volta o menu automático de páginas).
    st.markdown(
        f"""
        <style>
        :root {{
            --bg:{CORES['bg']}; --panel:{CORES['panel']}; --panel2:{CORES['panel2']};
            --line:{CORES['line']}; --ink:{CORES['ink']}; --muted:{CORES['muted']};
            --dim:{CORES['dim']}; --accent:{CORES['accent']}; --warn:{CORES['warn']};
            --ok:{CORES['ok']}; --crit:{CORES['crit']}; --roxo:{CORES['roxo']};
        }}
        .stApp {{ background: radial-gradient(1200px 800px at 20% -10%, #10203c 0%, var(--bg) 55%); }}
        .block-container {{ padding-top: 1.1rem; padding-left: 1.8rem; padding-right: 1.8rem; }}
        html, body, [class*="css"] {{ font-family: {FONTE}; }}

        /* textos padrão claros */
        .stApp, .stMarkdown, p, span, label, .stCaption {{ color: var(--ink); }}

        /* esconde o menu automático de páginas do Streamlit (as TVs ficam
           no nosso menu "TV Operacional", não espalhadas na barra) */
        [data-testid="stSidebarNav"] {{ display: none !important; }}

        /* barra branca do topo (header do Streamlit) → transparente */
        header[data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}

        /* botões e links da área principal (Atualizar, Entrar, export, Abrir na TV) → dark */
        .stButton > button, .stDownloadButton > button, .stLinkButton > a,
        .stFormSubmitButton > button, [data-testid="stFormSubmitButton"] button {{
            background: var(--panel2) !important; color: var(--ink) !important;
            border: 1px solid var(--line) !important; border-radius: 12px !important;
            font-weight: 700 !important;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover, .stLinkButton > a:hover,
        .stFormSubmitButton > button:hover, [data-testid="stFormSubmitButton"] button:hover {{
            border-color: var(--accent) !important; background: rgba(91,140,255,.16) !important; color: #fff !important;
        }}
        /* st.page_link (o "▶ Abrir na TV" dos cards) → botão dark, não caixa branca */
        a[data-testid="stPageLink-NavLink"] {{
            background: var(--panel2) !important; border: 1px solid var(--line) !important;
            border-radius: 12px !important; padding: 10px 14px !important; justify-content: center !important;
        }}
        a[data-testid="stPageLink-NavLink"]:hover {{
            background: rgba(91,140,255,.16) !important; border-color: var(--accent) !important;
        }}
        a[data-testid="stPageLink-NavLink"] p,
        a[data-testid="stPageLink-NavLink"] span {{ color: var(--ink) !important; font-weight: 700 !important; }}

        /* -------- SIDEBAR -------- */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #0a1428 0%, #0b1220 100%) !important;
            border-right: 1px solid var(--line); width: 250px !important;
        }}
        section[data-testid="stSidebar"] * {{ color: var(--ink) !important; }}
        .sidebar-logo {{ padding: 6px 8px 18px 8px; }}
        .sidebar-logo .v360 {{ font-size: 40px; font-weight: 900; letter-spacing: -2px; line-height: .95; color: #fff; }}
        .sidebar-logo .molina {{ font-size: 11px; font-weight: 700; letter-spacing: 2px; color: var(--muted); margin-top: 2px; }}
        section[data-testid="stSidebar"] .stButton > button {{
            width: 100% !important; text-align: left !important; background: transparent !important;
            border: 1px solid transparent !important; color: var(--ink) !important; border-radius: 12px !important;
            padding: 9px 12px !important; min-height: 38px !important; font-weight: 700 !important; box-shadow: none !important;
        }}
        section[data-testid="stSidebar"] .stButton > button:hover {{
            background: rgba(91,140,255,.10) !important; border-color: rgba(91,140,255,.25) !important;
        }}
        .menu-active .stButton > button {{
            background: linear-gradient(90deg, rgba(91,140,255,.28), rgba(91,140,255,.08)) !important;
            border-color: rgba(91,140,255,.55) !important; box-shadow: 0 6px 18px rgba(91,140,255,.18) !important;
        }}

        /* -------- TÍTULOS -------- */
        .v360-title {{ font-size: clamp(26px,3vw,38px); font-weight: 900; color: var(--ink);
            letter-spacing: -.5px; margin-bottom: 2px; }}
        .v360-subtitle {{ font-size: 14px; color: var(--muted); margin-bottom: 16px; }}
        .v360-section {{ font-size: 20px; font-weight: 800; color: var(--ink); margin: 26px 0 10px;
            padding-bottom: 8px; border-bottom: 1px solid var(--line); }}

        /* -------- PILLS -------- */
        .pill {{ display:inline-flex; align-items:center; gap:6px; background: var(--panel2);
            border: 1px solid var(--line); color: var(--muted); border-radius: 999px;
            padding: 5px 12px; font-size: 12px; font-weight: 700; margin-right: 8px; }}
        .pill .dot {{ width:8px; height:8px; border-radius:50%; background: var(--accent); }}
        .pill.live .dot {{ background: var(--ok); box-shadow: 0 0 0 0 rgba(47,206,143,.6); animation: pulse 1.8s infinite; }}
        @keyframes pulse {{ 0%{{box-shadow:0 0 0 0 rgba(47,206,143,.5);}} 70%{{box-shadow:0 0 0 7px rgba(47,206,143,0);}} 100%{{box-shadow:0 0 0 0 rgba(47,206,143,0);}} }}

        /* -------- CARDS KPI -------- */
        .kpi {{ background: linear-gradient(160deg, var(--panel) 0%, var(--panel2) 100%);
            border: 1px solid var(--line); border-radius: 18px; padding: 18px 18px 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,.25); min-height: 128px; position: relative; overflow: hidden; }}
        .kpi::before {{ content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background: var(--accent); opacity:.9; }}
        .kpi .lbl {{ color: var(--muted); font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing:.4px; }}
        .kpi .val {{ font-size: clamp(34px,4.4vw,48px); font-weight: 900; line-height: 1; margin-top: 10px; color: var(--ink); }}
        .kpi .sub {{ color: var(--dim); font-size: 12.5px; font-weight: 600; margin-top: 8px; }}

        /* -------- CARD CLICÁVEL DA TV (o card inteiro é o botão) -------- */
        a.tvcard-link {{ text-decoration: none !important; display: block; }}
        .tvcard {{ background: linear-gradient(160deg, var(--panel), var(--panel2));
            border: 1px solid var(--line); border-radius: 16px; padding: 16px; margin-bottom: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,.25);
            transition: transform .15s, border-color .15s, box-shadow .15s; }}
        .tvcard:hover {{ transform: translateY(-2px); border-color: var(--accent);
            box-shadow: 0 14px 36px rgba(91,140,255,.20); }}
        /* o Streamlit pinta TODO texto dentro de <a> com a cor primária (azul);
           forçamos branco em tudo do card, com especificidade alta */
        a.tvcard-link, a.tvcard-link *, a.tvcard-link:hover, a.tvcard-link:visited {{ color: #ffffff !important; }}
        .tvcard-title {{ font-weight: 900; text-align: center;
            font-size: clamp(18px,1.5vw,22px); color: #ffffff !important; }}
        a.tvcard-link .tvcard-sub {{ text-align: center; margin-top: 6px; font-size: 13px;
            color: #93a1bd !important; }}
        /* botão no azul-escuro do fundo da página (hover discreto, sem acender) */
        .tvbtn {{ margin-top: 16px; text-align: center; background: var(--bg);
            border: 1px solid var(--accent); border-radius: 12px; padding: 11px 12px;
            color: #ffffff !important; font-weight: 800; font-size: 14px; }}
        a.tvcard-link:hover .tvbtn {{ background: #16223d; border-color: var(--accent);
            color: #ffffff !important; }}

        /* -------- NOTAS / ALERTAS -------- */
        .nota {{ border-radius: 14px; padding: 12px 16px; margin: 6px 0; font-size: 14px;
            border: 1px solid var(--line); border-left: 5px solid var(--accent); background: var(--panel); color: var(--ink); }}
        .nota.ok {{ border-left-color: var(--ok); }}
        .nota.alerta {{ border-left-color: var(--warn); }}
        .nota.crit {{ border-left-color: var(--crit); }}
        .nota.todo {{ border-style: dashed; color: var(--muted); }}

        /* -------- EXPANDER / INPUTS DARK -------- */
        div[data-testid="stExpander"] {{ background: var(--panel); border: 1px solid var(--line); border-radius: 14px; }}
        div[data-testid="stExpander"] summary {{ color: var(--ink) !important; }}
        div[data-baseweb="select"] > div {{ background: var(--panel2) !important; border-color: var(--line) !important; color: var(--ink) !important; }}
        .stTextInput input, .stNumberInput input {{ background: var(--panel2) !important; color: var(--ink) !important; border-color: var(--line) !important; }}
        div[data-testid="stDataFrame"] {{ background: var(--panel); border: 1px solid var(--line); border-radius: 14px; }}
        .v360-foot {{ color: var(--dim); font-size: 12px; margin-top: 20px; padding-top: 12px; border-top: 1px solid var(--line); }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# HELPERS DE APRESENTAÇÃO
# ---------------------------------------------------------------------
def fmt(v) -> str:
    try:
        return f"{int(round(float(v))):,}".replace(",", ".")
    except Exception:
        return "0"


def titulo(txt: str, subtitulo: str = "", pills: list[str] | None = None):
    st.markdown(f'<div class="v360-title">{txt}</div>', unsafe_allow_html=True)
    if subtitulo:
        st.markdown(f'<div class="v360-subtitle">{subtitulo}</div>', unsafe_allow_html=True)
    if pills:
        st.markdown(" ".join(pills), unsafe_allow_html=True)


def secao(txt: str):
    st.markdown(f'<div class="v360-section">{txt}</div>', unsafe_allow_html=True)


def pill(texto: str, cor: str | None = None, live: bool = False) -> str:
    cls = "pill live" if live else "pill"
    dot = f'<span class="dot" style="background:{cor};"></span>' if cor else '<span class="dot"></span>'
    return f'<span class="{cls}">{dot}{texto}</span>'


def kpi(titulo_txt: str, valor, sub: str = "", cor: str = NEUTRO, icone: str = ""):
    ic = f"{icone} " if icone else ""
    st.markdown(
        f"""
        <div class="kpi" style="--accent:{cor};">
            <div class="lbl">{ic}{titulo_txt}</div>
            <div class="val">{valor}</div>
            <div class="sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def nota(texto: str, tipo: str = "info", icone: str = "💡"):
    cls = {"ok": "ok", "alerta": "alerta", "crit": "crit", "todo": "todo"}.get(tipo, "")
    st.markdown(f'<div class="nota {cls}">{icone} {texto}</div>', unsafe_allow_html=True)


def rodape(texto: str):
    st.markdown(f'<div class="v360-foot">{texto}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------
# GRÁFICOS  (layout dark padrão)
# ---------------------------------------------------------------------
def layout(fig, altura: int = 420, titulo_grafico: str = ""):
    fig.update_layout(
        height=altura,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=CORES["ink"], size=13, family=FONTE),
        margin=dict(l=10, r=10, t=60 if titulo_grafico else 30, b=30),
        xaxis_title="", yaxis_title="", legend_title="",
        title=dict(text=titulo_grafico, font=dict(size=15, color=CORES["muted"])),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(color=CORES["muted"])),
    )
    fig.update_xaxes(showgrid=False, color=CORES["muted"], linecolor=CORES["line"])
    fig.update_yaxes(showgrid=True, gridcolor=CORES["line"], color=CORES["muted"], zeroline=False)
    return fig


def donut(rotulos, valores, titulo_grafico="", mapa_cores=None, altura=360):
    fig = go.Figure(go.Pie(
        labels=list(rotulos), values=list(valores), hole=0.62, sort=False,
        marker=dict(line=dict(color=CORES["bg"], width=2)),
        textinfo="label+percent", textfont=dict(color=CORES["ink"], size=12),
    ))
    if mapa_cores:
        fig.update_traces(marker=dict(
            colors=[mapa_cores.get(r, CORES["accent"]) for r in rotulos],
            line=dict(color=CORES["bg"], width=2)))
    else:
        fig.update_traces(marker=dict(colors=SEQUENCIA, line=dict(color=CORES["bg"], width=2)))
    return layout(fig, altura, titulo_grafico)
