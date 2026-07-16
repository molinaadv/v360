# =====================================================================
# V360 MOLINA — USUÁRIOS  (só o master gerencia)
# =====================================================================
# Cria/edita/exclui logins na tabela v360_usuarios e define quais
# unidades cada pessoa enxerga (recorte aplicado em todo o app).
# =====================================================================
import pandas as pd
import streamlit as st

import theme as t
import auth
import usuarios_db


def _unidades_lista(df_tasks):
    if df_tasks is None or "unidade_nome" not in df_tasks.columns:
        return []
    return sorted(df_tasks["unidade_nome"].dropna().astype(str).unique())


def render(df_tasks):
    u = auth.usuario_atual()
    if not u or u.get("role") != "master":
        st.warning("Apenas o usuário master pode gerenciar usuários.")
        return

    t.titulo("🔐 USUÁRIOS",
             "Crie logins e defina quais unidades cada pessoa enxerga.",
             pills=[t.pill("somente master", t.CORES["roxo"])])

    unidades = _unidades_lista(df_tasks)

    # ---- Novo usuário ----
    t.secao("Novo usuário")
    with st.form("novo_usuario", clear_on_submit=True):
        c1, c2 = st.columns(2)
        email = c1.text_input("E-mail")
        nome = c2.text_input("Nome")
        c3, c4 = st.columns(2)
        senha = c3.text_input("Senha", type="password")
        role = c4.selectbox("Perfil", ["gestor", "master"],
                            help="master também pode gerenciar usuários.")
        todas = st.checkbox("Pode ver TODAS as unidades", value=False)
        uni_sel = st.multiselect("Unidades que pode ver", unidades,
                                 disabled=todas, help="Deixe vazio e marque a caixa acima para todas.")
        ok = st.form_submit_button("➕ Criar usuário")
    if ok:
        if not email or not senha:
            st.error("E-mail e senha são obrigatórios.")
        elif not todas and not uni_sel:
            st.error("Escolha as unidades ou marque 'todas as unidades'.")
        else:
            try:
                usuarios_db.criar(email, senha, nome, role, "*" if todas else uni_sel)
                st.success(f"Usuário {email} criado.")
                st.rerun()
            except Exception as e:
                st.error(f"Não consegui criar (confira se a tabela existe e a chave "
                         f"tem permissão de escrita): {e}")

    # ---- Cadastrados ----
    t.secao("Usuários cadastrados")
    regs = usuarios_db.listar()
    if not regs:
        t.nota("Nenhum usuário no banco ainda. O master vem dos Secrets. "
               "Se você acabou de criar a tabela, crie o primeiro usuário acima.", "todo", "👤")
        return

    def _escopo(un):
        if un in ("*", None) or un == ["*"]:
            return "todas"
        if isinstance(un, (list, tuple)):
            return ", ".join(map(str, un))
        return str(un)

    tab = pd.DataFrame([{
        "Nome": r.get("nome"), "E-mail": r.get("email"), "Perfil": r.get("role"),
        "Ativo": "sim" if r.get("ativo", True) else "não",
        "Unidades": _escopo(r.get("unidades")),
    } for r in regs])
    st.dataframe(tab, use_container_width=True, hide_index=True)

    # ---- Editar / excluir ----
    t.secao("Editar ou excluir")
    rotulos = [f'{r.get("nome") or r.get("email")} · {r.get("email")}' for r in regs]
    idx = st.selectbox("Selecione o usuário", range(len(regs)), format_func=lambda i: rotulos[i])
    reg = regs[idx]
    un_atual = reg.get("unidades")
    todas_atual = un_atual in ("*", None) or un_atual == ["*"]

    with st.form("editar_usuario"):
        c1, c2 = st.columns(2)
        nome_e = c1.text_input("Nome", value=reg.get("nome", ""))
        role_e = c2.selectbox("Perfil", ["gestor", "master"],
                             index=0 if reg.get("role") != "master" else 1)
        c3, c4 = st.columns(2)
        senha_e = c3.text_input("Nova senha (deixe vazio p/ manter)", type="password")
        ativo_e = c4.checkbox("Ativo", value=bool(reg.get("ativo", True)))
        todas_e = st.checkbox("Pode ver TODAS as unidades", value=bool(todas_atual))
        default_un = un_atual if isinstance(un_atual, (list, tuple)) and not todas_atual else []
        uni_e = st.multiselect("Unidades que pode ver", unidades,
                               default=[x for x in default_un if x in unidades], disabled=todas_e)
        cc1, cc2 = st.columns(2)
        salvar = cc1.form_submit_button("💾 Salvar alterações")
        excluir = cc2.form_submit_button("🗑️ Excluir usuário")

    if salvar:
        try:
            usuarios_db.atualizar(reg["id"], {
                "nome": nome_e, "role": role_e, "ativo": ativo_e,
                "unidades": "*" if todas_e else uni_e,
                "senha": senha_e,
            })
            st.success("Usuário atualizado.")
            st.rerun()
        except Exception as e:
            st.error(f"Não consegui salvar: {e}")
    if excluir:
        try:
            usuarios_db.excluir(reg["id"])
            st.success("Usuário excluído.")
            st.rerun()
        except Exception as e:
            st.error(f"Não consegui excluir: {e}")
