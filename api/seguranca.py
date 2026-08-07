# -*- coding: utf-8 -*-
"""
V360 API — quem está perguntando e o que pode ver.

MUDANÇA CENTRAL EM RELAÇÃO À STREAMLIT
--------------------------------------
Na Streamlit, o recorte de unidades era passado por quem chamava
(`ia_modelo.conversar(..., unidades, ...)`) — e isso era seguro porque quem
chamava era o próprio servidor.

Numa API, o cliente é um browser ou um celular. Ele NÃO pode declarar o próprio
escopo: bastaria mandar `unidades: "*"` para ver o escritório inteiro.

Então o corpo do request nunca carrega escopo. O token diz QUEM é a pessoa; o
escopo é buscado aqui, no servidor, na mesma tabela `v360_usuarios` que a
Streamlit já usa.

O token guarda só o e-mail. As unidades são relidas a cada request (com cache
curto), para que tirar acesso de alguém tenha efeito em menos de um minuto sem
precisar invalidar token.
"""

from __future__ import annotations

import hashlib
import time

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from nucleo import SEGREDOS, cache_ttl, exigir, supabase

TABELA = "v360_usuarios"

# Mesmo pepper do `usuarios_db.py` — as senhas já cadastradas continuam valendo.
# Se mudar aqui, todo mundo perde o login.
PEPPER = "v360$molina$"

HORAS_TOKEN = 12

_bearer = HTTPBearer(auto_error=True)


def hash_senha(senha: str) -> str:
    return hashlib.sha256((PEPPER + str(senha)).encode("utf-8")).hexdigest()


def _segredo_jwt() -> str:
    return exigir("JWT_SECRET")


# ─────────────────────────────────────────────────────────────────────────────
# usuários
# ─────────────────────────────────────────────────────────────────────────────

@cache_ttl(60)
def _usuarios() -> list:
    try:
        return supabase().table(TABELA).select("*").execute().data or []
    except Exception:
        return []


def _master_do_ambiente() -> dict | None:
    """Bootstrap: o master continua existindo mesmo com a tabela vazia,
    igual ao `auth.py` da Streamlit. Sem isso, um erro na tabela tranca
    todo mundo para fora."""
    email = SEGREDOS.get("MASTER_EMAIL")
    senha = SEGREDOS.get("MASTER_SENHA")
    if not (email and senha):
        return None
    return {"email": email.strip().lower(), "senha_texto": senha,
            "nome": SEGREDOS.get("MASTER_NOME", "Master"),
            "role": "master", "unidades": "*"}


def autenticar(email: str, senha: str) -> dict | None:
    """Devolve o usuário ou None. Não diz QUAL parte falhou — e-mail inexistente
    e senha errada respondem igual, para não confirmar cadastro a quem sonda."""
    email = str(email or "").strip().lower()

    m = _master_do_ambiente()
    if m and email == m["email"] and senha == m["senha_texto"]:
        return {k: m[k] for k in ("email", "nome", "role", "unidades")}

    h = hash_senha(senha)
    for reg in _usuarios():
        if (str(reg.get("email", "")).strip().lower() == email
                and reg.get("ativo", True)
                and reg.get("senha_hash") == h):
            return {"email": email, "nome": reg.get("nome") or email,
                    "role": reg.get("role", "gestor"),
                    "unidades": reg.get("unidades", "*")}
    return None


def _escopo_de(email: str) -> dict | None:
    """Relê o usuário — é a fonte da verdade do recorte, não o token."""
    m = _master_do_ambiente()
    if m and email == m["email"]:
        return {k: m[k] for k in ("email", "nome", "role", "unidades")}
    for reg in _usuarios():
        if str(reg.get("email", "")).strip().lower() == email and reg.get("ativo", True):
            return {"email": email, "nome": reg.get("nome") or email,
                    "role": reg.get("role", "gestor"),
                    "unidades": reg.get("unidades", "*")}
    return None


# ─────────────────────────────────────────────────────────────────────────────
# token
# ─────────────────────────────────────────────────────────────────────────────

def emitir_token(usuario: dict) -> dict:
    agora = int(time.time())
    exp = agora + HORAS_TOKEN * 3600
    # só o e-mail vai assinado. Papel e unidades são resolvidos a cada request:
    # se o token carregasse as unidades, mudar o acesso de alguém só teria
    # efeito depois que o token dele vencesse.
    token = jwt.encode({"sub": usuario["email"], "iat": agora, "exp": exp},
                       _segredo_jwt(), algorithm="HS256")
    return {"token": token, "expira_em": exp,
            "nome": usuario["nome"], "role": usuario["role"]}


def usuario_atual(cred: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    """Dependência das rotas protegidas. Devolve o usuário COM o recorte já
    resolvido no servidor."""
    try:
        dados = jwt.decode(cred.credentials, _segredo_jwt(), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "sessão expirada")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "token inválido")

    u = _escopo_de(dados.get("sub", ""))
    if not u:
        # existia quando o token foi emitido, não existe mais (ou foi desativado)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "usuário sem acesso")
    return u


def nomes_das_unidades(unidades) -> list:
    """Nomes que entram no prompt. Para o master é a lista real da base —
    o modelo precisa saber que 'compensa' é unidade e não assunto."""
    if unidades != "*":
        return list(unidades)
    return _todas_unidades()


@cache_ttl(600)
def _todas_unidades() -> list:
    try:
        r = (supabase().table("vw_tasks_completa")
             .select("unidade_nome").limit(20000).execute().data or [])
        return sorted({x["unidade_nome"] for x in r if x.get("unidade_nome")})
    except Exception:
        return []
