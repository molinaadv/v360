# -*- coding: utf-8 -*-
"""
V360 Streamlit — cliente da API do Assistente.

Este arquivo vai na RAIZ do repo (junto do `pagina_assistente.py`), não na
pasta `api/`.

Depois que a API estiver de pé, a Streamlit para de importar `ia_modelo` e
`ia_tools` e passa a chamar aqui. Assim existe UMA cópia das funções — a do
servidor — e o celular e a Streamlit não têm como divergir de número.

TROCA NO `pagina_assistente.py`:

    import ia_modelo                                    # remover
    import cliente_api                                  # entra no lugar

    r = ia_modelo.conversar(st.session_state.ia_hist,   # remover
                            _system(nomes_unidades),
                            unidades, st.secrets, modelo)

    r = cliente_api.conversar(st.session_state.ia_hist, pergunta)   # entra

O `_system()`, o `unidades` e o `st.secrets` somem da chamada: prompt e recorte
agora são responsabilidade do servidor.
"""

from __future__ import annotations

import requests
import streamlit as st

TIMEOUT = 120


def _base() -> str:
    return str(st.secrets["V360_API_URL"]).rstrip("/")


def _token() -> str | None:
    """Token da sessão. Emitido no login da Streamlit, com o mesmo e-mail e
    senha que o usuário já digitou — a API valida contra a mesma tabela."""
    return st.session_state.get("api_token")


def entrar(email: str, senha: str) -> bool:
    """Chame junto do login da Streamlit (`auth._achar`), com as credenciais
    que o usuário acabou de digitar."""
    try:
        r = requests.post(f"{_base()}/entrar",
                          json={"email": email, "senha": senha}, timeout=30)
        if r.status_code != 200:
            return False
        st.session_state["api_token"] = r.json()["token"]
        return True
    except requests.RequestException:
        return False


def conversar(historico: list, pergunta: str, modelo: str | None = None) -> dict:
    """Mesma forma de retorno do antigo `ia_modelo.conversar` — a tela não muda.

    O histórico é substituído no lugar pelo que a API devolveu, para o
    `pagina_assistente` seguir passando a mesma lista na pergunta seguinte.
    """
    if not _token():
        return {"texto": "Sessão sem token da API. Saia e entre de novo.",
                "tracos": [], "ultimo_dado": {}, "suspeitos": [],
                "uso": {}, "modelo": "—"}

    corpo = {"pergunta": pergunta, "historico": historico}
    if modelo:
        corpo["modelo"] = modelo

    try:
        r = requests.post(f"{_base()}/conversar", json=corpo,
                          headers={"Authorization": f"Bearer {_token()}"},
                          timeout=TIMEOUT)
    except requests.Timeout:
        return {"texto": "A API demorou demais para responder. Tente de novo.",
                "tracos": [], "ultimo_dado": {}, "suspeitos": [],
                "uso": {}, "modelo": "—"}
    except requests.RequestException as e:
        return {"texto": f"Não consegui falar com a API ({e.__class__.__name__}).",
                "tracos": [], "ultimo_dado": {}, "suspeitos": [],
                "uso": {}, "modelo": "—"}

    if r.status_code == 401:
        st.session_state.pop("api_token", None)
        return {"texto": "Sua sessão expirou. Entre de novo.", "tracos": [],
                "ultimo_dado": {}, "suspeitos": [], "uso": {}, "modelo": "—"}
    if r.status_code != 200:
        det = (r.json().get("detail") if r.headers.get("content-type", "").startswith("application/json")
               else r.text[:200])
        return {"texto": f"A API respondeu {r.status_code}: {det}", "tracos": [],
                "ultimo_dado": {}, "suspeitos": [], "uso": {}, "modelo": "—"}

    d = r.json()
    historico[:] = d["historico"]      # mantém a mesma lista da sessão
    return {"texto": d["texto"], "tracos": d["tracos"],
            "ultimo_dado": d["dado"], "suspeitos": d["suspeitos"],
            "uso": d["uso"], "modelo": d["modelo"]}
