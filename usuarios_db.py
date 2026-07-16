# =====================================================================
# V360 MOLINA — USUÁRIOS no Supabase  (CRUD para o master)
# =====================================================================
# Tabela `v360_usuarios` (crie com supabase_v360_usuarios.sql).
# Senha guardada com hash (sha256 + pepper) — nunca em texto puro.
# O master do Secrets é o bootstrap: sempre existe, mesmo sem tabela.
# =====================================================================
import hashlib

import streamlit as st

import data

TABELA = "v360_usuarios"
PEPPER = "v360$molina$"   # sal fixo do app


def hash_senha(senha: str) -> str:
    return hashlib.sha256((PEPPER + str(senha)).encode("utf-8")).hexdigest()


@st.cache_data(ttl=60, show_spinner=False)
def listar() -> list:
    """Usuários da tabela. Se a tabela não existir ainda, retorna []."""
    try:
        sb = data.get_supabase()
        resp = sb.table(TABELA).select("*").order("nome").execute()
        return resp.data or []
    except Exception:
        return []


def criar(email, senha, nome, role, unidades):
    sb = data.get_supabase()
    reg = {
        "email": str(email).strip().lower(),
        "senha_hash": hash_senha(senha),
        "nome": nome or email,
        "role": role,
        "unidades": unidades,          # "*" (todas) ou lista de nomes
        "ativo": True,
    }
    sb.table(TABELA).insert(reg).execute()
    listar.clear()


def atualizar(id_, campos: dict):
    sb = data.get_supabase()
    campos = dict(campos)
    if campos.get("senha"):            # troca de senha (opcional)
        campos["senha_hash"] = hash_senha(campos.pop("senha"))
    else:
        campos.pop("senha", None)
    sb.table(TABELA).update(campos).eq("id", id_).execute()
    listar.clear()


def excluir(id_):
    sb = data.get_supabase()
    sb.table(TABELA).delete().eq("id", id_).execute()
    listar.clear()
