# -*- coding: utf-8 -*-
"""
V360 API — infraestrutura mínima.

Existe para tirar o Streamlit de dentro do `ia_tools.py`. Substitui exatamente
três coisas que antes vinham do framework:

  st.secrets        → variáveis de ambiente (SEGREDOS)
  st.cache_resource → singleton do cliente Supabase
  st.cache_data     → @cache_ttl, cache em memória com validade

Nada mais. Se aparecer regra de negócio aqui, está no arquivo errado.
"""

from __future__ import annotations

import functools
import os
import time

from supabase import create_client

# `st.secrets` virou ambiente. No Render isso são as Environment Variables;
# rodando local, um .env carregado antes de subir o uvicorn.
SEGREDOS = os.environ


def exigir(nome: str) -> str:
    v = SEGREDOS.get(nome)
    if not v:
        raise RuntimeError(
            f"variável de ambiente {nome} não definida — a API não sobe sem ela"
        )
    return v


_cliente = None


def supabase():
    """Cliente único do processo (era @st.cache_resource).

    Criado na primeira chamada, não no import: assim um segredo faltando vira
    erro de request com mensagem clara, e não um crash no boot que o Render
    reporta só como 'deploy failed'.
    """
    global _cliente
    if _cliente is None:
        _cliente = create_client(exigir("SUPABASE_URL"), exigir("SUPABASE_KEY"))
    return _cliente


def cache_ttl(segundos: int):
    """Equivalente ao @st.cache_data(ttl=...) para função sem argumento ou com
    argumentos hasheáveis. Guarda por chave e expira por tempo.

    Processo único, memória local — se um dia a API rodar com várias
    instâncias, cada uma terá o seu. Para o catálogo de indicadores isso é
    irrelevante (muda quando você faz INSERT, não sozinho).
    """
    def decorador(fn):
        guardado: dict = {}

        @functools.wraps(fn)
        def dentro(*args, **kwargs):
            chave = (args, tuple(sorted(kwargs.items())))
            achado = guardado.get(chave)
            agora = time.time()
            if achado and agora - achado[0] < segundos:
                return achado[1]
            valor = fn(*args, **kwargs)
            guardado[chave] = (agora, valor)
            return valor

        dentro.limpar = guardado.clear
        return dentro

    return decorador
