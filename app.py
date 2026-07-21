import base64
from pathlib import Path
from datetime import date, timedelta, datetime, timezone
import uuid
import io
import zipfile

import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client, Client

# =====================================================
# V360 CLIENTES - MOLINA ADVOGADOS / BOA VISTA
# Streamlit + Supabase
# =====================================================

st.set_page_config(
    page_title="V360 Clientes",
    page_icon="📍",
    layout="wide"
)

TABELA_USUARIOS = "captacao_usuarios"
TABELA_LEADS = "captacao_leads"
TABELA_HISTORICO = "captacao_lead_historico"
TABELA_BENEFICIOS = "captacao_beneficios"
TABELA_LOCAIS = "captacao_locais_captacao"
TABELA_PENDENCIAS = "captacao_pendencias"
TABELA_TIPOS_PENDENCIA = "captacao_tipos_pendencia"
TABELA_UNIDADES = "captacao_unidades"
TABELA_USUARIO_UNIDADES = "captacao_usuario_unidades"
TABELA_USUARIO_CIDADES = "captacao_usuario_cidades"
TABELA_TIPOS_ARQUIVO = "captacao_tipos_arquivo"
TABELA_BAIRROS = "captacao_bairros"
TABELA_ARQUIVOS = "captacao_arquivos"
TABELA_AGENDAMENTOS = "captacao_agendamentos"
BUCKET_ARQUIVOS = "captacao-temporario"
LOGO_FILE = "Logo_Molina_1_Traco_negativomenor.png"
VERSAO_APP = "producao-v360-cidade-boa-vista-corrigida"

# -------------------------------
# CONEXÃO SUPABASE
# -------------------------------
@st.cache_resource
def conectar_supabase() -> Client:
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_ANON_KEY", "")
    if not url or not key:
        st.error("Configure SUPABASE_URL e SUPABASE_ANON_KEY no secrets do Streamlit.")
        st.stop()
    return create_client(url, key)

supabase = conectar_supabase()

# -------------------------------
# LISTAS PADRÃO
# -------------------------------
BAIRROS_BOA_VISTA = [
    "13 de Setembro",
    "Aeroporto",
    "Alvorada",
    "Aparecida",
    "Aquilino Mota Duarte",
    "Araceli Souto Maior",
    "Asa Branca",
    "Bela Vista",
    "Buritis",
    "Caçari",
    "Caimbé",
    "Calungá",
    "Cambará",
    "Canarinho",
    "Caranã",
    "Cauamé",
    "Centenário",
    "Centro",
    "Cidade Satélite",
    "Cinturão Verde",
    "Cruviana",
    "Dr. Silvio Botelho",
    "Equatorial",
    "Estados",
    "Jardim Caranã",
    "Jardim Floresta",
    "Jardim Neves",
    "Jardim Olímpico",
    "Jardim Primavera",
    "Jardim Tropical",
    "Jóquei Clube",
    "Laura Moreira",
    "Liberdade",
    "Marechal Rondon",
    "Mecejana",
    "Murilo Teixeira",
    "Nova Canaã",
    "Nova Cidade",
    "Olímpico",
    "Operário",
    "Paraviana",
    "Pintolândia",
    "Piscicultura",
    "Prata",
    "Professora Said Salomão",
    "Raiar do Sol",
    "Santa Luzia",
    "Santa Tereza",
    "São Francisco",
    "São Vicente",
    "Senador Hélio Campos",
    "Sílvio Leite",
    "Tancredo Neves",
    "Trinta e Um de Março",
    "União",
    "Outro",
]


BAIRROS_FIXOS_POR_CIDADE = {
    "manacapuru": [
        "Aparecida",
        "Área Rural de Manacapuru",
        "Biribiri",
        "Centro",
        "Correnteza",
        "Liberdade",
        "Morada do Sol",
        "Nova Manacá",
        "São Francisco",
        "São José",
        "Terra Preta",
        "União",
        "Vale Verde",
    ],
    "presidente figueiredo": [
        "Aida Mendonça",
        "Centro",
        "Galo da Serra",
        "Galo da Serra II",
        "Honório Roldão",
        "José Dutra",
        "Morada do Sol",
        "Orquídeas",
        "Sol Nascente",
        "Tancredo Neves",
        "Vale das Nascentes",
    ],
    "maués": [
        "Centro",
        "Do Éden",
        "Donga Michiles",
        "Maresia",
        "Mário Fonseca",
        "Novo Bairro",
        "Ramalho Júnior",
        "Santa Luzia",
        "Santa Tereza",
    ],
    "parintins": [
        "Castanheira",
        "Centro",
        "Distrito Industrial",
        "Djard Vieira",
        "Emílio Moreira",
        "Francesa",
        "Itaúna",
        "Itaúna II",
        "Jacareacanga",
        "João Novo",
        "Lady Laura",
        "Macurany",
        "Nossa Senhora de Nazaré",
        "Palmares",
        "Pascoal Allággio",
        "Paulo Corrêa",
        "Raimundo Muniz",
        "Santa Clara",
        "Santa Rita",
        "Santoca",
        "São Benedito",
        "São José",
        "São Vicente de Paula",
        "Teixeirão",
        "União",
        "Val Paraíso",
        "Vitória Régia",
    ],
}



BAIRROS_MANACAPURU_FIXO = [
    "Aparecida",
    "Área Rural de Manacapuru",
    "Biribiri",
    "Centro",
    "Correnteza",
    "Liberdade",
    "Morada do Sol",
    "Nova Manacá",
    "São Francisco",
    "São José",
    "Terra Preta",
    "União",
    "Vale Verde",
]


CIDADES_POR_UF = {
    "AM": [
        "Alvarães", "Amaturá", "Anamã", "Anori", "Apuí", "Atalaia do Norte",
        "Autazes", "Barcelos", "Barreirinha", "Benjamin Constant", "Beruri",
        "Boa Vista do Ramos", "Boca do Acre", "Borba", "Caapiranga", "Canutama",
        "Carauari", "Careiro", "Careiro da Várzea", "Coari", "Codajás",
        "Eirunepé", "Envira", "Fonte Boa", "Guajará", "Humaitá", "Ipixuna",
        "Iranduba", "Itacoatiara", "Itamarati", "Itapiranga", "Japurá", "Juruá",
        "Jutaí", "Lábrea", "Manacapuru", "Manaquiri", "Manaus", "Manicoré",
        "Maraã", "Maués", "Nhamundá", "Nova Olinda do Norte", "Novo Airão",
        "Novo Aripuanã", "Parintins", "Pauini", "Presidente Figueiredo",
        "Rio Preto da Eva", "Santa Isabel do Rio Negro", "Santo Antônio do Içá",
        "São Gabriel da Cachoeira", "São Paulo de Olivença", "São Sebastião do Uatumã",
        "Silves", "Tabatinga", "Tapauá", "Tefé", "Tonantins", "Uarini",
        "Urucará", "Urucurituba", "Outro",
    ],
    "RR": [
        "Boa Vista", "Alto Alegre", "Amajari", "Bonfim", "Cantá", "Caracaraí",
        "Caroebe", "Iracema", "Mucajaí", "Normandia", "Pacaraima",
        "Rorainópolis", "São João da Baliza", "São Luiz", "Uiramutã", "Outro",
    ],
    "MT": ["Cuiabá", "Rondonópolis", "Outro"],
    "RO": ["Porto Velho", "Outro"],
}


AREAS_ACAO = ["Previdenciário", "Trabalhista", "Cível", "Família", "Outro"]

TIPOS_BENEFICIO = [
    "LOAS Idoso", "LOAS Deficiente", "Auxílio-doença / Incapacidade temporária",
    "Aposentadoria por idade urbana", "Aposentadoria rural", "Salário-maternidade",
    "Pensão por morte", "Auxílio-reclusão", "Revisão de benefício", "Outro"
]

STATUS_LEAD = ["Novo", "Em atendimento", "Agendado", "Convertido", "Perdido"]
MOTIVOS_PERDA = [
    "", "Não possui direito", "Cliente desistiu", "Já possui advogado",
    "Não apresentou documentos", "Sem contato", "Benefício negado anteriormente",
    "Valor de honorários", "Outro"
]


STATUS_AGENDAMENTO = [
    "Agendado",
    "Confirmado",
    "Atendido",
    "Não compareceu",
    "Remarcado",
    "Cancelado",
]

MODALIDADES_AGENDAMENTO = [
    "Presencial",
    "Telefone",
    "WhatsApp",
    "Videochamada",
]

STATUS_PENDENCIA = ["Aberta", "Em andamento", "Resolvida", "Cancelada"]
PRIORIDADE_PENDENCIA = ["Normal", "Alta", "Urgente", "Baixa"]
TIPOS_PENDENCIA_PADRAO = [
    "RG/CNH", "CPF", "Comprovante de residência", "Laudo médico", "CNIS",
    "Carteira de trabalho", "Procuração", "Contrato", "Extrato bancário", "Outro"
]

TIPOS_ARQUIVO_PADRAO = [
    "Documentos do cliente",
    "RG/CNH",
    "CPF",
    "Comprovante de residência",
    "Laudos",
    "Exames",
    "Receitas médicas",
    "CNIS",
    "Carteira de trabalho",
    "Certidão",
    "Procuração",
    "Contrato",
    "Outros",
]

# -------------------------------
# VISUAL / MARCA
# -------------------------------
def get_logo_base64() -> str:
    caminho = Path(LOGO_FILE)
    if not caminho.exists():
        caminho = Path(__file__).parent / LOGO_FILE
    if caminho.exists():
        return base64.b64encode(caminho.read_bytes()).decode("utf-8")
    return ""


def aplicar_css_base():
    st.markdown(
        """
        <style>
        :root {
            --v360-navy: #061A33;
            --v360-navy-2: #09294D;
            --v360-cyan: #18BDF2;
            --v360-blue: #0077C8;
            --v360-text: #1E2A3A;
            --v360-soft: #F4F8FC;
        }
        .block-container { padding-top: 1rem; }
        h1, h2, h3 { color: var(--v360-text); }
        .stButton > button {
            border-radius: 12px;
            border: 1px solid #D8E2ED;
            font-weight: 700;
        }
        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid #E0E8F0;
            border-radius: 16px;
            padding: 16px;
            box-shadow: 0 8px 24px rgba(6,26,51,0.06);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def aplicar_css_mobile():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        header[data-testid="stHeader"] { background: transparent; }
        .block-container {
            max-width: 460px;
            padding: 0 !important;
            background: #F4F8FC;
        }
        .main .block-container { margin: 0 auto; }
        .mobile-header {
            background: linear-gradient(145deg, #061A33 0%, #09294D 65%, #064A80 100%);
            color: white;
            padding: 14px 16px 12px 16px;
            border-bottom: 4px solid #18BDF2;
            border-radius: 0 0 18px 18px;
            box-shadow: 0 10px 22px rgba(6,26,51,.18);
            overflow: hidden;
            margin-bottom: 10px;
        }
        .brand-line {
            display:flex;
            flex-direction:row;
            align-items:center;
            justify-content:space-between;
            gap:12px;
            width:100%;
        }
        .v360-title { font-size: 28px; font-weight: 950; letter-spacing: -1px; line-height:1; white-space:nowrap; }
        .v360-sub { color:#18BDF2; font-size:12px; font-weight:900; letter-spacing:3px; margin-top:5px; white-space:nowrap; }
        .molina-logo-wrap { flex:1; display:flex; justify-content:flex-end; min-width:0; }
        .molina-logo { width: 100%; max-width: 175px; max-height: 54px; height:auto; object-fit:contain; display:block; }
        .mobile-user-line { color:#B8D9EF; font-size:12px; margin-top:8px; }
        .mobile-nav-box {
            margin: 10px 14px 8px 14px;
            padding: 8px;
            background: rgba(255,255,255,.92);
            border: 1px solid #DCE8F4;
            border-radius: 16px;
            box-shadow: 0 8px 20px rgba(6,26,51,.08);
        }
        .mobile-nav-box div[role="radiogroup"] {
            display:grid !important;
            grid-template-columns: repeat(3, 1fr);
            gap:6px;
        }
        .mobile-nav-box div[role="radiogroup"] label {
            background:#F4F8FC !important;
            border:1px solid #DCE8F4 !important;
            border-radius:14px !important;
            padding:10px 8px !important;
            margin:0 !important;
            min-height:44px;
            display:flex !important;
            align-items:center !important;
            justify-content:center !important;
            text-align:center !important;
            font-weight:900 !important;
            color:#34435A !important;
            font-size:12px !important;
        }
        .mobile-nav-box div[role="radiogroup"] label:has(input:checked) {
            background: linear-gradient(90deg, #18BDF2, #0077C8) !important;
            border-color:#18BDF2 !important;
            color:white !important;
            box-shadow: 0 8px 18px rgba(0,119,200,.20);
        }
        .mobile-nav-box div[role="radiogroup"] label:has(input:checked) * { color:white !important; }
        .mobile-nav-box div[role="radiogroup"] label > div:first-child { display:none !important; }
        .mobile-card {
            margin: 10px 14px 16px 14px;
            padding: 18px 16px 16px 16px;
            background: white;
            border-radius: 22px;
            border: 1px solid #E0E8F0;
            box-shadow: 0 12px 28px rgba(6,26,51,.10);
        }
        .card-title { display:flex; align-items:center; gap:12px; margin-bottom:4px; }
        .pin-circle {
            background: linear-gradient(145deg, #0077C8, #18BDF2);
            color:white; min-width:48px; width:48px; height:48px; border-radius:50%;
            display:flex; align-items:center; justify-content:center; font-size:24px;
        }
        .card-title h2 { margin:0; font-size:27px; color:#1E2A3A; }
        .card-sub { color:#65748A; margin:0 0 12px 60px; }
        label, .stTextInput label, .stTextArea label, .stSelectbox label { font-weight: 700 !important; color:#34435A !important; }
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
            border-radius: 12px !important;
            min-height: 48px;
        }
        .mobile-card .stButton > button {
            width: 100%;
            height: 50px;
            border-radius: 14px;
            border: none;
            background: linear-gradient(90deg, #18BDF2, #0077C8);
            color: white;
            font-size: 16px;
            font-weight: 900;
            box-shadow: 0 10px 22px rgba(0,119,200,.22);
        }
        .mobile-card .stButton > button:hover { color:white; filter: brightness(1.02); }
        .mobile-note { text-align:center; color:#65748A; font-size:14px; padding-top:6px; }
        div[data-testid="stAlert"] { margin-left:16px; margin-right:16px; }
        @media (max-width: 390px) {
            .v360-title { font-size: 24px; }
            .v360-sub { font-size: 10px; letter-spacing:2.5px; }
            .molina-logo { max-width: 150px; max-height: 48px; }
            .card-title h2 { font-size: 24px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def aplicar_css_sidebar_desktop():
    st.markdown(
        """
        <style>
        /* SIDEBAR V360 - versão atualizada */
        section[data-testid="stSidebar"],
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div {
            background: linear-gradient(180deg, #061A33 0%, #09294D 56%, #0A3D7A 100%) !important;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(24,189,242,.35) !important;
            box-shadow: 8px 0 26px rgba(6,26,51,.10);
        }
        [data-testid="stSidebar"] * {
            color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] a,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] div {
            color: #FFFFFF !important;
        }
        .sidebar-brand {
    text-align: center;
    padding: 20px 8px 18px 8px;
    margin: 0 0 16px 0;
    border-bottom: 1px solid rgba(255,255,255,.16);
}

.sidebar-v360 {
    font-size: 58px;
    line-height: 1;
    font-weight: 950;
    letter-spacing: -2px;
    color: #FFFFFF !important;
}

.sidebar-cap {
    margin-top: 10px;
    color: #18BDF2 !important;
    font-size: 18px;
    font-weight: 950;
    letter-spacing: 5px;
}
        .sidebar-user-card {
            background: rgba(255,255,255,.09) !important;
            border: 1px solid rgba(255,255,255,.18) !important;
            border-radius: 16px;
            padding: 14px 12px;
            margin: 8px 0 18px 0;
            box-shadow: 0 10px 24px rgba(0,0,0,.14);
        }
        .sidebar-user-name {
            font-weight: 900;
            font-size: 15px;
            margin-bottom: 7px;
            color:#FFFFFF !important;
        }
        .sidebar-user-profile {
            color: #B8D9EF !important;
            font-weight: 700;
            font-size: 13px;
        }
        .sidebar-menu-title {
            color: #B8D9EF !important;
            text-transform: uppercase;
            font-size: 12px;
            font-weight: 950;
            letter-spacing: 1.4px;
            margin: 12px 0 8px 0;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label {
            background: rgba(255,255,255,.07) !important;
            border: 1px solid rgba(255,255,255,.14) !important;
            border-radius: 12px !important;
            padding: 9px 10px !important;
            margin-bottom: 8px !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background: rgba(24,189,242,.18) !important;
            border-color: rgba(24,189,242,.55) !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
            border-color: #18BDF2 !important;
        }
        [data-testid="stSidebar"] .stButton > button {
            width: 100%;
            background: rgba(255,255,255,.09) !important;
            border: 1px solid rgba(255,255,255,.22) !important;
            color: #FFFFFF !important;
            border-radius: 12px;
            font-weight: 850;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background: rgba(24,189,242,.20) !important;
            border-color: rgba(24,189,242,.60) !important;
            color: #FFFFFF !important;
        }
        .sidebar-version {
            margin-top: 18px;
            color: rgba(255,255,255,.45) !important;
            font-size: 10px;
            text-align:center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def header_mobile():
    logo64 = get_logo_base64()
    logo_html = f'<img class="molina-logo" src="data:image/png;base64,{logo64}" />' if logo64 else '<div style="font-weight:800">MOLINA<br><span style="font-size:12px;letter-spacing:3px">ADVOGADOS</span></div>'
    user_line = ""
    if st.session_state.get("usuario"):
        u = st.session_state.usuario
        user_line = f"<div class='mobile-user-line'>Boa Vista • {u.get('nome','')}</div>"
    st.markdown(
        f"""
        <div class="mobile-header">
            <div class="brand-line">
                <div>
                    <div class="v360-title"><span style="color:#18BDF2">V</span>360</div>
                    <div class="v360-sub">CLIENTES</div>
                </div>
                <div class="molina-logo-wrap">{logo_html}</div>
            </div>
            {user_line}
        </div>
        """,
        unsafe_allow_html=True,
    )


def abrir_card_mobile(titulo="Novo Cliente", subtitulo="Preencha os dados do cliente"):
    st.markdown(
        f"""
        <div class="mobile-card">
            <div class="card-title"><div class="pin-circle">📍</div><h2>{titulo}</h2></div>
            <p class="card-sub">{subtitulo}</p>
        """,
        unsafe_allow_html=True,
    )


def fechar_card_mobile():
    st.markdown("</div>", unsafe_allow_html=True)


def mobile_bottom_nav(ativo="Novo Cliente"):
    novo_class = "mobile-tab active" if ativo == "Novo Cliente" else "mobile-tab"
    minhas_class = "mobile-tab active" if ativo == "Minhas Clientes" else "mobile-tab"
    st.markdown(
        f"""
        <div class="mobile-tabs">
            <div class="{novo_class}">➕<br>Novo Lead</div>
            <div class="{minhas_class}">📋<br>Minhas Captações</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def header_desktop(usuario):
    logo64 = get_logo_base64()
    logo_html = f'<img src="data:image/png;base64,{logo64}" style="height:52px; object-fit:contain;" />' if logo64 else "<b>MOLINA ADVOGADOS</b>"
    st.markdown(
        f"""
        <div style="background:linear-gradient(90deg,#061A33,#09294D); padding:18px 24px; border-radius:18px; margin-bottom:22px; display:flex; align-items:center; justify-content:space-between; color:white;">
            <div>
                <div style="font-size:30px;font-weight:900;"><span style="color:#18BDF2">V</span>360 Clientes</div>
                <div style="color:#B8D9EF;">Boa Vista • Usuário: {usuario['nome']}</div>
            </div>
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

aplicar_css_base()

# -------------------------------
# FUNÇÕES AUXILIARES
# -------------------------------
def normalizar_texto(valor: str) -> str:
    if not valor:
        return ""
    return " ".join(valor.strip().split()).title()


def apenas_digitos(valor: str) -> str:
    if not valor:
        return ""
    return "".join(ch for ch in str(valor) if ch.isdigit())


def limpar_cpf(valor: str) -> str:
    return apenas_digitos(valor)


def formatar_cpf(valor: str) -> str:
    digitos = apenas_digitos(valor)
    if len(digitos) != 11:
        return valor or ""
    return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"


def formatar_telefone(valor: str) -> str:
    digitos = apenas_digitos(valor)
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    if len(digitos) == 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    return valor.strip() if isinstance(valor, str) else ""


def cpf_valido_ou_vazio(valor: str) -> bool:
    digitos = apenas_digitos(valor)
    return digitos == "" or len(digitos) == 11


def telefone_valido(valor: str) -> bool:
    digitos = apenas_digitos(valor)
    return len(digitos) in (10, 11)


def buscar_lead_por_cpf(cpf: str):
    cpf_limpo = limpar_cpf(cpf)
    if not cpf_limpo:
        return None
    try:
        resp = (
            supabase.table(TABELA_LEADS)
            .select("id,nome_cliente,cpf,telefone,bairro,captador_nome,data_captacao,status_lead")
            .eq("cpf", cpf_limpo)
            .limit(1)
            .execute()
        )
        return resp.data[0] if resp.data else None
    except Exception:
        return None


def preparar_dataframe_exibicao(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    if "cpf" in df2.columns:
        df2["cpf"] = df2["cpf"].fillna("").apply(formatar_cpf)
    if "telefone" in df2.columns:
        df2["telefone"] = df2["telefone"].fillna("").apply(formatar_telefone)
    return df2


def buscar_usuario(email: str, senha: str):
    try:
        resp = (
            supabase.table(TABELA_USUARIOS)
            .select("*")
            .eq("email", email.strip().lower())
            .eq("senha", senha)
            .eq("ativo", True)
            .limit(1)
            .execute()
        )
        return resp.data[0] if resp.data else None
    except Exception as e:
        st.error(f"Erro ao buscar usuário: {e}")
        return None


def listar_usuarios_ativos():
    try:
        resp = (
            supabase.table(TABELA_USUARIOS)
            .select("*")
            .eq("ativo", True)
            .order("nome")
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


def listar_usuarios_todos():
    try:
        resp = (
            supabase.table(TABELA_USUARIOS)
            .select("*")
            .order("nome")
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


def atualizar_usuario(usuario_id: str, dados: dict):
    return supabase.table(TABELA_USUARIOS).update(dados).eq("id", usuario_id).execute()


def remover_vinculos_usuario(usuario_id: str):
    if not usuario_id:
        return None
    return supabase.table(TABELA_USUARIO_UNIDADES).delete().eq("usuario_id", usuario_id).execute()


def substituir_usuario_unidades(usuario_id: str, unidades: list[str]):
    if not usuario_id:
        return
    try:
        remover_vinculos_usuario(usuario_id)
    except Exception:
        pass
    vincular_usuario_unidades(usuario_id, unidades)


def listar_beneficios():
    try:
        resp = (
            supabase.table(TABELA_BENEFICIOS)
            .select("nome,ativo")
            .eq("ativo", True)
            .order("nome")
            .execute()
        )
        itens = [r["nome"] for r in (resp.data or []) if r.get("nome")]
        return itens or TIPOS_BENEFICIO
    except Exception:
        return TIPOS_BENEFICIO


def listar_locais_captacao():
    try:
        resp = (
            supabase.table(TABELA_LOCAIS)
            .select("nome,ativo")
            .eq("ativo", True)
            .order("nome")
            .execute()
        )
        return [r["nome"] for r in (resp.data or []) if r.get("nome")]
    except Exception:
        return []


def listar_tipos_arquivo():
    try:
        resp = (
            supabase.table(TABELA_TIPOS_ARQUIVO)
            .select("nome,ativo")
            .eq("ativo", True)
            .order("nome")
            .execute()
        )
        itens = [r["nome"] for r in (resp.data or []) if r.get("nome")]
        return itens or TIPOS_ARQUIVO_PADRAO
    except Exception:
        return TIPOS_ARQUIVO_PADRAO





def normalizar_uf(valor: str) -> str:
    valor = normalizar_texto(valor).strip().upper()
    mapa = {
        "AMAZONAS": "AM",
        "AM": "AM",
        "RORAIMA": "RR",
        "RR": "RR",
        "MATO GROSSO": "MT",
        "MT": "MT",
        "RONDÔNIA": "RO",
        "RONDONIA": "RO",
        "RO": "RO",
    }
    return mapa.get(valor, valor[:2] if valor else "")


def normalizar_nome_unidade(nome: str, cidade: str = "", estado: str = "") -> str:
    """Mantém o nome real do escritório/unidade."""
    return normalizar_texto(nome).strip()


def listar_unidades(apenas_ativas: bool = True) -> list[dict]:
    try:
        q = supabase.table(TABELA_UNIDADES).select("*")
        if apenas_ativas:
            q = q.eq("ativo", True)
        resp = q.execute()

        unidades = []
        vistos = set()
        for row in (resp.data or []):
            nome = normalizar_texto(row.get("nome", "")).strip()
            cidade = normalizar_texto(row.get("cidade", "")).strip()
            estado = normalizar_uf(row.get("estado", ""))

            if not nome:
                continue

            chave = nome.casefold()
            if chave in vistos:
                continue
            vistos.add(chave)

            unidades.append({
                **row,
                "nome": nome,
                "cidade": cidade,
                "estado": estado,
            })

        return sorted(unidades, key=lambda x: x.get("nome", "").casefold())

    except Exception:
        return []


def listar_unidades_usuario(usuario_id: str):
    if not usuario_id:
        return []
    try:
        resp = (
            supabase.table(TABELA_USUARIO_UNIDADES)
            .select("unidade_nome")
            .eq("usuario_id", usuario_id)
            .execute()
        )
        return [r.get("unidade_nome") for r in (resp.data or []) if r.get("unidade_nome")]
    except Exception:
        return []


def usuario_eh_geral(usuario: dict) -> bool:
    perfil = (usuario or {}).get("perfil", "")
    # Gestor geral vê todas as unidades. Supervisor/gestor_unidade/gestor_regional respeitam as unidades liberadas.
    return perfil in ["gestor_geral", "gestor"]



def resolver_nome_unidade_cadastrada(valor: str) -> str:
    """
    Converte nomes antigos ou abreviados para o nome real cadastrado.
    Ex.: Boa Vista -> Boa Vista - Roraima.
    """
    valor_limpo = normalizar_texto(valor).strip()
    if not valor_limpo:
        return ""

    unidades_ativas = listar_unidades(True)
    por_nome = {
        normalizar_texto(u.get("nome", "")).strip().casefold(): u.get("nome", "")
        for u in unidades_ativas
        if u.get("nome")
    }

    chave = valor_limpo.casefold()
    if chave in por_nome:
        return por_nome[chave]

    aliases = {
        "boa vista": "boa vista - roraima",
        "roraima / boa vista": "boa vista - roraima",
        "boa vista - rr": "boa vista - roraima",
        "amazonas": "online",
    }

    destino = aliases.get(chave)
    if destino and destino in por_nome:
        return por_nome[destino]

    return valor_limpo


def unidades_permitidas_usuario(usuario: dict) -> list[str]:
    if not usuario:
        return []

    if usuario_eh_geral(usuario):
        return [u.get("nome") for u in listar_unidades(True) if u.get("nome")]

    unidades_brutas = listar_unidades_usuario(str(usuario.get("id", "")))

    # Compatibilidade com versões antigas da tabela de usuários.
    for campo in ["unidade", "unidade_padrao", "unidade_nome"]:
        valor = usuario.get(campo)
        if valor:
            unidades_brutas.append(valor)

    # O cabeçalho antigo pode mostrar Boa Vista, enquanto a unidade oficial
    # está cadastrada como Boa Vista - Roraima.
    if not unidades_brutas:
        unidades_brutas = ["Boa Vista"]

    unidades_resolvidas = []
    for unidade in unidades_brutas:
        nome_real = resolver_nome_unidade_cadastrada(unidade)
        if nome_real and nome_real not in unidades_resolvidas:
            unidades_resolvidas.append(nome_real)

    return unidades_resolvidas



def filtrar_clientes_do_atendente(df: pd.DataFrame, usuario: dict) -> pd.DataFrame:
    """
    Retorna todos os clientes pertencentes ao atendente.

    Compatibilidade:
    - registros atuais vinculados por captador_id;
    - registros antigos vinculados apenas pelo nome do captador;
    - registros eventualmente vinculados pelo e-mail do captador.
    """
    if df is None or df.empty or not usuario:
        return pd.DataFrame(columns=df.columns if df is not None else [])

    usuario_id = str(usuario.get("id") or "").strip()
    usuario_nome = normalizar_texto(usuario.get("nome") or "").strip().casefold()
    usuario_email = str(usuario.get("email") or "").strip().casefold()

    mascara = pd.Series(False, index=df.index)

    if "captador_id" in df.columns and usuario_id:
        mascara = mascara | (
            df["captador_id"].fillna("").astype(str).str.strip() == usuario_id
        )

    if "captador_nome" in df.columns and usuario_nome:
        mascara = mascara | (
            df["captador_nome"]
            .fillna("")
            .astype(str)
            .map(normalizar_texto)
            .str.strip()
            .str.casefold()
            == usuario_nome
        )

    for coluna_email in ["captador_email", "email_captador", "usuario_email"]:
        if coluna_email in df.columns and usuario_email:
            mascara = mascara | (
                df[coluna_email]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.casefold()
                == usuario_email
            )

    return df[mascara].copy()


def aplicar_escopo_unidade(df: pd.DataFrame, usuario: dict) -> pd.DataFrame:
    """
    Aplica o escopo de unidades do usuário.

    Compatibilidade importante:
    - clientes antigos podem estar gravados como "Boa Vista";
    - a unidade atual pode estar cadastrada como "Boa Vista - Roraima";
    - clientes antigos do Amazonas podem estar como "Amazonas" e a unidade atual como "Online".

    O filtro compara os nomes já resolvidos para a unidade oficial.
    """
    if df.empty:
        return df

    df = df.copy()

    if "unidade" not in df.columns:
        df["unidade"] = "Boa Vista"

    if usuario_eh_geral(usuario):
        return df

    permitidas = [
        resolver_nome_unidade_cadastrada(unidade)
        for unidade in unidades_permitidas_usuario(usuario)
        if unidade
    ]
    permitidas_normalizadas = {
        normalizar_texto(unidade).strip().casefold()
        for unidade in permitidas
        if unidade
    }

    def normalizar_unidade_registro(valor):
        valor_limpo = normalizar_texto(valor or "Boa Vista").strip()
        if not valor_limpo:
            valor_limpo = "Boa Vista"

        nome_resolvido = resolver_nome_unidade_cadastrada(valor_limpo)
        return normalizar_texto(nome_resolvido).strip().casefold()

    unidades_registros = df["unidade"].apply(normalizar_unidade_registro)

    return df[unidades_registros.isin(permitidas_normalizadas)].copy()


def nome_estado_por_uf(uf: str) -> str:
    mapa = {
        "AM": "Amazonas",
        "RR": "Roraima",
        "MT": "Mato Grosso",
        "RO": "Rondônia",
    }
    return mapa.get((uf or "").strip().upper(), (uf or "").strip().upper() or "Roraima")



def cidades_de_unidades(unidades: list[str]) -> list[str]:
    """
    Retorna as cidades disponíveis para as unidades informadas.

    Inclui:
    - a cidade principal cadastrada em captacao_unidades;
    - as cidades cadastradas para a UF;
    - a lista padrão da UF.

    Isso garante que Boa Vista apareça para a unidade
    BOA VISTA - RORAIMA, mesmo que ainda não existam bairros cadastrados.
    """
    cidades = []
    unidades_cadastradas = listar_unidades(True)

    for unidade_nome in unidades or []:
        unidade_norm = normalizar_texto(unidade_nome).strip().casefold()

        unidade_encontrada = next(
            (
                u for u in unidades_cadastradas
                if normalizar_texto(u.get("nome", "")).strip().casefold() == unidade_norm
            ),
            None,
        )

        uf = estado_da_unidade(unidade_nome)

        # Boa Vista - Roraima deve sempre disponibilizar Boa Vista,
        # mesmo que o registro antigo da unidade esteja com cidade/UF incorreta.
        if uf == "RR" and ("boa vista" in unidade_norm or "roraima" in unidade_norm):
            if "Boa Vista" not in cidades:
                cidades.append("Boa Vista")

        if unidade_encontrada:
            cidade_base = normalizar_texto(unidade_encontrada.get("cidade", "")).strip()
            # Não mistura cidade de outra UF quando o cadastro histórico da unidade
            # estiver inconsistente.
            if cidade_base and estado_por_cidade(cidade_base) == uf and cidade_base not in cidades:
                cidades.append(cidade_base)

        for cidade in listar_cidades_cadastradas(uf):
            if cidade and cidade not in cidades:
                cidades.append(cidade)

        for cidade in CIDADES_POR_UF.get(uf, []):
            if cidade and cidade not in cidades:
                cidades.append(cidade)

    return sorted(cidades, key=lambda item: item.casefold()) or ["Boa Vista"]


def listar_cidades_usuario(usuario_id: str) -> list[str]:
    if not usuario_id:
        return []
    try:
        resp = (
            supabase.table(TABELA_USUARIO_CIDADES)
            .select("cidade,ativo")
            .eq("usuario_id", usuario_id)
            .eq("ativo", True)
            .execute()
        )
        return [r.get("cidade") for r in (resp.data or []) if r.get("cidade")]
    except Exception:
        return []


def vincular_usuario_cidades(usuario_id: str, cidades: list[str]):
    if not usuario_id or not cidades:
        return
    for cidade in cidades:
        cidade_limpa = normalizar_texto(cidade)
        if not cidade_limpa:
            continue
        estado = estado_por_cidade(cidade_limpa)
        try:
            supabase.table(TABELA_USUARIO_CIDADES).insert({
                "usuario_id": usuario_id,
                "estado": estado,
                "cidade": cidade_limpa,
                "ativo": True,
            }).execute()
        except Exception:
            pass


def remover_cidades_usuario(usuario_id: str):
    if not usuario_id:
        return None
    try:
        return supabase.table(TABELA_USUARIO_CIDADES).delete().eq("usuario_id", usuario_id).execute()
    except Exception:
        return None


def substituir_usuario_cidades(usuario_id: str, cidades: list[str]):
    remover_cidades_usuario(usuario_id)
    vincular_usuario_cidades(usuario_id, cidades)


def estado_por_cidade(cidade: str) -> str:
    cidade_norm = normalizar_texto(cidade).lower()
    for uf, cidades in CIDADES_POR_UF.items():
        if cidade_norm in [normalizar_texto(c).lower() for c in cidades]:
            return uf

    try:
        resp = (
            supabase.table(TABELA_BAIRROS)
            .select("estado,cidade")
            .ilike("cidade", normalizar_texto(cidade))
            .limit(1)
            .execute()
        )
        if resp.data:
            estado = str(resp.data[0].get("estado", "")).upper()
            if estado:
                return estado
    except Exception:
        pass

    return "RR" if cidade_norm == "boa vista" else "AM"


def cidades_permitidas_usuario(usuario: dict, unidade_nome: str) -> list[str]:
    uf = estado_da_unidade(unidade_nome)
    todas = listar_cidades_cadastradas(uf) or CIDADES_POR_UF.get(uf, ["Outro"])

    if not usuario or usuario_eh_geral(usuario):
        return todas

    cidades_usuario = listar_cidades_usuario(str(usuario.get("id", "")))

    if not cidades_usuario:
        return todas

    cidades_filtradas = [c for c in cidades_usuario if estado_por_cidade(c) == uf or c == "Outro"]
    return cidades_filtradas or todas


def listar_bairros_por_cidade(estado: str, cidade: str) -> list[str]:
    """
    Busca bairros no Supabase. Se o Supabase não retornar, usa lista fixa local
    para as cidades já cadastradas, evitando cair no campo manual.
    """
    estado = (estado or "").strip().upper()
    cidade = normalizar_texto(cidade).strip()
    cidade_key = cidade.lower()

    if not cidade:
        return []

    try:
        resp = (
            supabase.table(TABELA_BAIRROS)
            .select("nome")
            .eq("estado", estado)
            .eq("cidade", cidade)
            .eq("ativo", True)
            .order("nome")
            .execute()
        )
        bairros = sorted({r.get("nome") for r in (resp.data or []) if r.get("nome")})
        if bairros:
            return bairros
    except Exception:
        pass

    try:
        resp = (
            supabase.table(TABELA_BAIRROS)
            .select("nome")
            .eq("cidade", cidade)
            .eq("ativo", True)
            .order("nome")
            .execute()
        )
        bairros = sorted({r.get("nome") for r in (resp.data or []) if r.get("nome")})
        if bairros:
            return bairros
    except Exception:
        pass

    if cidade_key in BAIRROS_FIXOS_POR_CIDADE:
        return BAIRROS_FIXOS_POR_CIDADE[cidade_key]

    if cidade_key == "boa vista":
        return BAIRROS_BOA_VISTA

    return []


def criar_bairro_cidade(estado: str, cidade: str, bairro: str):
    dados = {
        "estado": (estado or "").strip().upper(),
        "cidade": normalizar_texto(cidade),
        "nome": normalizar_texto(bairro),
        "ativo": True,
    }
    return supabase.table(TABELA_BAIRROS).insert(dados).execute()



def listar_cidades_cadastradas(estado: str | None = None) -> list[str]:
    """
    Lista cidades cadastradas. Usa a tabela de bairros como base:
    cada cidade cadastrada recebe um bairro marcador chamado 'Outro'.
    """
    cidades = set()

    try:
        q = supabase.table(TABELA_BAIRROS).select("estado,cidade").eq("ativo", True)
        if estado:
            q = q.eq("estado", estado)
        resp = q.execute()
        for r in (resp.data or []):
            c = r.get("cidade")
            if c:
                cidades.add(normalizar_texto(c))
    except Exception:
        pass

    if estado:
        for c in CIDADES_POR_UF.get(estado, []):
            cidades.add(c)
    else:
        for lista in CIDADES_POR_UF.values():
            for c in lista:
                cidades.add(c)

    return sorted(cidades)


def criar_cidade(estado: str, cidade: str):
    """
    Cadastra uma cidade usando bairro marcador 'Outro'.
    Assim ela aparece nos selects mesmo antes de cadastrar bairros específicos.
    """
    estado = (estado or "").strip().upper()
    cidade = normalizar_texto(cidade)
    if not cidade:
        raise ValueError("Informe a cidade.")
    return supabase.table(TABELA_BAIRROS).insert({
        "estado": estado,
        "cidade": cidade,
        "nome": "Outro",
        "ativo": True,
    }).execute()


def selecionar_unidade_usuario(usuario: dict, key: str = "unidade_lead") -> str:
    unidades = list(dict.fromkeys([
        u for u in unidades_permitidas_usuario(usuario) if u
    ]))

    if not unidades:
        st.error("Seu usuário não possui uma unidade/escritório liberado.")
        st.stop()

    if len(unidades) == 1:
        unidade = unidades[0]
        uf = estado_da_unidade(unidade)
        st.text_input(
            "Unidade *",
            value=unidade,
            disabled=True,
            key=f"{key}_unidade_disabled",
        )
        st.text_input(
            "Estado *",
            value=nome_estado_por_uf(uf),
            disabled=True,
            key=f"{key}_estado_disabled",
        )
        return unidade

    unidade = st.selectbox(
        "Unidade *",
        unidades,
        key=key,
        help="Selecione o escritório responsável por este cliente.",
    )
    uf = estado_da_unidade(unidade)
    st.text_input(
        "Estado *",
        value=nome_estado_por_uf(uf),
        disabled=True,
        key=f"{key}_estado_info",
    )
    return unidade


def estado_da_unidade(unidade_nome: str) -> str:
    unidade_norm = normalizar_texto(unidade_nome).strip().casefold()

    # Regras prioritárias para unidades cujo nome já identifica a UF.
    # Isso evita que um cadastro antigo/incorreto em captacao_unidades
    # faça Boa Vista - Roraima carregar cidades do Amazonas.
    if "boa vista" in unidade_norm or "roraima" in unidade_norm:
        return "RR"
    if "porto velho" in unidade_norm:
        return "RO"
    if unidade_norm in {"cuiabá", "cuiaba", "rondonópolis", "rondonopolis"}:
        return "MT"

    try:
        for unidade in listar_unidades(True):
            nome = normalizar_texto(unidade.get("nome", "")).strip().casefold()
            if nome == unidade_norm:
                estado = normalizar_uf(unidade.get("estado", ""))
                if estado:
                    return estado
    except Exception:
        pass

    return "AM"


def cidades_da_unidade(unidade_nome: str) -> list[str]:
    uf = estado_da_unidade(unidade_nome)
    return CIDADES_POR_UF.get(uf, ["Outro"])


def selecionar_cidade_por_unidade(unidade_nome: str, key: str = "cidade_lead") -> str:
    uf = estado_da_unidade(unidade_nome)
    usuario_atual = st.session_state.get("usuario")
    cidades = cidades_permitidas_usuario(usuario_atual, unidade_nome)

    if len(cidades) <= 1:
        cidade = cidades[0] if cidades else "Outro"
        if cidade == "Outro":
            return normalizar_texto(st.text_input(f"Cidade * - {nome_estado_por_uf(uf)}", key=key))
        st.text_input(f"Cidade * - {nome_estado_por_uf(uf)}", value=cidade, disabled=True, key=f"{key}_cidade_disabled")
        return cidade

    cidade = st.selectbox(f"Cidade * - {nome_estado_por_uf(uf)}", cidades, key=key)
    if cidade == "Outro":
        return normalizar_texto(st.text_input("Digite a cidade *", key=f"{key}_outro"))
    return cidade



def selecionar_bairro_inline(cidade: str, key: str = "bairro_inline") -> str:
    cidade = normalizar_texto(cidade).strip()

    if cidade.lower() == "manacapuru":
        st.caption(f"{len(BAIRROS_MANACAPURU_FIXO)} bairro(s) cadastrados para Manacapuru.")
        return st.selectbox(
            "Bairro *",
            BAIRROS_MANACAPURU_FIXO,
            key=f"{key}_manacapuru"
        )

    try:
        estado = estado_por_cidade(cidade)
        resp = (
            supabase.table(TABELA_BAIRROS)
            .select("nome")
            .eq("estado", estado)
            .eq("cidade", cidade)
            .eq("ativo", True)
            .order("nome")
            .execute()
        )
        bairros = sorted({r.get("nome") for r in (resp.data or []) if r.get("nome")})
    except Exception:
        bairros = []

    if not bairros:
        try:
            resp = (
                supabase.table(TABELA_BAIRROS)
                .select("nome")
                .eq("cidade", cidade)
                .eq("ativo", True)
                .order("nome")
                .execute()
            )
            bairros = sorted({r.get("nome") for r in (resp.data or []) if r.get("nome")})
        except Exception:
            bairros = []

    if not bairros and "BAIRROS_FIXOS_POR_CIDADE" in globals():
        bairros = BAIRROS_FIXOS_POR_CIDADE.get(cidade.lower(), [])

    if not bairros and cidade.lower() == "boa vista":
        bairros = BAIRROS_BOA_VISTA

    if bairros:
        st.caption(f"{len(bairros)} bairro(s) cadastrados para {cidade}.")
        return st.selectbox("Bairro *", bairros, key=f"{key}_select")

    return st.text_input(
        "Bairro *",
        placeholder="Digite o bairro do cliente",
        key=f"{key}_manual",
        autocomplete="off",
    )


def selecionar_bairro_por_cidade(cidade: str, key: str = "bairro_lead") -> str:
    cidade = normalizar_texto(cidade)
    estado = estado_por_cidade(cidade)
    bairros = listar_bairros_por_cidade(estado, cidade)

    if bairros:
        st.caption(f"{len(bairros)} bairro(s) cadastrados para {cidade}.")
        return st.selectbox("Bairro *", bairros, key=f"{key}_select")

    bairro_digitado = st.text_input(
        "Bairro *",
        placeholder="Digite o bairro do cliente",
        key=f"{key}_manual",
        help="Esta cidade ainda não possui bairros cadastrados. Digite manualmente ou cadastre em Cadastros > Bairros por cidade.",
    )
    return normalizar_texto(bairro_digitado)


def vincular_usuario_unidades(usuario_id: str, unidades: list[str]):
    if not usuario_id or not unidades:
        return
    for unidade in unidades:
        try:
            supabase.table(TABELA_USUARIO_UNIDADES).insert({
                "usuario_id": usuario_id,
                "unidade_nome": unidade,
            }).execute()
        except Exception:
            pass

def criar_beneficio(nome: str):
    return supabase.table(TABELA_BENEFICIOS).insert({"nome": normalizar_texto(nome), "ativo": True}).execute()


def criar_local_captacao(nome: str):
    return supabase.table(TABELA_LOCAIS).insert({"nome": normalizar_texto(nome), "ativo": True}).execute()


def criar_tipo_arquivo(nome: str):
    return supabase.table(TABELA_TIPOS_ARQUIVO).insert({"nome": normalizar_texto(nome), "ativo": True}).execute()


def criar_unidade(nome: str, cidade: str, estado: str):
    """
    Cadastra uma nova unidade/escritório no Supabase.
    Mantém o nome informado, normaliza cidade e padroniza a UF.
    """
    nome_limpo = normalizar_texto(nome).strip()
    cidade_limpa = normalizar_texto(cidade).strip()
    estado_limpo = normalizar_uf(estado)

    if not nome_limpo:
        raise ValueError("Informe o nome da unidade.")
    if not cidade_limpa:
        raise ValueError("Informe a cidade da unidade.")
    if not estado_limpo:
        raise ValueError("Informe o estado da unidade.")

    # Evita duplicidade de unidade por nome, ignorando maiúsculas/minúsculas.
    existente = (
        supabase.table(TABELA_UNIDADES)
        .select("nome")
        .ilike("nome", nome_limpo)
        .limit(1)
        .execute()
    )
    if existente.data:
        raise ValueError(f"A unidade '{nome_limpo}' já está cadastrada.")

    dados = {
        "nome": nome_limpo,
        "cidade": cidade_limpa,
        "estado": estado_limpo,
        "ativo": True,
    }
    return supabase.table(TABELA_UNIDADES).insert(dados).execute()

def listar_tipos_pendencia():
    try:
        resp = (
            supabase.table(TABELA_TIPOS_PENDENCIA)
            .select("nome,ativo")
            .eq("ativo", True)
            .order("nome")
            .execute()
        )
        itens = [r["nome"] for r in (resp.data or []) if r.get("nome")]
        return itens or TIPOS_PENDENCIA_PADRAO
    except Exception:
        return TIPOS_PENDENCIA_PADRAO


def criar_tipo_pendencia(nome: str):
    return supabase.table(TABELA_TIPOS_PENDENCIA).insert({"nome": normalizar_texto(nome), "ativo": True}).execute()


def salvar_pendencia(dados: dict):
    return supabase.table(TABELA_PENDENCIAS).insert(dados).execute()


def atualizar_pendencia(pendencia_id: str, dados: dict):
    return supabase.table(TABELA_PENDENCIAS).update(dados).eq("id", pendencia_id).execute()


def carregar_pendencias() -> pd.DataFrame:
    try:
        resp = (
            supabase.table(TABELA_PENDENCIAS)
            .select("*")
            .order("criado_em", desc=True)
            .execute()
        )
        df = pd.DataFrame(resp.data or [])
        for col in ["criado_em", "prazo", "resolvido_em"]:
            if not df.empty and col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar pendências: {e}")
        return pd.DataFrame()


def filtrar_pendencias_por_escopo(df: pd.DataFrame, usuario: dict) -> pd.DataFrame:
    if df.empty:
        return df
    df2 = df.copy()
    for col in ["unidade", "visibilidade", "captador_destino_id"]:
        if col not in df2.columns:
            df2[col] = ""
    df2["unidade"] = df2["unidade"].fillna("Boa Vista").replace("", "Boa Vista")

    if usuario.get("perfil") == "captador":
        uid = str(usuario.get("id", ""))
        unidades = unidades_permitidas_usuario(usuario)
        mask_unidade = df2["unidade"].isin(unidades)
        mask_vis = df2["visibilidade"].fillna("Todos").isin(["Todos", "todos", "todos_unidade"])
        mask_dest = df2["captador_destino_id"].fillna("").astype(str).eq(uid)
        return df2[mask_unidade & (mask_vis | mask_dest)]

    if usuario_eh_geral(usuario):
        return df2
    unidades = unidades_permitidas_usuario(usuario)
    return df2[df2["unidade"].isin(unidades)]


def resumo_documentos_pendencias(df_pend: pd.DataFrame) -> pd.DataFrame:
    if df_pend.empty or "lead_id" not in df_pend.columns:
        return df_pend
    df2 = df_pend.copy()
    df2["documentos_enviados"] = 0
    df2["documentos_baixados"] = 0
    df2["situacao_documentos"] = "Sem documentos"
    lead_ids = [str(x) for x in df2["lead_id"].dropna().astype(str).tolist() if str(x)]
    arquivos = carregar_arquivos_por_leads(lead_ids)
    if arquivos.empty:
        return df2
    arquivos["lead_id"] = arquivos["lead_id"].astype(str)
    arquivos["baixado"] = arquivos["status_arquivo"].fillna("Pendente").eq("Baixado")
    resumo = arquivos.groupby("lead_id").agg(
        documentos_enviados_calc=("status_arquivo", "count"),
        documentos_baixados_calc=("baixado", "sum"),
    ).reset_index()
    resumo["documentos_baixados_calc"] = resumo["documentos_baixados_calc"].astype(int)
    df2["lead_id_str"] = df2["lead_id"].fillna("").astype(str)
    df2 = df2.merge(resumo, left_on="lead_id_str", right_on="lead_id", how="left", suffixes=("", "_r"))
    df2["documentos_enviados"] = df2["documentos_enviados_calc"].fillna(0).astype(int) if "documentos_enviados_calc" in df2.columns else 0
    df2["documentos_baixados"] = df2["documentos_baixados_calc"].fillna(0).astype(int) if "documentos_baixados_calc" in df2.columns else 0
    df2["situacao_documentos"] = df2.apply(
        lambda r: "Sem documentos" if r["documentos_enviados"] == 0 else (
            "Documentos baixados" if r["documentos_enviados"] == r["documentos_baixados"] else (
                "Parcialmente baixados" if r["documentos_baixados"] > 0 else "Não baixados"
            )
        ),
        axis=1,
    )
    return df2.drop(columns=[c for c in ["lead_id_str", "lead_id_r", "documentos_enviados_calc", "documentos_baixados_calc"] if c in df2.columns])


def aplicar_filtro_documentos_df(df: pd.DataFrame, filtro: str) -> pd.DataFrame:
    if df.empty or filtro == "Todos":
        return df
    if filtro == "Não baixados":
        return df[(df["documentos_enviados"] > 0) & (df["documentos_baixados"] == 0)]
    if filtro == "Parcialmente baixados":
        return df[(df["documentos_baixados"] > 0) & (df["documentos_baixados"] < df["documentos_enviados"])]
    if filtro == "Documentos baixados":
        return df[(df["documentos_enviados"] > 0) & (df["documentos_baixados"] == df["documentos_enviados"])]
    if filtro == "Sem documentos":
        return df[df["documentos_enviados"] == 0]
    return df


def label_lead(row) -> str:
    cpf = formatar_cpf(row.get("cpf", "") or "")
    return f"{row.get('nome_cliente','')} | {cpf} | {row.get('telefone','')} | {row.get('bairro','')}"


def salvar_historico(lead_id: str, usuario_nome: str, status: str, observacao: str, acao: str = "Atualização"):
    if not lead_id:
        return None
    dados = {
        "lead_id": lead_id,
        "usuario_nome": usuario_nome,
        "status": status,
        "observacao": observacao.strip() if observacao else "",
        "acao": acao,
    }
    return supabase.table(TABELA_HISTORICO).insert(dados).execute()


def carregar_historico(lead_id: str) -> pd.DataFrame:
    try:
        resp = (
            supabase.table(TABELA_HISTORICO)
            .select("*")
            .eq("lead_id", lead_id)
            .order("criado_em", desc=True)
            .execute()
        )
        dfh = pd.DataFrame(resp.data or [])
        if not dfh.empty and "criado_em" in dfh.columns:
            dfh["criado_em"] = pd.to_datetime(dfh["criado_em"], errors="coerce")
        return dfh
    except Exception:
        return pd.DataFrame()



def transferir_leads_em_lote(
    lead_ids: list[str],
    novo_captador: dict,
    usuario_responsavel: dict,
    motivo: str = "",
):
    """
    Transfere clientes em lote para outro atendente e registra histórico individual.
    """
    if not lead_ids:
        raise ValueError("Nenhum cliente selecionado.")
    if not novo_captador or not novo_captador.get("id"):
        raise ValueError("Novo atendente inválido.")

    dados_update = {
        "captador_id": str(novo_captador.get("id")),
        "captador_nome": novo_captador.get("nome"),
    }

    supabase.table(TABELA_LEADS).update(dados_update).in_("id", lead_ids).execute()

    texto_motivo = motivo.strip()
    for lead_id in lead_ids:
        observacao = (
            f"Lead transferido para {novo_captador.get('nome')} "
            f"por {usuario_responsavel.get('nome')}."
        )
        if texto_motivo:
            observacao += f" Motivo: {texto_motivo}"
        try:
            salvar_historico(
                str(lead_id),
                usuario_responsavel.get("nome", ""),
                "Transferido",
                observacao,
                "Transferência de cliente",
            )
        except Exception:
            pass

    return True



def listar_advogados_ativos() -> list[dict]:
    usuarios = listar_usuarios_ativos()
    perfis_validos = {"advogado", "gestor", "gestor_geral", "gestor_regional", "gestor_unidade"}
    return [u for u in usuarios if str(u.get("perfil", "")).lower() in perfis_validos]


def salvar_agendamento(dados: dict):
    return supabase.table(TABELA_AGENDAMENTOS).insert(dados).execute()


def atualizar_agendamento(agendamento_id: str, dados: dict):
    return supabase.table(TABELA_AGENDAMENTOS).update(dados).eq("id", agendamento_id).execute()


def carregar_agendamentos() -> pd.DataFrame:
    try:
        resp = (
            supabase.table(TABELA_AGENDAMENTOS)
            .select("*")
            .order("data_agendamento")
            .order("hora_inicio")
            .execute()
        )
        df = pd.DataFrame(resp.data or [])
        if not df.empty and "data_agendamento" in df.columns:
            df["data_agendamento"] = pd.to_datetime(df["data_agendamento"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar agenda: {e}")
        return pd.DataFrame()


def verificar_conflito_agenda(advogado_id: str, data_agendamento, hora_inicio, hora_fim) -> bool:
    try:
        resp = (
            supabase.table(TABELA_AGENDAMENTOS)
            .select("hora_inicio,hora_fim,status_agendamento")
            .eq("advogado_id", advogado_id)
            .eq("data_agendamento", data_agendamento.isoformat())
            .execute()
        )
        novo_hi = hora_inicio.strftime("%H:%M")
        novo_hf = hora_fim.strftime("%H:%M")
        for item in (resp.data or []):
            if item.get("status_agendamento") == "Cancelado":
                continue
            hi = str(item.get("hora_inicio") or "")[:5]
            hf = str(item.get("hora_fim") or hi)[:5]
            if novo_hi < hf and novo_hf > hi:
                return True
        return False
    except Exception:
        return False


def montar_calendario_mensal(df_agenda: pd.DataFrame, ano: int, mes: int) -> str:
    import calendar
    nomes_dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    semanas = calendar.Calendar(firstweekday=0).monthdayscalendar(ano, mes)
    eventos = {}
    if not df_agenda.empty:
        for _, row in df_agenda.iterrows():
            data_val = row.get("data_agendamento")
            if pd.isna(data_val):
                continue
            eventos.setdefault(int(pd.to_datetime(data_val).day), []).append(row)

    html = """
    <style>
    .agenda-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:6px}
    .agenda-head{font-weight:900;text-align:center;padding:8px;background:#EAF4FC;border-radius:8px}
    .agenda-day{min-height:120px;border:1px solid #DCE8F4;border-radius:10px;padding:8px;background:#FFF}
    .agenda-day-muted{background:#F7F9FC}
    .agenda-num{font-weight:900;margin-bottom:6px}
    .agenda-event{font-size:12px;background:#EAF7FF;border-left:4px solid #18BDF2;border-radius:7px;padding:5px 6px;margin:4px 0}
    </style><div class="agenda-grid">
    """
    for nome in nomes_dias:
        html += f'<div class="agenda-head">{nome}</div>'
    for semana in semanas:
        for dia in semana:
            if dia == 0:
                html += '<div class="agenda-day agenda-day-muted"></div>'
                continue
            html += f'<div class="agenda-day"><div class="agenda-num">{dia}</div>'
            for row in eventos.get(dia, [])[:4]:
                hora = str(row.get("hora_inicio") or "")[:5]
                cliente = str(row.get("cliente_nome") or "Cliente")
                advogado = str(row.get("advogado_nome") or "")
                html += f'<div class="agenda-event"><b>{hora}</b> — {cliente}<br>{advogado}</div>'
            extra = len(eventos.get(dia, [])) - 4
            if extra > 0:
                html += f'<div class="agenda-event">+ {extra} atendimento(s)</div>'
            html += "</div>"
    return html + "</div>"


def carregar_leads():
    try:
        resp = (
            supabase.table(TABELA_LEADS)
            .select("*")
            .order("data_captacao", desc=True)
            .execute()
        )
        df = pd.DataFrame(resp.data or [])
        if not df.empty:
            df["data_captacao"] = pd.to_datetime(df["data_captacao"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar leads: {e}")
        return pd.DataFrame()


def salvar_lead(dados: dict):
    return supabase.table(TABELA_LEADS).insert(dados).execute()


def garantir_observacao_lead(lead_id: str, observacao: str) -> bool:
    """
    Confere se a observação foi gravada no cliente.
    Caso o retorno do INSERT venha sem o campo ou o banco devolva vazio,
    executa um UPDATE de segurança e confere novamente.
    """
    if not lead_id:
        return False

    observacao_limpa = (observacao or "").strip()

    try:
        resp = (
            supabase.table(TABELA_LEADS)
            .select("id,observacao")
            .eq("id", str(lead_id))
            .limit(1)
            .execute()
        )
        atual = ""
        if resp.data:
            atual = str(resp.data[0].get("observacao") or "").strip()

        if atual == observacao_limpa:
            return True

        supabase.table(TABELA_LEADS).update({
            "observacao": observacao_limpa
        }).eq("id", str(lead_id)).execute()

        resp_conf = (
            supabase.table(TABELA_LEADS)
            .select("observacao")
            .eq("id", str(lead_id))
            .limit(1)
            .execute()
        )
        confirmado = ""
        if resp_conf.data:
            confirmado = str(resp_conf.data[0].get("observacao") or "").strip()

        return confirmado == observacao_limpa
    except Exception:
        return False


def atualizar_lead(lead_id: str, dados: dict):
    return supabase.table(TABELA_LEADS).update(dados).eq("id", lead_id).execute()

def caminho_arquivo_storage(lead_id: str, nome_arquivo: str) -> str:
    nome_limpo = "".join(ch if ch.isalnum() or ch in ".-_" else "_" for ch in nome_arquivo)
    return f"{lead_id}/{uuid.uuid4().hex}_{nome_limpo}"



def lista_arquivos_com_foto(arquivos_upload, foto_camera=None, nome_base: str = "foto_documento.jpg"):
    """
    Junta arquivos do upload múltiplo com uma foto/arquivo único.
    O campo de foto sempre é salvo como .jpg, independentemente da extensão original.
    """
    arquivos = list(arquivos_upload or [])
    if foto_camera:
        nome_jpg = nome_base
        if not nome_jpg.lower().endswith(".jpg"):
            nome_jpg = nome_jpg.rsplit(".", 1)[0] + ".jpg"
        try:
            foto_camera.name = nome_jpg
        except Exception:
            pass
        arquivos.append(foto_camera)
    return arquivos

def salvar_metadado_arquivo(lead_id: str, arquivo, tipo_documento: str, usuario: dict, caminho: str):
    dados = {
        "lead_id": lead_id,
        "nome_arquivo": arquivo.name,
        "tipo_documento": tipo_documento or "Documento",
        "caminho_storage": caminho,
        "content_type": getattr(arquivo, "type", None) or "application/octet-stream",
        "tamanho_bytes": getattr(arquivo, "size", None),
        "status_arquivo": "Pendente",
        "enviado_por": usuario.get("nome"),
        "removido_storage": False,
    }
    return supabase.table(TABELA_ARQUIVOS).insert(dados).execute()


def enviar_arquivo_temporario(lead_id: str, arquivo, tipo_documento: str, usuario: dict):
    caminho = caminho_arquivo_storage(lead_id, arquivo.name)
    conteudo = arquivo.getvalue()
    content_type = getattr(arquivo, "type", None) or "application/octet-stream"
    supabase.storage.from_(BUCKET_ARQUIVOS).upload(
        caminho,
        conteudo,
        file_options={"content-type": content_type, "upsert": "false"},
    )
    salvar_metadado_arquivo(lead_id, arquivo, tipo_documento, usuario, caminho)
    return caminho


def carregar_arquivos_lead(lead_id: str) -> pd.DataFrame:
    try:
        resp = (
            supabase.table(TABELA_ARQUIVOS)
            .select("*")
            .eq("lead_id", lead_id)
            .order("criado_em", desc=True)
            .execute()
        )
        df = pd.DataFrame(resp.data or [])
        for col in ["criado_em", "data_download"]:
            if not df.empty and col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


def baixar_arquivo_storage(caminho: str) -> bytes:
    return supabase.storage.from_(BUCKET_ARQUIVOS).download(caminho)


def marcar_arquivos_baixados(arquivo_ids: list[str], usuario_nome: str):
    if not arquivo_ids:
        return None
    dados = {
        "status_arquivo": "Baixado",
        "baixado_por": usuario_nome,
        "data_download": datetime.now(timezone.utc).isoformat(),
        "removido_storage": False,
    }
    return supabase.table(TABELA_ARQUIVOS).update(dados).in_("id", arquivo_ids).execute()


def carregar_arquivos_por_leads(lead_ids: list[str]) -> pd.DataFrame:
    if not lead_ids:
        return pd.DataFrame()
    try:
        resp = (
            supabase.table(TABELA_ARQUIVOS)
            .select("lead_id,status_arquivo,data_download,baixado_por")
            .in_("lead_id", [str(x) for x in lead_ids])
            .execute()
        )
        return pd.DataFrame(resp.data or [])
    except Exception:
        return pd.DataFrame()


def resumo_arquivos_para_leads(df_leads: pd.DataFrame) -> pd.DataFrame:
    if df_leads.empty or "id" not in df_leads.columns:
        return df_leads
    df2 = df_leads.copy()
    arquivos = carregar_arquivos_por_leads(df2["id"].astype(str).tolist())
    df2["documentos_enviados"] = 0
    df2["documentos_baixados"] = 0
    df2["status_documentos"] = "Sem documentos"
    if arquivos.empty:
        return df2
    arquivos["lead_id"] = arquivos["lead_id"].astype(str)
    arquivos["baixado"] = arquivos["status_arquivo"].fillna("Pendente").eq("Baixado")
    resumo = arquivos.groupby("lead_id").agg(
        documentos_enviados=("status_arquivo", "count"),
        documentos_baixados=("baixado", "sum"),
    ).reset_index()
    resumo["documentos_baixados"] = resumo["documentos_baixados"].astype(int)
    df2["id_str"] = df2["id"].astype(str)
    df2 = df2.merge(resumo, left_on="id_str", right_on="lead_id", how="left", suffixes=("", "_calc"))
    for col in ["documentos_enviados", "documentos_baixados"]:
        calc = f"{col}_calc"
        if calc in df2.columns:
            df2[col] = df2[calc].fillna(df2[col]).fillna(0).astype(int)
            df2 = df2.drop(columns=[calc])
    df2["status_documentos"] = df2.apply(
        lambda r: "Sem documentos" if r["documentos_enviados"] == 0 else (
            "Documentos baixados" if r["documentos_enviados"] == r["documentos_baixados"] else "Aguardando download"
        ),
        axis=1,
    )
    drop_cols = [c for c in ["id_str", "lead_id"] if c in df2.columns]
    return df2.drop(columns=drop_cols)


def criar_zip_arquivos(arquivos_df: pd.DataFrame, nome_cliente: str = "cliente") -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        usados = set()
        for _, arq in arquivos_df.iterrows():
            caminho = arq.get("caminho_storage", "")
            if not caminho:
                continue
            dados = baixar_arquivo_storage(caminho)
            nome = arq.get("nome_arquivo") or "arquivo"
            tipo = arq.get("tipo_documento") or "Documento"
            nome_zip = f"{tipo}_{nome}".replace("/", "_").replace("\\", "_")
            base_nome = nome_zip
            i = 2
            while nome_zip in usados:
                nome_zip = f"{i}_{base_nome}"
                i += 1
            usados.add(nome_zip)
            zipf.writestr(nome_zip, dados)
    buffer.seek(0)
    return buffer.getvalue()


def exibir_arquivos_do_lead(lead_id: str, usuario: dict, nome_cliente: str = "cliente"):
    st.markdown("### 📎 Arquivos do Cliente")
    arquivos_df = carregar_arquivos_lead(lead_id)
    if arquivos_df.empty:
        st.info("Nenhum arquivo enviado para este cliente.")
        return

    arquivos_df["status_arquivo"] = arquivos_df["status_arquivo"].fillna("Pendente")
    total = len(arquivos_df)
    baixados_qtd = int((arquivos_df["status_arquivo"] == "Baixado").sum())
    disponiveis = arquivos_df[arquivos_df["caminho_storage"].fillna("") != ""].copy()

    c1, c2, c3 = st.columns(3)
    c1.metric("📎 Enviados", total)
    c2.metric("📥 Baixados", baixados_qtd)
    c3.metric("⏳ A baixar", max(total - baixados_qtd, 0))

    st.dataframe(
        arquivos_df[[c for c in ["nome_arquivo", "tipo_documento", "status_arquivo", "enviado_por", "baixado_por", "data_download"] if c in arquivos_df.columns]].rename(columns={
            "nome_arquivo": "Arquivo",
            "tipo_documento": "Tipo",
            "status_arquivo": "Status",
            "enviado_por": "Enviado por",
            "baixado_por": "Baixado por",
            "data_download": "Data download",
        }),
        use_container_width=True,
        hide_index=True,
    )

    if disponiveis.empty:
        st.info("Não há arquivos disponíveis para download.")
        return

    try:
        nome_zip = normalizar_texto(nome_cliente or "cliente").replace(" ", "_") or "cliente"
        zip_bytes = criar_zip_arquivos(disponiveis, nome_zip)
        clicou = st.download_button(
            f"⬇️ Baixar documentação completa ({len(disponiveis)} arquivo(s))",
            data=zip_bytes,
            file_name=f"{nome_zip}_documentos.zip",
            mime="application/zip",
            key=f"download_zip_{lead_id}",
        )
        if clicou:
            ids = [str(x) for x in disponiveis["id"].tolist()]
            marcar_arquivos_baixados(ids, usuario.get("nome", ""))
            salvar_historico(
                lead_id,
                usuario.get("nome", ""),
                "Arquivos baixados",
                f"Documentação completa baixada em ZIP ({len(disponiveis)} arquivo(s)).",
                "Download de arquivos",
            )
            st.success("Download registrado. Os arquivos permanecem armazenados para segurança.")
            st.rerun()
    except Exception as e:
        st.error(f"Erro ao preparar ZIP dos documentos: {e}")



def rotulo_perfil_usuario(perfil: str) -> str:
    mapa = {
        "captador": "atendente",
        "atendente": "atendente",
        "pendencia": "pendência",
        "supervisor": "supervisor",
        "gestor_unidade": "gestor_unidade",
        "gestor_regional": "gestor_regional",
        "gestor_geral": "gestor_geral",
        "gestor": "gestor",
        "advogado": "advogado",
    }
    return mapa.get(str(perfil or "").lower(), str(perfil or ""))


def pode_ver_todos(usuario: dict) -> bool:
    return usuario.get("perfil") in ["gestor", "supervisor", "gestor_geral", "gestor_regional", "gestor_unidade"]


def pode_acessar_pendencias(usuario: dict) -> bool:
    return usuario.get("perfil") in ["gestor", "supervisor", "gestor_geral", "gestor_regional", "gestor_unidade", "pendencia"]


def pode_gerenciar_usuarios(usuario: dict) -> bool:
    return usuario.get("perfil") in ["gestor_geral", "gestor_regional", "gestor_unidade"]


def perfis_que_usuario_pode_criar(usuario: dict) -> list[str]:
    perfil = usuario.get("perfil")

    if perfil == "gestor_geral":
        return [
            "captador",
            "pendencia",
            "supervisor",
            "gestor_unidade",
            "gestor_regional",
            "gestor_geral",
        ]

    if perfil == "gestor_regional":
        return [
            "captador",
            "pendencia",
            "supervisor",
            "gestor_unidade",
        ]

    if perfil == "gestor_unidade":
        return [
            "captador",
            "pendencia",
            "supervisor",
        ]

    return []


def usuario_dentro_do_escopo_admin(admin: dict, alvo: dict) -> bool:
    if not admin or not alvo:
        return False

    perfil_admin = admin.get("perfil")
    perfil_alvo = alvo.get("perfil")

    if perfil_admin == "gestor_geral":
        return True

    if perfil_admin == "gestor_regional":
        if perfil_alvo in ["gestor_geral", "gestor_regional"]:
            return False

        unidades_admin = set(unidades_permitidas_usuario(admin))
        unidades_alvo = set(listar_unidades_usuario(str(alvo.get("id", ""))))

        unidade_padrao = (
            alvo.get("unidade_padrao")
            or alvo.get("unidade")
            or alvo.get("unidade_nome")
        )
        if unidade_padrao:
            unidades_alvo.add(resolver_nome_unidade_cadastrada(unidade_padrao))

        return bool(unidades_admin.intersection(unidades_alvo))

    if perfil_admin == "gestor_unidade":
        if perfil_alvo not in ["captador", "atendente", "pendencia", "supervisor"]:
            return False

        unidades_admin = set(unidades_permitidas_usuario(admin))
        unidades_alvo = set(listar_unidades_usuario(str(alvo.get("id", ""))))

        unidade_padrao = (
            alvo.get("unidade_padrao")
            or alvo.get("unidade")
            or alvo.get("unidade_nome")
        )
        if unidade_padrao:
            unidades_alvo.add(resolver_nome_unidade_cadastrada(unidade_padrao))

        return bool(unidades_admin.intersection(unidades_alvo))

    return False


def filtrar_usuarios_por_escopo_admin(usuarios: list[dict], admin: dict) -> list[dict]:
    if admin.get("perfil") == "gestor_geral":
        return usuarios
    return [u for u in usuarios if usuario_dentro_do_escopo_admin(admin, u)]

# -------------------------------
# LOGIN
# -------------------------------
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "atendente_pagina" not in st.session_state:
    st.session_state.atendente_pagina = "Novo Cliente"

if st.session_state.usuario is None:
    aplicar_css_mobile()
    header_mobile()
    abrir_card_mobile("Acesso", "Entre para registrar clientes")
    with st.form("form_login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("ENTRAR")
    fechar_card_mobile()

    if entrar:
        usuario = buscar_usuario(email, senha)
        if usuario:
            st.session_state.usuario = usuario
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos, ou usuário inativo.")

    st.caption("Utilize seu usuário e senha fornecidos pelo administrador.")
    st.stop()

usuario = st.session_state.usuario
perfil = usuario.get("perfil")

# -------------------------------
# ROTAS DO CAPTADOR - ESTILO CELULAR
# -------------------------------
if perfil in ["captador", "atendente"]:
    aplicar_css_mobile()
    header_mobile()

    opcoes_atendente = ["➕ Novo Cliente", "📋 Minhas", "📎 Documentos", "📌 Pendências"]
    mapa_atendente = {"➕ Novo Cliente": "Novo Cliente", "📋 Meus": "Minhas Clientes", "📎 Documentos": "Documentos", "📌 Pendências": "Pendências"}
    pagina_atual_label = next((k for k, v in mapa_atendente.items() if v == st.session_state.atendente_pagina), "➕ Novo Cliente")
    st.markdown("<div class='mobile-nav-box'>", unsafe_allow_html=True)
    nav_escolhida = st.radio(
        "Navegação",
        opcoes_atendente,
        index=opcoes_atendente.index(pagina_atual_label),
        horizontal=True,
        label_visibility="collapsed",
        key="atendente_nav_radio",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    nova_pagina = mapa_atendente[nav_escolhida]
    if nova_pagina != st.session_state.atendente_pagina:
        st.session_state.atendente_pagina = nova_pagina
        st.rerun()

    if st.session_state.atendente_pagina == "Novo Cliente":
        abrir_card_mobile("Novo Cliente", "Preencha os dados do cliente")
        with st.form("form_novo_lead_mobile", clear_on_submit=True):
            unidade_lead = selecionar_unidade_usuario(usuario, key="unidade_lead_mobile")
            cidade_lead = selecionar_cidade_por_unidade(unidade_lead, key="cidade_lead_mobile")
            nome_cliente = st.text_input("Nome do cliente *", placeholder="Digite o nome completo")
            cpf = st.text_input("CPF", placeholder="000.000.000-00")
            telefone = st.text_input("Telefone *", placeholder="(95) 99999-9999")
            bairro = selecionar_bairro_inline(cidade_lead, key="bairro_lead_mobile")
            locais_opcoes = listar_locais_captacao()
            if locais_opcoes:
                local_sel = st.selectbox("Local da clientes *", ["Outro / digitar"] + locais_opcoes)
                local_captacao = st.text_input("Digite o local" if local_sel == "Outro / digitar" else "Confirmar local", value="" if local_sel == "Outro / digitar" else local_sel, placeholder="Ex.: Feira, praça, INSS, ação social...")
            else:
                local_captacao = st.text_input("Local da clientes *", placeholder="Ex.: Feira, praça, INSS, ação social...")
            area_acao = st.selectbox("Área da ação *", AREAS_ACAO)
            tipo_beneficio = st.selectbox("Tipo de benefício *", listar_beneficios())
            observacao = st.text_area("Observação", placeholder="Informações úteis para o atendimento posterior")
            tipo_documento_upload = st.selectbox("Tipo dos arquivos", listar_tipos_arquivo(), key="tipo_doc_upload_mobile")
            arquivos_upload = st.file_uploader("📎 Anexar documentos/arquivos", accept_multiple_files=True, type=["pdf", "png", "jpg", "jpeg", "webp"], key="arquivos_upload_mobile")
            foto_camera_upload = st.file_uploader("📷 Tirar foto do documento", accept_multiple_files=False, type=["png", "jpg", "jpeg", "webp"], key="foto_camera_upload_mobile", help="Use este campo para abrir a câmera do celular ou escolher uma foto da galeria.")
            enviar = st.form_submit_button("💾 SALVAR CLIENTE")
            st.markdown("<div class='mobile-note'>🔒 Atendente identificado automaticamente</div>", unsafe_allow_html=True)
        fechar_card_mobile()

        if enviar:
            cpf_limpo = limpar_cpf(cpf)
            duplicado = buscar_lead_por_cpf(cpf_limpo) if cpf_limpo else None
            if not nome_cliente or not telefone or not bairro or not cidade_lead or not local_captacao:
                st.error("Preencha os campos obrigatórios marcados com *.")
            elif not cpf_valido_ou_vazio(cpf):
                st.error("CPF inválido. Use 11 números.")
            elif not telefone_valido(telefone):
                st.error("Telefone inválido. Use DDD + número, exemplo: (95) 99999-9999.")
            elif duplicado:
                st.warning(
                    f"⚠️ Cliente já cadastrado: {duplicado.get('nome_cliente','')} | "
                    f"Atendente: {duplicado.get('captador_nome','')} | "
                    f"Status: {duplicado.get('status_lead','')}"
                )
            else:
                dados = {
                    "captador_id": usuario["id"],
                    "captador_nome": usuario["nome"],
                    "unidade": unidade_lead,
                    "cidade": cidade_lead,
                    "nome_cliente": normalizar_texto(nome_cliente),
                    "cpf": cpf_limpo,
                    "telefone": formatar_telefone(telefone),
                    "bairro": bairro,
                    "local_captacao": normalizar_texto(local_captacao),
                    "area_acao": area_acao,
                    "tipo_beneficio": tipo_beneficio,
                    "observacao": observacao.strip(),
                    "status_lead": "Novo",
                }
                try:
                    resp = salvar_lead(dados)
                    novo_id = (resp.data or [{}])[0].get("id") if hasattr(resp, "data") else None
                    if novo_id:
                        observacao_ok = garantir_observacao_lead(novo_id, observacao)
                        salvar_historico(novo_id, usuario["nome"], "Novo", observacao.strip(), "Cliente cadastrado")
                        arquivos_para_enviar = lista_arquivos_com_foto(
                            arquivos_upload,
                            foto_camera_upload,
                            f"foto_{limpar_cpf(cpf) or novo_id}.jpg",
                        )
                        if arquivos_para_enviar:
                            enviados = 0
                            for arquivo in arquivos_para_enviar:
                                enviar_arquivo_temporario(novo_id, arquivo, tipo_documento_upload, usuario)
                                enviados += 1
                            salvar_historico(novo_id, usuario["nome"], "Novo", f"{enviados} arquivo(s) anexado(s) ao lead.", "Arquivos anexados")
                    if novo_id and observacao.strip() and not observacao_ok:
                        st.warning(
                            "O cliente foi salvo, mas não foi possível confirmar a observação. "
                            "Abra o cliente em Atualizar Cliente para conferir."
                        )
                    else:
                        st.success("Cliente salvo com sucesso, incluindo a observação!")
                except Exception as e:
                    st.error(f"Erro ao salvar cliente: {e}")

    elif st.session_state.atendente_pagina == "Minhas Clientes":
        abrir_card_mobile("Meus Clientes", "Filtre e acompanhe seus clientes")
        df = carregar_leads()
        if df.empty:
            st.info("Nenhum cliente encontrado.")
        else:
            df = filtrar_clientes_do_atendente(df, usuario)
            df = resumo_arquivos_para_leads(df)
            st.caption(f"{len(df)} cliente(s) localizado(s) para este usuário.")
            if df.empty:
                st.info("Você ainda não possui clientes cadastrados.")
            else:
                hoje = date.today()
                st.markdown("#### 📈 Meu resumo")
                mes_ini = hoje.replace(day=1)
                df_mes = df[df["data_captacao"].dt.date >= mes_ini].copy()
                total_mes = len(df_mes)
                conv_mes = int((df_mes["status_lead"] == "Convertido").sum()) if not df_mes.empty else 0
                atendimento_mes = int((df_mes["status_lead"] == "Em atendimento").sum()) if not df_mes.empty else 0
                docs_abertos = int((df["documentos_enviados"] > df["documentos_baixados"]).sum())
                c1, c2 = st.columns(2)
                c1.metric("Clientes no mês", total_mes)
                c2.metric("Convertidos", conv_mes)
                c3, c4 = st.columns(2)
                c3.metric("Em atendimento", atendimento_mes)
                c4.metric("Docs a baixar", docs_abertos)

                st.markdown("#### 🔎 Filtros")
                periodo = st.selectbox("Período", ["Últimos 7 dias", "Últimos 30 dias", "Mês atual", "Todos", "Personalizado"], index=1, key="minhas_periodo_mobile")
                data_ini = st.date_input("Data inicial", hoje - timedelta(days=30), key="minhas_data_ini_mobile")
                data_fim = st.date_input("Data final", hoje, key="minhas_data_fim_mobile")
                if periodo == "Últimos 7 dias":
                    data_ini, data_fim = hoje - timedelta(days=7), hoje
                elif periodo == "Últimos 30 dias":
                    data_ini, data_fim = hoje - timedelta(days=30), hoje
                elif periodo == "Mês atual":
                    data_ini, data_fim = hoje.replace(day=1), hoje
                elif periodo == "Todos":
                    data_ini = df["data_captacao"].dt.date.min()
                    data_fim = df["data_captacao"].dt.date.max()

                status_filtro = st.multiselect("Status", STATUS_LEAD, default=STATUS_LEAD, key="minhas_status_mobile")
                bairro_filtro = st.multiselect("Bairro", sorted(df["bairro"].fillna("").replace("", "Não informado").unique().tolist()), key="minhas_bairro_mobile")
                local_filtro = st.multiselect("Localidade", sorted(df["local_captacao"].fillna("").replace("", "Não informado").unique().tolist()), key="minhas_local_mobile")
                if "cidade" not in df.columns:
                    df["cidade"] = df["unidade"].fillna("Boa Vista") if "unidade" in df.columns else "Boa Vista"
                cidade_filtro = st.multiselect("Cidade", sorted(df["cidade"].fillna("Boa Vista").replace("", "Boa Vista").unique().tolist()), key="minhas_cidade_mobile")
                docs_filtro = st.selectbox("Documentos", ["Todos", "Com documentos não baixados", "Documentos baixados", "Sem documentos", "Com documentos"], key="minhas_docs_mobile")

                df_filtrado = df[(df["data_captacao"].dt.date >= data_ini) & (df["data_captacao"].dt.date <= data_fim)].copy()
                if status_filtro:
                    df_filtrado = df_filtrado[df_filtrado["status_lead"].isin(status_filtro)]
                if bairro_filtro:
                    df_filtrado = df_filtrado[df_filtrado["bairro"].fillna("").replace("", "Não informado").isin(bairro_filtro)]
                if local_filtro:
                    df_filtrado = df_filtrado[df_filtrado["local_captacao"].fillna("").replace("", "Não informado").isin(local_filtro)]
                if cidade_filtro and "cidade" in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado["cidade"].fillna("Boa Vista").replace("", "Boa Vista").isin(cidade_filtro)]
                if docs_filtro == "Com documentos não baixados":
                    df_filtrado = df_filtrado[df_filtrado["documentos_enviados"] > df_filtrado["documentos_baixados"]]
                elif docs_filtro == "Documentos baixados":
                    df_filtrado = df_filtrado[(df_filtrado["documentos_enviados"] > 0) & (df_filtrado["documentos_enviados"] == df_filtrado["documentos_baixados"])]
                elif docs_filtro == "Sem documentos":
                    df_filtrado = df_filtrado[df_filtrado["documentos_enviados"] == 0]
                elif docs_filtro == "Com documentos":
                    df_filtrado = df_filtrado[df_filtrado["documentos_enviados"] > 0]

                colunas = [
                    "data_captacao", "nome_cliente", "telefone", "cidade", "bairro", "local_captacao", "unidade",
                    "tipo_beneficio", "status_lead", "observacao",
                    "documentos_enviados", "documentos_baixados", "status_documentos"
                ]
                colunas = [c for c in colunas if c in df_filtrado.columns]
                st.dataframe(preparar_dataframe_exibicao(df_filtrado[colunas]), use_container_width=True, hide_index=True)
        fechar_card_mobile()

    elif st.session_state.atendente_pagina == "Pendências":
        abrir_card_mobile("Pendências", "Documentos solicitados pela unidade")
        dfp = carregar_pendencias()
        dfp = filtrar_pendencias_por_escopo(dfp, usuario)
        dfp = resumo_documentos_pendencias(dfp)
        if dfp.empty:
            st.info("Nenhuma pendência documental para você no momento.")
        else:
            st.markdown("#### 🔎 Filtros")
            busca_pend = st.text_input("Buscar por cliente, CPF ou descrição", key="pend_busca_atendente")
            status_pend = st.multiselect("Status", STATUS_PENDENCIA, default=["Aberta", "Em andamento"], key="pend_status_atendente")
            docs_pend = st.selectbox("Situação dos documentos", ["Todos", "Não baixados", "Parcialmente baixados", "Documentos baixados", "Sem documentos"], key="pend_docs_atendente")

            dfp_f = dfp.copy()
            if status_pend:
                dfp_f = dfp_f[dfp_f["status"].fillna("Aberta").isin(status_pend)]
            dfp_f = aplicar_filtro_documentos_df(dfp_f, docs_pend)
            if busca_pend.strip():
                termo = busca_pend.strip().lower()
                mask = pd.Series(False, index=dfp_f.index)
                for c in ["cliente_nome", "cpf", "descricao", "tipo_pendencia"]:
                    if c in dfp_f.columns:
                        mask = mask | dfp_f[c].fillna("").astype(str).str.lower().str.contains(termo, na=False)
                dfp_f = dfp_f[mask]

            if dfp_f.empty:
                st.warning("Nenhuma pendência encontrada com os filtros selecionados.")
            else:
                dfp_f["label"] = (
                    dfp_f["cliente_nome"].fillna("") + " | " +
                    dfp_f["tipo_pendencia"].fillna("") + " | " +
                    dfp_f["status"].fillna("Aberta") + " | 📎 " +
                    dfp_f["documentos_enviados"].astype(str) + " / 📥 " +
                    dfp_f["documentos_baixados"].astype(str)
                )
                pend_label = st.selectbox("Selecione a pendência", dfp_f["label"].tolist(), key="pend_select_atendente")
                pend = dfp_f[dfp_f["label"] == pend_label].iloc[0]
                st.write(f"**Cliente:** {pend.get('cliente_nome','')}")
                st.write(f"**Tipo:** {pend.get('tipo_pendencia','')}")
                st.write(f"**Descrição:** {pend.get('descricao','')}")
                st.write(f"**Prioridade:** {pend.get('prioridade','Normal')} | **Status:** {pend.get('status','Aberta')}")
                st.write(f"📎 **Enviados:** {int(pend.get('documentos_enviados',0))} | 📥 **Baixados:** {int(pend.get('documentos_baixados',0))}")

                with st.form("form_docs_pend_atendente", clear_on_submit=True):
                    novo_status_p = st.selectbox("Atualizar status da pendência", STATUS_PENDENCIA, index=STATUS_PENDENCIA.index(pend.get("status", "Aberta")) if pend.get("status", "Aberta") in STATUS_PENDENCIA else 0)
                    obs_p = st.text_area("Observação", placeholder="Ex.: Cliente entregou laudo atualizado")
                    tipo_doc_p = st.selectbox("Tipo dos arquivos", listar_tipos_arquivo(), key="tipo_doc_pend_atendente")
                    arquivos_p = st.file_uploader("📎 Anexar documentos/arquivos", accept_multiple_files=True, type=["pdf", "png", "jpg", "jpeg", "webp"], key="arquivos_pend_atendente")
                    foto_p_upload = st.file_uploader("📷 Tirar foto do documento", accept_multiple_files=False, type=["png", "jpg", "jpeg", "webp"], key="foto_pend_atendente", help="Use este campo para abrir a câmera do celular ou escolher uma foto da galeria.")
                    salvar_p = st.form_submit_button("📎 ENVIAR / ATUALIZAR")
                if salvar_p:
                    try:
                        enviados = 0
                        lead_id_p = str(pend.get("lead_id", ""))
                        arquivos_p_enviar = lista_arquivos_com_foto(
                            arquivos_p,
                            foto_p_upload,
                            f"foto_pendencia_{lead_id_p}.jpg",
                        )
                        if arquivos_p_enviar and lead_id_p:
                            for arquivo in arquivos_p_enviar:
                                enviar_arquivo_temporario(lead_id_p, arquivo, tipo_doc_p, usuario)
                                enviados += 1
                            salvar_historico(lead_id_p, usuario["nome"], novo_status_p, f"{enviados} arquivo(s) enviado(s) para pendência: {pend.get('tipo_pendencia','')}.", "Pendência documental")
                        dados_up = {"status": novo_status_p, "atualizado_em": datetime.now(timezone.utc).isoformat()}
                        if novo_status_p == "Resolvida":
                            dados_up["resolvido_em"] = datetime.now(timezone.utc).isoformat()
                            dados_up["resolvido_por"] = usuario.get("nome")
                        atualizar_pendencia(str(pend["id"]), dados_up)
                        st.success("Pendência atualizada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar pendência: {e}")

        fechar_card_mobile()

    else:
        abrir_card_mobile("Documentos", "Adicione documentos em clientes já cadastrados")
        df = carregar_leads()
        if df.empty:
            st.info("Nenhum cliente encontrado.")
        else:
            df = filtrar_clientes_do_atendente(df, usuario)
            if df.empty:
                st.info("Você ainda não possui clientes cadastrados.")
            else:
                df = resumo_arquivos_para_leads(df)
                st.markdown("#### 🔎 Localizar cliente")
                situacao_docs = st.selectbox(
                    "Situação dos documentos",
                    ["Todos", "Com documentos não baixados", "Documentos baixados", "Sem documentos", "Com documentos"],
                    key="docs_situacao_mobile",
                )
                busca_doc = st.text_input("Buscar por nome, CPF ou telefone", placeholder="Digite parte do nome, CPF ou telefone", key="docs_busca_mobile")

                df_docs = df.copy()
                if situacao_docs == "Com documentos não baixados":
                    df_docs = df_docs[df_docs["documentos_enviados"] > df_docs["documentos_baixados"]]
                elif situacao_docs == "Documentos baixados":
                    df_docs = df_docs[(df_docs["documentos_enviados"] > 0) & (df_docs["documentos_enviados"] == df_docs["documentos_baixados"])]
                elif situacao_docs == "Sem documentos":
                    df_docs = df_docs[df_docs["documentos_enviados"] == 0]
                elif situacao_docs == "Com documentos":
                    df_docs = df_docs[df_docs["documentos_enviados"] > 0]

                if busca_doc.strip():
                    termo = busca_doc.strip().lower()
                    mask = pd.Series(False, index=df_docs.index)
                    for c in ["nome_cliente", "cpf", "telefone"]:
                        if c in df_docs.columns:
                            mask = mask | df_docs[c].fillna("").astype(str).str.lower().str.contains(termo, na=False)
                    df_docs = df_docs[mask]

                if df_docs.empty:
                    st.warning("Nenhum cliente encontrado com os filtros selecionados.")
                else:
                    df_docs["label_doc"] = (
                        df_docs["nome_cliente"].fillna("") + " | " +
                        df_docs["telefone"].fillna("") + " | " +
                        df_docs["bairro"].fillna("") + " | 📎 " +
                        df_docs["documentos_enviados"].astype(str) + " enviados / 📥 " +
                        df_docs["documentos_baixados"].astype(str) + " baixados"
                    )
                    lead_label = st.selectbox("Selecione o cliente", df_docs["label_doc"].tolist())
                    lead = df_docs[df_docs["label_doc"] == lead_label].iloc[0]

                    st.write(f"**Cliente:** {lead.get('nome_cliente','')}")
                    st.write(f"**Status:** {lead.get('status_lead','Novo')}")
                    st.write(f"📎 **Enviados:** {int(lead.get('documentos_enviados',0))} | 📥 **Baixados:** {int(lead.get('documentos_baixados',0))}")
                    if int(lead.get('documentos_enviados',0)) == 0:
                        st.info("Este cliente ainda não possui documentos enviados.")
                    elif int(lead.get('documentos_enviados',0)) == int(lead.get('documentos_baixados',0)):
                        st.success("Documentação recebida/baixada pela equipe.")
                    else:
                        st.warning("Ainda há documentos aguardando download pela equipe.")

                    with st.form("form_add_docs_atendente", clear_on_submit=True):
                        tipo_documento_extra = st.selectbox("Tipo dos arquivos", listar_tipos_arquivo(), key="tipo_doc_extra_mobile")
                        arquivos_extra = st.file_uploader("📎 Anexar documentos/arquivos", accept_multiple_files=True, type=["pdf", "png", "jpg", "jpeg", "webp"], key="arquivos_extra_mobile")
                        foto_extra_upload = st.file_uploader("📷 Tirar foto do documento", accept_multiple_files=False, type=["png", "jpg", "jpeg", "webp"], key="foto_extra_mobile", help="Use este campo para abrir a câmera do celular ou escolher uma foto da galeria.")
                        enviar_docs = st.form_submit_button("📎 ENVIAR DOCUMENTOS")

                    if enviar_docs:
                        arquivos_extra_enviar = lista_arquivos_com_foto(
                            arquivos_extra,
                            foto_extra_upload,
                            f"foto_extra_{str(lead['id'])}.jpg",
                        )
                        if not arquivos_extra_enviar:
                            st.error("Selecione pelo menos um arquivo ou uma foto.")
                        else:
                            try:
                                enviados = 0
                                for arquivo in arquivos_extra_enviar:
                                    enviar_arquivo_temporario(str(lead["id"]), arquivo, tipo_documento_extra, usuario)
                                    enviados += 1
                                salvar_historico(str(lead["id"]), usuario["nome"], lead.get("status_lead", "Novo"), f"{enviados} novo(s) arquivo(s) anexado(s) pelo atendente.", "Arquivos anexados")
                                st.success(f"{enviados} documento(s) enviado(s) com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao enviar documentos: {e}")
        fechar_card_mobile()

    if st.button("Sair"):
        st.session_state.usuario = None
        st.rerun()
    st.stop()

# -------------------------------
# MENU DESKTOP - GESTOR / SUPERVISOR
# -------------------------------
aplicar_css_sidebar_desktop()
header_desktop(usuario)

st.sidebar.markdown(
    """
    <div class="sidebar-brand">
        <div class="sidebar-v360">
            <span class="v-letter">V</span><span class="num-letter">360</span>
        </div>
        <div class="sidebar-cap">
            CLIENTES
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    f"""
    <div class="sidebar-user-card">
        <div class="sidebar-user-name">👤 {usuario['nome']}</div>
        <div class="sidebar-user-profile">🏷️ {rotulo_perfil_usuario(usuario['perfil']).title()}</div>
    </div>
    <div class="sidebar-menu-title">Menu</div>
    """,
    unsafe_allow_html=True,
)

if usuario.get("perfil") == "pendencia":
    opcoes_base = {
        "📌 Pendências": "Pendências",
    }
else:
    opcoes_base = {
        "➕ Novo Cliente": "Novo Cliente",
        "📋 Meus Clientes": "Minhas Clientes",
    }

    if usuario.get("perfil") in ["captador", "atendente"]:
        opcoes_base.update({
            "📎 Enviar Documentos": "Documentos",
            "📌 Pendências": "Minhas Pendências",
        })

    if pode_ver_todos(usuario):
        opcoes_base.update({
            "📊 Dashboard Executivo": "Painel Gestor",
            "💡 Insights V360": "Insights V360",
            "✏️ Atualizar Cliente": "Atualizar Cliente",
            "🔁 Transferência de Clientes": "Transferência de Clientes",
            "📅 Agenda de Atendimentos": "Agenda de Atendimentos",
            "📌 Pendências": "Pendências",
            "⚙️ Cadastros": "Cadastros",
        })
        if pode_gerenciar_usuarios(usuario):
            opcoes_base.update({"👥 Usuários": "Usuários"})

pagina_label = st.sidebar.radio("", list(opcoes_base.keys()), label_visibility="collapsed")
pagina = opcoes_base[pagina_label]

st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.markdown(f"<div class='sidebar-version'>Versão: {VERSAO_APP}</div>", unsafe_allow_html=True)
if st.sidebar.button("🚪 Sair"):
    st.session_state.usuario = None
    st.rerun()

# -------------------------------
# NOVO LEAD DESKTOP
# -------------------------------
if pagina == "Novo Cliente":
    st.title("➕ Novo Cliente")
    st.caption("O atendente é preenchido automaticamente pelo usuário logado.")

    with st.form("form_novo_lead", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            unidade_lead = selecionar_unidade_usuario(usuario, key="unidade_lead_desktop")
            cidade_lead = selecionar_cidade_por_unidade(unidade_lead, key="cidade_lead_desktop")
            nome_cliente = st.text_input("Nome do cliente *")
            cpf = st.text_input("CPF")
            telefone = st.text_input("Telefone *")
            bairro = selecionar_bairro_inline(cidade_lead, key="bairro_lead_desktop")
        with col2:
            locais_opcoes = listar_locais_captacao()
            if locais_opcoes:
                local_sel = st.selectbox("Local da clientes *", ["Outro / digitar"] + locais_opcoes)
                local_captacao = st.text_input("Digite o local" if local_sel == "Outro / digitar" else "Confirmar local", value="" if local_sel == "Outro / digitar" else local_sel, placeholder="Ex.: Feira, praça, INSS, ação social...")
            else:
                local_captacao = st.text_input("Local da clientes *", placeholder="Ex.: Feira, praça, INSS, ação social...")
            area_acao = st.selectbox("Área da ação *", AREAS_ACAO)
            tipo_beneficio = st.selectbox("Tipo de benefício *", listar_beneficios())
            observacao = st.text_area("Observação", placeholder="Informações úteis para o atendimento posterior")
            tipo_documento_upload = st.selectbox("Tipo dos arquivos", listar_tipos_arquivo(), key="tipo_doc_upload_desktop")
            arquivos_upload = st.file_uploader("📎 Anexar documentos/arquivos", accept_multiple_files=True, type=["pdf", "png", "jpg", "jpeg", "webp"], key="arquivos_upload_desktop")
            foto_camera_desktop_upload = st.file_uploader("📷 Tirar foto do documento", accept_multiple_files=False, type=["png", "jpg", "jpeg", "webp"], key="foto_camera_desktop", help="Use este campo para abrir a câmera do celular ou escolher uma foto da galeria.")

        enviar = st.form_submit_button("Salvar Cliente")

    if enviar:
        cpf_limpo = limpar_cpf(cpf)
        duplicado = buscar_lead_por_cpf(cpf_limpo) if cpf_limpo else None

        if not nome_cliente or not telefone or not bairro or not cidade_lead or not local_captacao:
            st.error("Preencha os campos obrigatórios marcados com *.")
        elif not cpf_valido_ou_vazio(cpf):
            st.error("CPF inválido. Use 11 números.")
        elif not telefone_valido(telefone):
            st.error("Telefone inválido. Use DDD + número, exemplo: (95) 99999-9999.")
        elif duplicado:
            st.warning(
                f"⚠️ Cliente já cadastrado: {duplicado.get('nome_cliente','')} | "
                f"Atendente: {duplicado.get('captador_nome','')} | "
                f"Status: {duplicado.get('status_lead','')}"
            )
        else:
            dados = {
                "captador_id": usuario["id"],
                "captador_nome": usuario["nome"],
                "unidade": unidade_lead,
                "cidade": cidade_lead,
                "nome_cliente": normalizar_texto(nome_cliente),
                "cpf": cpf_limpo,
                "telefone": telefone.strip(),
                "bairro": bairro,
                "local_captacao": normalizar_texto(local_captacao),
                "area_acao": area_acao,
                "tipo_beneficio": tipo_beneficio,
                "observacao": observacao.strip(),
                "status_lead": "Novo",
            }
            try:
                resp = salvar_lead(dados)
                novo_id = (resp.data or [{}])[0].get("id") if hasattr(resp, "data") else None
                if novo_id:
                    observacao_ok = garantir_observacao_lead(novo_id, observacao)
                    salvar_historico(novo_id, usuario["nome"], "Novo", observacao.strip(), "Cliente cadastrado")
                    arquivos_para_enviar = lista_arquivos_com_foto(
                        arquivos_upload,
                        foto_camera_desktop_upload,
                        f"foto_{limpar_cpf(cpf) or novo_id}.jpg",
                    )
                    if arquivos_para_enviar:
                        enviados = 0
                        for arquivo in arquivos_para_enviar:
                            enviar_arquivo_temporario(novo_id, arquivo, tipo_documento_upload, usuario)
                            enviados += 1
                        salvar_historico(novo_id, usuario["nome"], "Novo", f"{enviados} arquivo(s) anexado(s) ao lead.", "Arquivos anexados")
                st.success("Cliente salvo com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar lead: {e}")

# -------------------------------
# MINHAS CAPTAÇÕES
# -------------------------------
elif pagina == "Minhas Clientes":
    st.title("📋 Meus Clientes")
    df = aplicar_escopo_unidade(carregar_leads(), usuario)

    if df.empty:
        st.info("Nenhum cliente encontrado.")
    else:
        if not pode_ver_todos(usuario):
            df = filtrar_clientes_do_atendente(df, usuario)

        st.caption(f"{len(df)} cliente(s) localizado(s) para este usuário.")

        col1, col2 = st.columns(2)
        with col1:
            status_filtro = st.multiselect("Status", STATUS_LEAD, default=STATUS_LEAD)
        with col2:
            bairro_filtro = st.multiselect("Bairro", sorted(df["bairro"].dropna().unique().tolist()))

        if status_filtro:
            df = df[df["status_lead"].isin(status_filtro)]
        if bairro_filtro:
            df = df[df["bairro"].isin(bairro_filtro)]

        colunas = [
            "data_captacao", "nome_cliente", "telefone", "cidade", "bairro", "local_captacao",
            "area_acao", "tipo_beneficio", "status_lead", "captador_nome", "observacao",
            "quem_atendeu", "motivo_perda"
        ]
        colunas = [c for c in colunas if c in df.columns]
        st.dataframe(preparar_dataframe_exibicao(df[colunas]), use_container_width=True, hide_index=True)

        csv = df[colunas].to_csv(index=False).encode("utf-8-sig")
        st.download_button("Baixar CSV", csv, "meus_clientes.csv", "text/csv")


# -------------------------------
# ENVIAR DOCUMENTOS PARA CLIENTE JÁ CADASTRADO
# -------------------------------
elif pagina == "Documentos":
    st.title("📎 Enviar Documentos")
    st.caption("Localize um cliente já cadastrado e envie documentos mesmo que ele não tenha pendência aberta.")

    df_docs = aplicar_escopo_unidade(carregar_leads(), usuario)

    if df_docs.empty:
        st.info("Nenhum cliente disponível no seu escopo.")
    else:
        df_docs = resumo_arquivos_para_leads(df_docs)

        st.markdown("### 🔎 Localizar cliente")
        c1, c2, c3 = st.columns([1.8, 1, 1])
        with c1:
            busca_doc = st.text_input(
                "Nome, CPF ou telefone",
                placeholder="Digite parte do nome, CPF ou telefone...",
                key="docs_busca_desktop",
            )
        with c2:
            unidade_doc = st.multiselect(
                "Unidade",
                sorted([x for x in df_docs.get("unidade", pd.Series(dtype=str)).fillna("").unique().tolist() if x]),
                key="docs_unidade_desktop",
            )
        with c3:
            situacao_docs = st.selectbox(
                "Situação dos documentos",
                ["Todos", "Com documentos não baixados", "Documentos baixados", "Sem documentos", "Com documentos"],
                key="docs_situacao_desktop",
            )

        df_f = df_docs.copy()

        if unidade_doc and "unidade" in df_f.columns:
            df_f = df_f[df_f["unidade"].isin(unidade_doc)]

        if situacao_docs == "Com documentos não baixados":
            df_f = df_f[df_f["documentos_enviados"] > df_f["documentos_baixados"]]
        elif situacao_docs == "Documentos baixados":
            df_f = df_f[
                (df_f["documentos_enviados"] > 0)
                & (df_f["documentos_enviados"] == df_f["documentos_baixados"])
            ]
        elif situacao_docs == "Sem documentos":
            df_f = df_f[df_f["documentos_enviados"] == 0]
        elif situacao_docs == "Com documentos":
            df_f = df_f[df_f["documentos_enviados"] > 0]

        if busca_doc.strip():
            termo = busca_doc.strip().lower()
            termo_num = apenas_digitos(busca_doc)
            mask = pd.Series(False, index=df_f.index)

            for col in ["nome_cliente", "cpf", "telefone", "bairro", "cidade"]:
                if col in df_f.columns:
                    mask = mask | df_f[col].fillna("").astype(str).str.lower().str.contains(termo, na=False)

            if termo_num:
                if "cpf" in df_f.columns:
                    mask = mask | df_f["cpf"].fillna("").astype(str).apply(apenas_digitos).str.contains(termo_num, na=False)
                if "telefone" in df_f.columns:
                    mask = mask | df_f["telefone"].fillna("").astype(str).apply(apenas_digitos).str.contains(termo_num, na=False)

            df_f = df_f[mask]

        st.caption(f"{len(df_f)} cliente(s) encontrado(s).")

        if df_f.empty:
            st.warning("Nenhum cliente encontrado com os filtros selecionados.")
        else:
            for col in ["nome_cliente", "telefone", "bairro", "cidade", "captador_nome"]:
                if col not in df_f.columns:
                    df_f[col] = ""
                df_f[col] = df_f[col].fillna("").astype(str)

            df_f["label_doc"] = (
                df_f["nome_cliente"] + " | "
                + df_f["telefone"] + " | "
                + df_f["cidade"] + " | "
                + df_f["bairro"] + " | Atendente: "
                + df_f["captador_nome"]
            )

            lead_label = st.selectbox(
                "Selecione o cliente",
                df_f["label_doc"].tolist(),
                key="docs_cliente_desktop",
            )
            lead = df_f[df_f["label_doc"] == lead_label].iloc[0]

            i1, i2, i3, i4 = st.columns(4)
            i1.metric("Cliente", str(lead.get("nome_cliente", "")))
            i2.metric("Status", str(lead.get("status_lead", "Novo")))
            i3.metric("Documentos enviados", int(lead.get("documentos_enviados", 0)))
            i4.metric("Documentos baixados", int(lead.get("documentos_baixados", 0)))

            with st.form("form_enviar_docs_cliente_desktop", clear_on_submit=True):
                tipo_documento = st.selectbox(
                    "Tipo dos arquivos",
                    listar_tipos_arquivo(),
                    key="tipo_doc_cliente_desktop",
                )
                arquivos = st.file_uploader(
                    "📎 Anexar documentos/arquivos",
                    accept_multiple_files=True,
                    type=["pdf", "png", "jpg", "jpeg", "webp"],
                    key="arquivos_cliente_desktop",
                )
                foto = st.file_uploader(
                    "📷 Tirar foto ou escolher imagem",
                    accept_multiple_files=False,
                    type=["png", "jpg", "jpeg", "webp"],
                    key="foto_cliente_desktop",
                    help="No celular, este campo pode abrir a câmera ou a galeria.",
                )
                observacao_docs = st.text_area(
                    "Observação",
                    placeholder="Ex.: Documento entregue pelo cliente durante atendimento externo.",
                    key="obs_docs_cliente_desktop",
                )
                enviar_docs = st.form_submit_button("📎 Enviar documentos")

            if enviar_docs:
                arquivos_enviar = lista_arquivos_com_foto(
                    arquivos,
                    foto,
                    f"foto_cliente_{str(lead.get('id'))}.jpg",
                )

                if not arquivos_enviar:
                    st.error("Selecione pelo menos um arquivo ou uma foto.")
                else:
                    try:
                        enviados = 0
                        for arquivo in arquivos_enviar:
                            enviar_arquivo_temporario(
                                str(lead["id"]),
                                arquivo,
                                tipo_documento,
                                usuario,
                            )
                            enviados += 1

                        texto_hist = f"{enviados} documento(s) anexado(s) pelo atendente."
                        if observacao_docs.strip():
                            texto_hist += f" Observação: {observacao_docs.strip()}"

                        salvar_historico(
                            str(lead["id"]),
                            usuario.get("nome", ""),
                            lead.get("status_lead", "Novo"),
                            texto_hist,
                            "Documentos anexados",
                        )

                        st.success(f"{enviados} documento(s) enviado(s) com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao enviar documentos: {e}")


# -------------------------------
# PAINEL GESTOR - EXECUTIVO V360
# -------------------------------
elif pagina == "Painel Gestor":
    st.title("📊 Dashboard Executivo V360 Clientes")
    st.caption("Visão executiva por unidade, clientes, conversão, produtividade, bairros, locais e gargalos.")

    st.markdown(
        """
        <style>
        .exec-card {
            background: linear-gradient(145deg, #061A33 0%, #0A3D7A 100%);
            border: 1px solid rgba(24,189,242,.25);
            border-radius: 18px;
            padding: 18px 16px;
            box-shadow: 0 12px 28px rgba(6,26,51,.12);
            min-height: 118px;
        }
        .exec-card-title { color: #B8D9EF; font-size: 12px; font-weight: 900; text-transform: uppercase; letter-spacing: .8px; }
        .exec-card-value { color: white; font-size: 33px; font-weight: 950; margin-top: 8px; line-height: 1; }
        .exec-card-sub { color: #18BDF2; font-size: 13px; font-weight: 700; margin-top: 10px; }
        .v360-section-title {
            color: #061A33;
            font-weight: 950;
            font-size: 22px;
            margin-top: 20px;
            margin-bottom: 8px;
        }
        .insight-box {
            background: linear-gradient(145deg, #EEF8FF 0%, #FFFFFF 100%);
            border-left: 5px solid #18BDF2;
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 10px;
            font-weight: 650;
            box-shadow: 0 8px 22px rgba(6,26,51,0.05);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    unidades_dashboard = unidades_permitidas_usuario(usuario)
    df_original = aplicar_escopo_unidade(carregar_leads(), usuario)

    if usuario.get("perfil") == "gestor_regional":
        st.caption(
            "Escopo regional: "
            + (", ".join(unidades_dashboard) if unidades_dashboard else "nenhuma unidade vinculada")
        )
    elif usuario.get("perfil") == "gestor_unidade":
        st.caption(
            "Escopo da unidade: "
            + (", ".join(unidades_dashboard) if unidades_dashboard else "nenhuma unidade vinculada")
        )

    if df_original.empty:
        st.info("Nenhum cliente encontrado nas unidades vinculadas a este usuário.")
        st.stop()

    df = df_original.copy()
    for col in ["status_lead", "captador_nome", "bairro", "tipo_beneficio", "motivo_perda", "local_captacao", "quem_atendeu"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")
    df["status_lead"] = df["status_lead"].replace("", "Novo")
    df["captador_nome"] = df["captador_nome"].replace("", "Não informado")
    df["bairro"] = df["bairro"].replace("", "Não informado")
    df["tipo_beneficio"] = df["tipo_beneficio"].replace("", "Não informado")
    df["local_captacao"] = df["local_captacao"].replace("", "Não informado")

    hoje = date.today()

    st.markdown("### 🔎 Filtros Executivos")
    colf1, colf2, colf3, colf4 = st.columns(4)
    with colf1:
        periodo = st.selectbox("Período", ["Últimos 7 dias", "Últimos 30 dias", "Mês atual", "Todos", "Personalizado"], index=1)
    with colf2:
        data_ini = st.date_input("Data inicial", hoje - timedelta(days=30))
    with colf3:
        data_fim = st.date_input("Data final", hoje)
    with colf4:
        status_filtro = st.multiselect("Status", STATUS_LEAD, default=STATUS_LEAD)

    if periodo == "Últimos 7 dias":
        data_ini, data_fim = hoje - timedelta(days=7), hoje
    elif periodo == "Últimos 30 dias":
        data_ini, data_fim = hoje - timedelta(days=30), hoje
    elif periodo == "Mês atual":
        data_ini, data_fim = hoje.replace(day=1), hoje
    elif periodo == "Todos":
        data_ini = df["data_captacao"].dt.date.min()
        data_fim = df["data_captacao"].dt.date.max()

    if "unidade" not in df.columns:
        df["unidade"] = "Boa Vista"
    df["unidade"] = df["unidade"].fillna("Boa Vista").replace("", "Boa Vista")

    colf5, colf6, colf7, colf8, colf9 = st.columns(5)
    with colf5:
        unidade_filtro = st.multiselect(
            "Unidade",
            sorted(df["unidade"].dropna().unique().tolist()),
            key="dashboard_unidade_filtro",
        )
    with colf6:
        atendente_filtro = st.multiselect("Atendente", sorted(df["captador_nome"].dropna().unique().tolist()))
    with colf7:
        bairro_filtro = st.multiselect("Bairro", sorted(df["bairro"].dropna().unique().tolist()))
    with colf8:
        beneficio_filtro = st.multiselect("Benefício", sorted(df["tipo_beneficio"].dropna().unique().tolist()))
    with colf9:
        local_filtro = st.multiselect("Local", sorted(df["local_captacao"].dropna().unique().tolist()))

    df = df[(df["data_captacao"].dt.date >= data_ini) & (df["data_captacao"].dt.date <= data_fim)]
    if status_filtro:
        df = df[df["status_lead"].isin(status_filtro)]
    if unidade_filtro:
        df = df[df["unidade"].isin(unidade_filtro)]
    if atendente_filtro:
        df = df[df["captador_nome"].isin(atendente_filtro)]
    if bairro_filtro:
        df = df[df["bairro"].isin(bairro_filtro)]
    if beneficio_filtro:
        df = df[df["tipo_beneficio"].isin(beneficio_filtro)]
    if local_filtro:
        df = df[df["local_captacao"].isin(local_filtro)]

    if df.empty:
        st.warning("Nenhum cliente encontrado com os filtros selecionados.")
        st.stop()

    total = len(df)
    novos = int((df["status_lead"] == "Novo").sum())
    atendimento = int((df["status_lead"] == "Em atendimento").sum())
    convertidos = int((df["status_lead"] == "Convertido").sum())
    perdidos = int((df["status_lead"] == "Perdido").sum())
    conversao = (convertidos / total * 100) if total else 0
    perda_pct = (perdidos / total * 100) if total else 0

    def card_exec(titulo, valor, subtitulo=""):
        st.markdown(
            f"""
            <div class="exec-card">
                <div class="exec-card-title">{titulo}</div>
                <div class="exec-card-value">{valor}</div>
                <div class="exec-card-sub">{subtitulo}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 1 - CARDS EXECUTIVOS
    st.markdown("<div class='v360-section-title'>1. Cards Executivos</div>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: card_exec("📍 Clientes", total, "clientes no período")
    with c2: card_exec("📞 Em atendimento", atendimento, f"{novos} novos aguardando")
    with c3: card_exec("✅ Convertidos", convertidos, f"{conversao:.1f}% de conversão")
    with c4: card_exec("❌ Perdidos", perdidos, f"{perda_pct:.1f}% de perda")
    with c5: card_exec("📈 Conversão", f"{conversao:.1f}%", f"{convertidos}/{total} clientes")

    # Preparações gerais
    ranking = df.groupby("captador_nome").agg(
        clientes=("id", "count"),
        convertidos=("status_lead", lambda s: (s == "Convertido").sum()),
        em_atendimento=("status_lead", lambda s: (s == "Em atendimento").sum()),
        perdidos=("status_lead", lambda s: (s == "Perdido").sum()),
    ).reset_index()
    ranking["conversao_%"] = (ranking["convertidos"] / ranking["clientes"] * 100).round(1)
    ranking = ranking.sort_values(["convertidos", "clientes"], ascending=False)

    bairros = df.groupby("bairro").agg(
        clientes=("id", "count"),
        convertidos=("status_lead", lambda s: (s == "Convertido").sum()),
        perdidos=("status_lead", lambda s: (s == "Perdido").sum()),
    ).reset_index()
    bairros["conversao_%"] = (bairros["convertidos"] / bairros["clientes"] * 100).round(1)
    bairros = bairros.sort_values("clientes", ascending=False)

    locais = df.groupby("local_captacao").agg(
        clientes=("id", "count"),
        convertidos=("status_lead", lambda s: (s == "Convertido").sum()),
        perdidos=("status_lead", lambda s: (s == "Perdido").sum()),
    ).reset_index()
    locais["conversao_%"] = (locais["convertidos"] / locais["clientes"] * 100).round(1)
    locais = locais.sort_values("clientes", ascending=False)

    # 2 e 3
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("<div class='v360-section-title'>2. Funil de Conversão</div>", unsafe_allow_html=True)
        funil_df = pd.DataFrame({
            "Etapa": ["Clientes", "Novos", "Em atendimento", "Convertidos", "Perdidos"],
            "Quantidade": [total, novos, atendimento, convertidos, perdidos],
        })
        fig = px.funnel(funil_df, x="Quantidade", y="Etapa", text="Quantidade")
        fig.update_layout(height=390, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("<div class='v360-section-title'>3. Evolução Diária</div>", unsafe_allow_html=True)
        df_dia = df.copy()
        df_dia["dia"] = df_dia["data_captacao"].dt.date
        diario = df_dia.groupby("dia").size().reset_index(name="Clientes")
        fig = px.line(diario, x="dia", y="Clientes", markers=True)
        fig.update_layout(height=390, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # 4 - Ranking atendentes
    st.markdown("<div class='v360-section-title'>4. Ranking de Atendentes</div>", unsafe_allow_html=True)
    col3, col4 = st.columns([1.15, .85])
    with col3:
        fig = px.bar(ranking.head(10), x="clientes", y="captador_nome", orientation="h", text="clientes", title="Ranking por volume de clientes")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=430, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        st.dataframe(ranking.rename(columns={
            "captador_nome": "Atendente", "clientes": "Clientes", "convertidos": "Convertidos",
            "em_atendimento": "Em atendimento", "perdidos": "Perdidos", "conversao_%": "Conversão %"
        }), use_container_width=True, hide_index=True)

    # 5 - Benefícios
    st.markdown("<div class='v360-section-title'>5. Benefícios Mais Clientes</div>", unsafe_allow_html=True)
    beneficio_df = df["tipo_beneficio"].value_counts().reset_index().head(12)
    beneficio_df.columns = ["Benefício", "Quantidade"]
    fig = px.bar(beneficio_df, x="Quantidade", y="Benefício", orientation="h", text="Quantidade")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=430, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # 6 e 7 - Bairros
    col5, col6 = st.columns(2)
    with col5:
        st.markdown("<div class='v360-section-title'>6. Bairros com Mais Clientes</div>", unsafe_allow_html=True)
        fig = px.bar(bairros.head(15), x="clientes", y="bairro", orientation="h", text="clientes")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=430, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with col6:
        st.markdown("<div class='v360-section-title'>7. Bairros com Maior Conversão</div>", unsafe_allow_html=True)
        bairros_conv = bairros[bairros["clientes"] >= 3].copy()
        if bairros_conv.empty:
            st.info("Ainda não há volume suficiente por bairro. Mínimo: 3 clientes por bairro.")
        else:
            bairros_conv = bairros_conv.sort_values(["conversao_%", "convertidos", "clientes"], ascending=False).head(15)
            fig = px.bar(bairros_conv, x="conversao_%", y="bairro", orientation="h", text="conversao_%")
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=430, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(bairros_conv.rename(columns={"bairro":"Bairro", "clientes":"Clientes", "convertidos":"Convertidos", "perdidos":"Perdidos", "conversao_%":"Conversão %"}), use_container_width=True, hide_index=True)

    # 8 - Locais clientes
    st.markdown("<div class='v360-section-title'>8. Locais de Clientes</div>", unsafe_allow_html=True)
    col7, col8 = st.columns(2)
    with col7:
        fig = px.bar(locais.head(15), x="clientes", y="local_captacao", orientation="h", text="clientes", title="Locais com mais clientes")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=430, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with col8:
        locais_conv = locais[locais["clientes"] >= 3].copy()
        if locais_conv.empty:
            st.info("Ainda não há volume suficiente por local. Mínimo: 3 clientes por local.")
        else:
            locais_conv = locais_conv.sort_values(["conversao_%", "convertidos", "clientes"], ascending=False).head(15)
            st.dataframe(locais_conv.rename(columns={
                "local_captacao":"Local", "clientes":"Clientes", "convertidos":"Convertidos",
                "perdidos":"Perdidos", "conversao_%":"Conversão %"
            }), use_container_width=True, hide_index=True)

    # 9 - Motivos perda
    st.markdown("<div class='v360-section-title'>9. Motivos de Perda</div>", unsafe_allow_html=True)
    perdas = df[df["status_lead"] == "Perdido"].copy()
    if perdas.empty:
        st.info("Nenhum cliente perdido no período selecionado.")
    else:
        perdas_df = perdas["motivo_perda"].fillna("Não informado").replace("", "Não informado").value_counts().reset_index()
        perdas_df.columns = ["Motivo", "Quantidade"]
        fig = px.bar(perdas_df, x="Quantidade", y="Motivo", orientation="h", text="Quantidade")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=390, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # 10 - Base completa
    st.markdown("<div class='v360-section-title'>10. Base Completa</div>", unsafe_allow_html=True)
    colunas_base = [
        "data_captacao", "nome_cliente", "cpf", "telefone", "cidade", "bairro", "local_captacao",
        "area_acao", "tipo_beneficio", "status_lead", "captador_nome",
        "quem_atendeu", "motivo_perda", "observacao"
    ]
    colunas_base = [c for c in colunas_base if c in df.columns]
    st.dataframe(preparar_dataframe_exibicao(df[colunas_base]), use_container_width=True, hide_index=True)
    csv = df[colunas_base].to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Baixar base filtrada", csv, "v360_captacao_executivo.csv", "text/csv")

# -------------------------------
# INSIGHTS V360
# -------------------------------
elif pagina == "Insights V360":
    st.title("💡 Insights V360")
    st.caption("Inteligência comercial por unidade, oportunidades e alertas da clientes.")

    st.markdown(
        """
        <style>
        .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 14px;
            margin-bottom: 18px;
        }
        .insight-card-v360 {
            background: linear-gradient(145deg, #FFFFFF 0%, #F4FAFF 100%);
            border: 1px solid #DCE8F4;
            border-left: 5px solid #18BDF2;
            border-radius: 18px;
            padding: 16px 16px;
            box-shadow: 0 10px 24px rgba(6,26,51,.07);
            min-height: 118px;
        }
        .insight-card-title { color:#061A33; font-size:14px; font-weight:950; margin-bottom:8px; }
        .insight-card-value { color:#0A3D7A; font-size:22px; font-weight:950; line-height:1.1; }
        .insight-card-sub { color:#65748A; font-size:13px; font-weight:700; margin-top:8px; }
        .alert-card {
            background:#FFF8E8;
            border:1px solid #FFE4A3;
            border-left:5px solid #F59E0B;
            border-radius:16px;
            padding:14px 16px;
            margin-bottom:10px;
            font-weight:700;
        }
        .op-card {
            background:#EEFDF7;
            border:1px solid #BDEEDB;
            border-left:5px solid #10B981;
            border-radius:16px;
            padding:14px 16px;
            margin-bottom:10px;
            font-weight:700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    df_original = aplicar_escopo_unidade(carregar_leads(), usuario)
    if df_original.empty:
        st.info("Nenhum dado encontrado. Cadastre alguns clientes para gerar os insights.")
        st.stop()

    df = df_original.copy()
    for col in ["status_lead", "captador_nome", "bairro", "tipo_beneficio", "motivo_perda", "local_captacao", "quem_atendeu"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")
    df["status_lead"] = df["status_lead"].replace("", "Novo")
    df["captador_nome"] = df["captador_nome"].replace("", "Não informado")
    df["bairro"] = df["bairro"].replace("", "Não informado")
    df["tipo_beneficio"] = df["tipo_beneficio"].replace("", "Não informado")
    df["local_captacao"] = df["local_captacao"].replace("", "Não informado")

    hoje = date.today()
    st.markdown("### 🔎 Filtros dos Insights")
    colf1, colf2, colf3, colf4 = st.columns(4)
    with colf1:
        periodo = st.selectbox("Período", ["Últimos 7 dias", "Últimos 30 dias", "Mês atual", "Todos", "Personalizado"], index=1, key="ins_periodo")
    with colf2:
        data_ini = st.date_input("Data inicial", hoje - timedelta(days=30), key="ins_data_ini")
    with colf3:
        data_fim = st.date_input("Data final", hoje, key="ins_data_fim")
    with colf4:
        status_filtro = st.multiselect("Status", STATUS_LEAD, default=STATUS_LEAD, key="ins_status")

    if periodo == "Últimos 7 dias":
        data_ini, data_fim = hoje - timedelta(days=7), hoje
    elif periodo == "Últimos 30 dias":
        data_ini, data_fim = hoje - timedelta(days=30), hoje
    elif periodo == "Mês atual":
        data_ini, data_fim = hoje.replace(day=1), hoje
    elif periodo == "Todos":
        data_ini = df["data_captacao"].dt.date.min()
        data_fim = df["data_captacao"].dt.date.max()

    colf5, colf6, colf7, colf8 = st.columns(4)
    with colf5:
        atendente_filtro = st.multiselect("Atendente", sorted(df["captador_nome"].dropna().unique().tolist()), key="ins_atendente")
    with colf6:
        bairro_filtro = st.multiselect("Bairro", sorted(df["bairro"].dropna().unique().tolist()), key="ins_bairro")
    with colf7:
        beneficio_filtro = st.multiselect("Benefício", sorted(df["tipo_beneficio"].dropna().unique().tolist()), key="ins_beneficio")
    with colf8:
        local_filtro = st.multiselect("Local", sorted(df["local_captacao"].dropna().unique().tolist()), key="ins_local")

    df = df[(df["data_captacao"].dt.date >= data_ini) & (df["data_captacao"].dt.date <= data_fim)]
    if status_filtro:
        df = df[df["status_lead"].isin(status_filtro)]
    if atendente_filtro:
        df = df[df["captador_nome"].isin(atendente_filtro)]
    if bairro_filtro:
        df = df[df["bairro"].isin(bairro_filtro)]
    if beneficio_filtro:
        df = df[df["tipo_beneficio"].isin(beneficio_filtro)]
    if local_filtro:
        df = df[df["local_captacao"].isin(local_filtro)]

    if df.empty:
        st.warning("Nenhum cliente encontrado com os filtros selecionados.")
        st.stop()

    total = len(df)
    convertidos = int((df["status_lead"] == "Convertido").sum())
    perdidos = int((df["status_lead"] == "Perdido").sum())
    conversao = (convertidos / total * 100) if total else 0
    perda_pct = (perdidos / total * 100) if total else 0

    def top_valor(coluna):
        vc = df[coluna].replace("", "Não informado").value_counts()
        if vc.empty:
            return "Sem dados", 0, 0
        nome = vc.index[0]
        qtd = int(vc.iloc[0])
        pct = (qtd / total * 100) if total else 0
        return nome, qtd, pct

    def agg_conversao(campo, minimo=3):
        base = df.groupby(campo).agg(
            clientes=("id", "count"),
            convertidos=("status_lead", lambda s: (s == "Convertido").sum()),
        ).reset_index()
        if base.empty:
            return base
        base["conversao_%"] = (base["convertidos"] / base["clientes"] * 100).round(1)
        base = base[base["clientes"] >= minimo]
        return base.sort_values(["conversao_%", "convertidos", "clientes"], ascending=False)

    def card_insight(titulo, valor, subtitulo=""):
        # Importante: retornar HTML sem espaços iniciais.
        # O Streamlit/Markdown interpreta linhas com 4+ espaços como bloco de código.
        return (
            f"<div class='insight-card-v360'>"
            f"<div class='insight-card-title'>{titulo}</div>"
            f"<div class='insight-card-value'>{valor}</div>"
            f"<div class='insight-card-sub'>{subtitulo}</div>"
            f"</div>"
        )

    top_bairro, top_bairro_qtd, top_bairro_pct = top_valor("bairro")
    top_atendente, top_atendente_qtd, top_atendente_pct = top_valor("captador_nome")
    top_beneficio, top_beneficio_qtd, top_beneficio_pct = top_valor("tipo_beneficio")
    top_local, top_local_qtd, top_local_pct = top_valor("local_captacao")

    perdas = df[df["status_lead"] == "Perdido"].copy()
    if perdas.empty:
        top_motivo, top_motivo_qtd, top_motivo_pct = "Sem perdas", 0, 0
    else:
        motivo_vc = perdas["motivo_perda"].fillna("Não informado").replace("", "Não informado").value_counts()
        top_motivo = motivo_vc.index[0]
        top_motivo_qtd = int(motivo_vc.iloc[0])
        top_motivo_pct = (top_motivo_qtd / len(perdas) * 100) if len(perdas) else 0

    st.markdown("## 📌 Resumo Executivo")
    st.markdown(
        "<div class='insights-grid'>" +
        card_insight("🏆 Bairro líder em clientes", top_bairro, f"{top_bairro_qtd} leads • {top_bairro_pct:.1f}% do período") +
        card_insight("🥇 Atendente destaque", top_atendente, f"{top_atendente_qtd} leads • {top_atendente_pct:.1f}% do período") +
        card_insight("📋 Benefício mais procurado", top_beneficio, f"{top_beneficio_qtd} leads • {top_beneficio_pct:.1f}% do período") +
        card_insight("🏪 Local mais produtivo", top_local, f"{top_local_qtd} leads • {top_local_pct:.1f}% do período") +
        card_insight("⚠️ Principal motivo de perda", top_motivo, f"{top_motivo_qtd} ocorrências • {top_motivo_pct:.1f}% das perdas") +
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("## 📈 Inteligência Comercial")
    df_int = df.copy()
    df_int["dia_semana_num"] = df_int["data_captacao"].dt.weekday
    dias_map = {0:"Segunda-feira", 1:"Terça-feira", 2:"Quarta-feira", 3:"Quinta-feira", 4:"Sexta-feira", 5:"Sábado", 6:"Domingo"}
    df_int["dia_semana"] = df_int["dia_semana_num"].map(dias_map)

    def melhor_bairro_beneficio(texto_beneficio):
        sub = df[df["tipo_beneficio"].str.contains(texto_beneficio, case=False, na=False)].copy()
        if sub.empty:
            return "Sem dados", "Nenhum cliente encontrado"
        sub_conv = sub[sub["status_lead"] == "Convertido"]
        base = sub_conv if not sub_conv.empty else sub
        vc = base["bairro"].value_counts()
        nome = vc.index[0]
        qtd = int(vc.iloc[0])
        label = "contratos" if not sub_conv.empty else "clientes"
        return nome, f"{qtd} {label} de {texto_beneficio}"

    bairro_loas, sub_loas = melhor_bairro_beneficio("LOAS")
    bairro_aux, sub_aux = melhor_bairro_beneficio("Auxílio")

    dia_vc = df_int["dia_semana"].value_counts()
    melhor_dia = dia_vc.index[0] if not dia_vc.empty else "Sem dados"
    melhor_dia_qtd = int(dia_vc.iloc[0]) if not dia_vc.empty else 0

    mes_atual = hoje.replace(day=1)
    df_mes = df_original.copy()
    if not df_mes.empty:
        df_mes["data_captacao"] = pd.to_datetime(df_mes["data_captacao"], errors="coerce")
        df_mes = df_mes[df_mes["data_captacao"].dt.date >= mes_atual]
    conv_mes = df_mes[df_mes["status_lead"] == "Convertido"] if not df_mes.empty and "status_lead" in df_mes.columns else pd.DataFrame()
    if conv_mes.empty:
        melhor_captador_mes, melhor_captador_mes_sub = "Sem conversões", "Nenhum contrato no mês atual"
    else:
        vc = conv_mes["captador_nome"].fillna("Não informado").replace("", "Não informado").value_counts()
        melhor_captador_mes = vc.index[0]
        melhor_captador_mes_sub = f"{int(vc.iloc[0])} conversões no mês"

    locais_conv = agg_conversao("local_captacao")
    bairros_conv = agg_conversao("bairro")
    benef_conv = agg_conversao("tipo_beneficio")
    capt_conv = agg_conversao("captador_nome")

    def top_conv(base, campo, nome_vazio="Sem dados"):
        if base.empty:
            return nome_vazio, "Volume mínimo: 3 clientes"
        linha = base.iloc[0]
        return linha[campo], f"{linha['conversao_%']:.1f}% • {int(linha['convertidos'])}/{int(linha['clientes'])} convertidos"

    local_tx, local_tx_sub = top_conv(locais_conv, "local_captacao")
    bairro_tx, bairro_tx_sub = top_conv(bairros_conv, "bairro")
    beneficio_tx, beneficio_tx_sub = top_conv(benef_conv, "tipo_beneficio")
    atendente_tx, atendente_tx_sub = top_conv(capt_conv, "captador_nome")

    st.markdown(
        "<div class='insights-grid'>" +
        card_insight("📈 Melhor bairro para LOAS", bairro_loas, sub_loas) +
        card_insight("📈 Melhor bairro para Auxílio Doença", bairro_aux, sub_aux) +
        card_insight("📈 Melhor dia da semana para clientes", melhor_dia, f"{melhor_dia_qtd} leads no período") +
        card_insight("📈 Melhor atendente do mês", melhor_captador_mes, melhor_captador_mes_sub) +
        card_insight("📈 Local com maior taxa de conversão", local_tx, local_tx_sub) +
        card_insight("📈 Bairro com maior conversão geral", bairro_tx, bairro_tx_sub) +
        card_insight("📈 Benefício com maior conversão", beneficio_tx, beneficio_tx_sub) +
        card_insight("📈 Atendente com maior taxa de conversão", atendente_tx, atendente_tx_sub) +
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("## 🎯 Oportunidades")
    oportunidades = []
    if not bairros_conv.empty:
        bairros_volume = df.groupby("bairro").size().reset_index(name="clientes").sort_values("clientes", ascending=False)
        top_vol_bairro = bairros_volume.iloc[0]
        conv_top_vol = bairros_conv[bairros_conv["bairro"] == top_vol_bairro["bairro"]]
        if not conv_top_vol.empty and float(conv_top_vol.iloc[0]["conversao_%"]) < conversao:
            oportunidades.append(
                f"<b>{top_vol_bairro['bairro']}</b> possui alto volume de leads, mas conversão abaixo da média. Recomenda-se revisar abordagem e acompanhamento."
            )
    if not locais_conv.empty:
        linha = locais_conv.iloc[0]
        oportunidades.append(
            f"<b>{linha['local_captacao']}</b> apresenta a maior taxa de conversão ({linha['conversao_%']:.1f}%). Recomenda-se priorizar novas ações nesse local."
        )
    if not benef_conv.empty:
        linha = benef_conv.iloc[0]
        oportunidades.append(
            f"<b>{linha['tipo_beneficio']}</b> é o benefício com melhor conversão ({linha['conversao_%']:.1f}%). Pode ser prioridade em campanhas e roteiros de clientes."
        )
    if not oportunidades:
        oportunidades.append("Ainda não há volume suficiente para oportunidades avançadas. Continue cadastrando clientes para o V360 identificar padrões.")
    for item in oportunidades:
        st.markdown(f"<div class='op-card'>🎯 {item}</div>", unsafe_allow_html=True)

    st.markdown("## 🚨 Alertas")
    alertas = []
    if perda_pct >= 30:
        alertas.append(f"Taxa de perda em <b>{perda_pct:.1f}%</b> no período filtrado. Verificar motivos de perda e velocidade de atendimento.")
    pendentes = int(((df["status_lead"] == "Novo") | (df["status_lead"] == "Em atendimento")).sum())
    if pendentes >= max(5, int(total * 0.4)):
        alertas.append(f"Existem <b>{pendentes}</b> leads ainda sem conclusão. Pode haver gargalo no atendimento posterior.")
    if total < 10:
        alertas.append("Volume de dados ainda baixo. Alguns insights podem mudar bastante com novos cadastros.")
    if not alertas:
        alertas.append("Nenhum alerta crítico identificado no período filtrado.")
    for item in alertas:
        st.markdown(f"<div class='alert-card'>🚨 {item}</div>", unsafe_allow_html=True)



# -------------------------------
# AGENDA DE ATENDIMENTOS
# -------------------------------
elif pagina == "Agenda de Atendimentos":
    st.title("📅 Agenda de Atendimentos")
    st.caption("Visualize, filtre e atualize os atendimentos agendados.")

    df_agenda = carregar_agendamentos()
    if df_agenda.empty:
        st.info("Nenhum atendimento agendado.")
        st.stop()

    for col in [
        "id", "lead_id", "cliente_nome", "telefone", "tipo_beneficio",
        "unidade", "cidade", "advogado_nome", "data_agendamento",
        "hora_inicio", "hora_fim", "modalidade", "local_atendimento",
        "observacao", "status_agendamento"
    ]:
        if col not in df_agenda.columns:
            df_agenda[col] = ""

    df_agenda["status_agendamento"] = df_agenda["status_agendamento"].fillna("Agendado")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        data_ini_ag = st.date_input("Data inicial", value=date.today(), key="agenda_data_ini")
    with f2:
        data_fim_ag = st.date_input("Data final", value=date.today() + timedelta(days=30), key="agenda_data_fim")
    with f3:
        unidade_ag = st.multiselect("Unidade", sorted([x for x in df_agenda["unidade"].dropna().unique().tolist() if x]))
    with f4:
        advogado_ag = st.multiselect("Advogado", sorted([x for x in df_agenda["advogado_nome"].dropna().unique().tolist() if x]))

    f5, f6, f7, f8 = st.columns(4)
    with f5:
        status_ag = st.multiselect("Situação", STATUS_AGENDAMENTO, default=STATUS_AGENDAMENTO)
    with f6:
        modalidade_ag = st.multiselect("Modalidade", MODALIDADES_AGENDAMENTO)
    with f7:
        beneficio_ag = st.multiselect("Benefício", sorted([x for x in df_agenda["tipo_beneficio"].dropna().unique().tolist() if x]))
    with f8:
        busca_ag = st.text_input("Buscar cliente ou telefone")

    df_f = df_agenda.copy()
    datas = pd.to_datetime(df_f["data_agendamento"], errors="coerce").dt.date
    df_f = df_f[(datas >= data_ini_ag) & (datas <= data_fim_ag)]

    if unidade_ag:
        df_f = df_f[df_f["unidade"].isin(unidade_ag)]
    if advogado_ag:
        df_f = df_f[df_f["advogado_nome"].isin(advogado_ag)]
    if status_ag:
        df_f = df_f[df_f["status_agendamento"].isin(status_ag)]
    if modalidade_ag:
        df_f = df_f[df_f["modalidade"].isin(modalidade_ag)]
    if beneficio_ag:
        df_f = df_f[df_f["tipo_beneficio"].isin(beneficio_ag)]
    if busca_ag.strip():
        termo = busca_ag.strip().lower()
        df_f = df_f[
            df_f["cliente_nome"].fillna("").astype(str).str.lower().str.contains(termo, na=False)
            | df_f["telefone"].fillna("").astype(str).str.lower().str.contains(termo, na=False)
        ]

    st.caption(f"{len(df_f)} atendimento(s) encontrado(s).")

    tab_cal, tab_lista = st.tabs(["🗓️ Calendário mensal", "📋 Lista de atendimentos"])

    with tab_cal:
        hoje = date.today()
        c1, c2 = st.columns(2)
        with c1:
            mes_ag = st.selectbox(
                "Mês",
                list(range(1, 13)),
                index=hoje.month - 1,
                format_func=lambda m: [
                    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
                ][m - 1],
            )
        with c2:
            ano_ag = st.number_input("Ano", min_value=2020, max_value=2100, value=hoje.year, step=1)

        df_mes = df_f[
            (pd.to_datetime(df_f["data_agendamento"], errors="coerce").dt.month == mes_ag)
            & (pd.to_datetime(df_f["data_agendamento"], errors="coerce").dt.year == int(ano_ag))
        ]
        st.markdown(montar_calendario_mensal(df_mes, int(ano_ag), int(mes_ag)), unsafe_allow_html=True)

    with tab_lista:
        if df_f.empty:
            st.warning("Nenhum atendimento encontrado.")
        else:
            df_lista = df_f.copy()
            df_lista["data"] = pd.to_datetime(df_lista["data_agendamento"], errors="coerce").dt.strftime("%d/%m/%Y")
            cols = [
                "data", "hora_inicio", "hora_fim", "cliente_nome", "telefone",
                "advogado_nome", "tipo_beneficio", "unidade", "cidade",
                "modalidade", "local_atendimento", "status_agendamento"
            ]
            st.dataframe(
                df_lista[cols].rename(columns={
                    "data": "Data",
                    "hora_inicio": "Início",
                    "hora_fim": "Fim",
                    "cliente_nome": "Cliente",
                    "telefone": "Telefone",
                    "advogado_nome": "Advogado",
                    "tipo_beneficio": "Benefício",
                    "unidade": "Unidade",
                    "cidade": "Cidade",
                    "modalidade": "Modalidade",
                    "local_atendimento": "Local",
                    "status_agendamento": "Situação",
                }),
                use_container_width=True,
                hide_index=True,
            )

            df_f["label_agenda"] = (
                pd.to_datetime(df_f["data_agendamento"], errors="coerce").dt.strftime("%d/%m/%Y").fillna("")
                + " " + df_f["hora_inicio"].fillna("").astype(str).str[:5]
                + " | " + df_f["cliente_nome"].fillna("")
                + " | " + df_f["advogado_nome"].fillna("")
            )
            label = st.selectbox("Selecionar atendimento para atualizar", df_f["label_agenda"].tolist())
            ag = df_f[df_f["label_agenda"] == label].iloc[0]

            with st.form("form_atualizar_agendamento"):
                novo_status = st.selectbox(
                    "Situação do atendimento",
                    STATUS_AGENDAMENTO,
                    index=STATUS_AGENDAMENTO.index(ag.get("status_agendamento", "Agendado"))
                    if ag.get("status_agendamento", "Agendado") in STATUS_AGENDAMENTO else 0,
                )
                nova_obs = st.text_area("Observação", value=str(ag.get("observacao") or ""))
                salvar_ag = st.form_submit_button("💾 Salvar atualização")

            if salvar_ag:
                atualizar_agendamento(str(ag.get("id")), {
                    "status_agendamento": novo_status,
                    "observacao": nova_obs.strip(),
                    "atualizado_em": datetime.now(timezone.utc).isoformat(),
                })
                mapa_status = {
                    "Atendido": "Em atendimento",
                    "Não compareceu": "Em atendimento",
                    "Cancelado": "Em atendimento",
                    "Remarcado": "Agendado",
                    "Confirmado": "Agendado",
                    "Agendado": "Agendado",
                }
                novo_status_lead = mapa_status.get(novo_status)
                if ag.get("lead_id") and novo_status_lead:
                    atualizar_lead(str(ag.get("lead_id")), {"status_lead": novo_status_lead})
                    salvar_historico(
                        str(ag.get("lead_id")),
                        usuario.get("nome", ""),
                        novo_status_lead,
                        f"Agendamento atualizado para {novo_status}. {nova_obs.strip()}",
                        "Atualização de agendamento",
                    )
                st.success("Agendamento atualizado com sucesso!")
                st.rerun()


# -------------------------------
# TRANSFERÊNCIA DE LEADS
# -------------------------------
elif pagina == "Transferência de Clientes":
    st.title("🔁 Transferência de Clientes")
    st.caption("Transfira um ou vários clientes para outro atendente, com registro no histórico.")

    df_transferencia = aplicar_escopo_unidade(carregar_leads(), usuario)

    if df_transferencia.empty:
        st.info("Nenhum cliente disponível no seu escopo.")
        st.stop()

    for col in [
        "id", "nome_cliente", "cpf", "telefone", "cidade", "bairro",
        "captador_id", "captador_nome", "status_lead", "data_captacao", "unidade"
    ]:
        if col not in df_transferencia.columns:
            df_transferencia[col] = ""

    atendentees_ativos = [
        u for u in listar_usuarios_ativos()
        if u.get("perfil") == "captador"
    ]

    # Mantém apenas atendentes dentro do escopo do gestor.
    atendentees_escopo = []
    unidades_admin = set(unidades_permitidas_usuario(usuario))
    for atendente in atendentees_ativos:
        unidades_atendente = set(listar_unidades_usuario(str(atendente.get("id", ""))))
        unidade_padrao = (
            atendente.get("unidade_padrao")
            or atendente.get("unidade")
            or atendente.get("unidade_nome")
        )
        if unidade_padrao:
            unidades_atendente.add(unidade_padrao)
        if usuario_eh_geral(usuario) or unidades_admin.intersection(unidades_atendente):
            atendentees_escopo.append(atendente)

    if not atendentees_escopo:
        st.warning("Nenhum atendente ativo disponível dentro do seu escopo.")
        st.stop()

    st.markdown("### 1. Filtrar clientes")
    f1, f2, f3, f4 = st.columns(4)

    with f1:
        atendentes_origem = sorted(
            [x for x in df_transferencia["captador_nome"].fillna("").unique().tolist() if x]
        )
        filtro_captador_origem = st.multiselect(
            "Atendente atual",
            atendentes_origem,
            key="transf_filtro_captador_origem",
        )

    with f2:
        filtro_status = st.multiselect(
            "Status",
            STATUS_LEAD,
            default=STATUS_LEAD,
            key="transf_filtro_status",
        )

    with f3:
        cidades_transferencia = sorted(
            [x for x in df_transferencia["cidade"].fillna("").unique().tolist() if x]
        )
        filtro_cidade = st.multiselect(
            "Cidade",
            cidades_transferencia,
            key="transf_filtro_cidade",
        )

    with f4:
        unidades_transferencia = sorted(
            [x for x in df_transferencia["unidade"].fillna("").unique().tolist() if x]
        )
        filtro_unidade = st.multiselect(
            "Unidade",
            unidades_transferencia,
            key="transf_filtro_unidade",
        )

    f5, f6, f7 = st.columns([1.5, 1, 1])
    with f5:
        busca_transferencia = st.text_input(
            "Buscar por nome, CPF, telefone ou bairro",
            placeholder="Digite parte do nome, CPF, telefone ou bairro...",
            key="transf_busca",
        )
    with f6:
        data_minima = pd.to_datetime(
            df_transferencia["data_captacao"], errors="coerce"
        ).dropna().dt.date.min()
        data_maxima = pd.to_datetime(
            df_transferencia["data_captacao"], errors="coerce"
        ).dropna().dt.date.max()
        data_inicial = st.date_input(
            "Data inicial",
            value=data_minima or date.today(),
            key="transf_data_inicial",
        )
    with f7:
        data_final = st.date_input(
            "Data final",
            value=data_maxima or date.today(),
            key="transf_data_final",
        )

    df_filtrado = df_transferencia.copy()
    df_filtrado["data_captacao_dt"] = pd.to_datetime(
        df_filtrado["data_captacao"], errors="coerce"
    )

    if filtro_captador_origem:
        df_filtrado = df_filtrado[
            df_filtrado["captador_nome"].isin(filtro_captador_origem)
        ]
    if filtro_status:
        df_filtrado = df_filtrado[
            df_filtrado["status_lead"].isin(filtro_status)
        ]
    if filtro_cidade:
        df_filtrado = df_filtrado[
            df_filtrado["cidade"].isin(filtro_cidade)
        ]
    if filtro_unidade:
        df_filtrado = df_filtrado[
            df_filtrado["unidade"].isin(filtro_unidade)
        ]

    if not df_filtrado.empty:
        datas = df_filtrado["data_captacao_dt"].dt.date
        df_filtrado = df_filtrado[
            (datas >= data_inicial) & (datas <= data_final)
        ]

    if busca_transferencia.strip():
        termo = busca_transferencia.strip().lower()
        termo_digitos = apenas_digitos(busca_transferencia)
        mask = pd.Series(False, index=df_filtrado.index)

        for col in ["nome_cliente", "cpf", "telefone", "bairro", "cidade", "captador_nome"]:
            mask = mask | df_filtrado[col].fillna("").astype(str).str.lower().str.contains(
                termo, na=False
            )

        if termo_digitos:
            mask = mask | df_filtrado["cpf"].fillna("").astype(str).apply(
                apenas_digitos
            ).str.contains(termo_digitos, na=False)
            mask = mask | df_filtrado["telefone"].fillna("").astype(str).apply(
                apenas_digitos
            ).str.contains(termo_digitos, na=False)

        df_filtrado = df_filtrado[mask]

    st.caption(f"{len(df_filtrado)} lead(s) encontrado(s).")

    if df_filtrado.empty:
        st.warning("Nenhum cliente encontrado com os filtros selecionados.")
        st.stop()

    df_filtrado = df_filtrado.copy()
    df_filtrado["Selecionar"] = False

    colunas_editor = [
        "Selecionar",
        "nome_cliente",
        "cpf",
        "telefone",
        "cidade",
        "bairro",
        "captador_nome",
        "status_lead",
        "data_captacao",
    ]

    st.markdown("### 2. Selecionar clientes")
    df_editado = st.data_editor(
        preparar_dataframe_exibicao(df_filtrado[colunas_editor]),
        use_container_width=True,
        hide_index=True,
        disabled=[
            "nome_cliente",
            "cpf",
            "telefone",
            "cidade",
            "bairro",
            "captador_nome",
            "status_lead",
            "data_captacao",
        ],
        column_config={
            "Selecionar": st.column_config.CheckboxColumn(
                "Selecionar",
                help="Marque os clientes que deseja transferir.",
                default=False,
            ),
            "nome_cliente": "Cliente",
            "cpf": "CPF",
            "telefone": "Telefone",
            "cidade": "Cidade",
            "bairro": "Bairro",
            "captador_nome": "Atendente atual",
            "status_lead": "Status",
            "data_captacao": "Data da clientes",
        },
        key="transf_editor_leads",
    )

    # O data_editor preserva os índices originais do DataFrame filtrado.
    # Por isso usamos .loc (índice por rótulo), e não .iloc (posição),
    # evitando IndexError quando o filtro retorna poucas linhas com índices altos.
    selecionados_indices = df_editado.index[df_editado["Selecionar"] == True].tolist()
    lead_ids_selecionados = [
        str(df_filtrado.loc[i, "id"])
        for i in selecionados_indices
        if i in df_filtrado.index
    ]

    st.info(f"{len(lead_ids_selecionados)} lead(s) selecionado(s).")

    st.markdown("### 3. Definir novo atendente")
    nomes_atendentees_destino = [c.get("nome") for c in atendentees_escopo]
    novo_captador_nome = st.selectbox(
        "Novo atendente",
        nomes_atendentees_destino,
        key="transf_novo_captador",
    )
    motivo_transferencia = st.text_area(
        "Motivo da transferência",
        placeholder="Ex.: Redistribuição de carteira, mudança de unidade, desligamento...",
        key="transf_motivo",
    )

    confirmar_transferencia = st.checkbox(
        "Confirmo que desejo transferir os clientes selecionados.",
        key="transf_confirmacao",
    )

    if st.button(
        "🔁 Transferir clientes selecionados",
        type="primary",
        disabled=not lead_ids_selecionados,
    ):
        if not confirmar_transferencia:
            st.error("Marque a confirmação antes de transferir.")
        else:
            novo_captador = next(
                (c for c in atendentees_escopo if c.get("nome") == novo_captador_nome),
                None,
            )
            try:
                transferir_leads_em_lote(
                    lead_ids_selecionados,
                    novo_captador,
                    usuario,
                    motivo_transferencia,
                )
                st.success(
                    f"{len(lead_ids_selecionados)} lead(s) transferido(s) "
                    f"para {novo_captador_nome} com sucesso."
                )
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao transferir leads: {e}")



# -------------------------------
# MINHAS PENDÊNCIAS - ATENDENTE
# -------------------------------
elif pagina == "Minhas Pendências":
    st.title("📌 Minhas Pendências")
    st.caption("Consulte pendências atribuídas a você ou à sua unidade e envie os documentos solicitados.")

    dfp = carregar_pendencias()
    dfp = filtrar_pendencias_por_escopo(dfp, usuario)
    dfp = resumo_documentos_pendencias(dfp)

    if dfp.empty:
        st.info("Nenhuma pendência documental para você no momento.")
    else:
        st.markdown("### 🔎 Filtros")
        p1, p2, p3 = st.columns([1.8, 1, 1])
        with p1:
            busca_pend = st.text_input(
                "Cliente, CPF, telefone ou descrição",
                placeholder="Digite parte do nome, CPF, telefone ou descrição...",
                key="minhas_pend_busca_desktop",
            )
        with p2:
            status_pend = st.multiselect(
                "Status",
                STATUS_PENDENCIA,
                default=["Aberta", "Em andamento"],
                key="minhas_pend_status_desktop",
            )
        with p3:
            docs_pend = st.selectbox(
                "Situação dos documentos",
                ["Todos", "Não baixados", "Parcialmente baixados", "Documentos baixados", "Sem documentos"],
                key="minhas_pend_docs_desktop",
            )

        dfp_f = dfp.copy()

        if status_pend:
            dfp_f = dfp_f[dfp_f["status"].fillna("Aberta").isin(status_pend)]

        dfp_f = aplicar_filtro_documentos_df(dfp_f, docs_pend)

        if busca_pend.strip():
            termo = busca_pend.strip().lower()
            mask = pd.Series(False, index=dfp_f.index)
            for col in ["cliente_nome", "cpf", "telefone", "descricao", "tipo_pendencia"]:
                if col in dfp_f.columns:
                    mask = mask | dfp_f[col].fillna("").astype(str).str.lower().str.contains(termo, na=False)
            dfp_f = dfp_f[mask]

        st.caption(f"{len(dfp_f)} pendência(s) encontrada(s).")

        if dfp_f.empty:
            st.warning("Nenhuma pendência encontrada com os filtros selecionados.")
        else:
            for col in ["cliente_nome", "tipo_pendencia", "status", "prioridade", "descricao"]:
                if col not in dfp_f.columns:
                    dfp_f[col] = ""
                dfp_f[col] = dfp_f[col].fillna("").astype(str)

            dfp_f["label_pend"] = (
                dfp_f["cliente_nome"] + " | "
                + dfp_f["tipo_pendencia"] + " | "
                + dfp_f["status"] + " | Prioridade: "
                + dfp_f["prioridade"]
            )

            pend_label = st.selectbox(
                "Selecione a pendência",
                dfp_f["label_pend"].tolist(),
                key="minhas_pend_select_desktop",
            )
            pend = dfp_f[dfp_f["label_pend"] == pend_label].iloc[0]

            st.write(f"**Cliente:** {pend.get('cliente_nome', '')}")
            st.write(f"**Tipo:** {pend.get('tipo_pendencia', '')}")
            st.write(f"**Descrição:** {pend.get('descricao', '')}")
            st.write(
                f"**Prioridade:** {pend.get('prioridade', 'Normal')} | "
                f"**Status:** {pend.get('status', 'Aberta')}"
            )
            st.write(
                f"📎 **Enviados:** {int(pend.get('documentos_enviados', 0))} | "
                f"📥 **Baixados:** {int(pend.get('documentos_baixados', 0))}"
            )

            with st.form("form_minhas_pendencias_desktop", clear_on_submit=True):
                status_atual = pend.get("status", "Aberta")
                novo_status = st.selectbox(
                    "Atualizar status",
                    STATUS_PENDENCIA,
                    index=STATUS_PENDENCIA.index(status_atual) if status_atual in STATUS_PENDENCIA else 0,
                )
                tipo_doc = st.selectbox(
                    "Tipo dos arquivos",
                    listar_tipos_arquivo(),
                    key="tipo_doc_minhas_pend_desktop",
                )
                arquivos_p = st.file_uploader(
                    "📎 Anexar documentos/arquivos",
                    accept_multiple_files=True,
                    type=["pdf", "png", "jpg", "jpeg", "webp"],
                    key="arquivos_minhas_pend_desktop",
                )
                foto_p = st.file_uploader(
                    "📷 Tirar foto ou escolher imagem",
                    accept_multiple_files=False,
                    type=["png", "jpg", "jpeg", "webp"],
                    key="foto_minhas_pend_desktop",
                )
                observacao_p = st.text_area(
                    "Observação",
                    placeholder="Ex.: Cliente entregou o documento solicitado.",
                )
                salvar_p = st.form_submit_button("📎 Enviar / atualizar")

            if salvar_p:
                try:
                    lead_id = str(pend.get("lead_id", ""))
                    arquivos_enviar = lista_arquivos_com_foto(
                        arquivos_p,
                        foto_p,
                        f"foto_pendencia_{lead_id}.jpg",
                    )

                    enviados = 0
                    if arquivos_enviar and lead_id:
                        for arquivo in arquivos_enviar:
                            enviar_arquivo_temporario(
                                lead_id,
                                arquivo,
                                tipo_doc,
                                usuario,
                            )
                            enviados += 1

                    dados_up = {
                        "status": novo_status,
                        "atualizado_em": datetime.now(timezone.utc).isoformat(),
                    }

                    if novo_status == "Resolvida":
                        dados_up["resolvido_em"] = datetime.now(timezone.utc).isoformat()
                        dados_up["resolvido_por"] = usuario.get("nome")

                    atualizar_pendencia(str(pend["id"]), dados_up)

                    if lead_id:
                        texto = f"Pendência atualizada para {novo_status}."
                        if enviados:
                            texto += f" {enviados} documento(s) enviado(s)."
                        if observacao_p.strip():
                            texto += f" Observação: {observacao_p.strip()}"

                        salvar_historico(
                            lead_id,
                            usuario.get("nome", ""),
                            novo_status,
                            texto,
                            "Pendência documental",
                        )

                    st.success("Pendência atualizada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar pendência: {e}")


# -------------------------------
# PENDÊNCIAS DOCUMENTAIS
# -------------------------------
elif pagina == "Pendências":
    st.title("📌 Pendências Documentais")
    st.caption("Solicite documentos aos atendentes e acompanhe downloads da documentação.")

    df_leads_all = aplicar_escopo_unidade(carregar_leads(), usuario)
    usuarios_ativos = listar_usuarios_ativos()
    unidades_permitidas = unidades_permitidas_usuario(usuario)

    tab_criar, tab_lista = st.tabs(["Abrir Pendência", "Acompanhar Pendências"])

    with tab_criar:
        st.subheader("Abrir nova pendência")
        if df_leads_all.empty:
            st.info("Nenhum cliente disponível no seu escopo para abrir pendência.")
        else:
            df_select = df_leads_all.copy()
            for col in ["nome_cliente", "cpf", "telefone", "cidade", "bairro", "captador_nome", "status_lead", "local_captacao", "unidade"]:
                if col not in df_select.columns:
                    df_select[col] = ""
                df_select[col] = df_select[col].fillna("").astype(str)

            st.markdown("#### 🔎 Buscar cliente")
            col_busca1, col_busca2, col_busca3, col_busca4 = st.columns([1.4, 1, 1, 1])
            with col_busca1:
                termo_lead = st.text_input(
                    "Nome, CPF ou telefone",
                    placeholder="Digite parte do nome, CPF ou telefone...",
                    key="pend_busca_lead",
                )
            with col_busca2:
                status_opcoes = sorted([x for x in df_select["status_lead"].dropna().unique().tolist() if x])
                filtro_status_lead = st.selectbox("Status do cliente", ["Todos"] + status_opcoes, key="pend_status_lead")
            with col_busca3:
                bairro_opcoes = sorted([x for x in df_select["bairro"].dropna().unique().tolist() if x])
                filtro_bairro_lead = st.selectbox("Bairro", ["Todos"] + bairro_opcoes, key="pend_bairro_lead")
            with col_busca4:
                atendente_opcoes = sorted([x for x in df_select["captador_nome"].dropna().unique().tolist() if x])
                filtro_captador_lead = st.selectbox("Atendente", ["Todos"] + atendente_opcoes, key="pend_atendente_lead")

            if termo_lead:
                termo_norm = termo_lead.lower().strip()
                termo_dig = apenas_digitos(termo_lead)
                mask_texto = (
                    df_select["nome_cliente"].str.lower().str.contains(termo_norm, na=False) |
                    df_select["bairro"].str.lower().str.contains(termo_norm, na=False) |
                    df_select["cidade"].str.lower().str.contains(termo_norm, na=False) |
                    df_select["local_captacao"].str.lower().str.contains(termo_norm, na=False) |
                    df_select["captador_nome"].str.lower().str.contains(termo_norm, na=False)
                )
                if termo_dig:
                    mask_texto = mask_texto | df_select["cpf"].apply(apenas_digitos).str.contains(termo_dig, na=False) | df_select["telefone"].apply(apenas_digitos).str.contains(termo_dig, na=False)
                df_select = df_select[mask_texto]

            if filtro_status_lead != "Todos":
                df_select = df_select[df_select["status_lead"] == filtro_status_lead]
            if filtro_bairro_lead != "Todos":
                df_select = df_select[df_select["bairro"] == filtro_bairro_lead]
            if filtro_captador_lead != "Todos":
                df_select = df_select[df_select["captador_nome"] == filtro_captador_lead]

            st.caption(f"{len(df_select)} cliente(s) encontrado(s) com os filtros selecionados.")

            if df_select.empty:
                st.warning("Nenhum cliente encontrado. Ajuste a busca ou limpe os filtros.")
                st.stop()

            df_select = df_select.sort_values("data_captacao", ascending=False) if "data_captacao" in df_select.columns else df_select
            df_select["label_lead"] = df_select.apply(label_lead, axis=1)
            with st.form("form_criar_pendencia"):
                lead_label = st.selectbox("Cliente / Cliente", df_select["label_lead"].tolist())
                lead = df_select[df_select["label_lead"] == lead_label].iloc[0]
                colp1, colp2 = st.columns(2)
                with colp1:
                    tipo_pend = st.selectbox("Tipo de pendência", listar_tipos_pendencia())
                    prioridade = st.selectbox("Prioridade", PRIORIDADE_PENDENCIA)
                    prazo = st.date_input("Prazo", date.today() + timedelta(days=3))
                with colp2:
                    visibilidade = st.radio("Visibilidade", ["Todos os atendentes da unidade", "Atendente específico"], horizontal=False)
                    atendentes = [u for u in usuarios_ativos if u.get("perfil") == "captador"]
                    # Mantém somente atendentes do escopo do gestor quando possível
                    atendentees_escopo = []
                    for c in atendentes:
                        us = listar_unidades_usuario(str(c.get("id", "")))
                        unidade_c = c.get("unidade_padrao") or c.get("unidade") or c.get("unidade_nome")
                        if unidade_c and unidade_c not in us:
                            us.append(unidade_c)
                        if not us:
                            us = [lead.get("unidade", "Boa Vista")]
                        if set(us).intersection(set(unidades_permitidas)):
                            atendentees_escopo.append(c)
                    nomes_capt = [c.get("nome") for c in atendentees_escopo]
                    captador_nome = st.selectbox("Atendente", nomes_capt, disabled=(visibilidade == "Todos os atendentes da unidade")) if nomes_capt else ""
                descricao = st.text_area("Descrição da pendência", placeholder="Ex.: Solicitar laudo médico atualizado e comprovante de residência.")
                criar_p = st.form_submit_button("📌 Abrir pendência")

            if criar_p:
                try:
                    atendente_destino = None
                    if visibilidade == "Atendente específico" and captador_nome:
                        atendente_destino = next((c for c in atendentees_escopo if c.get("nome") == captador_nome), None)
                    dados = {
                        "lead_id": str(lead.get("id")),
                        "cliente_nome": lead.get("nome_cliente"),
                        "cpf": lead.get("cpf"),
                        "telefone": lead.get("telefone"),
                        "unidade": lead.get("unidade") or "Boa Vista",
                        "cidade": lead.get("cidade") or lead.get("unidade") or "Boa Vista",
                        "bairro": lead.get("bairro"),
                        "tipo_pendencia": tipo_pend,
                        "descricao": descricao.strip(),
                        "prioridade": prioridade,
                        "prazo": prazo.isoformat(),
                        "status": "Aberta",
                        "visibilidade": "Todos" if visibilidade == "Todos os atendentes da unidade" else "Atendente",
                        "captador_destino_id": str(atendente_destino.get("id")) if atendente_destino else None,
                        "captador_destino_nome": atendente_destino.get("nome") if atendente_destino else None,
                        "criado_por_id": str(usuario.get("id")),
                        "criado_por_nome": usuario.get("nome"),
                    }
                    salvar_pendencia(dados)
                    salvar_historico(str(lead.get("id")), usuario.get("nome", ""), "Pendência aberta", descricao.strip(), "Pendência documental")
                    st.success("Pendência aberta com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao abrir pendência: {e}")

    with tab_lista:
        st.subheader("Acompanhar pendências")
        dfp = carregar_pendencias()
        dfp = filtrar_pendencias_por_escopo(dfp, usuario)
        dfp = resumo_documentos_pendencias(dfp)
        if dfp.empty:
            st.info("Nenhuma pendência encontrada.")
        else:
            # Garante colunas usadas nos filtros
            for col in ["cliente_nome", "cpf", "telefone", "bairro", "unidade", "tipo_pendencia", "prioridade", "status", "visibilidade", "captador_destino_nome", "descricao"]:
                if col not in dfp.columns:
                    dfp[col] = ""
                dfp[col] = dfp[col].fillna("").astype(str)

            st.markdown("#### 🔎 Buscar e filtrar pendências")

            col1, col2, col3 = st.columns([1.6, 1, 1])
            with col1:
                busca_p = st.text_input(
                    "Buscar por cliente, CPF, telefone, atendente ou descrição",
                    placeholder="Digite nome, CPF, telefone, atendente, tipo ou parte da descrição...",
                    key="acompanhar_pend_busca",
                )
            with col2:
                status_p = st.multiselect(
                    "Status da pendência",
                    STATUS_PENDENCIA,
                    default=STATUS_PENDENCIA,
                    key="acompanhar_pend_status",
                )
            with col3:
                docs_p = st.selectbox(
                    "Situação dos documentos",
                    ["Todos", "Não baixados", "Parcialmente baixados", "Documentos baixados", "Sem documentos"],
                    key="acompanhar_pend_docs",
                )

            col4, col5, col6, col7 = st.columns(4)
            with col4:
                unidade_p = st.multiselect(
                    "Unidade",
                    sorted([x for x in dfp["unidade"].fillna("Boa Vista").replace("", "Boa Vista").unique().tolist() if x]),
                    key="acompanhar_pend_unidade",
                )
            with col5:
                tipo_p = st.multiselect(
                    "Tipo de pendência",
                    sorted([x for x in dfp["tipo_pendencia"].dropna().unique().tolist() if x]),
                    key="acompanhar_pend_tipo",
                )
            with col6:
                atendente_p = st.multiselect(
                    "Atendente",
                    sorted([x for x in dfp["captador_destino_nome"].fillna("").replace("", "Todos/Não definido").unique().tolist() if x]),
                    key="acompanhar_pend_atendente",
                )
            with col7:
                bairro_p = st.multiselect(
                    "Bairro",
                    sorted([x for x in dfp["bairro"].fillna("").replace("", "Não informado").unique().tolist() if x]),
                    key="acompanhar_pend_bairro",
                )

            col8, col9, col10 = st.columns(3)
            with col8:
                prioridade_p = st.multiselect(
                    "Prioridade",
                    PRIORIDADE_PENDENCIA,
                    default=PRIORIDADE_PENDENCIA,
                    key="acompanhar_pend_prioridade",
                )
            with col9:
                visibilidade_p = st.selectbox(
                    "Visibilidade",
                    ["Todas", "Todos os atendentes", "Atendente específico"],
                    key="acompanhar_pend_visibilidade",
                )
            with col10:
                prazo_p = st.selectbox(
                    "Prazo",
                    ["Todos", "Vencidas", "Vencem hoje", "Próximas"],
                    key="acompanhar_pend_prazo",
                )

            dfp_f = dfp.copy()

            if status_p:
                dfp_f = dfp_f[dfp_f["status"].fillna("Aberta").isin(status_p)]

            dfp_f = aplicar_filtro_documentos_df(dfp_f, docs_p)

            if unidade_p:
                dfp_f = dfp_f[dfp_f["unidade"].fillna("Boa Vista").replace("", "Boa Vista").isin(unidade_p)]

            if tipo_p:
                dfp_f = dfp_f[dfp_f["tipo_pendencia"].isin(tipo_p)]

            if atendente_p:
                dfp_f = dfp_f[dfp_f["captador_destino_nome"].fillna("").replace("", "Todos/Não definido").isin(atendente_p)]

            if bairro_p:
                dfp_f = dfp_f[dfp_f["bairro"].fillna("").replace("", "Não informado").isin(bairro_p)]

            if prioridade_p:
                dfp_f = dfp_f[dfp_f["prioridade"].fillna("Normal").replace("", "Normal").isin(prioridade_p)]

            if visibilidade_p == "Todos os atendentes":
                dfp_f = dfp_f[dfp_f["visibilidade"].fillna("").str.lower().isin(["todos", "todos_unidade", "todos os atendentes da unidade"])]
            elif visibilidade_p == "Atendente específico":
                dfp_f = dfp_f[dfp_f["visibilidade"].fillna("").str.lower().isin(["atendente", "atendente específico", "atendente especifico"])]

            if prazo_p != "Todos" and "prazo" in dfp_f.columns:
                prazo_dt = pd.to_datetime(dfp_f["prazo"], errors="coerce").dt.date
                hoje_p = date.today()
                if prazo_p == "Vencidas":
                    dfp_f = dfp_f[prazo_dt < hoje_p]
                elif prazo_p == "Vencem hoje":
                    dfp_f = dfp_f[prazo_dt == hoje_p]
                elif prazo_p == "Próximas":
                    dfp_f = dfp_f[prazo_dt > hoje_p]

            if busca_p.strip():
                termo = busca_p.strip().lower()
                termo_dig = apenas_digitos(busca_p)
                mask = pd.Series(False, index=dfp_f.index)

                for c in ["cliente_nome", "cpf", "telefone", "bairro", "captador_destino_nome", "tipo_pendencia", "descricao", "prioridade", "status"]:
                    if c in dfp_f.columns:
                        mask = mask | dfp_f[c].fillna("").astype(str).str.lower().str.contains(termo, na=False)

                if termo_dig:
                    if "cpf" in dfp_f.columns:
                        mask = mask | dfp_f["cpf"].fillna("").astype(str).apply(apenas_digitos).str.contains(termo_dig, na=False)
                    if "telefone" in dfp_f.columns:
                        mask = mask | dfp_f["telefone"].fillna("").astype(str).apply(apenas_digitos).str.contains(termo_dig, na=False)

                dfp_f = dfp_f[mask]

            st.caption(f"{len(dfp_f)} pendência(s) encontrada(s) com os filtros selecionados.")

            if dfp_f.empty:
                st.warning("Nenhuma pendência encontrada com os filtros selecionados.")
            else:
                cols = ["criado_em", "cliente_nome", "cpf", "telefone", "bairro", "unidade", "tipo_pendencia", "prioridade", "prazo", "status", "visibilidade", "captador_destino_nome", "documentos_enviados", "documentos_baixados", "situacao_documentos"]
                cols = [c for c in cols if c in dfp_f.columns]
                st.dataframe(dfp_f[cols].rename(columns={
                    "criado_em":"Criada em", "cliente_nome":"Cliente", "cpf":"CPF", "telefone":"Telefone", "bairro":"Bairro", "unidade":"Unidade",
                    "tipo_pendencia":"Tipo", "prioridade":"Prioridade", "prazo":"Prazo", "status":"Status",
                    "visibilidade":"Visibilidade", "captador_destino_nome":"Atendente",
                    "documentos_enviados":"Docs enviados", "documentos_baixados":"Docs baixados", "situacao_documentos":"Situação docs"
                }), use_container_width=True, hide_index=True)

                dfp_f["label"] = (
                    dfp_f["cliente_nome"].fillna("") + " | " +
                    dfp_f["tipo_pendencia"].fillna("") + " | " +
                    dfp_f["status"].fillna("Aberta") + " | 📎 " +
                    dfp_f["documentos_enviados"].astype(str) + " / 📥 " +
                    dfp_f["documentos_baixados"].astype(str)
                )
                pend_label = st.selectbox("Selecionar pendência para atualizar/baixar documentos", dfp_f["label"].tolist())
                pend = dfp_f[dfp_f["label"] == pend_label].iloc[0]
                st.write(f"**Descrição:** {pend.get('descricao','')}")
                st.write(f"📎 **Enviados:** {int(pend.get('documentos_enviados',0))} | 📥 **Baixados:** {int(pend.get('documentos_baixados',0))}")

                with st.form("form_update_pendencia_gestor"):
                    novo_status = st.selectbox("Status da pendência", STATUS_PENDENCIA, index=STATUS_PENDENCIA.index(pend.get("status", "Aberta")) if pend.get("status", "Aberta") in STATUS_PENDENCIA else 0)
                    obs_status = st.text_area("Observação da atualização", placeholder="Ex.: Documentos recebidos e conferidos.")
                    salvar_status = st.form_submit_button("Salvar status")
                if salvar_status:
                    dados_up = {"status": novo_status, "atualizado_em": datetime.now(timezone.utc).isoformat()}
                    if novo_status == "Resolvida":
                        dados_up["resolvido_em"] = datetime.now(timezone.utc).isoformat()
                        dados_up["resolvido_por"] = usuario.get("nome")
                    atualizar_pendencia(str(pend["id"]), dados_up)
                    if pend.get("lead_id"):
                        salvar_historico(str(pend.get("lead_id")), usuario.get("nome", ""), novo_status, obs_status.strip() or f"Pendência alterada para {novo_status}.", "Pendência documental")
                    st.success("Pendência atualizada.")
                    st.rerun()

                if pend.get("lead_id"):
                    exibir_arquivos_do_lead(str(pend.get("lead_id")), usuario, pend.get("cliente_nome", "cliente"))


# -------------------------------
# ATUALIZAR LEAD - V2
# -------------------------------
elif pagina == "Atualizar Cliente":
    st.title("✏️ Atualizar Cliente")
    st.caption("Busque o cliente, atualize o funil e registre o histórico do atendimento.")
    df = aplicar_escopo_unidade(carregar_leads(), usuario)

    if df.empty:
        st.info("Nenhum cliente encontrado.")
        st.stop()

    termo = st.text_input("Pesquisar por nome, CPF, telefone ou atendente", placeholder="Digite parte do nome, CPF, telefone ou atendente...")
    df_busca = df.copy()
    if termo:
        termo_norm = termo.lower().strip()
        cols_busca = ["nome_cliente", "cpf", "telefone", "captador_nome", "bairro", "status_lead"]
        mask = pd.Series(False, index=df_busca.index)
        for c in cols_busca:
            if c in df_busca.columns:
                mask = mask | df_busca[c].fillna("").astype(str).str.lower().str.contains(termo_norm, na=False)
        df_busca = df_busca[mask]

    if df_busca.empty:
        st.warning("Nenhum cliente encontrado para essa busca.")
        st.stop()

    df_busca["label"] = (
        df_busca["nome_cliente"].fillna("") + " | " +
        df_busca["telefone"].fillna("") + " | " +
        df_busca["bairro"].fillna("") + " | " +
        df_busca["status_lead"].fillna("")
    )
    lead_label = st.selectbox("Selecione o cliente", df_busca["label"].tolist())
    lead = df_busca[df_busca["label"] == lead_label].iloc[0]
    lead_id = str(lead["id"])

    st.markdown("### Ficha do Cliente")
    c1, c2, c3 = st.columns(3)
    c1.metric("Cliente", lead.get("nome_cliente", ""))
    c2.metric("Status", lead.get("status_lead", "Novo"))
    c3.metric("Atendente", lead.get("captador_nome", ""))

    col_a, col_b = st.columns(2)
    with col_a:
        st.write(f"**CPF:** {formatar_cpf(lead.get('cpf','') or '')}")
        st.write(f"**Telefone:** {formatar_telefone(lead.get('telefone','') or '')}")
        st.write(f"**Cidade:** {lead.get('cidade','') or lead.get('unidade','')}")
        st.write(f"**Bairro:** {lead.get('bairro','')}")
        st.write(f"**Local:** {lead.get('local_captacao','')}")
    with col_b:
        st.write(f"**Benefício:** {lead.get('tipo_beneficio','')}")
        st.write(f"**Área:** {lead.get('area_acao','')}")
        data_cap = lead.get("data_captacao")
        st.write(f"**Data clientes:** {data_cap.strftime('%d/%m/%Y %H:%M') if hasattr(data_cap, 'strftime') else data_cap}")
        st.write(f"**Quem atendeu:** {lead.get('quem_atendeu','') or 'Ainda não informado'}")

    exibir_arquivos_do_lead(lead_id, usuario, lead.get("nome_cliente", "cliente"))

    st.markdown("### Atualização do Atendimento")
    with st.form("form_atualizar_lead_v2"):
        col1, col2 = st.columns(2)
        with col1:
            status_atual = lead.get("status_lead", "Novo")
            status_idx = STATUS_LEAD.index(status_atual) if status_atual in STATUS_LEAD else 0
            status = st.selectbox("Status do Cliente", STATUS_LEAD, index=status_idx)

            usuarios = listar_usuarios_ativos()
            nomes_usuarios = [u["nome"] for u in usuarios]
            quem_atendeu_atual = lead.get("quem_atendeu") or ""
            lista_atendentes = [""] + nomes_usuarios
            idx_atendente = lista_atendentes.index(quem_atendeu_atual) if quem_atendeu_atual in lista_atendentes else 0
            quem_atendeu = st.selectbox("Quem atendeu", lista_atendentes, index=idx_atendente)

            st.markdown("#### Dados do agendamento")
            st.caption("Preencha quando o status for Agendado.")
            advogados_agenda = listar_advogados_ativos()
            nomes_advogados = [u.get("nome") for u in advogados_agenda]
            advogado_agenda_nome = st.selectbox("Advogado responsável", [""] + nomes_advogados)
            data_agenda = st.date_input("Data do atendimento", value=date.today())
            hora_inicio_agenda = st.time_input(
                "Hora inicial",
                value=datetime.strptime("09:00", "%H:%M").time(),
            )
            duracao_agenda = st.selectbox(
                "Duração prevista",
                [15, 30, 45, 60, 90, 120],
                index=1,
                format_func=lambda x: f"{x} minutos",
            )
        with col2:
            motivo_atual = lead.get("motivo_perda") or ""
            idx_motivo = MOTIVOS_PERDA.index(motivo_atual) if motivo_atual in MOTIVOS_PERDA else 0
            motivo_perda = st.selectbox("Motivo da perda", MOTIVOS_PERDA, index=idx_motivo)
            observacao_atual = lead.get("observacao") or ""
            observacao_principal = st.text_area("Observação principal do cliente", value=observacao_atual)
            modalidade_agenda = st.selectbox(
                "Modalidade do atendimento",
                MODALIDADES_AGENDAMENTO,
                key="modalidade_agendamento_cliente",
            )

            local_agenda = ""
            link_agenda = ""

            if modalidade_agenda == "Presencial":
                local_agenda = st.text_input(
                    "Local do atendimento",
                    placeholder="Ex.: Escritório Boa Vista, sala 2",
                    key="local_agendamento_cliente",
                )
            elif modalidade_agenda == "Videochamada":
                link_agenda = st.text_input(
                    "Link da reunião",
                    placeholder="Ex.: https://meet.google.com/...",
                    key="link_agendamento_cliente",
                )
            elif modalidade_agenda == "WhatsApp":
                link_agenda = st.text_input(
                    "Número ou link do WhatsApp",
                    placeholder="Ex.: (95) 99999-9999 ou link do WhatsApp",
                    key="whatsapp_agendamento_cliente",
                )
            elif modalidade_agenda == "Telefone":
                st.caption("Para atendimento por telefone, não é necessário informar local ou link.")

            observacao_agenda = st.text_area(
                "Observação do agendamento",
                key="observacao_agendamento_cliente",
            )

        observacao_atendimento = st.text_area(
            "Nova observação do atendimento / histórico",
            placeholder="Ex.: Cliente respondeu, documentos solicitados, atendimento agendado..."
        )
        salvar = st.form_submit_button("💾 Salvar Atualização")

    if salvar:
        if status == "Perdido" and not motivo_perda:
            st.error("Informe o motivo da perda quando o status for Perdido.")
        elif status == "Agendado" and not advogado_agenda_nome:
            st.error("Selecione o advogado responsável.")
        elif status == "Agendado" and modalidade_agenda == "Presencial" and not local_agenda.strip():
            st.error("Informe o local do atendimento presencial.")
        elif status == "Agendado" and modalidade_agenda in ["Videochamada", "WhatsApp"] and not link_agenda.strip():
            st.error("Informe o link ou contato do atendimento.")
        else:
            dados = {
                "status_lead": status,
                "quem_atendeu": quem_atendeu or None,
                "motivo_perda": motivo_perda if status == "Perdido" else None,
                "observacao": observacao_principal.strip(),
            }
            if status == "Convertido" and lead.get("status_lead") != "Convertido":
                dados["data_conversao"] = "now()"
                dados["responsavel_conversao"] = quem_atendeu or usuario["nome"]

            # Supabase não aceita now() como string para timestamptz via update; grava pelo banco se coluna existir usando datetime ISO.
            if dados.get("data_conversao") == "now()":
                from datetime import datetime, timezone
                dados["data_conversao"] = datetime.now(timezone.utc).isoformat()

            try:
                atualizar_lead(lead_id, dados)

                if status == "Agendado":
                    advogado_agenda = next(
                        (u for u in advogados_agenda if u.get("nome") == advogado_agenda_nome),
                        None,
                    )
                    inicio_dt = datetime.combine(data_agenda, hora_inicio_agenda)
                    fim_dt = inicio_dt + timedelta(minutes=int(duracao_agenda))
                    hora_fim_agenda = fim_dt.time()

                    if verificar_conflito_agenda(
                        str(advogado_agenda.get("id")),
                        data_agenda,
                        hora_inicio_agenda,
                        hora_fim_agenda,
                    ):
                        st.error("Esse advogado já possui atendimento nesse horário.")
                        st.stop()

                    salvar_agendamento({
                        "lead_id": lead_id,
                        "cliente_nome": lead.get("nome_cliente"),
                        "telefone": lead.get("telefone"),
                        "tipo_beneficio": lead.get("tipo_beneficio"),
                        "unidade": lead.get("unidade") or "Boa Vista",
                        "cidade": lead.get("cidade") or "",
                        "advogado_id": str(advogado_agenda.get("id")),
                        "advogado_nome": advogado_agenda_nome,
                        "data_agendamento": data_agenda.isoformat(),
                        "hora_inicio": hora_inicio_agenda.strftime("%H:%M"),
                        "hora_fim": hora_fim_agenda.strftime("%H:%M"),
                        "modalidade": modalidade_agenda,
                        "local_atendimento": (
                            local_agenda.strip()
                            if modalidade_agenda == "Presencial"
                            else link_agenda.strip()
                        ),
                        "observacao": observacao_agenda.strip(),
                        "status_agendamento": "Agendado",
                        "criado_por_id": str(usuario.get("id")),
                        "criado_por_nome": usuario.get("nome"),
                    })

                    salvar_historico(
                        lead_id,
                        usuario["nome"],
                        "Agendado",
                        f"Atendimento agendado para {data_agenda.strftime('%d/%m/%Y')} às "
                        f"{hora_inicio_agenda.strftime('%H:%M')} com {advogado_agenda_nome}. "
                        f"Modalidade: {modalidade_agenda}. "
                        f"Local/contato: {(local_agenda.strip() if modalidade_agenda == 'Presencial' else link_agenda.strip()) or 'Não informado'}.",
                        "Agendamento criado",
                    )
                else:
                    texto_hist = observacao_atendimento.strip() or f"Status alterado para {status}."
                    salvar_historico(
                        lead_id,
                        usuario["nome"],
                        status,
                        texto_hist,
                        "Atualização de atendimento",
                    )

                st.success("Cliente atualizado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar lead: {e}")

    st.markdown("### Histórico do Cliente")
    hist = carregar_historico(lead_id)
    if hist.empty:
        st.info("Nenhum histórico registrado para este cliente.")
    else:
        hist_exibir = hist.copy()
        if "criado_em" in hist_exibir.columns:
            hist_exibir["criado_em"] = hist_exibir["criado_em"].dt.strftime("%d/%m/%Y %H:%M")
        cols = ["criado_em", "acao", "usuario_nome", "status", "observacao"]
        cols = [c for c in cols if c in hist_exibir.columns]
        st.dataframe(hist_exibir[cols], use_container_width=True, hide_index=True)

# -------------------------------
# CADASTROS
# -------------------------------
elif pagina == "Cadastros":
    st.title("⚙️ Cadastros")
    st.caption("Cadastre benefícios, locais de clientes, tipos de arquivos e unidades sem precisar alterar o código.")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Benefícios", "Locais de Clientes", "Tipos de Arquivo", "Tipos de Pendência", "Unidades", "Cidades", "Bairros por cidade"])
    with tab1:
        st.subheader("Benefícios")
        with st.form("form_novo_beneficio"):
            nome_beneficio = st.text_input("Novo benefício", placeholder="Ex.: Aposentadoria por invalidez")
            salvar_beneficio = st.form_submit_button("Adicionar benefício")
        if salvar_beneficio:
            if not nome_beneficio.strip():
                st.error("Informe o nome do benefício.")
            else:
                try:
                    criar_beneficio(nome_beneficio)
                    st.success("Benefício cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar benefício: {e}")
        st.dataframe(pd.DataFrame({"Benefícios ativos": listar_beneficios()}), use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Locais de Clientes")
        with st.form("form_novo_local"):
            nome_local = st.text_input("Novo local", placeholder="Ex.: Feira do Nova Cidade")
            salvar_local = st.form_submit_button("Adicionar local")
        if salvar_local:
            if not nome_local.strip():
                st.error("Informe o nome do local.")
            else:
                try:
                    criar_local_captacao(nome_local)
                    st.success("Local cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar local: {e}")
        locais = listar_locais_captacao()
        if locais:
            st.dataframe(pd.DataFrame({"Locais ativos": locais}), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum local cadastrado ainda. O atendente poderá digitar livremente até você cadastrar os principais locais.")

    with tab3:
        st.subheader("Tipos de Arquivo")
        with st.form("form_novo_tipo_arquivo"):
            nome_tipo_arquivo = st.text_input("Novo tipo de arquivo", placeholder="Ex.: Extrato CNIS, Foto do cliente, Comprovante médico")
            salvar_tipo_arquivo = st.form_submit_button("Adicionar tipo de arquivo")
        if salvar_tipo_arquivo:
            if not nome_tipo_arquivo.strip():
                st.error("Informe o tipo de arquivo.")
            else:
                try:
                    criar_tipo_arquivo(nome_tipo_arquivo)
                    st.success("Tipo de arquivo cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar tipo de arquivo: {e}")
        st.dataframe(pd.DataFrame({"Tipos de arquivo ativos": listar_tipos_arquivo()}), use_container_width=True, hide_index=True)


    with tab4:
        st.subheader("Tipos de Pendência")
        with st.form("form_novo_tipo_pendencia"):
            nome_tp = st.text_input("Novo tipo de pendência", placeholder="Ex.: Laudo atualizado")
            salvar_tp = st.form_submit_button("Adicionar tipo")
        if salvar_tp:
            if not nome_tp.strip():
                st.error("Informe o tipo de pendência.")
            else:
                try:
                    criar_tipo_pendencia(nome_tp)
                    st.success("Tipo de pendência cadastrado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar tipo de pendência: {e}")
        st.dataframe(pd.DataFrame({"Tipos de pendência ativos": listar_tipos_pendencia()}), use_container_width=True, hide_index=True)

    with tab5:
        st.subheader("Unidades")
        with st.form("form_nova_unidade"):
            colu1, colu2, colu3 = st.columns(3)
            with colu1:
                nome_unidade = st.text_input("Nome da unidade", placeholder="Ex.: Amazonas")
            with colu2:
                cidade_unidade = st.text_input("Cidade", placeholder="Ex.: Manaus")
            with colu3:
                estado_unidade = st.text_input("Estado", placeholder="Ex.: AM")
            salvar_unidade = st.form_submit_button("Adicionar unidade")
        if salvar_unidade:
            if not nome_unidade.strip() or not cidade_unidade.strip() or not estado_unidade.strip():
                st.error("Informe nome, cidade e estado da unidade.")
            else:
                try:
                    criar_unidade(nome_unidade, cidade_unidade, estado_unidade)
                    st.success("Unidade cadastrada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar unidade: {e}")
        unidades_df = pd.DataFrame(listar_unidades(True))
        if not unidades_df.empty:
            cols_unidades = [c for c in ["nome", "cidade", "estado", "ativo"] if c in unidades_df.columns]
            st.dataframe(unidades_df[cols_unidades], use_container_width=True, hide_index=True)



    with tab6:
        st.subheader("Cidades")
        st.caption("Cadastre cidades para aparecerem nos selects do atendente e no cadastro de usuários.")

        with st.form("form_nova_cidade"):
            cc1, cc2 = st.columns(2)
            with cc1:
                estado_cidade = st.selectbox(
                    "Estado",
                    ["AM", "RR"],
                    format_func=nome_estado_por_uf,
                    key="cad_cidade_estado",
                )
            with cc2:
                nome_cidade = st.text_input("Nova cidade", placeholder="Ex.: Balbina")
            salvar_cidade = st.form_submit_button("Adicionar cidade")

        if salvar_cidade:
            if not nome_cidade.strip():
                st.error("Informe o nome da cidade.")
            else:
                try:
                    criar_cidade(estado_cidade, nome_cidade)
                    st.success("Cidade cadastrada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.warning(f"Não foi possível cadastrar ou a cidade já existe: {e}")

        try:
            cidades_linhas = []
            for uf in ["AM", "RR"]:
                for c in listar_cidades_cadastradas(uf):
                    cidades_linhas.append({"Estado": uf, "Cidade": c})
            cidades_df = pd.DataFrame(cidades_linhas).drop_duplicates().sort_values(["Estado", "Cidade"])
            st.dataframe(cidades_df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.warning(f"Não foi possível listar cidades: {e}")


    with tab7:
        st.subheader("Bairros por cidade")
        st.caption("Cadastre bairros para que o atendente selecione em vez de digitar manualmente.")
        with st.form("form_novo_bairro_cidade"):
            cb1, cb2, cb3 = st.columns(3)
            with cb1:
                estado_bairro = st.selectbox(
                    "Estado",
                    ["AM", "RR"],
                    format_func=nome_estado_por_uf,
                    key="cad_bairro_estado",
                )
            with cb2:
                cidade_bairro = st.selectbox(
                    "Cidade",
                    CIDADES_POR_UF.get(estado_bairro, ["Outro"]),
                    key=f"cad_bairro_cidade_{estado_bairro}",
                )
            with cb3:
                nome_bairro = st.text_input("Bairro", placeholder="Ex.: Centro")
            salvar_bairro = st.form_submit_button("Adicionar bairro")
        if salvar_bairro:
            if not nome_bairro.strip():
                st.error("Informe o nome do bairro.")
            else:
                try:
                    criar_bairro_cidade(estado_bairro, cidade_bairro, nome_bairro)
                    st.success("Bairro cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar bairro: {e}")

        try:
            bairros_df = pd.DataFrame(
                supabase.table(TABELA_BAIRROS)
                .select("estado,cidade,nome,ativo")
                .eq("ativo", True)
                .order("estado")
                .order("cidade")
                .order("nome")
                .execute()
                .data or []
            )
            if bairros_df.empty:
                st.info("Nenhum bairro cadastrado ainda.")
            else:
                st.dataframe(bairros_df.rename(columns={"estado":"Estado", "cidade":"Cidade", "nome":"Bairro", "ativo":"Ativo"}), use_container_width=True, hide_index=True)
        except Exception as e:
            st.warning(f"Não foi possível listar bairros cadastrados: {e}")


# -------------------------------
# USUÁRIOS
# -------------------------------
elif pagina == "Usuários":
    st.title("👥 Usuários")
    st.caption("Gestão de usuários com segurança por perfil e unidade.")

    if not pode_gerenciar_usuarios(usuario):
        st.error("Você não tem permissão para gerenciar usuários.")
        st.stop()

    perfil_admin = usuario.get("perfil")
    PERFIS_USUARIO = perfis_que_usuario_pode_criar(usuario)
    unidades_todas = [u.get("nome") for u in listar_unidades(True) if u.get("nome")]
    unidades_opts = unidades_todas if perfil_admin == "gestor_geral" else [u for u in unidades_permitidas_usuario(usuario) if u in unidades_todas]
    if perfil_admin == "gestor_unidade" and unidades_opts:
        unidades_opts = unidades_opts[:1]
    cidades_opts = cidades_de_unidades(unidades_opts)

    if not unidades_opts and perfil_admin != "gestor_geral":
        if perfil_admin == "gestor_unidade":
            st.warning("Seu usuário Gestor de Unidade não possui uma unidade ativa vinculada. Peça ao Gestor Regional ou Geral para ajustar o cadastro.")
        else:
            st.warning("Seu usuário Gestor Regional não possui unidades ativas vinculadas. Peça ao Gestor Geral para ajustar o cadastro.")
        st.stop()

    if perfil_admin == "gestor_geral":
        st.info("Gestor geral: pode criar e editar usuários de todas as unidades.")
    elif perfil_admin == "gestor_regional":
        st.info("Gestor regional: pode criar gestores de unidade, supervisores, atendentes e usuários de pendência nas unidades liberadas.")
    else:
        st.info("Gestor de unidade: pode criar e editar supervisores, atendentes e usuários de pendência somente da própria unidade.")

    # Mensagens rápidas após salvar/criar usuário.
    # Como o app usa st.rerun(), o st.success comum some rapidamente.
    if st.session_state.get("mensagem_usuario_sucesso"):
        st.success(st.session_state.pop("mensagem_usuario_sucesso"))
    if st.session_state.get("mensagem_usuario_erro"):
        st.error(st.session_state.pop("mensagem_usuario_erro"))

    tab_criar, tab_editar, tab_lista = st.tabs(["➕ Criar usuário", "✏️ Editar usuário", "📋 Lista de usuários"])

    with tab_criar:
        st.subheader("Criar novo usuário")
        with st.form("form_usuario_criar"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome", key="criar_nome")
                email = st.text_input("E-mail", key="criar_email")
            with col2:
                senha = st.text_input("Senha", type="password", key="criar_senha")
                perfil_novo = st.selectbox("Perfil", PERFIS_USUARIO, format_func=rotulo_perfil_usuario, key="criar_perfil")

                if perfil_novo == "gestor_geral":
                    unidades_usuario = unidades_todas
                    st.multiselect(
                        "Unidades liberadas",
                        unidades_todas,
                        default=unidades_todas,
                        disabled=True,
                        help="Gestor geral vê todas as unidades automaticamente.",
                        key="criar_unidades_geral",
                    )
                    cidades_usuario = cidades_de_unidades(unidades_todas)
                    st.multiselect(
                        "Cidades liberadas",
                        cidades_usuario,
                        default=cidades_usuario,
                        disabled=True,
                        help="Gestor geral vê todas as cidades automaticamente.",
                        key="criar_cidades_geral",
                    )
                else:
                    if perfil_admin == "gestor_unidade":
                        unidades_usuario = unidades_opts[:1]
                        st.selectbox(
                            "Unidade liberada",
                            unidades_opts,
                            index=0,
                            disabled=True,
                            key="criar_unidade_fixa_gestor_unidade",
                            help="O Gestor de Unidade só pode criar usuários na própria unidade.",
                        )
                    else:
                        unidades_usuario = st.multiselect(
                            "Unidades liberadas",
                            unidades_opts,
                            default=unidades_opts[:1] if unidades_opts else [],
                            key="criar_unidades",
                            help="Selecione somente unidades dentro do seu escopo."
                        )

                    cidades_disponiveis_criar = cidades_de_unidades(unidades_usuario or unidades_opts)

                    if perfil_admin == "gestor_unidade" and len(cidades_disponiveis_criar) == 1:
                        cidades_usuario = cidades_disponiveis_criar
                        st.selectbox(
                            "Cidade liberada",
                            cidades_disponiveis_criar,
                            index=0,
                            disabled=True,
                            key="criar_cidade_fixa_gestor_unidade",
                        )
                    else:
                        cidades_usuario = st.multiselect(
                            "Cidades liberadas",
                            cidades_disponiveis_criar,
                            default=cidades_disponiveis_criar[:1] if cidades_disponiveis_criar else [],
                            key="criar_cidades",
                            help="Selecione uma ou mais cidades dentro das unidades liberadas."
                        )
            criar = st.form_submit_button("Criar Usuário")

        if criar:
            if not nome or not email or not senha:
                st.error("Preencha nome, e-mail e senha.")
            elif perfil_novo not in PERFIS_USUARIO:
                st.error("Você não tem permissão para criar usuário com esse perfil.")
            elif perfil_novo != "gestor_geral" and not unidades_usuario:
                st.error("Selecione ao menos uma unidade para o usuário.")
            elif perfil_novo != "gestor_geral" and not cidades_usuario:
                st.error("Selecione ao menos uma cidade para o usuário.")
            else:
                try:
                    resp_user = supabase.table(TABELA_USUARIOS).insert({
                        "nome": normalizar_texto(nome),
                        "email": email.strip().lower(),
                        "senha": senha,
                        "perfil": perfil_novo,
                        "ativo": True,
                        "unidade_padrao": unidades_usuario[0] if unidades_usuario else None,
                    }).execute()
                    novo_usuario_id = (resp_user.data or [{}])[0].get("id") if hasattr(resp_user, "data") else None
                    if novo_usuario_id:
                        vincular_usuario_unidades(novo_usuario_id, unidades_usuario)
                        vincular_usuario_cidades(novo_usuario_id, cidades_usuario)
                    st.session_state["mensagem_usuario_sucesso"] = f"Usuário {normalizar_texto(nome)} criado com sucesso."
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao criar usuário: {e}")

    with tab_editar:
        st.subheader("Editar usuário existente")
        usuarios_todos = filtrar_usuarios_por_escopo_admin(listar_usuarios_todos(), usuario)
        if not usuarios_todos:
            st.info("Nenhum usuário encontrado dentro do seu escopo.")
        else:
            busca_usuario = st.text_input("Buscar por nome ou e-mail", key="buscar_usuario_editar")
            usuarios_filtrados = usuarios_todos
            if busca_usuario:
                termo = busca_usuario.strip().lower()
                usuarios_filtrados = [
                    u for u in usuarios_todos
                    if termo in str(u.get("nome", "")).lower() or termo in str(u.get("email", "")).lower()
                ]

            if not usuarios_filtrados:
                st.warning("Nenhum usuário encontrado para essa busca.")
            else:
                def label_usuario(u):
                    ativo_txt = "Ativo" if u.get("ativo", True) else "Inativo"
                    return f"{u.get('nome','')} | {u.get('email','')} | {rotulo_perfil_usuario(u.get('perfil',''))} | {ativo_txt}"

                labels = [label_usuario(u) for u in usuarios_filtrados]
                escolhido = st.selectbox("Selecionar usuário", labels, key="usuario_para_editar")
                usuario_edit = usuarios_filtrados[labels.index(escolhido)]
                usuario_id = str(usuario_edit.get("id"))

                if not usuario_dentro_do_escopo_admin(usuario, usuario_edit):
                    st.error("Você não tem permissão para editar este usuário.")
                    st.stop()

                unidades_atual = listar_unidades_usuario(usuario_id)
                if not unidades_atual and usuario_edit.get("unidade_padrao"):
                    unidades_atual = [usuario_edit.get("unidade_padrao")]
                cidades_atual = listar_cidades_usuario(usuario_id)

                with st.form("form_usuario_editar"):
                    col1, col2 = st.columns(2)
                    with col1:
                        nome_edit = st.text_input("Nome", value=usuario_edit.get("nome") or "")
                        email_edit = st.text_input("E-mail", value=usuario_edit.get("email") or "")
                        alterar_senha = st.checkbox("Alterar senha", value=False)
                        nova_senha = st.text_input("Nova senha", type="password", disabled=not alterar_senha)
                    with col2:
                        perfil_atual = usuario_edit.get("perfil") or "captador"
                        if perfil_atual == "atendente":
                            perfil_atual = "captador"
                        perfis_edicao = PERFIS_USUARIO.copy()
                        if perfil_admin == "gestor_geral" and perfil_atual not in perfis_edicao:
                            perfis_edicao.append(perfil_atual)
                        if perfil_atual not in perfis_edicao:
                            perfis_edicao = [perfil_atual] + perfis_edicao
                        idx_perfil = perfis_edicao.index(perfil_atual) if perfil_atual in perfis_edicao else 0
                        perfil_edit = st.selectbox("Perfil", perfis_edicao, index=idx_perfil, format_func=rotulo_perfil_usuario)
                        ativo_edit = st.selectbox(
                            "Status do usuário",
                            ["Ativo", "Inativo"],
                            index=0 if usuario_edit.get("ativo", True) else 1,
                        )
                        unidades_validas = [u for u in unidades_atual if u in unidades_opts]

                        if perfil_edit == "gestor_geral":
                            unidades_edit = unidades_todas
                            st.multiselect(
                                "Unidades liberadas",
                                unidades_todas,
                                default=unidades_todas,
                                disabled=True,
                                help="Gestor geral vê todas as unidades automaticamente.",
                                key="editar_unidades_geral",
                            )
                            cidades_edit = cidades_de_unidades(unidades_todas)
                            st.multiselect(
                                "Cidades liberadas",
                                cidades_edit,
                                default=cidades_edit,
                                disabled=True,
                                help="Gestor geral vê todas as cidades automaticamente.",
                                key="editar_cidades_geral",
                            )
                        else:
                            if perfil_admin == "gestor_unidade":
                                unidades_edit = unidades_opts[:1]
                                st.selectbox(
                                    "Unidade liberada",
                                    unidades_opts,
                                    index=0,
                                    disabled=True,
                                    key="editar_unidade_fixa_gestor_unidade",
                                    help="O Gestor de Unidade não pode mover usuários para outra unidade.",
                                )
                            else:
                                unidades_edit = st.multiselect(
                                    "Unidades liberadas",
                                    unidades_opts,
                                    default=unidades_validas or (unidades_opts[:1] if unidades_opts else []),
                                    help="Selecione apenas as unidades dentro do seu escopo."
                                )

                            cidades_disponiveis_edit = cidades_de_unidades(unidades_edit or unidades_opts)
                            cidades_validas = [c for c in cidades_atual if c in cidades_disponiveis_edit]

                            if perfil_admin == "gestor_unidade" and len(cidades_disponiveis_edit) == 1:
                                cidades_edit = cidades_disponiveis_edit
                                st.selectbox(
                                    "Cidade liberada",
                                    cidades_disponiveis_edit,
                                    index=0,
                                    disabled=True,
                                    key="editar_cidade_fixa_gestor_unidade",
                                )
                            else:
                                cidades_edit = st.multiselect(
                                    "Cidades liberadas",
                                    cidades_disponiveis_edit,
                                    default=cidades_validas or (cidades_disponiveis_edit[:1] if cidades_disponiveis_edit else []),
                                    help="Selecione uma ou mais cidades dentro das unidades liberadas."
                                )
                    salvar_edit = st.form_submit_button("💾 Salvar alterações")

                if salvar_edit:
                    if perfil_edit == "atendente":
                        perfil_edit = "captador"

                    if not nome_edit or not email_edit:
                        st.error("Nome e e-mail são obrigatórios.")
                    elif alterar_senha and not nova_senha:
                        st.error("Informe a nova senha ou desmarque a opção Alterar senha.")
                    elif perfil_edit not in PERFIS_USUARIO:
                        st.error("Você não tem permissão para atribuir esse perfil.")
                    elif perfil_admin == "gestor_unidade" and perfil_edit not in ["captador", "pendencia", "supervisor"]:
                        st.error("Gestor de Unidade só pode atribuir os perfis Atendente, Pendência ou Supervisor.")
                    elif perfil_edit != "gestor_geral" and not unidades_edit:
                        st.error("Selecione ao menos uma unidade para o usuário.")
                    elif perfil_edit != "gestor_geral" and not cidades_edit:
                        st.error("Selecione ao menos uma cidade para o usuário.")
                    else:
                        dados_update = {
                            "nome": normalizar_texto(nome_edit),
                            "email": email_edit.strip().lower(),
                            "perfil": perfil_edit,
                            "ativo": ativo_edit == "Ativo",
                            "unidade_padrao": unidades_edit[0] if unidades_edit else None,
                        }
                        if alterar_senha:
                            dados_update["senha"] = nova_senha
                        try:
                            atualizar_usuario(usuario_id, dados_update)
                            substituir_usuario_unidades(usuario_id, unidades_edit)
                            substituir_usuario_cidades(usuario_id, cidades_edit)
                            st.session_state["mensagem_usuario_sucesso"] = f"Usuário {normalizar_texto(nome_edit)} atualizado com sucesso."
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar usuário: {e}")

    with tab_lista:
        st.subheader("Usuários cadastrados")
        usuarios = filtrar_usuarios_por_escopo_admin(listar_usuarios_todos(), usuario)
        dfu = pd.DataFrame(usuarios)
        if dfu.empty:
            st.info("Nenhum usuário cadastrado dentro do seu escopo.")
        else:
            if "id" in dfu.columns:
                def texto_unidades_liberadas(row):
                    perfil_row = row.get("perfil", "")
                    if perfil_row in ["gestor_geral", "gestor"]:
                        return "Todas"
                    unidades_row = listar_unidades_usuario(str(row.get("id", "")))
                    return ", ".join(unidades_row) if unidades_row else (row.get("unidade_padrao") or "Boa Vista")

                dfu["unidades_liberadas"] = dfu.apply(texto_unidades_liberadas, axis=1)

                def texto_cidades_liberadas(row):
                    perfil_row = row.get("perfil", "")
                    if perfil_row in ["gestor_geral", "gestor"]:
                        return "Todas"
                    cidades_row = listar_cidades_usuario(str(row.get("id", "")))
                    return ", ".join(cidades_row) if cidades_row else "Todas da unidade"

                dfu["cidades_liberadas"] = dfu.apply(texto_cidades_liberadas, axis=1)

            cols = ["nome", "email", "perfil", "ativo", "unidade_padrao", "unidades_liberadas", "cidades_liberadas"]
            cols = [c for c in cols if c in dfu.columns]
            dfu_exibir = dfu[cols].copy()
            if "perfil" in dfu_exibir.columns:
                dfu_exibir["perfil"] = dfu_exibir["perfil"].apply(rotulo_perfil_usuario)
            st.dataframe(dfu_exibir, use_container_width=True, hide_index=True)
