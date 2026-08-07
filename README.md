# V360 Molina — App de Relatório (dark, rebuild)

App Streamlit reescrito do zero com o **design dark dos painéis de TV** e uma
camada de dados mais leve. Substitui o `app 55.py` + `relatorio_fase1.py` +
`painel_executivo.py` + `insights.py`.

## Estrutura

| Arquivo | Papel |
|---|---|
| `app.py` | Entrada: login, menu lateral, filtros, roteamento, rodapé. |
| `data.py` | Camada de dados. Só as colunas usadas (sem `notes`/`description`), fuso Manaus embutido. |
| `theme.py` | Design system dark: tokens de cor da TV, CSS, cards KPI, pills, donut, layout Plotly. |
| `graficos.py` | Barras/barras-h/agrupadas reutilizáveis, já no tema. |
| `regras.py` | Regras de negócio (status, indicadores, subtipos de pendência, funil). |
| `export.py` | Export Excel com **mascaramento** de CPF/NB/senha. |
| `auth.py` | Login por e-mail/senha + escopo de unidades por usuário. |
| `pagina_tv.py` | Console "TV Operacional": abre todos os painéis de `pages/` num lugar só. |
| `pagina_*.py` | Executivo, Insights, Metas, Mapa, Colaboradores. |
| `pages/` | Seus painéis de TV (michelle, rodrigo, compensa…) + templates HTML. **Intactos.** |
| `painel_tv_operacional.py` | Motor do Painel Operacional ADM (tela cheia via `?setor=`). |
| `.streamlit/secrets.toml.example` | Modelo de Secrets (Supabase + usuários). |
| `requirements.txt` | Pins obrigatórios (Python 3.12; `pyarrow==16.1.0`). |

## Login e acesso por unidade
- Formulário de **e-mail + senha**. Usuários ficam em `st.secrets["usuarios"]`
  (nunca no código). Veja `.streamlit/secrets.toml.example`.
- `unidades = "*"` → vê tudo (master). `unidades = ["ATRIUM", ...]` → só essas.
  O filtro se aplica a todas as telas e ao seletor de Escritório.
- Master já configurado no exemplo: `alexandre.brito@molinaadvogado.adv.br`.

## TV Operacional (tudo num menu só)
- O menu **📺 TV Operacional** lista cada painel de `pages/` como cartão com
  botão "▶ Abrir na TV" — some a bagunça do menu automático do Streamlit
  (escondido via CSS).
- Também traz o **Painel Operacional ADM por unidade** (links `?setor=adm&unidade=…`).
- Para colocar um painel novo: jogue o `.py` em `pages/` e adicione uma linha
  em `TVS` no `pagina_tv.py`.

## O que ficou mais rápido
- `carregar_view` não usa mais `select("*")`: puxa só o allowlist de colunas de
  `data.COLUNAS`. Menos payload e **nunca** traz os campos sensíveis/pesados.
- Datas timestamptz convertidas p/ Manaus **uma vez** no carregamento.

## Fuso (America/Manaus)
- `data.hoje()` / `data.agora()` — nunca `date.today()`/`datetime.now()` puros.
- Colunas de **momento** (creation_date, data_conclusao…) → convertidas p/ Manaus.
- Colunas de **calendário** (`deadline`, `mes_referencia`) → **não** convertidas
  (senão empurram 1 dia).

## Deploy (Streamlit Cloud)
1. Suba a pasta no repositório.
2. Settings → Advanced → Python **3.12**.
3. Secrets: `SUPABASE_URL`, `SUPABASE_KEY`, `APP_PASSWORD`.
4. Se tiver o `painel_tv_operacional.py`, é só colocar ao lado — o menu
   "📺 TV Operacional" liga sozinho.

> Precisa do `indicadores_fase1.csv` só se você religar as 21 seções da Fase 1.
> A versão atual do Executivo usa as regras validadas direto de `regras.py`.

## Teste
`python _stubs/run_smoke.py` roda o app com dados fictícios e confirma que todas
as páginas renderizam sem erro (a pasta `_stubs/` é só para teste — não precisa
subir no deploy).
