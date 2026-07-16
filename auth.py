# =====================================================================
# V360 MOLINA — LOGIN (e-mail + senha) e controle de unidades
# =====================================================================
# Usuários vêm de st.secrets["usuarios"] (NÃO do código — assim a senha
# nunca vai pro repositório). Cada usuário tem:
#   email, senha, nome, role, unidades  ("*" = todas | lista de nomes)
#
# Master vê tudo. Um gestor (ex.: Rodrigo) só vê as unidades da lista dele.
# Exemplo de secrets em  .streamlit/secrets.toml.example
# =====================================================================
import json

import streamlit as st

import theme as t
import usuarios_db


def _usuarios_secrets() -> dict:
    """Usuários do Secrets (bootstrap, ex.: master). Senha em texto no Secrets."""
    try:
        u = st.secrets.get("usuarios")
    except Exception:
        u = None
    if not u:
        return {}
    out = {}
    for chave, cfg in u.items():
        d = dict(cfg)
        out[chave] = {
            "email": str(d.get("email", "")).strip().lower(),
            "senha": str(d.get("senha", "")),
            "nome": d.get("nome", chave),
            "role": d.get("role", "gestor"),
            "unidades": d.get("unidades", "*"),
        }
    return out


def _achar(email: str, senha: str):
    email = (email or "").strip().lower()
    # 1) Secrets (senha em texto)
    for u in _usuarios_secrets().values():
        if u["email"] == email and u["senha"] == senha:
            return u
    # 2) Tabela Supabase (senha com hash)
    h = usuarios_db.hash_senha(senha)
    for reg in usuarios_db.listar():
        if (str(reg.get("email", "")).strip().lower() == email
                and reg.get("ativo", True) and reg.get("senha_hash") == h):
            return {"email": email, "nome": reg.get("nome", email),
                    "role": reg.get("role", "gestor"), "unidades": reg.get("unidades", "*")}
    return None


def usuario_atual():
    return st.session_state.get("v360_user")


def unidades_permitidas():
    """Lista de unidades que o usuário pode ver, ou None = todas."""
    u = usuario_atual()
    if not u:
        return None
    un = u.get("unidades", "*")
    if isinstance(un, str) and un.strip().startswith("["):
        try:
            un = json.loads(un)
        except Exception:
            pass
    if un in ("*", None, "", ["*"]):
        return None
    return [str(x) for x in un] if isinstance(un, (list, tuple)) else [str(un)]


def aplicar_recorte(df):
    """Filtra um DataFrame às unidades permitidas (master = tudo)."""
    permitidas = unidades_permitidas()
    if permitidas is None or df is None or df.empty:
        return df
    col = "unidade_nome" if "unidade_nome" in df.columns else (
        "unidade_principal" if "unidade_principal" in df.columns else None)
    return df if col is None else df[df[col].astype(str).isin(permitidas)]


def login_gate() -> bool:
    """Mostra o formulário e bloqueia o app até autenticar. True = liberado."""
    if usuario_atual():
        return True

    st.markdown(
        "<div style='max-width:400px;margin:7% auto 0;text-align:center;'>"
        "<div style='font-size:52px;font-weight:900;letter-spacing:-2px;color:#f2f6ff;'>V360</div>"
        "<div style='font-size:12px;font-weight:700;letter-spacing:2px;color:#93a1bd;margin-bottom:6px;'>MOLINA ADVOGADOS</div>"
        "<div style='font-size:13px;color:#6b7a99;margin-bottom:22px;'>Relatório Operacional</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    col = st.columns([1, 2, 1])[1]
    with col:
        with st.form("login", clear_on_submit=False):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            ok = st.form_submit_button("Entrar", use_container_width=True)
        if ok:
            u = _achar(email, senha)
            if u:
                st.session_state["v360_user"] = u
                st.rerun()
            elif not _usuarios_secrets() and not usuarios_db.listar():
                st.error("Nenhum usuário configurado. Adicione o bloco [usuarios] "
                         "nos Secrets do app (veja secrets.toml.example).")
            else:
                st.error("E-mail ou senha incorretos.")
    return False


def barra_usuario():
    """Rodapé do menu lateral: quem está logado + sair."""
    u = usuario_atual()
    if not u:
        return
    permitidas = unidades_permitidas()
    escopo = "todas as unidades" if permitidas is None else f"{len(permitidas)} unidade(s)"
    st.sidebar.markdown(
        f'<div style="margin-top:14px;padding:10px 12px;border:1px solid {t.CORES["line"]};'
        f'border-radius:12px;background:{t.CORES["panel"]};font-size:12px;">'
        f'<b style="color:{t.CORES["ink"]};">{u["nome"]}</b><br>'
        f'<span style="color:{t.CORES["muted"]};">{escopo}</span></div>',
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Sair", key="logout", use_container_width=True):
        st.session_state.pop("v360_user", None)
        st.rerun()
