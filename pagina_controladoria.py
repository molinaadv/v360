"""
V360 · CONTROLADORIA INTELIGENTE
Central de alertas, filas e cobrança escalonada.

Lê: vw_controladoria_kpis, vw_controladoria_ocorrencias, vw_controladoria_setores
Escreve: só ações humanas (justificativa, tratado, nova regra) via RPC.
Envio de mensagem NÃO sai daqui — "Cobrar novamente" chama o webhook do n8n.

Deploy: pages/ do app v360-relatorios. Secrets: SUPABASE_URL, SUPABASE_KEY.
"""

import requests
import pandas as pd
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from supabase import create_client

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
TZ = ZoneInfo("America/Manaus")
WEBHOOK_COBRAR = st.secrets.get("N8N_WEBHOOK_COBRAR", "")   # .../webhook/v360-cobrar
USUARIO = st.secrets.get("USUARIO_ATUAL", "Administrador")

st.set_page_config(page_title="V360 · Controladoria", page_icon="🛡️", layout="wide")

# Tokens dark do design system V360 (§4 da base de conhecimento).
# Para voltar ao claro do protótipo: trocar este bloco inteiro, nada mais.
CSS = """
<style>
:root{--bg:#0b1220;--panel:#141d2e;--panel2:#1b2740;--line:#26324d;--ink:#f2f6ff;
--muted:#93a1bd;--dim:#6b7a99;--accent:#5b8cff;--warn:#f5a524;--ok:#2fce8f;
--crit:#ef7a7a;--roxo:#8b7bff}
[data-testid="stHeader"],[data-testid="stDecoration"]{display:none;min-height:0!important}
[data-testid="stAppViewContainer"]>.main{padding-top:0}
.stApp{background:var(--bg);color:var(--ink)}
.v-h1{font-size:30px;font-weight:800;color:var(--ink);margin:6px 0 2px}
.v-sub{color:var(--muted);font-size:14px;margin-bottom:18px}
.v-kpi{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:14px 16px}
.v-kpi .lb{color:var(--muted);font-size:12px}
.v-kpi .vl{font-size:28px;font-weight:850;margin-top:6px}
.v-kpi .sm{color:var(--dim);font-size:11px;margin-top:4px}
.v-card{background:var(--panel);border:1px solid var(--line);border-left:5px solid var(--warn);
border-radius:14px;padding:16px;margin-bottom:12px}
.v-card.critico{border-left-color:var(--crit)}
.v-card.alerta{border-left-color:var(--warn)}
.v-card.atencao{border-left-color:var(--accent)}
.v-card.fechada{border-left-color:var(--ok);opacity:.75}
.v-tt{font-weight:850;font-size:17px}
.v-ds{color:var(--muted);font-size:13px;margin-top:2px}
.v-bd{padding:4px 10px;border-radius:999px;font-size:11px;font-weight:850;float:right}
.bd-critico{background:#3a1a1f;color:#ff9a9a}
.bd-alerta{background:#3a2d13;color:#ffc766}
.bd-atencao{background:#16283f;color:#8fbaff}
.bd-fechada{background:#123528;color:#6fe0b0}
.v-st{display:flex;gap:10px;margin:14px 0;flex-wrap:wrap}
.v-st div{background:var(--panel2);border:1px solid var(--line);border-radius:11px;
padding:8px 12px;min-width:104px}
.v-st .l{font-size:11px;color:var(--muted)}
.v-st .v{font-size:17px;font-weight:850;margin-top:2px}
.v-mt{font-size:12px;color:var(--dim);line-height:1.7}
.v-bar{height:7px;background:#0e1626;border-radius:99px;overflow:hidden;margin-top:6px}
.v-bar span{display:block;height:100%}
.v-sec{background:var(--panel);border:1px solid var(--line);border-radius:14px;
padding:12px 14px;margin-bottom:10px}
.v-ai{background:linear-gradient(135deg,#16305c,#2b4ea8);border-radius:15px;padding:16px;
color:#e9f1ff;font-size:13px;line-height:1.6}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------
# DADOS
# ----------------------------------------------------------------------
@st.cache_resource
def _cli():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


@st.cache_data(ttl=120)
def carregar():
    sb = _cli()
    kpis = pd.DataFrame(sb.table("vw_controladoria_kpis").select("*").execute().data)
    ocs = pd.DataFrame(sb.table("vw_controladoria_ocorrencias").select("*")
                       .order("faixa_atual").execute().data)
    setores = pd.DataFrame(sb.table("vw_controladoria_setores").select("*").execute().data)
    return kpis, ocs, setores


def rpc(nome, params):
    _cli().rpc(nome, params).execute()
    st.cache_data.clear()


try:
    kpis, ocs, setores = carregar()
except Exception as e:
    st.error(f"Não consegui ler o Supabase: {e}")
    st.stop()

k = kpis.iloc[0].to_dict() if not kpis.empty else {}
agora = datetime.now(TZ)

# ----------------------------------------------------------------------
# HEADER + KPIs
# ----------------------------------------------------------------------
c1, c2 = st.columns([4, 1])
with c1:
    st.markdown('<div class="v-h1">🛡️ Controladoria Inteligente</div>', unsafe_allow_html=True)
    st.markdown('<div class="v-sub">Central de alertas, acompanhamento de filas e '
                'comunicação automática com responsáveis e gestores.</div>',
                unsafe_allow_html=True)
with c2:
    st.write("")
    nova = st.button("➕ Nova regra", use_container_width=True, type="primary")

CARDS = [
    ("Alertas críticos", int(k.get("criticos", 0)), "var(--crit)",
     f"{int(k.get('pioraram', 0))} pioraram desde ontem"),
    ("Em atenção", int(k.get("atencao", 0)) + int(k.get("alertas", 0)), "var(--warn)",
     f"{int(k.get('regras_ativas', 0))} filas monitoradas"),
    ("Normalizados hoje", int(k.get("normalizados_hoje", 0)), "var(--ok)", "Ocorrências encerradas"),
    ("Pendências monitoradas", int(k.get("pendencias_monitoradas", 0)), "var(--ink)", "Todas as filas"),
    ("Sem resposta", int(k.get("sem_resposta", 0)), "var(--roxo)", "Aguardando retorno"),
    ("Regras ativas", int(k.get("regras_ativas", 0)), "var(--accent)", "3 verificações por dia"),
]
cols = st.columns(6)
for col, (lb, vl, cor, sm) in zip(cols, CARDS):
    col.markdown(
        f'<div class="v-kpi"><div class="lb">{lb}</div>'
        f'<div class="vl" style="color:{cor}">{vl}</div>'
        f'<div class="sm">{sm}</div></div>', unsafe_allow_html=True)

st.write("")
esq, dir_ = st.columns([1.45, 0.9])

# ----------------------------------------------------------------------
# CENTRAL DE ALERTAS
# ----------------------------------------------------------------------
with esq:
    st.markdown("### Central de alertas")
    abas = st.tabs(["Todos", "Críticos", "Atenção", "Resolvidos"])
    filtros = {0: None, 1: ["critico"], 2: ["alerta", "atencao"], 3: "fechadas"}

    for i, aba in enumerate(abas):
        with aba:
            if ocs.empty:
                st.info("Nenhuma ocorrência registrada ainda. "
                        "Rode o motor uma vez para popular.")
                continue

            f = filtros[i]
            if f == "fechadas":
                df = ocs[ocs["situacao"] == "fechada"]
            elif f:
                df = ocs[(ocs["situacao"] == "aberta") & (ocs["faixa_atual"].isin(f))]
            else:
                df = ocs[ocs["situacao"] == "aberta"]

            if df.empty:
                st.success("Nada por aqui. Fila limpa.")
                continue

            ordem = {"critico": 0, "alerta": 1, "atencao": 2}
            df = df.sort_values(
                by="faixa_atual", key=lambda s: s.map(ordem).fillna(9))

            for _, r in df.iterrows():
                fechada = r["situacao"] == "fechada"
                faixa = "fechada" if fechada else r["faixa_atual"]
                rot = {"critico": "CRÍTICO", "alerta": "ALERTA",
                       "atencao": "ATENÇÃO", "fechada": "RESOLVIDO"}[faixa]
                var = int(r["variacao"] or 0)
                cor_var = "var(--crit)" if var > 0 else "var(--ok)"
                sinal = f"+{var}" if var > 0 else str(var)

                meta = []
                if r.get("responsavel_nome"):
                    meta.append(f"Responsável: {r['responsavel_nome']}")
                if r.get("gestor_nome"):
                    meta.append(f"Gestor: {r['gestor_nome']}")
                if not fechada and r.get("dias_aberta") is not None:
                    meta.append(f"{int(r['dias_aberta'])} dias sem normalização")
                if r.get("cobrancas"):
                    meta.append(f"{int(r['cobrancas'])} cobrança(s)")
                ultima = r.get("ultima_verificacao")
                linha2 = (f"Última verificação: {pd.to_datetime(ultima).tz_convert(TZ):%d/%m %H:%M}"
                          if ultima else "Ainda não verificada")

                html = (
                    f'<div class="v-card {faixa}">'
                    f'<span class="v-bd bd-{faixa}">{rot}</span>'
                    f'<div class="v-tt">{r["regra_nome"]}</div>'
                    f'<div class="v-ds">{r.get("descricao") or ""}</div>'
                    f'<div class="v-st">'
                    f'<div><div class="l">Quantidade atual</div><div class="v">{int(r["abertas_atual"] or 0)}</div></div>'
                    f'<div><div class="l">Limite</div><div class="v">{int(r["limite"] or 0)}</div></div>'
                    f'<div><div class="l">Ontem</div><div class="v">{int(r["abertas_ontem"] or 0)}</div></div>'
                    f'<div><div class="l">Variação</div><div class="v" style="color:{cor_var}">{sinal}</div></div>'
                    f'<div><div class="l">Vencidas</div><div class="v" style="color:var(--crit)">{int(r["atrasadas_atual"] or 0)}</div></div>'
                    f'</div>'
                    f'<div class="v-mt">{" • ".join(meta)}<br>{linha2}</div>'
                    + (f'<div class="v-mt">📝 <i>{r["justificativa"]}</i> — {r.get("justificada_por","")}</div>'
                       if r.get("justificativa") else "")
                    + '</div>'
                )
                st.markdown(html, unsafe_allow_html=True)

                if not fechada:
                    b1, b2, b3 = st.columns(3)
                    oid = int(r["ocorrencia_id"])
                    if b1.button("📣 Cobrar novamente", key=f"cb{oid}", use_container_width=True):
                        if not WEBHOOK_COBRAR:
                            st.warning("Webhook do n8n não configurado nos Secrets.")
                        else:
                            try:
                                requests.post(WEBHOOK_COBRAR, json={
                                    "ocorrencia_id": oid, "usuario": USUARIO}, timeout=15)
                                st.success("Cobrança disparada pelo n8n.")
                            except Exception as e:
                                st.error(f"Falhou: {e}")
                    with b2.popover("📝 Justificativa", use_container_width=True):
                        txt = st.text_area("Motivo", key=f"jt{oid}",
                                           value=r.get("justificativa") or "")
                        if st.button("Salvar", key=f"js{oid}"):
                            rpc("fn_controladoria_justificar",
                                {"p_ocorrencia_id": oid, "p_texto": txt, "p_usuario": USUARIO})
                            st.rerun()
                    if b3.button("✅ Marcar como tratado", key=f"tr{oid}", use_container_width=True):
                        rpc("fn_controladoria_tratar",
                            {"p_ocorrencia_id": oid, "p_usuario": USUARIO})
                        st.rerun()
                st.divider()

# ----------------------------------------------------------------------
# SITUAÇÃO POR SETOR + RESUMO
# ----------------------------------------------------------------------
with dir_:
    st.markdown("### Situação por setor")
    if setores.empty:
        st.caption("Cadastre as regras para ver as filas aqui.")
    else:
        for _, s in setores.sort_values("abertas", ascending=False).iterrows():
            pct = int(s.get("pct_do_teto") or 0)
            cor = ("var(--crit)" if s.get("faixa") == "critico" else
                   "var(--warn)" if s.get("faixa") == "alerta" else
                   "var(--accent)" if s.get("faixa") == "atencao" else "var(--ok)")
            st.markdown(
                f'<div class="v-sec"><b>{s["setor"]}</b>'
                f'<span style="float:right;font-weight:850">{int(s["abertas"] or 0)}</span>'
                f'<div class="v-bar"><span style="width:{pct}%;background:{cor}"></span></div>'
                f'<div class="v-mt">{int(s["atrasadas"] or 0)} vencidas · teto {int(s["lim_critico"] or 0)}</div>'
                f'</div>', unsafe_allow_html=True)

    if not ocs.empty:
        ab = ocs[ocs["situacao"] == "aberta"]
        if not ab.empty:
            pior = ab.sort_values("variacao", ascending=False).iloc[0]
            melhor = ab.sort_values("variacao").iloc[0]
            txt = (f"<b>{pior['regra_nome']}</b> é a fila mais pressionada, com "
                   f"{int(pior['abertas_atual'] or 0)} pendências "
                   f"({int(pior['variacao'] or 0):+d} desde ontem).")
            if int(melhor["variacao"] or 0) < 0:
                txt += (f" <b>{melhor['regra_nome']}</b> reduziu "
                        f"{abs(int(melhor['variacao']))} e mostra tendência de recuperação.")
            st.markdown(f'<div class="v-ai"><b>Resumo</b><br>{txt}</div>', unsafe_allow_html=True)

    st.caption(f"Fonte: Legal One API · Supabase · atualizado {agora:%d/%m %H:%M}")


# ----------------------------------------------------------------------
# NOVA REGRA
# ----------------------------------------------------------------------
@st.dialog("Criar nova regra de controladoria", width="large")
def dialog_regra():
    nome = st.text_input("Nome da regra", "Protocolo acima do limite")
    desc = st.text_input("Descrição", "")
    modo = st.radio("Escopo", ["Por subtipos", "Por setor_meta"], horizontal=True)
    subtipos, setor = None, None
    if modo == "Por subtipos":
        raw = st.text_area("Subtipos (um por linha — bate letra por letra)", height=90)
        subtipos = [s.strip() for s in raw.splitlines() if s.strip()] or None
    else:
        setor = st.text_input("setor_meta")
    unid = st.text_input("Unidades (vírgula · vazio = todas)")

    st.markdown("**Limites — abertas**")
    a1, a2, a3 = st.columns(3)
    la, lb, lc = (a1.number_input("Atenção", 0, value=40),
                  a2.number_input("Alerta", 0, value=50),
                  a3.number_input("Crítico", 0, value=70))
    st.markdown("**Limites — atrasadas**")
    b1, b2, b3 = st.columns(3)
    ta, tb, tc = (b1.number_input("Atenção ", 0, value=8),
                  b2.number_input("Alerta ", 0, value=12),
                  b3.number_input("Crítico ", 0, value=20))

    c1_, c2_ = st.columns(2)
    rnome = c1_.text_input("Responsável"); remail = c2_.text_input("E-mail do responsável")
    gnome = c1_.text_input("Gestor");      gemail = c2_.text_input("E-mail do gestor")
    space = st.text_input("Espaço do Google Chat (spaces/...)")

    if st.button("Salvar regra", type="primary"):
        if not nome or (not subtipos and not setor):
            st.error("Preencha o nome e o escopo (subtipos ou setor).")
            return
        _cli().table("v360_controladoria_regras").insert({
            "nome": nome, "descricao": desc or None,
            "subtipos": subtipos, "setor_meta": setor or None,
            "unidades": [u.strip() for u in unid.split(",") if u.strip()] or None,
            "lim_atencao": la, "lim_alerta": lb, "lim_critico": lc,
            "lim_atr_atencao": ta, "lim_atr_alerta": tb, "lim_atr_critico": tc,
            "responsavel_nome": rnome or None, "responsavel_email": remail or None,
            "gestor_nome": gnome or None, "gestor_email": gemail or None,
            "chat_space": space or None,
        }).execute()
        st.cache_data.clear()
        st.success("Regra criada.")
        st.rerun()


if nova:
    dialog_regra()
