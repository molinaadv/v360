# =====================================================================
# V360 MOLINA — RELATÓRIO OPERACIONAL  (app novo, dark, rápido)
# =====================================================================
# Login por e-mail/senha (com escopo de unidades) + camada de dados leve
# + design dark dos painéis de TV. O menu "TV Operacional" concentra
# todos os painéis de /pages num lugar só.
#
# Deploy: Python 3.12 + requirements.txt pinado (pyarrow==16.1.0!).
# Secrets: SUPABASE_URL, SUPABASE_KEY, [usuarios] (ver secrets.toml.example).
# =====================================================================
import base64
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

import data
import theme as t
import auth
import pagina_executivo
import pagina_fase1
import pagina_insights
import pagina_metas
import pagina_mapa
import pagina_performance
import pagina_comparativo
import pagina_audiencias
import pagina_captacao
import pagina_tv
import pagina_usuarios

try:
    import painel_tv_operacional as tvop
except Exception:
    tvop = None

st.set_page_config(page_title="V360 Molina — Relatório", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")
t.injetar_css()


# =====================================================================
# CARGA DE DADOS  (cacheada; só as colunas necessárias)
# =====================================================================
try:
    df_tasks, df_metas, df_colabs = data.carregar_tudo()
except Exception as e:
    st.error("Erro ao carregar dados do Supabase.")
    st.exception(e)
    st.stop()

# --- TV em tela cheia por URL (?setor=...&unidade=...): abre sem login,
#     igual aos painéis de /pages ---
if tvop is not None:
    tvop.intercept(df_tasks, df_colabs, df_metas)

# =====================================================================
# LOGIN
# =====================================================================
if not auth.login_gate():
    st.stop()

if df_tasks is None or df_tasks.empty:
    st.warning("Nenhuma tarefa encontrada nas views do Supabase.")
    st.stop()

# compromissos (audiências/perícias JUD) — best-effort, não derruba o app
try:
    df_comp = data.carregar_compromissos()
except Exception:
    df_comp = pd.DataFrame()

# recorte por unidade do usuário (master = tudo)
df_tasks = auth.aplicar_recorte(df_tasks)
df_metas = auth.aplicar_recorte(df_metas)
df_colabs = auth.aplicar_recorte(df_colabs)
df_comp = auth.aplicar_recorte(df_comp)


# =====================================================================
# SIDEBAR + MENU
# =====================================================================
st.sidebar.markdown(
    '<div class="sidebar-logo"><div class="v360">V360</div>'
    '<div class="molina">MOLINA ADVOGADOS</div></div>',
    unsafe_allow_html=True,
)

PAGINAS = [
    ("🏠  Executivo",     "Executivo"),
    ("💡  Insights V360", "Insights"),
    ("🎯  Metas",         "Metas"),
    ("🗺️  Mapa",          "Mapa"),
    ("👥  Performance",   "Performance"),
    ("🔀  Comparativo",   "Comparativo"),
    ("⚖️  Audiências e Perícias", "Audiencias"),
    ("💼  V360 Clientes", "Captacao"),
    ("📺  TV Operacional", "TV"),
]

# menu de usuários só para o master
_u = auth.usuario_atual()
if _u and _u.get("role") == "master":
    PAGINAS.append(("🔐  Usuários", "Usuarios"))

if "pagina" not in st.session_state:
    st.session_state["pagina"] = "Executivo"


def ir_para(p):
    st.session_state["pagina"] = p


for rotulo, destino in PAGINAS:
    ativo = st.session_state["pagina"] == destino
    if ativo:
        st.sidebar.markdown('<div class="menu-active">', unsafe_allow_html=True)
    st.sidebar.button(rotulo, key=f"menu_{destino}", use_container_width=True,
                      on_click=ir_para, args=(destino,))
    if ativo:
        st.sidebar.markdown("</div>", unsafe_allow_html=True)

auth.barra_usuario()

# logo no rodapé da barra
_logo = Path(__file__).with_name("Logo_Molina_1_Traco_negativo.png")
if _logo.exists():
    b64 = base64.b64encode(_logo.read_bytes()).decode()
    st.sidebar.markdown(
        f'<div style="margin-top:16px;opacity:.85;"><img src="data:image/png;base64,{b64}" '
        f'style="width:150px;"></div>', unsafe_allow_html=True)

pagina = st.session_state["pagina"]


# =====================================================================
# FILTROS SUPERIORES  (não aparecem na TV)
# =====================================================================
df_f = df_tasks
df_metas_f = df_metas
df_comp_f = df_comp
ano_filtro = data.hoje().year
mes_filtro = data.hoje().month

if pagina != "TV":
    MESES = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio",
             6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro",
             11: "Novembro", 12: "Dezembro"}
    anos = list(range(2024, data.hoje().year + 1))

    c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5])
    with c1:
        ano_filtro = st.selectbox("Ano", anos, index=anos.index(data.hoje().year))
    with c2:
        mes_filtro = st.selectbox("Mês", list(MESES), format_func=lambda x: MESES[x],
                                  index=data.hoje().month - 1)
    with c3:
        unidades = ["Todos"] + sorted(df_tasks["unidade_nome"].dropna().astype(str).unique())
        unidade_filtro = st.selectbox("Escritório", unidades)
    with c4:
        resp = ["Todos"] + sorted(df_tasks["usuario_executor"].dropna().astype(str).unique())
        resp_filtro = st.selectbox("Responsável", resp)

    if st.columns([5, 1])[1].button("🔄 Atualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    df_f = df_tasks
    if unidade_filtro != "Todos":
        df_f = df_f[df_f["unidade_nome"] == unidade_filtro]
    if resp_filtro != "Todos":
        df_f = df_f[df_f["usuario_executor"] == resp_filtro]

    df_comp_f = df_comp
    if unidade_filtro != "Todos" and not df_comp.empty and "unidade_nome" in df_comp.columns:
        df_comp_f = df_comp[df_comp["unidade_nome"] == unidade_filtro]

    mes_ref = date(ano_filtro, mes_filtro, 1)
    if not df_metas.empty and "mes_referencia" in df_metas.columns:
        # competência é data de calendário → parse naive, sem converter fuso
        mref = pd.to_datetime(df_metas["mes_referencia"], errors="coerce").dt.date
        df_metas_f = df_metas[mref == mes_ref].copy()
    else:
        df_metas_f = df_metas


# =====================================================================
# ROTEAMENTO
# =====================================================================
try:
    if pagina == "Executivo":
        pagina_fase1.render(df_f, df_metas_f, ano_filtro, mes_filtro)
    elif pagina == "Insights":
        pagina_insights.render(df_f, df_metas_f, ano_filtro, mes_filtro)
    elif pagina == "Metas":
        pagina_metas.render(df_f, df_metas_f, ano_filtro, mes_filtro)
    elif pagina == "Mapa":
        pagina_mapa.render(df_f, df_metas_f, ano_filtro, mes_filtro)
    elif pagina == "Performance":
        pagina_performance.render(df_f, df_metas_f, ano_filtro, mes_filtro)
    elif pagina == "Comparativo":
        pagina_comparativo.render(df_f, df_metas_f, ano_filtro, mes_filtro)
    elif pagina == "Audiencias":
        pagina_audiencias.render(df_f, df_comp_f, ano_filtro, mes_filtro)
    elif pagina == "Captacao":
        # leads da captação (view/tabela própria); recorte por unidade quando aplicável
        df_leads = data.carregar_leads()
        permitidas = auth.unidades_permitidas()
        if permitidas is not None and not df_leads.empty and "unidade" in df_leads.columns:
            df_leads = df_leads[df_leads["unidade"].astype(str).isin(permitidas)]
        pagina_captacao.render(df_leads)
    elif pagina == "TV":
        pagina_tv.render(df_tasks, df_colabs, df_metas)
    elif pagina == "Usuarios":
        pagina_usuarios.render(df_tasks)
except Exception as e:
    st.error(f"A página '{pagina}' falhou ao renderizar.")
    st.exception(e)

ts = data.agora().strftime("%d/%m %H:%M")
t.rodape(f"Fonte: Legal One API · atualizado {ts} (Manaus)")
