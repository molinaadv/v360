# -*- coding: utf-8 -*-
"""
V360 — Assistente (Streamlit).

Tela. Toda a conversa com o modelo vive em `ia_modelo.py`; as consultas ao banco,
em `ia_tools.py`. Aqui fica só o prompt, o desenho e o estado da sessão.

Trocar de modelo (Claude / Kimi) não muda nada deste arquivo além do seletor.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import plotly.graph_objects as go
import requests
import streamlit as st

import ia_modelo

TZ = ZoneInfo("America/Manaus")

# Detalhe técnico na tela (nome da função consultada, view, modelo, tokens).
# False = visão do gestor. True = modo depuração — foi assim que se percebeu
# que o modelo tinha inventado número (cartão dizia 13, texto dizia 23).
DETALHES = False

VOCABULARIO = """
VOCABULÁRIO DO ESCRITÓRIO — mapeamentos JÁ CONFIRMADOS. Use direto, sem
consultar listar_subtipos antes (estes nomes estão certos):

- "pasta" / "pasta aberta" / "abriu pasta" — SEM área especificada, mande os 4:
      subtipo = ["Enviado p/ Análise", "Enviado p/ Análise ADM",
                 "Enviado p/ Análise Cível", "Enviado p/ Análise Trabalhista"]
  Se citarem uma área, mande só a dela:
      previdenciário judicial → ["Enviado p/ Análise"]
      previdenciário administrativo (ADM) → ["Enviado p/ Análise ADM"]
      cível → ["Enviado p/ Análise Cível"]
      trabalhista → ["Enviado p/ Análise Trabalhista"]
  NÃO existe "Enviado p/ Análise 1" — ignore.
  NUNCA responda "pasta" com meta_vs_realizado.

  ⚠ NOMES OFICIAIS destes dois números (use exatamente assim):
    • `no_mes` (com base="conclusao") → "PASTAS ABERTAS". A tarefa "Enviado p/ Análise" é o
      pedido de validação; quando o analista a CUMPRE, ele confirmou documento
      e direito — a pasta está aberta de fato. Cumprido = pasta aberta.
      É ESTE o número que responde "quantas pastas abriu / pastas abertas".
      Chame contar_em_aberto SEM base (o padrão já é conclusao).
    • `em_aberto` → "PASTAS PENDENTES DE ANÁLISE". Pedido de validação que
      ninguém conferiu ainda. Não é pasta aberta — é candidata, pode ser
      reprovada.
  NUNCA chame o `em_aberto` de "pastas abertas": inverte o sentido.

  ⚠ NÃO CONFUNDA com "pendência" (item abaixo): "pasta pendente de análise" é o
  `em_aberto` DESTES subtipos; "pendência" são os subtipos 'Pendência na
  Análise*', que é outro indicador. Se o gestor disser só "pendência", pergunte
  qual dos dois ele quer, ou responda os dois separando os nomes.

- "agendamento de segurança" é indicador SEPARADO — NÃO entra na conta de pastas:
      subtipo = ["Enviado p/ Análise - Agendemento de Segurança"]
  Copie o nome EXATAMENTE assim, inclusive "Agendemento" (a base tem esse erro
  de digitação; escrever certo devolve zero). É subtipo NOVO, então número
  baixo é esperado — não trate como erro nem como queda.
- "enviada p/ confecção" / "enviadas para confecção":
      subtipo = ["Enviada p/ Confecção"]  E  base = "criacao"
  Aqui conta por CADASTRO da tarefa (creation_date), não por conclusão — é
  regra do escritório, diferente das pastas. O campo `no_mes` vem rotulado
  "cadastradas no mês"; ao responder, chame de "enviadas para confecção no mês".

- "pendência": subtipo = ["Pendência na Análise", "Pendência na Análise - ADM",
      "Pendência na Análise- Cível"]

INDICADORES OFICIAIS — para QUALQUER um destes, chame contar_indicador com o
nome exato. NÃO passe subtipos: a função resolve os subtipos e o critério
(conclusão ou cadastro) direto do catálogo no banco.

  Colaborador que abriu mais pastas ( destaque da meta )  [Abertura · conclusão]
  Organização de Pastas  [Abertura · cadastro]
  Acompanhamento ADM  [Acompanhamento ADM · cadastro]
  Agendamento Administrativo  [Agendamento · cadastro]
  Pastas Abertas Cível  [Análise · conclusão]
  Pastas Abertas Previdenciarias e Meta  [Análise · conclusão]
  Pastas Abertas Trabalhista  [Análise · conclusão]
  Pastas a serem analisadas  [Análise · cadastro]
  Voltaram da Denúncia  [Análise · cadastro]
  Análise Final Cível  [Análise Final Cível · cadastro]
  Análise Final Previdenciária  [Análise Final Previdenciária · cadastro]
  Benefício ADM - Deferido  [Benefício ADM - Deferido · cadastro]
  Benefício ADM - Indeferido  [Benefício ADM - Indeferido · cadastro]
  Inicial Revisada para Protocolar  [Confecção · cadastro]
  Inicial enviada ao protocolo  [Confecção · cadastro]
  Inicial enviada ao protocolo - Cível  [Confecção · cadastro]
  Inicial na Confecção  [Confecção · cadastro]
  Inicial na Revisão  [Confecção · cadastro]
  Pastas a serem distribuidas  [Confecção · cadastro]
  Denúncia  [Denúncia · cadastro]
  Acordo Agendado  [Implantação · cadastro]
  Pré-Acordo  [Implantação · cadastro]
  Pendencia de pastas abertas  [Pendencia · cadastro]
  Pendencia de pastas abertas - Iniciadas  [Pendencia · cadastro]

Se o gestor usar um termo que não está aqui, chame listar_indicadores com um
trecho do termo antes de responder. Nunca invente indicador.
- "meta" / "bateu a meta": aí sim meta_vs_realizado.

O campo `subtipo` é sempre uma LISTA, mesmo com um nome só.
Unidade é MAIÚSCULA na base: "atrium" → "ATRIUM".

listar_subtipos serve para assunto FORA desta lista. Se ele devolver vazio,
tente um trecho MENOR (ex.: "Alvará" em vez de "Aguardando Levantamento do
Alvará"). Não repita a mesma busca.
"""

SYSTEM = """Você é o assistente do V360, painel interno da Molina Advogados (direito previdenciário, Manaus/AM).

Você responde a advogados e gestores do escritório sobre os dados operacionais.

REGRAS:
- Todo número vem das funções. Você NUNCA estima, arredonda de cabeça ou inventa um valor. Copie os valores EXATOS do resultado — se a função devolveu 13, escreva 13, nunca outro número. Use o `rotulo_no_mes` que vier no resultado para nomear o número do mês. Percentual só se vier pronto no campo `variacao_pct`; não calcule de cabeça. Se não tem função pra pergunta, diga o que não consegue responder e sugira o painel certo.
- Os nomes de subtipo batem letra por letra. Se não tiver certeza do nome exato, chame listar_subtipos ANTES de contar. Nunca chute o nome.
- "Em aberto" = Pendente, Não cumprido ou Iniciado. "Cumprido no mês" usa mes_conclusao.
- Crédito de produtividade é de quem CONCLUIU (usuario_executor), nunca do responsável.
- COMPARAÇÃO É OBRIGATÓRIA: sempre que der um número do mês, diga também como está vs. o mês anterior, usando o campo `comparacao` que a função devolve. Nunca calcule o percentual de cabeça — use o `variacao_pct`. Se ele vier null, diga que não há base de comparação.
- O mês corrente está em andamento. A comparação certa é com o MESMO PERÍODO do mês anterior (`mes_anterior_mesmo_periodo`), não com o mês fechado. Nunca anuncie queda comparando mês parcial com mês cheio.
- Para tendência, evolução ou "cresceu/caiu" em mais de um mês, use serie_mensal. Repasse os `avisos` que ela devolver quando forem relevantes — principalmente sobre status preso e mês incompleto.
- serie_mensal tem duas bases: conclusão (o que foi entregue) e criação (o que entrou). São coisas diferentes; diga qual está usando e não misture na mesma frase.
- Você só enxerga as unidades do usuário logado. Isso já é aplicado automaticamente — não peça permissão nem tente contornar.
- Você NÃO tem acesso a CPF, número de benefício, senha do INSS, telefone ou endereço de cliente. Esses dados ficam no campo notes do Legal One e estão fora do seu escopo por segurança. Se pedirem, explique isso em uma frase e diga que a consulta deve ser feita direto no Legal One.
- Você não dá parecer jurídico, não prevê resultado de processo e não estima valores.
- NUNCA repita uma chamada de função idêntica. Se o resultado veio vazio, o problema é o argumento (nome do subtipo, mês, unidade) — corrija o argumento ou use outra função. Repetir igual devolve o mesmo vazio.
- Se uma função devolver vazio ou "sem meta cadastrada", diga isso ao usuário em vez de insistir.

COMPARAÇÃO (sempre):
- Toda resposta com quantidade do mês vem acompanhada da comparação com o mês anterior. O contar_em_aberto já devolve isso no campo "comparacao"; para tendência de vários meses use serie_mensal.
- Se variacao_pct vier null, NÃO invente percentual: diga que não há base de comparação (mês anterior zerado).
- Repasse os "avisos" da função quando forem relevantes — principalmente que o mês corrente está incompleto. Nunca anuncie queda no mês corrente sem essa ressalva.
- Entrada (criadas) e entrega (cumpridas) são coisas diferentes. Diga qual das duas você está reportando.

ESTILO:
- Português brasileiro, direto, sem rodeio. 2 a 4 frases.
- Comece pelo número que responde a pergunta. Depois, no máximo, o que ele significa.
- Se aparecer muita tarefa "Iniciado" em aberto, mencione: pode ser status preso (fantasma de sync), vale rodar o Re-sync.
- Nada de bullet a não ser que a pergunta peça lista.
- NUNCA narre o que vai fazer. Nada de "vou consultar", "vou buscar", "preciso dos subtipos". Chame a função direto e, quando o resultado chegar, escreva só a resposta final. Texto de planejamento é ruído para o gestor.
- Quando a função devolver `por_area`, SEMPRE detalhe: uma linha por área (use o rótulo que veio em `area`, não o nome técnico do subtipo) e o TOTAL GERAL no fim. Área com zero também aparece. Aqui a lista é obrigatória, não é exceção.
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
  .ia-alerta{background:#2a1520;border:1px solid #7a3348;color:#ef7a7a;
    border-radius:12px;padding:11px 14px;margin:10px 0;font-size:12.5px;line-height:1.5}
  .ia-alerta b{color:#ff9aa8}
</style>
"""


def _bloco_unidades(nomes: list) -> str:
    """Lista real de unidades no prompt. Sem isto o modelo não sabe se
    'compensa' é unidade, área ou assunto — e para para perguntar."""
    if not nomes:
        return ""
    return ("\nUNIDADES EXISTENTES NA BASE (nomes EXATOS, use como vieram):\n"
            + ", ".join(nomes) +
            "\nO gestor fala em minúsculo e sem 'ação' — traduza. Se o núcleo "
            "tiver o par 'X' e 'AÇÃO X', mande OS DOIS na lista `unidade`, a não "
            "ser que ele peça só um. O campo `unidade` é sempre LISTA.\n")


def _system(nomes_unidades: list | None = None) -> str:
    """Prompt + data de HOJE. Sem isso o modelo chuta o mês (chegou a consultar
    2025-01) — ele não tem relógio."""
    hoje = datetime.now(TZ)
    dias = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
    return (f"{SYSTEM}\n{VOCABULARIO}\n{_bloco_unidades(nomes_unidades or [])}"
            f"HOJE é {dias[hoje.weekday()]}, {hoje:%d/%m/%Y}, em Manaus. "
            f"O mês corrente é {hoje:%Y-%m} e está EM ANDAMENTO. "
            f"Quando o usuário disser 'este mês', use {hoje:%Y-%m}; "
            f"'mês passado' é {(hoje.replace(day=1) - timedelta(days=1)):%Y-%m}.")


def _kpis(dado: dict) -> str:
    """Cartões grandes quando a função devolve contagem. Cor semântica do projeto."""
    cards = []
    if "em_aberto" in dado and "no_mes" in dado:
        cards = [("#2fce8f", dado["no_mes"], dado.get("rotulo_no_mes", "no mês")),
                 ("#f5a524", dado["em_aberto"], "em aberto"),
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


def _fonte(dado: dict, modelo: str, uso: dict) -> str:
    f = dado.get("fonte")
    if not f:
        return ""
    hora = datetime.now(TZ).strftime("%d/%m %H:%M")
    if not DETALHES:
        # procedência sem jargão: o gestor precisa saber de onde veio e quando
        return (f'<div class="ia-src">Números apurados na base do Legal One · '
                f'consultado {hora} (Manaus)</div>')

    tags = f'<span class="tag">{f["view"]}</span>'
    if f.get("regra"):
        tags += f'<span class="tag">{f["regra"]}</span>'
    tags += f'<span class="tag">{modelo}</span>'
    ent = uso.get("input_tokens") or uso.get("prompt_tokens")
    sai = uso.get("output_tokens") or uso.get("completion_tokens")
    if ent and sai:
        tags += f'<span class="tag">{ent}→{sai} tok</span>'
    return f'<div class="ia-src">Fonte: {tags} · Legal One API · consultado {hora}</div>'


CORES = {"aberta": "#2fce8f", "pendente": "#f5a524", "neutro": "#5b8cff",
         "linha": "#26324d", "ink": "#f2f6ff", "muted": "#93a1bd"}


def _layout(fig, altura: int):
    fig.update_layout(
        height=altura, margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=CORES["muted"], size=12),
        legend=dict(orientation="h", y=1.12, x=0, bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor=CORES["linha"], zeroline=False),
        yaxis=dict(gridcolor=CORES["linha"], zeroline=False),
    )
    return fig


# rótulo curto: em meia largura, "PREVIDENCIÁRIO ADMINISTRATIVO" come o gráfico
CURTO = {"PREVIDENCIÁRIO JUDICIAL": "Prev. Judicial",
         "PREVIDENCIÁRIO ADMINISTRATIVO": "Prev. Administrativo",
         "AGENDAMENTO DE SEGURANÇA": "Agend. Segurança",
         "CÍVEL": "Cível", "TRABALHISTA": "Trabalhista"}


def _graficos(dado: dict) -> list:
    """Lista de (título, figura) montada a partir do RESULTADO DA CONSULTA —
    nunca do texto do modelo. Se o modelo errar um número na frase, o gráfico
    continua certo. Pode devolver dois: quebra por área + comparativo."""
    if not dado:
        return []
    saida = []

    # 1) quebra por área (pastas): barras horizontais, aberta x pendente
    areas = dado.get("por_area")
    if areas:
        rot = [CURTO.get(a["area"], a["area"].title()) for a in areas][::-1]
        fig = go.Figure([
            go.Bar(y=rot, x=[a["no_mes"] for a in areas][::-1],
                   name=dado.get("rotulo_no_mes", "no mês").capitalize(),
                   orientation="h", marker_color=CORES["aberta"],
                   text=[a["no_mes"] for a in areas][::-1],
                   textposition="outside", cliponaxis=False),
            go.Bar(y=rot, x=[a["em_aberto"] for a in areas][::-1],
                   name="Pendentes de análise", orientation="h",
                   marker_color=CORES["pendente"], text=[a["em_aberto"] for a in areas][::-1],
                   textposition="outside", cliponaxis=False),
        ])
        fig.update_layout(barmode="group")
        saida.append(("Por área", _layout(fig, 90 + 46 * len(areas))))

    # 2) série mensal: barras por mês, o corrente (parcial) mais apagado
    meses = dado.get("meses")
    if meses:
        cores = [CORES["neutro"]] * len(meses)
        if meses[-1].get("parcial"):
            cores[-1] = "#3a5a99"       # mês incompleto: visualmente atenuado
        fig = go.Figure([go.Bar(
            x=[m["mes"] for m in meses], y=[m["qtd"] for m in meses],
            marker_color=cores, text=[m["qtd"] for m in meses],
            textposition="outside", cliponaxis=False, showlegend=False)])
        saida.append(("Evolução mensal", _layout(fig, 260)))

    # 3) comparativo: este mês x MESMO PERÍODO do mês anterior (o mês corrente
    #    não fechou; comparar com o mês cheio inventaria uma queda)
    comp = dado.get("comparacao") or {}
    if "mes_anterior_mesmo_periodo" in comp and "no_mes" in dado:
        ant, atual = comp["mes_anterior_mesmo_periodo"], dado["no_mes"]
        fig = go.Figure([go.Bar(
            x=["Mês anterior<br>(mesmo período)", "Este mês"], y=[ant, atual],
            marker_color=[CORES["neutro"], CORES["aberta"]], text=[ant, atual],
            textposition="outside", cliponaxis=False, showlegend=False)])
        pct = comp.get("variacao_pct")
        titulo = "Comparativo" + (f" · {pct:+d}%" if isinstance(pct, int) else "")
        alt = 90 + 46 * len(areas) if areas else 240
        saida.append((titulo, _layout(fig, alt)))

    return saida


def _alerta(suspeitos: list) -> str:
    """Número no texto que não veio do banco. Não some com a resposta: mostra
    e deixa o humano julgar."""
    if not suspeitos:
        return ""
    n = ", ".join(str(x) for x in suspeitos)
    return (f'<div class="ia-alerta"><b>⚠ Conferir:</b> o texto cita '
            f'<b>{n}</b>, que não veio da consulta. Confie nos cartões e na '
            f'fonte abaixo, não na frase.</div>')


def _render(bloco: dict, idx: int = 0):
    if DETALHES:
        for t in bloco.get("tracos", []):
            st.markdown(f'<div class="ia-trace">consultou <b>{t}</b></div>',
                        unsafe_allow_html=True)
    if bloco.get("kpis"):
        st.markdown(bloco["kpis"], unsafe_allow_html=True)
    if bloco.get("alerta"):
        st.markdown(bloco["alerta"], unsafe_allow_html=True)
    st.markdown(bloco["texto"])
    figs = _graficos(bloco.get("dado") or {})
    if figs:
        cfg = {"displayModeBar": False}
        # st.columns() para 2+; para 1, um container. NUNCA `[st]`: o módulo
        # streamlit não é context manager e o `with col:` estourava TypeError.
        colunas = (st.columns(len(figs)) if len(figs) > 1
                   else [st.container()])
        for i, ((titulo, fig), col) in enumerate(zip(figs, colunas)):
            with col:
                st.markdown(
                    f'<div style="font-size:10.5px;color:#6b7a99;'
                    f'text-transform:uppercase;letter-spacing:.6px;'
                    f'margin:6px 0 -6px">{titulo}</div>', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True, config=cfg,
                                key=f"ia_graf_{idx}_{i}")
    if bloco.get("fonte"):
        st.markdown(bloco["fonte"], unsafe_allow_html=True)


def render(unidades, rotulo_recorte: str = "", nomes_unidades: list | None = None):
    """Chamada pelo app.py. `unidades` = '*' ou lista (vem do auth.aplicar_recorte)."""
    st.markdown(CSS, unsafe_allow_html=True)

    esc = "todas as unidades" if unidades == "*" else f"{len(unidades)} unidades"
    modelo = ia_modelo.PADRAO      # fixo; trocar em ia_modelo.PADRAO
    st.markdown(
        f"### Assistente&nbsp;&nbsp;"
        f"<span style='font-size:11px;color:#93a1bd;background:#141d2e;border:1px solid #26324d;"
        f"padding:5px 11px;border-radius:999px'>{rotulo_recorte or esc}</span>&nbsp;"
        f"<span style='font-size:11px;color:#2fce8f'>● ao vivo</span>",
        unsafe_allow_html=True)

    # Para voltar a comparar modelos, basta descomentar (MODELOS continua completo):
    # chaves = list(ia_modelo.MODELOS)
    # modelo = st.selectbox("Modelo", chaves, index=chaves.index(ia_modelo.PADRAO),
    #                       format_func=lambda k: ia_modelo.MODELOS[k]["rotulo"],
    #                       label_visibility="collapsed")

    if "ia_hist" not in st.session_state:
        st.session_state.ia_hist = []   # formato neutro (ia_modelo)
    if "ia_tela" not in st.session_state:
        st.session_state.ia_tela = []   # o que desenhamos

    for i, b in enumerate(st.session_state.ia_tela):
        with st.chat_message("user" if b["quem"] == "user" else "assistant"):
            if b["quem"] == "user":
                st.markdown(b["texto"])
            else:
                _render(b, i)

    pergunta = st.chat_input("Pergunte sobre suas unidades…")
    if not pergunta:
        return

    st.session_state.ia_hist.append({"quem": "user", "texto": pergunta})
    st.session_state.ia_tela.append({"quem": "user", "texto": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        try:
            with st.spinner("consultando a base…"):
                r = ia_modelo.conversar(st.session_state.ia_hist,
                                        _system(nomes_unidades),
                                        unidades, st.secrets, modelo)
        except requests.HTTPError as e:
            r = {"texto": f"A API recusou a chamada ({e.response.status_code}). "
                          f"Confira a chave nos Secrets.",
                 "tracos": [], "ultimo_dado": {}, "uso": {}, "modelo": modelo}
        except Exception as e:
            r = {"texto": f"Não consegui consultar agora: {e}",
                 "tracos": [], "ultimo_dado": {}, "uso": {}, "modelo": modelo}

        bloco = {"quem": "ia", "texto": r["texto"] or "Sem resposta.",
                 "tracos": r["tracos"],
                 "alerta": _alerta(r.get("suspeitos") or []),
                 "dado": r["ultimo_dado"],
                 "kpis": _kpis(r["ultimo_dado"]),
                 "fonte": _fonte(r["ultimo_dado"], r["modelo"], r["uso"])}
        _render(bloco, len(st.session_state.ia_tela))
        st.session_state.ia_tela.append(bloco)
