# -*- coding: utf-8 -*-
"""
V360 — Assistente (Streamlit).

Chat síncrono: Streamlit → API Anthropic → funções de ia_tools.py → Supabase.
NÃO passa pelo n8n (o n8n cuida do batch/agendado; aqui o usuário espera resposta).

Usa `requests` de propósito, em vez do SDK — nenhuma dependência nova além do
que já está pinado nos apps.
"""

from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import streamlit as st

import ia_tools

TZ = ZoneInfo("America/Manaus")
API_URL = "https://api.anthropic.com/v1/messages"
MODELO = "claude-sonnet-5"      # trocável por claude-haiku-4-5 se quiser mais barato
MAX_VOLTAS = 5                  # teto de chamadas de função por pergunta

SYSTEM = """Você é o assistente do V360, painel interno da Molina Advogados (direito previdenciário, Manaus/AM).

Você responde a advogados e gestores do escritório sobre os dados operacionais.

REGRAS:
- Todo número vem das funções. Você NUNCA estima, arredonda de cabeça ou inventa um valor. Se não tem função pra pergunta, diga o que não consegue responder e sugira o painel certo.
- Os nomes de subtipo batem letra por letra. Se não tiver certeza do nome exato, chame listar_subtipos ANTES de contar. Nunca chute o nome.
- "Em aberto" = Pendente, Não cumprido ou Iniciado. "Cumprido no mês" usa mes_conclusao.
- Crédito de produtividade é de quem CONCLUIU (usuario_executor), nunca do responsável.
- Você só enxerga as unidades do usuário logado. Isso já é aplicado automaticamente — não peça permissão nem tente contornar.
- Você NÃO tem acesso a CPF, número de benefício, senha do INSS, telefone ou endereço de cliente. Esses dados ficam no campo notes do Legal One e estão fora do seu escopo por segurança. Se pedirem, explique isso em uma frase e diga que a consulta deve ser feita direto no Legal One.
- Você não dá parecer jurídico, não prevê resultado de processo e não estima valores.

ESTILO:
- Português brasileiro, direto, sem rodeio. 2 a 4 frases.
- Comece pelo número que responde a pergunta. Depois, no máximo, o que ele significa.
- Se aparecer muita tarefa "Iniciado" em aberto, mencione: pode ser status preso (fantasma de sync), vale rodar o Re-sync.
- Nada de bullet a não ser que a pergunta peça lista.
"""

CSS = """
<style>
  .ia-trace{display:inline-flex;align-items:center;gap:7px;font-family:ui-monospace,Menlo,monospace;
    font-size:10.5px;color:#6b7a99;background:#0f1728;border:1px solid #26324d;
    padding:4px 10px;border-radius:8px;margin-bottom:10px}
  .ia-trace b{color:#4fb0e8;font-weight:600}
  .ia-trace.blk{border-color:#4a2b3a;color:#ef7a7a}
  .ia-kpis{display:flex;gap:10px;flex-wrap:wrap;margin:2px 0 12px}
  .ia-kpi{background:#1b2740;border:1px solid #26324d;border-radius:14px;padding:11px 16px;min-width:104px}
  .ia-kpi .n{font-size:30px;font-weight:800;line-height:1.05}
  .ia-kpi .l{font-size:10px;color:#6b7a99;text-transform:uppercase;letter-spacing:.6px;margin-top:3px}
  .ia-src{margin-top:12px;padding-top:10px;border-top:1px solid #26324d;font-size:10.5px;color:#6b7a99}
  .ia-src .tag{background:#0f1728;border:1px solid #26324d;padding:3px 8px;
    border-radius:7px;font-family:ui-monospace,monospace;margin-right:6px}
</style>
"""


def _chamar_api(mensagens: list, chave: str) -> dict:
    r = requests.post(
        API_URL,
        headers={"x-api-key": chave,
                 "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": MODELO, "max_tokens": 1024, "system": SYSTEM,
              "tools": ia_tools.SCHEMA, "messages": mensagens},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def _kpis(dado: dict) -> str:
    """Cartões grandes quando a função devolve contagem. Cor semântica do projeto."""
    cards = []
    if "em_aberto" in dado:
        cards = [("#f5a524", dado["em_aberto"], "em aberto"),
                 ("#2fce8f", dado["cumpridos_no_mes"], "cumpridos no mês"),
                 ("#8b7bff", dado["total"], "total")]
    elif dado.get("ranking"):
        cores = ["#2fce8f", "#f2f6ff", "#f2f6ff"]
        cards = [(cores[i], r["concluidas"], r["pessoa"].split()[0].title())
                 for i, r in enumerate(dado["ranking"][:3])]
    elif "total" in dado and "eventos" in dado:
        cards = [("#4fb0e8", dado["total"], "na semana"),
                 ("#2fce8f", dado.get("realizados", 0), "realizados")]
    if not cards:
        return ""
    html = "".join(f'<div class="ia-kpi"><div class="n" style="color:{c}">{n}</div>'
                   f'<div class="l">{l}</div></div>' for c, n, l in cards)
    return f'<div class="ia-kpis">{html}</div>'


def _fonte(dado: dict) -> str:
    f = dado.get("fonte")
    if not f:
        return ""
    tags = f'<span class="tag">{f["view"]}</span>'
    if f.get("regra"):
        tags += f'<span class="tag">{f["regra"]}</span>'
    hora = datetime.now(TZ).strftime("%d/%m %H:%M")
    return f'<div class="ia-src">Fonte: {tags} · Legal One API · consultado {hora}</div>'


def _render(bloco: dict):
    """Desenha uma resposta já processada (texto + traça + kpis + fonte)."""
    for t in bloco.get("tracos", []):
        st.markdown(f'<div class="ia-trace">consultou <b>{t}</b></div>',
                    unsafe_allow_html=True)
    if bloco.get("kpis"):
        st.markdown(bloco["kpis"], unsafe_allow_html=True)
    st.markdown(bloco["texto"])
    if bloco.get("fonte"):
        st.markdown(bloco["fonte"], unsafe_allow_html=True)


def render(unidades, rotulo_recorte: str = ""):
    """Chamada pelo app.py. `unidades` = '*' ou lista (vem do auth.aplicar_recorte)."""
    st.markdown(CSS, unsafe_allow_html=True)

    chave = st.secrets.get("ANTHROPIC_API_KEY")
    if not chave:
        st.error("Falta ANTHROPIC_API_KEY nos Secrets do app.")
        return

    esc = "todas as unidades" if unidades == "*" else f"{len(unidades)} unidades"
    st.markdown(
        f"### Assistente&nbsp;&nbsp;"
        f"<span style='font-size:11px;color:#93a1bd;background:#141d2e;border:1px solid #26324d;"
        f"padding:5px 11px;border-radius:999px'>{rotulo_recorte or esc}</span>&nbsp;"
        f"<span style='font-size:11px;color:#2fce8f'>● ao vivo</span>",
        unsafe_allow_html=True)

    if "ia_hist" not in st.session_state:
        st.session_state.ia_hist = []   # formato da API
    if "ia_tela" not in st.session_state:
        st.session_state.ia_tela = []   # o que desenhamos

    for b in st.session_state.ia_tela:
        with st.chat_message("user" if b["quem"] == "user" else "assistant"):
            if b["quem"] == "user":
                st.markdown(b["texto"])
            else:
                _render(b)

    pergunta = st.chat_input("Pergunte sobre suas unidades…")
    if not pergunta:
        return

    st.session_state.ia_hist.append({"role": "user", "content": pergunta})
    st.session_state.ia_tela.append({"quem": "user", "texto": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        tracos, ultimo_dado = [], {}
        try:
            with st.spinner("consultando a base…"):
                for _ in range(MAX_VOLTAS):
                    resp = _chamar_api(st.session_state.ia_hist, chave)
                    st.session_state.ia_hist.append(
                        {"role": "assistant", "content": resp["content"]})

                    if resp.get("stop_reason") != "tool_use":
                        break

                    resultados = []
                    for bloco in resp["content"]:
                        if bloco["type"] != "tool_use":
                            continue
                        args = bloco["input"]
                        dado = ia_tools.executar(bloco["name"], args, unidades)
                        ultimo_dado = dado if "erro" not in dado else ultimo_dado
                        arg_txt = ", ".join(f'"{v}"' for v in args.values()) or "—"
                        tracos.append(f'{bloco["name"]}</b>({arg_txt})<b>')
                        resultados.append({
                            "type": "tool_result",
                            "tool_use_id": bloco["id"],
                            "content": json.dumps(dado, ensure_ascii=False, default=str),
                        })
                    st.session_state.ia_hist.append({"role": "user", "content": resultados})

            texto = "".join(b["text"] for b in resp["content"] if b["type"] == "text")
        except requests.HTTPError as e:
            texto = f"A API recusou a chamada ({e.response.status_code}). Confira a chave nos Secrets."
        except Exception as e:
            texto = f"Não consegui consultar agora: {e}"

        bloco = {"quem": "ia", "texto": texto or "Sem resposta.",
                 "tracos": tracos,
                 "kpis": _kpis(ultimo_dado) if not tracos or ultimo_dado else "",
                 "fonte": _fonte(ultimo_dado)}
        _render(bloco)
        st.session_state.ia_tela.append(bloco)
