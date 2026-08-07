# V360 API — cérebro do Assistente

Serve `ia_tools` + `ia_modelo` por HTTP. Clientes: a Streamlit e o app do gestor.

## Render
- Root Directory: `api`
- Build:  `pip install -r requirements.txt`
- Start:  `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/saude`
- Plano **Starter** (o Free dorme e acorda em dezenas de segundos)

## Variáveis de ambiente
| Nome | Para quê |
|---|---|
| `SUPABASE_URL` | banco |
| `SUPABASE_KEY` | service_role |
| `MOONSHOT_API_KEY` | modelo em uso |
| `ANTHROPIC_API_KEY` | rota alternativa (opcional) |
| `JWT_SECRET` | assina o token — string longa e aleatória |
| `ORIGENS_PERMITIDAS` | domínios do front, separados por vírgula |
| `MASTER_EMAIL` / `MASTER_SENHA` | bootstrap, igual ao Secrets da Streamlit |

## Teste depois do deploy
```
curl https://SUA-API.onrender.com/saude
curl -X POST https://SUA-API.onrender.com/entrar \
  -H 'content-type: application/json' \
  -d '{"email":"...","senha":"..."}'
```
