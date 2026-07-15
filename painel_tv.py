# -*- coding: utf-8 -*-
"""
PAINEL TV · V360 — Molina Advogados
Página "Modo TV" para rodar DENTRO do V360 Relatórios (Streamlit).
Sincroniza com o Supabase a cada 5 min (mesma fonte do dashboard) e renderiza
o painel em tela cheia, girando sozinho entre Setor → Campeões → Meta.

COMO USAR
  1) Coloque este arquivo e o 'painel_template.html' na mesma pasta do repo.
     (Se seu app usa multipage, jogue em /pages para virar item de menu.)
  2) Adicione 'streamlit-autorefresh' no requirements.txt.
  3) Ligue os dados reais: ponha USAR_DADOS_REAIS = True e preencha
     carregar_dados() com a SUA view (a parte marcada com  >>> MAPEAR <<< ).
  4) Na TV: abra a URL desta página e aperte F para tela cheia.
"""

import json
import datetime as dt
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
USAR_DADOS_REAIS = False          # False = dados de exemplo (pra testar a TV já)
MINUTOS_SYNC     = 5              # ciclo de atualização
ALTURA_TV        = 1040          # altura do painel em px (ajuste à sua TV: 1040≈1080p)

st.set_page_config(
    page_title="Painel TV · V360",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# re-roda o script (e re-consulta o Supabase) a cada 5 min
st_autorefresh(interval=MINUTOS_SYNC * 60 * 1000, key="painel_tv_sync")

# esconde toda a moldura do Streamlit pra ficar painel puro
st.markdown("""
<style>
  #MainMenu, header, footer {visibility:hidden;}
  [data-testid="stSidebar"], [data-testid="collapsedControl"] {display:none;}
  .block-container {padding:0 !important; max-width:100% !important;}
  [data-testid="stAppViewContainer"] {background:#060b14;}
  iframe {border:none !important;}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# CARGA DOS DADOS  (cacheado por 5 min — só bate no banco nesse intervalo)
# ----------------------------------------------------------------------
@st.cache_data(ttl=MINUTOS_SYNC * 60, show_spinner=False)
def carregar_dados() -> dict:
    """Monta o dicionário que alimenta o painel.
       Estrutura esperada está em _dados_exemplo()."""
    if not USAR_DADOS_REAIS:
        return _dados_exemplo()

    # ================= >>> MAPEAR <<< =================
    # Reaproveite a conexão que o V360 Relatórios já usa para ler as views.
    # Troque 'consultar()' pela sua função/cliente. Exemplo com supabase-py:
    #
    #   from supabase import create_client
    #   sb = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    #   def consultar(view, **filtros):
    #       q = sb.table(view).select("*")
    #       for k, v in filtros.items():
    #           q = q.eq(k, v)
    #       return q.execute().data
    #
    # 1) SETOR — uma linha por área (Agendamento, Acompanhamento, etc.)
    #    Ajuste os nomes das colunas conforme a SUA view:
    #
    #   linhas = consultar("vw_v360_dashboard", setor="ADM")
    #   areas = [{
    #       "nome":        r["area"],
    #       "icone":       _icone(r["area"]),       # calendar|folder|shield|megaphone
    #       "atrasados":   r["atrasados"],
    #       "pendDia":     r["pendencias_dia"],
    #       "pendFut":     r["pendencias_futuras"],
    #       "cumpridoDia": r["cumpridos_dia"],
    #       "cumpridoMes": r["cumpridos_mes"],
    #   } for r in linhas]
    #
    # 2) CAMPEÕES — top colaboradores:
    #   colab = consultar("vw_v360_colaboradores")
    #   campeoes = sorted(
    #       [{"nome": r["nome"], "area": r.get("area",""), "pontos": r["cumpridos_mes"]} for r in colab],
    #       key=lambda x: x["pontos"], reverse=True)
    #
    # 3) META — unidade principal + outras:
    #   metas = consultar("vw_v360_metas_vs_meta")
    #   ...
    #
    # Por enquanto, com USAR_DADOS_REAIS=True mas sem o mapeamento preenchido,
    # caímos no exemplo pra não quebrar a TV:
    return _dados_exemplo()
    # ==================================================


def _icone(area: str) -> str:
    a = (area or "").lower()
    if "agend" in a:                          return "calendar"
    if "verific" in a or "exig" in a:         return "shield"
    if "den" in a:                            return "megaphone"
    return "folder"


def _dados_exemplo() -> dict:
    return {
        "setor": {
            "nome": "ADM",
            "titulo": "Painel Operacional ADM",
            "areas": [
                {"nome": "Agendamento",            "icone": "calendar",  "atrasados": 12, "pendDia": 8,  "pendFut": 35, "cumpridoDia": 7,  "cumpridoMes": 132},
                {"nome": "Acompanhamento ADM",     "icone": "folder",    "atrasados": 18, "pendDia": 10, "pendFut": 42, "cumpridoDia": 9,  "cumpridoMes": 145},
                {"nome": "Verificação de Exigência","icone": "shield",   "atrasados": 27, "pendDia": 14, "pendFut": 61, "cumpridoDia": 12, "cumpridoMes": 198},
                {"nome": "Denúncia",               "icone": "megaphone", "atrasados": 5,  "pendDia": 3,  "pendFut": 12, "cumpridoDia": 2,  "cumpridoMes": 37},
            ],
        },
        "campeoes": [
            {"nome": "Mariana Lopes",  "area": "Verificação",    "pontos": 198},
            {"nome": "Rafael Souza",   "area": "Acompanhamento", "pontos": 145},
            {"nome": "Carla Mendes",   "area": "Agendamento",    "pontos": 132},
            {"nome": "João Pereira",   "area": "Denúncia",       "pontos": 37},
            {"nome": "Beatriz Alves",  "area": "Agendamento",    "pontos": 94},
            {"nome": "Diego Ramos",    "area": "Verificação",    "pontos": 81},
            {"nome": "Larissa Costa",  "area": "Acompanhamento", "pontos": 69},
        ],
        "campeoesMetrica": "cumpridos no mês",
        "unidade": "Itacoatiara",
        "metaUnidade": {"meta": 780, "realizado": 703},
        "outrasUnidades": [
            {"nome": "Manaus",     "meta": 1200, "realizado": 1044},
            {"nome": "Parintins",  "meta": 540,  "realizado": 498},
            {"nome": "Manacapuru", "meta": 420,  "realizado": 301},
        ],
        # comportamento
        "segundosPorTela": 16,
        "minutosAtualizacao": MINUTOS_SYNC,
        "fonteDados": "Legal One API",
        "atualizarSupabaseMin": 0,   # 0: quem atualiza é o Streamlit (não o navegador)
    }


# ----------------------------------------------------------------------
# RENDER
# ----------------------------------------------------------------------
dados = carregar_dados()

template = Path(__file__).with_name("painel_template.html").read_text(encoding="utf-8")
dados_js = "const DADOS = " + json.dumps(dados, ensure_ascii=False) + ";"
html = template.replace("/*__DADOS__*/", dados_js)

components.html(html, height=ALTURA_TV, scrolling=False)
