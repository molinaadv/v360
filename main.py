# -*- coding: utf-8 -*-
"""
V360 API — o cérebro do Assistente, servido por HTTP.

Clientes: a Streamlit (`v360-relatorios`) e o app do gestor. Os dois falam com
as mesmas funções, então respondem o mesmo número — que é o motivo de existir.

ROTAS
  GET  /saude        — sem token. É o que o Render usa para health check.
  POST /entrar       — e-mail + senha → token
  POST /conversar    — pergunta → resposta (token obrigatório)
  GET  /indicadores  — nomes do catálogo (token obrigatório)

O QUE O CLIENTE NÃO CONTROLA (nunca aceitar pelo corpo do request):
  - o recorte de unidades  → vem do token, resolvido em `seguranca.py`
  - o system prompt        → montado em `prompt.py`, no servidor
  - qual função executar   → o modelo escolhe, `ia_tools.executar` valida
"""

from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import ia_modelo
import ia_tools
import prompt
from nucleo import SEGREDOS
from seguranca import autenticar, emitir_token, nomes_das_unidades, usuario_atual

app = FastAPI(title="V360 API", version="1.0")

# Origens permitidas. Deixar "*" aqui derruba a proteção do navegador contra
# outro site usar o token do seu gestor — liste os domínios de verdade.
ORIGENS = [o.strip() for o in SEGREDOS.get("ORIGENS_PERMITIDAS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS or ["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# contratos
# ─────────────────────────────────────────────────────────────────────────────

class Entrada(BaseModel):
    email: str
    senha: str


class Turno(BaseModel):
    """Um turno do histórico neutro do `ia_modelo`."""
    quem: str
    texto: str | None = None
    chamadas: list | None = None
    resultados: list | None = None
    raciocinio: str | None = None


class Pergunta(BaseModel):
    pergunta: str = Field(min_length=1, max_length=2000)
    # o cliente devolve o histórico que recebeu. A API é sem estado: guardar
    # sessão no servidor seria mais uma coisa para expirar e vazar.
    historico: list[Turno] = []
    modelo: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# rotas
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/saude")
def saude():
    return {"ok": True, "modelo_padrao": ia_modelo.PADRAO}


@app.post("/entrar")
def entrar(dados: Entrada):
    u = autenticar(dados.email, dados.senha)
    if not u:
        raise HTTPException(401, "e-mail ou senha inválidos")
    return emitir_token(u)


@app.get("/indicadores")
def indicadores(usuario: dict = Depends(usuario_atual)):
    return ia_tools.listar_indicadores(usuario["unidades"])


@app.post("/conversar")
def conversar(p: Pergunta, usuario: dict = Depends(usuario_atual)):
    unidades = usuario["unidades"]

    historico = [t.model_dump(exclude_none=True) for t in p.historico]
    historico.append({"quem": "user", "texto": p.pergunta})

    system = prompt.montar_system(nomes_das_unidades(unidades))

    try:
        r = ia_modelo.conversar(
            historico, system, unidades, SEGREDOS,
            chave_modelo=p.modelo or ia_modelo.PADRAO,
        )
    except RuntimeError as e:
        # erro do provedor (400/429/500 da Moonshot ou da Anthropic)
        raise HTTPException(502, f"o modelo não respondeu: {e}")

    # `conversar` mutou o histórico com os turnos novos — devolvemos para o
    # cliente reenviar na próxima pergunta.
    return {
        "texto": r["texto"],
        "dado": r["ultimo_dado"],
        "suspeitos": r.get("suspeitos", []),
        "tracos": r["tracos"],
        "modelo": r["modelo"],
        "uso": r["uso"],
        "historico": historico,
        "escopo": "todas as unidades" if unidades == "*" else f"{len(unidades)} unidades",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
