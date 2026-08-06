# -*- coding: utf-8 -*-
"""
V360 — camada de modelo do Assistente.

Isola o provedor. O `ia_tools.py` (contrato) e o `pagina_assistente.py` (tela)
não sabem se quem respondeu foi Claude ou Kimi.

DESENHO:
  - histórico guardado em formato NEUTRO (ver `_neutro_para_*`). Assim dá pra
    trocar de modelo no meio da conversa sem quebrar o histórico — o que é o
    ponto todo de poder comparar os dois na mesma pergunta.
  - poda antes de enviar: resultado de função antigo vira marcador curto.
    É o que mais pesa na conta (um agenda_semana devolve 40 eventos e era
    reenviado inteiro em toda pergunta seguinte).
  - quem executa a função continua sendo `ia_tools.executar`, que aplica o
    recorte de unidade. O modelo nunca controla isso.

FORMATO NEUTRO (lista de turnos):
  {"quem": "user",  "texto": str}
  {"quem": "ia",    "texto": str, "chamadas": [{"id","nome","args"}]}
  {"quem": "tool",  "resultados": [{"id","nome","dado"}]}
"""

from __future__ import annotations

import json

import requests

import ia_tools

# ─────────────────────────────────────────────────────────────────────────────
# catálogo de modelos
# ─────────────────────────────────────────────────────────────────────────────

MODELOS = {
    "claude-sonnet-5": {
        "rotulo": "Claude Sonnet 5",
        "provedor": "anthropic",
        "modelo": "claude-sonnet-5",
        "chave": "ANTHROPIC_API_KEY",
    },
    "claude-haiku-4-5": {
        "rotulo": "Claude Haiku 4.5",
        "provedor": "anthropic",
        "modelo": "claude-haiku-4-5-20251001",
        "chave": "ANTHROPIC_API_KEY",
    },
    "kimi-k2.6": {
        "rotulo": "Kimi K2.6",
        "provedor": "moonshot",
        "modelo": "kimi-k2.6",
        "chave": "MOONSHOT_API_KEY",
        # escolher entre 6 funções não precisa de raciocínio longo, e com
        # thinking ligado os tokens de pensamento comem o orçamento de saída
        # (resposta voltava vazia). Desligado também sai mais barato.
        "extra": {"thinking": {"type": "disabled"}, "temperature": 0.6},
    },
    "kimi-k3": {
        "rotulo": "Kimi K3",
        "provedor": "moonshot",
        "modelo": "kimi-k3",
        "chave": "MOONSHOT_API_KEY",
        # K3 não aceita desligar o raciocínio — só dar teto de saída folgado
        "extra": {},
    },
}

PADRAO = "claude-sonnet-5"

URL_ANTHROPIC = "https://api.anthropic.com/v1/messages"
URL_MOONSHOT = "https://api.moonshot.ai/v1/chat/completions"

MAX_SAIDA = 3000        # teto de tokens de saída. Em modelo com raciocínio o
                        # pensamento consome deste orçamento — 1024 era pouco e
                        # a resposta voltava vazia.
MAX_VOLTAS = 5          # teto de chamadas de função por pergunta
TURNOS_COM_DADO = 2     # quantas rodadas de função mantêm o JSON inteiro
MAX_TURNOS = 12         # janela de histórico enviada ao modelo


# ─────────────────────────────────────────────────────────────────────────────
# poda
# ─────────────────────────────────────────────────────────────────────────────

def podar(historico: list) -> list:
    """Corta a cauda antiga e esvazia resultados de função velhos.

    O par chamada→resultado é PRESERVADO (a API da Anthropic recusa um tool_use
    sem o tool_result correspondente). Só o conteúdo encolhe.
    """
    hist = historico[-MAX_TURNOS:]

    # não começar a janela num turno de resultado órfão
    while hist and hist[0]["quem"] != "user":
        hist = hist[1:]

    idx_tool = [i for i, t in enumerate(hist) if t["quem"] == "tool"]
    manter = set(idx_tool[-TURNOS_COM_DADO:])

    podado = []
    for i, t in enumerate(hist):
        if t["quem"] == "tool" and i not in manter:
            podado.append({"quem": "tool", "resultados": [
                {"id": r["id"], "nome": r["nome"],
                 "dado": {"nota": "resultado anterior — pergunte de novo se precisar"}}
                for r in t["resultados"]]})
        else:
            podado.append(t)
    return podado


def _txt(dado: dict) -> str:
    return json.dumps(dado, ensure_ascii=False, default=str)


# ─────────────────────────────────────────────────────────────────────────────
# tradução: neutro → formato do provedor
# ─────────────────────────────────────────────────────────────────────────────

def _neutro_para_anthropic(historico: list) -> list:
    msgs = []
    for t in historico:
        if t["quem"] == "user":
            msgs.append({"role": "user", "content": t["texto"]})
        elif t["quem"] == "ia":
            blocos = []
            if t.get("texto"):
                blocos.append({"type": "text", "text": t["texto"]})
            for c in t.get("chamadas", []):
                blocos.append({"type": "tool_use", "id": c["id"],
                               "name": c["nome"], "input": c["args"]})
            msgs.append({"role": "assistant", "content": blocos})
        else:
            msgs.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": r["id"],
                 "content": _txt(r["dado"])} for r in t["resultados"]]})
    return msgs


def _neutro_para_openai(historico: list, system: str) -> list:
    """Converte para o formato OpenAI/Moonshot.

    PEGADINHA DA MOONSHOT: com thinking ativo (padrão nos K2.x/K3), toda
    mensagem de assistente que traz `tool_calls` PRECISA devolver o
    `reasoning_content` que veio na resposta. Faltando, a API responde 400
    ("thinking is enabled but reasoning_content is missing...") e, pior, a
    mensagem defeituosa fica no histórico e derruba todas as rodadas seguintes.

    Se um turno com chamada não tiver raciocínio (ex.: foi o Claude que
    respondeu antes da troca de modelo), o turno E o resultado dele são
    omitidos — mandar um `tool` sem o `tool_call` correspondente também é 400.
    """
    msgs = [{"role": "system", "content": system}]
    pular_resultado = False

    for t in historico:
        if t["quem"] == "user":
            msgs.append({"role": "user", "content": t["texto"]})
            pular_resultado = False
        elif t["quem"] == "ia":
            if t.get("chamadas") and not t.get("raciocinio"):
                pular_resultado = True      # turno de outro provedor: descarta o par
                continue
            m = {"role": "assistant", "content": t.get("texto") or ""}
            if t.get("chamadas"):
                m["reasoning_content"] = t["raciocinio"]
                m["tool_calls"] = [
                    {"id": c["id"], "type": "function",
                     "function": {"name": c["nome"],
                                  "arguments": json.dumps(c["args"], ensure_ascii=False)}}
                    for c in t["chamadas"]]
            msgs.append(m)
            pular_resultado = False
        else:
            if pular_resultado:
                pular_resultado = False
                continue
            for r in t["resultados"]:
                msgs.append({"role": "tool", "tool_call_id": r["id"],
                             "content": _txt(r["dado"])})
    return msgs


def _tools_openai() -> list:
    """SCHEMA da Anthropic → formato de function calling da OpenAI."""
    return [{"type": "function",
             "function": {"name": t["name"],
                          "description": t["description"],
                          "parameters": t["input_schema"]}}
            for t in ia_tools.SCHEMA]


def _tools_anthropic(cache: bool) -> list:
    tools = [dict(t) for t in ia_tools.SCHEMA]
    if cache and tools:
        # marca o fim do prefixo fixo (system + tools). Ganho é modesto aqui —
        # o prefixo é pequeno; quem pesa é o histórico, tratado na poda.
        tools[-1] = {**tools[-1], "cache_control": {"type": "ephemeral"}}
    return tools


# ─────────────────────────────────────────────────────────────────────────────
# chamada + normalização da resposta
# ─────────────────────────────────────────────────────────────────────────────

def _post(url: str, headers: dict, corpo: dict) -> dict:
    r = requests.post(url, headers=headers, json=corpo, timeout=90)
    if r.status_code >= 400:
        # o corpo é onde a API explica o motivo — sem ele o erro vira adivinhação
        try:
            det = r.json().get("error", {}).get("message") or r.text[:300]
        except Exception:
            det = r.text[:300]
        raise RuntimeError(f"HTTP {r.status_code} — {det}")
    return r.json()


def _chamar_anthropic(historico, system, chave, modelo, cache, extra=None) -> dict:
    sistema = ([{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
               if cache else system)
    resp = _post(URL_ANTHROPIC,
                 {"x-api-key": chave, "anthropic-version": "2023-06-01",
                  "content-type": "application/json"},
                 {"model": modelo, "max_tokens": MAX_SAIDA, "system": sistema,
                  "tools": _tools_anthropic(cache),
                  "messages": _neutro_para_anthropic(historico)})

    texto = "".join(b["text"] for b in resp["content"] if b["type"] == "text")
    chamadas = [{"id": b["id"], "nome": b["name"], "args": b["input"]}
                for b in resp["content"] if b["type"] == "tool_use"]
    return {"texto": texto, "chamadas": chamadas, "raciocinio": "",
            "motivo": resp.get("stop_reason"), "uso": resp.get("usage", {})}


def _chamar_moonshot(historico, system, chave, modelo, _cache, extra=None) -> dict:
    corpo = {"model": modelo, "max_tokens": MAX_SAIDA,
             "tools": _tools_openai(),
             "messages": _neutro_para_openai(historico, system)}
    corpo.update(extra or {})
    resp = _post(URL_MOONSHOT,
                 {"Authorization": f"Bearer {chave}",
                  "Content-Type": "application/json"}, corpo)

    escolha = resp["choices"][0]
    msg = escolha["message"]
    chamadas = []
    for c in (msg.get("tool_calls") or []):
        try:
            args = json.loads(c["function"].get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {}
        chamadas.append({"id": c["id"], "nome": c["function"]["name"], "args": args})
    # guardado para ser devolvido na próxima rodada (exigência da Moonshot)
    return {"texto": msg.get("content") or "", "chamadas": chamadas,
            "raciocinio": msg.get("reasoning_content") or "",
            "motivo": escolha.get("finish_reason"),
            "uso": resp.get("usage", {})}


_DESPACHO = {"anthropic": _chamar_anthropic, "moonshot": _chamar_moonshot}


# ─────────────────────────────────────────────────────────────────────────────
# laço principal — é o que a tela chama
# ─────────────────────────────────────────────────────────────────────────────

def conversar(historico: list, system: str, unidades, segredos,
              chave_modelo: str = PADRAO, cache: bool = True) -> dict:
    """Roda pergunta → função → resposta até o modelo parar de chamar função.

    `historico` é mutado (turnos novos anexados) — é o histórico neutro da sessão.
    `segredos` = st.secrets (ou qualquer dict-like).
    Devolve {texto, tracos, ultimo_dado, uso, modelo}.
    """
    cfg = MODELOS.get(chave_modelo) or MODELOS[PADRAO]
    chave = segredos.get(cfg["chave"])
    if not chave:
        return {"texto": f"Falta {cfg['chave']} nos Secrets do app.",
                "tracos": [], "ultimo_dado": {}, "uso": {}, "modelo": cfg["rotulo"]}

    chamar = _DESPACHO[cfg["provedor"]]
    tracos, ultimo_dado, uso = [], {}, {}
    feitas: set = set()          # assinaturas já executadas nesta pergunta
    texto = ""

    for _ in range(MAX_VOLTAS):
        r = chamar(podar(historico), system, chave, cfg["modelo"], cache,
                   cfg.get("extra"))
        uso = r["uso"]
        historico.append({"quem": "ia", "texto": r["texto"],
                          "chamadas": r["chamadas"],
                          "raciocinio": r.get("raciocinio", "")})

        if not r["chamadas"]:
            texto = r["texto"]
            if not texto:
                # sem texto e sem função: quase sempre teto de saída estourado
                texto = (f"O modelo devolveu resposta vazia (motivo: "
                         f"{r.get('motivo') or 'desconhecido'}). Tente de novo "
                         f"ou troque de modelo no seletor.")
            break

        resultados = []
        for c in r["chamadas"]:
            assinatura = (c["nome"], json.dumps(c["args"], sort_keys=True))
            if assinatura in feitas:
                # o modelo repetiu a MESMA chamada. Sem isto ele insiste até o
                # teto de voltas e o usuário recebe "consultei demais".
                dado = {"erro": "chamada idêntica já feita nesta pergunta — o "
                                "resultado não muda. Use outra função ou outros "
                                "argumentos, ou responda com o que já tem."}
            else:
                feitas.add(assinatura)
                dado = ia_tools.executar(c["nome"], c["args"], unidades)
            if "erro" not in dado:
                ultimo_dado = dado
            args_txt = ", ".join(f'"{v}"' for v in c["args"].values()) or "—"
            tracos.append(f'{c["nome"]}</b>({args_txt})<b>')
            resultados.append({"id": c["id"], "nome": c["nome"], "dado": dado})
        historico.append({"quem": "tool", "resultados": resultados})
    else:
        texto = texto or "Consultei demais e não fechei a resposta. Refaça a pergunta mais específica."

    return {"texto": texto, "tracos": tracos, "ultimo_dado": ultimo_dado,
            "uso": uso, "modelo": cfg["rotulo"]}
