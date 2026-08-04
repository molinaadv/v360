# =====================================================================
# V360 CHAT — app independente (link direto)
# =====================================================================
# Mesmo motor do Assistente do V360: pagina_assistente.py + ia_tools.py.
# Aqui não há login por unidade — o escopo é fixo em todas as unidades,
# protegido por uma senha única. É o link que se manda pro dono.
#
# Deploy: Python 3.12, Main file = app.py
# Secrets: SUPABASE_URL, SUPABASE_KEY, ANTHROPIC_API_KEY, SENHA_CHAT
# =====================================================================
import streamlit as st

import pagina_assistente

st.set_page_config(page_title="V360 · Assistente", page_icon="💬",
                   layout="centered", initial_sidebar_state="collapsed")

CSS = """
<style>
  :root{--bg:#0b1220;--panel:#141d2e;--line:#26324d;--ink:#f2f6ff;--muted:#93a1bd;}
  .stApp{background:var(--bg);color:var(--ink);}
  [data-testid="stHeader"], [data-testid="stDecoration"]{
    background:transparent;min-height:0!important;}
  [data-testid="stSidebar"]{display:none;}
  [data-testid="stAppViewContainer"]>.main{padding-top:8px;}
  .marca{display:flex;align-items:baseline;gap:9px;margin:6px 0 18px;}
  .marca .v{font-size:26px;font-weight:800;letter-spacing:-.5px;color:#5b8cff;}
  .marca .m{font-size:11px;letter-spacing:2.4px;color:var(--muted);text-transform:uppercase;}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)
st.markdown('<div class="marca"><span class="v">V360</span>'
            '<span class="m">Molina Advogados</span></div>',
            unsafe_allow_html=True)


def liberado() -> bool:
    """Senha única. Sem cadastro de propósito: um link, uma senha."""
    esperada = st.secrets.get("SENHA_CHAT")
    if not esperada or st.session_state.get("ok"):
        return True

    st.write("Digite a senha de acesso para continuar.")
    senha = st.text_input("Senha", type="password", label_visibility="collapsed")
    if st.button("Entrar", type="primary"):
        if senha == esperada:
            st.session_state["ok"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    return False


if liberado():
    # "*" = todas as unidades. Este app não tem recorte por login.
    pagina_assistente.render("*", rotulo_recorte="todas as unidades")

    if st.session_state.get("ia_tela"):
        if st.button("Limpar conversa"):
            st.session_state["ia_hist"] = []
            st.session_state["ia_tela"] = []
            st.rerun()
