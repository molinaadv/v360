"""
V360 — Painel Rodrigo · ROTATIVO (Tela 1 ↔ Tela 2)
====================================================
Arquivo ÚNICO. Alterna as telas no navegador (30s cada), sem recarregar.
Só editar SEG_POR_TELA pra mudar o tempo de cada tela.
"""
from datetime import datetime
from collections import Counter

import pandas as pd
import streamlit as st

# ───────── CONFIG ─────────
NUCLEO_LABEL = "Gerência"
SLUG         = "rodrigo"
SEG_POR_TELA = [30000, 30000]     # ms por tela: [Tela 2, Tela 3]
REFRESH_MS   = 5 * 60 * 1000
CACHE_TTL    = 120
MODO_DEMO    = False

VIEW="vw_tasks_rodrigo"; COL_ASSUNTO="subtipo_nome"; COL_STATUS="status_nome"   # unidades vêm da view (grupo rodrigo)
COL_RESP="responsavel_nome"; COL_CRIADOR="usuario_criador"; COL_MES_CONCL="mes_conclusao"
STATUS_ABERTO=["Pendente","Não cumprido","Iniciado"]; STATUS_CUMPRIDO="Cumprido"
MESES_PT=["","Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

# Tela 1
RESP_DESTAQUE="Michelle Fascini"
A_ANALISE_FINAL="Análise Final"; A_ENVIADA_CONFECCAO="Enviada p/ Confecção"
A_INICIAL_CONFECCAO="Inicial enviada para confecção"; A_INICIAL_REVISAO="Inicial enviada para revisão"
A_REVISADA_PROTOCOLAR="Inicial Revisada para Protocolar"; A_PROTOCOLO="Inicial enviada ao protocolo"
A_PROTOCOLO_CIVEL="Inicial enviada ao protocolo - Cível"; A_PENDENCIA_CONFECCAO="Pendência na Confecção"
ASSUNTOS_T1=[A_ANALISE_FINAL,A_ENVIADA_CONFECCAO,A_INICIAL_CONFECCAO,A_INICIAL_REVISAO,
             A_REVISADA_PROTOCOLAR,A_PROTOCOLO,A_PROTOCOLO_CIVEL,A_PENDENCIA_CONFECCAO]

# Tela 2
G_INDEFERIDO=["Benefício ADM - Indeferido"]
G_DEFERIDOS=["Benefício ADM - Deferido","Benefício ADM - Deferido REENVIO","Prorrogação de Benefício ADM - Deferido",
             "Benefício ADM - Deferido Temporariamente","Prorrogação de Benefício ADM","PAB Concedido",
             "Benefício Implantado","Benefício ADM - Deferido em Perícia Revisional"]
G_PRE_ACORDO=["Pré-Acordo"]; G_ACORDO_AGENDADO=["Acordo Agendado"]; G_ACORDO_REALIZADO=["Acordo Realizado"]
LABELS={"Benefício ADM - Deferido":"Deferido","Benefício ADM - Deferido REENVIO":"Deferido REENVIO",
 "Prorrogação de Benefício ADM - Deferido":"Prorrog. Deferido","Benefício ADM - Deferido Temporariamente":"Deferido Temporário",
 "Prorrogação de Benefício ADM":"Prorrogação ADM","PAB Concedido":"PAB Concedido","Benefício Implantado":"Implantado",
 "Benefício ADM - Deferido em Perícia Revisional":"Deferido Perícia Rev."}
ASSUNTOS_T2=(G_INDEFERIDO+G_DEFERIDOS+G_PRE_ACORDO+G_ACORDO_AGENDADO+G_ACORDO_REALIZADO)

# Tela 3 — Alvará / Levantamento
G_ALVARA=["Precatório Disponível p/ Saque","Precatório Expedido",
          "RPV Disponível p/ Saque","RPV Expedido","Aguardando Levantamento do Alvará"]
LABELS_T3={"Precatório Disponível p/ Saque":"Precatório Disp. Saque","Precatório Expedido":"Precatório Expedido",
 "RPV Disponível p/ Saque":"RPV Disp. Saque","RPV Expedido":"RPV Expedido",
 "Aguardando Levantamento do Alvará":"Aguard. Levant. Alvará"}
A_ACOMP_BANCO="Acompanhamento de Cliente ao Banco"; A_ENVIADO_BANCO="Enviado ao Banco (Levantamento)"
A_ALVARA_LEVANTADO="Alvará Levantado"; A_AGEND_RECIBO="Agendamento Recibo - RPV/Alvará"
A_AGEND_OFICIO="Agendamento Receber Ofício - RPV"; A_PAGAR_CLIENTE="Pagar cliente"
SINGLES_T3=[A_ACOMP_BANCO,A_ENVIADO_BANCO,A_ALVARA_LEVANTADO,A_AGEND_RECIBO,A_AGEND_OFICIO,A_PAGAR_CLIENTE]
ASSUNTOS_T3=(G_ALVARA+SINGLES_T3)

st.set_page_config(page_title=f"Painel {NUCLEO_LABEL} · TV", page_icon="📄",
                   layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
  #MainMenu,header[data-testid="stHeader"],footer{display:none!important}
  [data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none!important}
  .block-container{padding:0!important;max-width:100%!important}
  [data-testid="stAppViewContainer"]{background:#0b1220}
  iframe{border:none!important}
</style>""", unsafe_allow_html=True)
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=REFRESH_MS, key=f"refresh_{SLUG}")
except Exception:
    pass

def _norm(s): return str(s).strip().upper()
def _mes_atual():
    h=datetime.now(); return f"{MESES_PT[h.month]} / {h.year}", f"{h.year}-{h.month:02d}"
@st.cache_resource
def _sb():
    from supabase import create_client
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
def _pull(assuntos):
    sb=_sb(); regs, ini=[],0
    while True:
        d=(sb.table(VIEW).select("*").in_(COL_ASSUNTO,assuntos).range(ini,ini+999).execute().data) or []
        regs.extend(d)
        if len(d)<1000: break
        ini+=1000
    return pd.DataFrame(regs)
def _pessoa(df):
    if COL_RESP in df.columns:
        return df[COL_RESP].fillna("— sem nome").astype(str).str.strip().replace("","— sem nome")
    return pd.Series(["— sem nome"]*len(df), index=df.index)
def _ehM(n): return "MICHELLE FASCINI" in _norm(n)

TEMPLATE_T1 = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tela 1 — Inicial Enviada para Confecção</title>
<style>
  :root{
    --bg:#0b1220; --panel:#141d2e; --panel2:#1b2740; --line:#26324d;
    --ink:#f2f6ff; --muted:#93a1bd; --dim:#6b7a99;
    --accent:#5b8cff; --warn:#f5a524; --ok:#2fce8f;
    --michelle:#8b7bff; --demais:#4fb0e8; --civel:#f38ba8; --pend:#ef7a7a;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%}
  body{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,Arial,sans-serif;
    background:radial-gradient(1300px 800px at 12% -12%,#17253e 0%,var(--bg) 55%);
    color:var(--ink);min-height:100%;padding:26px clamp(16px,3vw,50px) 30px;
    display:flex;flex-direction:column;gap:18px;
  }
  header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px}
  .htitle{display:flex;align-items:center;gap:16px}
  .badge-num{width:50px;height:50px;border-radius:14px;background:linear-gradient(135deg,var(--warn),#e08a00);
    display:grid;place-items:center;font-weight:800;font-size:22px;color:#1a1300;box-shadow:0 10px 26px -10px var(--warn)}
  h1{font-size:clamp(20px,2.5vw,32px);font-weight:800;letter-spacing:-.02em;line-height:1.05}
  .htitle .sub{color:var(--muted);font-size:14px;margin-top:3px}
  .meta{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
  .pill{font-size:12.5px;font-weight:700;padding:8px 14px;border-radius:999px;border:1px solid var(--line);
    background:var(--panel2);color:var(--muted);display:inline-flex;align-items:center;gap:8px}
  .pill .live{width:8px;height:8px;border-radius:50%;background:var(--ok);box-shadow:0 0 0 4px rgba(47,206,143,.2)}
  .pill.scope{background:rgba(91,140,255,.12);border-color:rgba(91,140,255,.4);color:#b7c9ff}

  .grid{display:grid;gap:18px;grid-template-columns:1.5fr 1fr;flex:1;min-height:0}
  @media(max-width:1000px){.grid{grid-template-columns:1fr}}
  .col{display:flex;flex-direction:column;gap:18px;min-height:0}

  .section{background:linear-gradient(180deg,var(--panel) 0%,var(--panel2) 100%);
    border:1px solid var(--line);border-radius:20px;padding:20px 22px;display:flex;flex-direction:column;gap:14px}
  .stitle{font-size:12.5px;font-weight:800;letter-spacing:.11em;text-transform:uppercase;color:var(--muted);
    display:flex;align-items:center;gap:9px}
  .stitle .sq{width:11px;height:11px;border-radius:3px}
  .stitle .n{margin-left:auto;font-size:11px;font-weight:800;color:var(--dim);letter-spacing:.04em;text-transform:none}

  .cards{display:grid;grid-template-columns:1fr 1fr;gap:14px}
  .stat{background:#0e1728;border:1px solid var(--line);border-radius:16px;padding:16px 18px 14px;position:relative}
  .stat .step{position:absolute;top:13px;right:14px;font-size:11px;font-weight:800;color:#33456b;
    background:#0b1424;border:1px solid var(--line);border-radius:8px;padding:2px 7px}
  .stat .num{font-size:clamp(40px,5.6vw,56px);font-weight:800;line-height:.92;letter-spacing:-.03em;color:var(--warn)}
  .stat .t{font-size:13.5px;font-weight:700;color:#c9d3e6;margin-top:8px;line-height:1.25}
  .stat .sml{font-size:11.5px;color:var(--dim);margin-top:3px}
  .stat.neutral .num{color:var(--accent)}

  .split-card{background:#0e1728;border:1px solid var(--line);border-radius:16px;padding:16px 18px;grid-column:1/-1}
  .split-card .head{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:14px}
  .split-card .head .t{font-size:13px;font-weight:700;color:var(--muted)}
  .split-card .head .tot{font-size:15px;font-weight:800;color:var(--ink)}
  .split-card .head .tot span{color:var(--muted);font-weight:600;font-size:12.5px}
  .duo{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:12px}
  .mini{display:flex;flex-direction:column;gap:3px}
  .mini .who{font-size:13.5px;font-weight:700;display:flex;align-items:center;gap:8px}
  .mini .who i{width:11px;height:11px;border-radius:50%}
  .mini .v{font-size:36px;font-weight:800;letter-spacing:-.02em;line-height:1}
  .splitbar{height:15px;border-radius:8px;overflow:hidden;display:flex;border:1px solid var(--line)}
  .splitbar>span{display:block;height:100%}

  .protorow{display:flex;align-items:stretch;gap:18px;flex-wrap:wrap}
  .donut{width:120px;height:120px;border-radius:50%;flex:0 0 auto;align-self:center;
    background:conic-gradient(var(--ok) calc(var(--p)*1%),#26324d 0);display:grid;place-items:center;position:relative}
  .donut::before{content:"";position:absolute;inset:13px;border-radius:50%;background:var(--panel)}
  .donut .c{position:relative;text-align:center}
  .donut .c b{font-size:28px;font-weight:800;color:var(--ok)}
  .donut .c small{display:block;font-size:10px;color:var(--muted);letter-spacing:.06em;text-transform:uppercase}
  .pcards{display:grid;grid-template-columns:1fr 1fr;gap:14px;flex:1;min-width:280px}
  .pcard{background:#0e1728;border:1px solid var(--line);border-radius:16px;padding:14px 16px}
  .pcard .pt{font-size:12.5px;font-weight:700;color:#c9d3e6;margin-bottom:12px;display:flex;align-items:center;gap:7px;line-height:1.2}
  .pcard.civel{border-color:rgba(243,139,168,.3)}
  .chip-civel{font-size:10px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;
    color:#ffc4d2;background:rgba(243,139,168,.16);border:1px solid rgba(243,139,168,.4);border-radius:6px;padding:1px 7px}
  .pduo{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  .pstat .pn{font-size:34px;font-weight:800;letter-spacing:-.02em;line-height:1}
  .pstat.open .pn{color:var(--warn)} .pstat.done .pn{color:var(--ok)}
  .pstat .pl{font-size:11px;color:var(--muted);margin-top:5px;font-weight:600}

  .resp{flex:1;min-height:0}
  .reslegend{display:flex;gap:16px;font-size:11.5px;color:var(--muted);font-weight:600;margin-top:2px}
  .reslegend i{width:10px;height:10px;border-radius:3px;display:inline-block;margin-right:5px;vertical-align:middle}
  .resp .rows{column-count:2;column-gap:22px;margin-top:2px}
  .rrow{display:flex;flex-direction:column;gap:4px;margin-bottom:11px;
     break-inside:avoid;-webkit-column-break-inside:avoid;page-break-inside:avoid}
  .rrow .top{display:flex;align-items:baseline;justify-content:space-between;gap:10px}
  .rrow .who{font-size:14px;font-weight:600;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .rrow .nums{display:flex;align-items:center;gap:10px}
  .rrow .nums b{font-size:17px;font-weight:800;line-height:1}
  .rrow .nums .a{color:var(--warn)} .rrow .nums .c{color:var(--ok)}
  .rrow .nums .pend{font-size:11.5px;font-weight:800;color:var(--pend);
     background:rgba(239,122,122,.13);border:1px solid rgba(239,122,122,.35);border-radius:7px;padding:2px 8px}
  .segbar{height:10px;border-radius:6px;background:#0e1728;overflow:hidden;display:flex;border:1px solid var(--line)}
  .segbar>span{display:block;height:100%}
  .segbar .sa{background:var(--warn)} .segbar .sc{background:var(--ok)}
  .resp .foot{margin-top:auto;padding-top:14px;border-top:1px dashed var(--line);color:var(--dim);font-size:12.5px}
  .resp .foot b{color:var(--ink)}
  .resp .head-note{font-size:12px;color:var(--dim);font-weight:600}

  footer{color:var(--dim);font-size:12px;text-align:center}
</style>
</head>
<body>
  <header>
    <div class="htitle">
      <div class="badge-num">1</div>
      <div>
        <h1>Inicial Enviada para Confecção</h1>
        <div class="sub">Painel Rodrigo · fluxo da inicial: confecção → revisão → protocolo</div>
      </div>
    </div>
    <div class="meta">
      <span class="pill scope">● unidades do Rodrigo</span>
      <span class="pill">Competência · {{COMPETENCIA}}</span>
      <span class="pill"><span class="live"></span> {{STATUS_FONTE}}</span>
    </div>
  </header>

  <div class="grid">
    <div class="col">
      <div class="section">
        <div class="stitle"><span class="sq" style="background:var(--warn)"></span> Confecção — em aberto</div>
        <div class="cards" style="grid-template-columns:1fr 1fr 1fr">
          <div class="stat">
            <span class="step">1</span>
            <div class="num">{{ANALISE_FINAL}}</div>
            <div class="t">Análise Final</div>
            <div class="sml">tarefas em aberto</div>
          </div>
          <div class="stat">
            <span class="step">2</span>
            <div class="num">{{ENVIADA_CONFECCAO}}</div>
            <div class="t">Enviada p/ Confecção</div>
            <div class="sml">todas as tarefas em aberto</div>
          </div>
          <div class="stat neutral">
            <span class="step">3</span>
            <div class="num">{{INICIAL_CONFECCAO}}</div>
            <div class="t">Inicial enviada para confecção</div>
            <div class="sml">só a petição inicial</div>
          </div>
          <div class="split-card">
            <div class="head">
              <div class="t">Inicial enviada p/ confecção · por responsável</div>
              <div class="tot">{{INICIAL_CONFECCAO}} <span>em aberto</span></div>
            </div>
            <div class="duo">
              <div class="mini">
                <div class="who"><i style="background:var(--michelle)"></i> Michelle Fascini</div>
                <div class="v" style="color:var(--michelle)">{{MICHELLE}}</div>
              </div>
              <div class="mini">
                <div class="who"><i style="background:var(--demais)"></i> Outros responsáveis</div>
                <div class="v" style="color:var(--demais)">{{OUTROS}}</div>
              </div>
            </div>
            <div class="splitbar">
              <span style="width:{{MICHELLE_PCT}}%;background:var(--michelle)"></span>
              <span style="width:{{OUTROS_PCT}}%;background:var(--demais)"></span>
            </div>
          </div>
        </div>
      </div>

      <div style="display:flex;gap:18px;align-items:stretch;flex-wrap:wrap">
        <div class="section" style="flex:2;min-width:280px">
          <div class="stitle"><span class="sq" style="background:var(--warn)"></span> Revisão — em aberto</div>
          <div class="cards">
            <div class="stat">
              <span class="step">4</span>
              <div class="num">{{REVISAO}}</div>
              <div class="t">Inicial enviada para revisão</div>
            </div>
            <div class="stat">
              <span class="step">5</span>
              <div class="num">{{REVISADA_PROTOCOLAR}}</div>
              <div class="t">Inicial Revisada para Protocolar</div>
            </div>
          </div>
        </div>
        <div class="section" style="flex:1;min-width:190px">
          <div class="stitle"><span class="sq" style="background:var(--pend)"></span> Confecção · pendência</div>
          <div class="stat" style="flex:1;display:flex;flex-direction:column;justify-content:center">
            <div class="num" style="color:var(--pend)">{{PENDENCIA_CONFECCAO}}</div>
            <div class="t">Pendência na Confecção</div>
            <div class="sml">subtipo · em aberto</div>
          </div>
        </div>
      </div>

      <div class="section" style="flex:1">
        <div class="stitle"><span class="sq" style="background:var(--ok)"></span> Protocolo — mês <span class="n">em aberto + cumpridas</span></div>
        <div class="protorow">
          <div class="donut" style="--p:{{DONUT_PCT}}"><div class="c"><b>{{DONUT_PCT}}%</b><small>protocolado</small></div></div>
          <div class="pcards">
            <div class="pcard">
              <div class="pt">Inicial enviada ao protocolo</div>
              <div class="pduo">
                <div class="pstat open"><div class="pn">{{PROTO_ABERTO}}</div><div class="pl">Em aberto</div></div>
                <div class="pstat done"><div class="pn">{{PROTO_CUMPRIDO}}</div><div class="pl">Cumpridas / mês</div></div>
              </div>
            </div>
            <div class="pcard civel">
              <div class="pt">Inicial ao protocolo <span class="chip-civel">Cível</span></div>
              <div class="pduo">
                <div class="pstat open"><div class="pn">{{PROTO_CIVEL_ABERTO}}</div><div class="pl">Em aberto</div></div>
                <div class="pstat done"><div class="pn">{{PROTO_CIVEL_CUMPRIDO}}</div><div class="pl">Cumpridas / mês</div></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="col">
      <div class="section resp">
        <div class="stitle"><span class="sq" style="background:var(--demais)"></span> Responsáveis · Inicial p/ confecção</div>
        <div class="split-card" style="grid-column:auto;margin:2px 0 8px">
          <div class="head">
            <div class="t">Inicial enviada p/ confecção · geral</div>
            <div class="tot">{{CONF_TOTAL_MES}} <span>no mês</span></div>
          </div>
          <div class="duo">
            <div class="mini">
              <div class="who"><i style="background:var(--warn)"></i> Abertos (geral)</div>
              <div class="v" style="color:var(--warn)">{{CONF_ABERTO}}</div>
            </div>
            <div class="mini">
              <div class="who"><i style="background:var(--ok)"></i> Cumpridos do mês</div>
              <div class="v" style="color:var(--ok)">{{CONF_CUMPRIDO}}</div>
            </div>
          </div>
          <div class="splitbar">
            <span style="width:{{CONF_ABERTO_PCT}}%;background:var(--warn)"></span>
            <span style="width:{{CONF_CUMPRIDO_PCT}}%;background:var(--ok)"></span>
          </div>
        </div>
        <div class="reslegend">
          <span><i style="background:var(--warn)"></i> Em aberto</span>
          <span><i style="background:var(--ok)"></i> Cumprido no mês</span>
          <span><i style="background:var(--pend)"></i> Pendência na Confecção</span>
        </div>
        <div class="head-note">por responsável — exceto Michelle Fascini (destacada à esquerda)</div>
        <div class="rows">
          {{RESP_ROWS}}
        </div>
        <div class="foot">Soma dos outros: <b>{{OUTROS}}</b> · com Michelle ({{MICHELLE}}) = <b>{{INICIAL_CONFECCAO}}</b> iniciais em confecção.</div>
      </div>
    </div>
  </div>

  <footer>Painel Rodrigo · Tela 1 de 6 · {{RODAPE}}</footer>
</body>
</html>
"""

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def carregar_t1():
    competencia, ym=_mes_atual()
    df=_pull(ASSUNTOS_T1)
    zeros={k:0 for k in ("analise_final","enviada_confeccao","inicial_confeccao","pendencia_confeccao",
        "revisao","revisada_protocolar","proto_aberto","proto_cumprido","proto_civel_aberto","proto_civel_cumprido")}
    if df.empty:
        return {"competencia":competencia,"fonte":"ao vivo (Supabase)","cont_resp":Counter(),
                "resp_cumprido":{},"resp_pendencia":{},**zeros}
    df=df.copy(); df["_pessoa"]=_pessoa(df)
    stt=df[COL_STATUS].fillna("")
    aberto=df[stt.isin(STATUS_ABERTO)]; cumpr_mes=df[(stt==STATUS_CUMPRIDO)&(df[COL_MES_CONCL].astype(str)==ym)]
    ab=lambda a:int((aberto[COL_ASSUNTO]==a).sum()); cu=lambda a:int((cumpr_mes[COL_ASSUNTO]==a).sum())
    ic_ab=aberto[aberto[COL_ASSUNTO]==A_INICIAL_CONFECCAO]
    ic_cu=cumpr_mes[cumpr_mes[COL_ASSUNTO]==A_INICIAL_CONFECCAO]
    pc_ab=aberto[aberto[COL_ASSUNTO]==A_PENDENCIA_CONFECCAO]
    if COL_CRIADOR in pc_ab.columns:
        pc_cri=pc_ab[COL_CRIADOR].fillna("— sem nome").astype(str).str.strip().replace("","— sem nome")
        pc_cri=pc_cri.where(pc_cri.str.upper()!="SISTEMA","— sem nome")
    else:
        pc_cri=pd.Series(["— sem nome"]*len(pc_ab), index=pc_ab.index)
    return {"competencia":competencia,"fonte":"ao vivo (Supabase)",
        "analise_final":ab(A_ANALISE_FINAL),"enviada_confeccao":ab(A_ENVIADA_CONFECCAO),
        "inicial_confeccao":ab(A_INICIAL_CONFECCAO),"pendencia_confeccao":ab(A_PENDENCIA_CONFECCAO),
        "revisao":ab(A_INICIAL_REVISAO),"revisada_protocolar":ab(A_REVISADA_PROTOCOLAR),
        "proto_aberto":ab(A_PROTOCOLO),"proto_cumprido":cu(A_PROTOCOLO),
        "proto_civel_aberto":ab(A_PROTOCOLO_CIVEL),"proto_civel_cumprido":cu(A_PROTOCOLO_CIVEL),
        "cont_resp":Counter(ic_ab["_pessoa"]),"resp_cumprido":dict(Counter(ic_cu["_pessoa"])),
        "resp_pendencia":dict(Counter(pc_cri))}

def render_t1():
    d=carregar_t1(); cont=d["cont_resp"]
    michelle=int(sum(v for k,v in cont.items() if _ehM(k)))
    outros=sum(v for k,v in cont.items() if not _ehM(k)); total_conf=michelle+outros
    m_pct=round(michelle/total_conf*100) if total_conf else 0; o_pct=100-m_pct if total_conf else 0
    resp_ab=d["cont_resp"]; resp_cu=d.get("resp_cumprido",{}); resp_pe=d.get("resp_pendencia",{})
    conf_aberto=sum(int(v) for v in resp_ab.values()); conf_cumprido=sum(int(v) for v in resp_cu.values())
    conf_total=conf_aberto+conf_cumprido; ca_pct=round(conf_aberto/conf_total*100) if conf_total else 0; cc_pct=100-ca_pct if conf_total else 0
    todas=set(resp_ab)|set(resp_cu)|set(resp_pe)
    nomes=sorted((n for n in todas if not _ehM(n)),key=lambda n:(int(resp_ab.get(n,0)),int(resp_cu.get(n,0)),int(resp_pe.get(n,0))),reverse=True)
    rows=""
    for nome in nomes:
        a=int(resp_ab.get(nome,0)); c=int(resp_cu.get(nome,0)); p=int(resp_pe.get(nome,0)); tot=a+c
        aw=round(a/tot*100) if tot else 0; cw=100-aw if tot else 0
        pend=(f'<span class="pend">{p} pend.</span>' if p else '<span class="pend" style="color:var(--dim);background:transparent;border-color:var(--line)">0</span>')
        rows+=f'<div class="rrow"><div class="top"><div class="who">{nome}</div><div class="nums"><b class="a">{a}</b><b class="c">{c}</b>{pend}</div></div><div class="segbar"><span class="sa" style="width:{aw}%"></span><span class="sc" style="width:{cw}%"></span></div></div>'
    if not rows: rows='<div class="head-note">Sem outras iniciais.</div>'
    proto_cu=d["proto_cumprido"]+d["proto_civel_cumprido"]; proto_ab=d["proto_aberto"]+d["proto_civel_aberto"]
    donut=round(proto_cu/((proto_cu+proto_ab) or 1)*100)
    tpl=TEMPLATE_T1
    repl={"{{COMPETENCIA}}":d["competencia"],"{{STATUS_FONTE}}":d["fonte"],"{{ANALISE_FINAL}}":str(d["analise_final"]),
      "{{ENVIADA_CONFECCAO}}":str(d["enviada_confeccao"]),"{{INICIAL_CONFECCAO}}":str(total_conf),"{{MICHELLE}}":str(michelle),
      "{{OUTROS}}":str(outros),"{{MICHELLE_PCT}}":str(m_pct),"{{OUTROS_PCT}}":str(o_pct),"{{REVISAO}}":str(d["revisao"]),
      "{{REVISADA_PROTOCOLAR}}":str(d["revisada_protocolar"]),"{{PENDENCIA_CONFECCAO}}":str(d.get("pendencia_confeccao",0)),
      "{{PROTO_ABERTO}}":str(d["proto_aberto"]),"{{PROTO_CUMPRIDO}}":str(d["proto_cumprido"]),
      "{{PROTO_CIVEL_ABERTO}}":str(d["proto_civel_aberto"]),"{{PROTO_CIVEL_CUMPRIDO}}":str(d["proto_civel_cumprido"]),
      "{{DONUT_PCT}}":str(donut),"{{CONF_ABERTO}}":str(conf_aberto),"{{CONF_CUMPRIDO}}":str(conf_cumprido),
      "{{CONF_ABERTO_PCT}}":str(ca_pct),"{{CONF_CUMPRIDO_PCT}}":str(cc_pct),"{{CONF_TOTAL_MES}}":str(conf_total),
      "{{RESP_ROWS}}":rows,"{{RODAPE}}":f"atualizado {datetime.now():%d/%m %H:%M}"}
    for k,v in repl.items(): tpl=tpl.replace(k,v)
    return tpl
TEMPLATE_T2 = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tela 2 — Benefícios & Acordos</title>
<style>
  :root{
    --bg:#0b1220; --panel:#141d2e; --panel2:#1b2740; --line:#26324d;
    --ink:#f2f6ff; --muted:#93a1bd; --dim:#6b7a99;
    --accent:#5b8cff; --warn:#f5a524; --ok:#2fce8f;
    --crit:#ef7a7a; --roxo:#8b7bff; --azul:#4fb0e8; --teal:#2fce8f;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%}
  body{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,Arial,sans-serif;
    background:radial-gradient(1300px 800px at 12% -12%,#17253e 0%,var(--bg) 55%);
    color:var(--ink);min-height:100%;padding:26px clamp(16px,3vw,50px) 28px;
    display:flex;flex-direction:column;gap:18px;
  }
  header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px}
  .htitle{display:flex;align-items:center;gap:16px}
  .badge-num{width:50px;height:50px;border-radius:14px;background:linear-gradient(135deg,var(--ok),#1f9e6d);
    display:grid;place-items:center;font-weight:800;font-size:22px;color:#052015;box-shadow:0 10px 26px -10px var(--ok)}
  h1{font-size:clamp(20px,2.5vw,32px);font-weight:800;letter-spacing:-.02em;line-height:1.05}
  .htitle .sub{color:var(--muted);font-size:14px;margin-top:3px}
  .meta{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
  .pill{font-size:12.5px;font-weight:700;padding:8px 14px;border-radius:999px;border:1px solid var(--line);
    background:var(--panel2);color:var(--muted);display:inline-flex;align-items:center;gap:8px}
  .pill .live{width:8px;height:8px;border-radius:50%;background:var(--ok);box-shadow:0 0 0 4px rgba(47,206,143,.2)}
  .pill.scope{background:rgba(91,140,255,.12);border-color:rgba(91,140,255,.4);color:#b7c9ff}
  .legend{display:flex;gap:18px;font-size:12px;color:var(--muted);font-weight:600}
  .legend i{width:11px;height:11px;border-radius:3px;display:inline-block;margin-right:6px;vertical-align:middle}

  /* 4 KPI cards */
  .kpirow{display:grid;grid-template-columns:repeat(2,1fr);grid-auto-rows:1fr;gap:16px;flex:1;min-height:0}
  @media(max-width:1000px){.kpirow{grid-template-columns:1fr 1fr}}
  .kcard{background:linear-gradient(180deg,var(--panel) 0%,var(--panel2) 100%);
    border:1px solid var(--line);border-radius:18px;padding:20px 24px;display:flex;flex-direction:column;justify-content:space-between;gap:14px}
  .ktitle{font-size:14px;font-weight:800;letter-spacing:.02em;display:flex;align-items:center;gap:9px}
  .ktitle i{width:12px;height:12px;border-radius:50%;flex:0 0 auto}
  .kduo{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:auto 0}
  .kstat .kn{font-size:clamp(34px,4.4vw,48px);font-weight:800;line-height:.9;letter-spacing:-.03em}
  .kstat .kn.open{color:var(--warn)} .kstat .kn.done{color:var(--ok)}
  .kstat .kl{font-size:11.5px;color:var(--muted);margin-top:6px;font-weight:600}
  .segbar{height:11px;border-radius:6px;background:#0e1728;overflow:hidden;display:flex;border:1px solid var(--line)}
  .segbar>span{display:block;height:100%}
  .segbar .sa{background:var(--warn)} .segbar .sc{background:var(--ok)}

  /* Deferidos */
  .section{background:linear-gradient(180deg,var(--panel) 0%,var(--panel2) 100%);
    border:1px solid var(--line);border-radius:20px;padding:20px 22px;display:flex;flex-direction:column;gap:16px;flex:1;min-height:0}
  .stitle{font-size:12.5px;font-weight:800;letter-spacing:.11em;text-transform:uppercase;color:var(--muted);
    display:flex;align-items:center;gap:9px}
  .stitle .sq{width:11px;height:11px;border-radius:3px}
  .stitle .n{margin-left:auto;font-size:11px;font-weight:800;color:var(--dim);letter-spacing:.04em;text-transform:none}
  .defwrap{display:grid;grid-template-columns:0.9fr 1.6fr;gap:22px;flex:1;min-height:0}
  @media(max-width:1000px){.defwrap{grid-template-columns:1fr}}
  .defsum{background:#0e1728;border:1px solid var(--line);border-radius:16px;padding:20px;
    display:flex;flex-direction:column;gap:16px;justify-content:center}
  .defsum .donutrow{display:flex;align-items:center;gap:18px}
  .donut{width:120px;height:120px;border-radius:50%;flex:0 0 auto;
    background:conic-gradient(var(--ok) calc(var(--p)*1%),#26324d 0);display:grid;place-items:center;position:relative}
  .donut::before{content:"";position:absolute;inset:13px;border-radius:50%;background:#0e1728}
  .donut .c{position:relative;text-align:center}
  .donut .c b{font-size:26px;font-weight:800;color:var(--ok)}
  .donut .c small{display:block;font-size:10px;color:var(--muted);letter-spacing:.06em;text-transform:uppercase}
  .defsum .duo{display:flex;flex-direction:column;gap:4px}
  .defsum .duo .who{font-size:13px;font-weight:700;color:var(--muted);display:flex;align-items:center;gap:8px}
  .defsum .duo .who i{width:11px;height:11px;border-radius:50%}
  .defsum .duo .v{font-size:40px;font-weight:800;line-height:1;letter-spacing:-.02em}
  .defsum .splitbar{height:15px;border-radius:8px;overflow:hidden;display:flex;border:1px solid var(--line)}
  .defsum .splitbar>span{display:block;height:100%}
  .defsum .foot{color:var(--dim);font-size:12px}

  .defrows{display:grid;grid-template-columns:1fr 1fr;gap:11px 22px;align-content:start}
  .drow{display:flex;flex-direction:column;gap:5px}
  .drow .top{display:flex;align-items:baseline;justify-content:space-between;gap:10px}
  .drow .who{font-size:13.5px;font-weight:600;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .drow .nums{display:flex;gap:9px}
  .drow .nums b{font-size:16px;font-weight:800;line-height:1}
  .drow .nums .a{color:var(--warn)} .drow .nums .c{color:var(--ok)}

  footer{color:var(--dim);font-size:12px;text-align:center}
</style>
</head>
<body>
  <header>
    <div class="htitle">
      <div class="badge-num">2</div>
      <div>
        <h1>Benefícios &amp; Acordos</h1>
        <div class="sub">Painel Rodrigo · desfechos · em aberto + cumpridos no mês</div>
      </div>
    </div>
    <div class="meta">
      <span class="legend"><span><i style="background:var(--warn)"></i>Em aberto</span><span><i style="background:var(--ok)"></i>Cumprido no mês</span></span>
      <span class="pill scope">● unidades do Rodrigo</span>
      <span class="pill">Competência · {{COMPETENCIA}}</span>
      <span class="pill"><span class="live"></span> {{STATUS_FONTE}}</span>
    </div>
  </header>

  <!-- 4 desfechos -->
  <div class="kpirow">
    <div class="kcard">
      <div class="ktitle"><i style="background:var(--crit)"></i> Indeferido</div>
      <div class="kduo">
        <div class="kstat"><div class="kn open">{{IND_AB}}</div><div class="kl">Em aberto</div></div>
        <div class="kstat"><div class="kn done">{{IND_CU}}</div><div class="kl">Cumpr. / mês</div></div>
      </div>
      <div class="segbar"><span class="sa" style="width:{{IND_AP}}%"></span><span class="sc" style="width:{{IND_CP}}%"></span></div>
    </div>
    <div class="kcard">
      <div class="ktitle"><i style="background:var(--azul)"></i> Pré-Acordo</div>
      <div class="kduo">
        <div class="kstat"><div class="kn open">{{PRE_AB}}</div><div class="kl">Em aberto</div></div>
        <div class="kstat"><div class="kn done">{{PRE_CU}}</div><div class="kl">Cumpr. / mês</div></div>
      </div>
      <div class="segbar"><span class="sa" style="width:{{PRE_AP}}%"></span><span class="sc" style="width:{{PRE_CP}}%"></span></div>
    </div>
    <div class="kcard">
      <div class="ktitle"><i style="background:var(--roxo)"></i> Acordo Agendado</div>
      <div class="kduo">
        <div class="kstat"><div class="kn open">{{AGE_AB}}</div><div class="kl">Em aberto</div></div>
        <div class="kstat"><div class="kn done">{{AGE_CU}}</div><div class="kl">Cumpr. / mês</div></div>
      </div>
      <div class="segbar"><span class="sa" style="width:{{AGE_AP}}%"></span><span class="sc" style="width:{{AGE_CP}}%"></span></div>
    </div>
    <div class="kcard">
      <div class="ktitle"><i style="background:var(--teal)"></i> Acordo Realizado</div>
      <div class="kduo">
        <div class="kstat"><div class="kn open">{{REA_AB}}</div><div class="kl">Em aberto</div></div>
        <div class="kstat"><div class="kn done">{{REA_CU}}</div><div class="kl">Cumpr. / mês</div></div>
      </div>
      <div class="segbar"><span class="sa" style="width:{{REA_AP}}%"></span><span class="sc" style="width:{{REA_CP}}%"></span></div>
    </div>
  </div>

  <!-- Deferidos -->
  <div class="section">
    <div class="stitle"><span class="sq" style="background:var(--ok)"></span> Deferidos <span class="n">consolidado + 8 subtipos · em aberto + cumpridos no mês</span></div>
    <div class="defwrap">
      <div class="defsum">
        <div class="donutrow">
          <div class="donut" style="--p:{{DEF_DONUT}}"><div class="c"><b>{{DEF_DONUT}}%</b><small>cumprido</small></div></div>
          <div style="display:flex;flex-direction:column;gap:14px">
            <div class="duo">
              <div class="who"><i style="background:var(--warn)"></i> Em aberto</div>
              <div class="v" style="color:var(--warn)">{{DEF_AB}}</div>
            </div>
            <div class="duo">
              <div class="who"><i style="background:var(--ok)"></i> Cumpridos / mês</div>
              <div class="v" style="color:var(--ok)">{{DEF_CU}}</div>
            </div>
          </div>
        </div>
        <div class="splitbar">
          <span style="width:{{DEF_AB_PCT}}%;background:var(--warn)"></span>
          <span style="width:{{DEF_CU_PCT}}%;background:var(--ok)"></span>
        </div>
        <div class="foot">Total no mês: <b style="color:var(--ink)">{{DEF_TOTAL}}</b> (8 subtipos somados)</div>
      </div>
      <div class="defrows">
        {{DEF_ROWS}}
      </div>
    </div>
  </div>

  <footer>Painel Rodrigo · Tela 2 de 6 · {{RODAPE}}</footer>
</body>
</html>
"""

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def carregar_t2():
    competencia, ym=_mes_atual()
    df=_pull(ASSUNTOS_T2)
    if df.empty:
        vazio={"aberto":0,"cumprido":0}
        return {"competencia":competencia,"fonte":"ao vivo (Supabase)",
            "grupos":{k:dict(vazio) for k in ["Indeferido","Deferidos","Pré-Acordo","Acordo Agendado","Acordo Realizado"]},
            "deferidos_det":[{"nome":s,"aberto":0,"cumprido":0} for s in G_DEFERIDOS]}
    stt=df[COL_STATUS].fillna("")
    aberto=df[stt.isin(STATUS_ABERTO)]; cumpr=df[(stt==STATUS_CUMPRIDO)&(df[COL_MES_CONCL].astype(str)==ym)]
    ab=lambda subs:int(aberto[COL_ASSUNTO].isin(subs).sum()); cu=lambda subs:int(cumpr[COL_ASSUNTO].isin(subs).sum())
    return {"competencia":competencia,"fonte":"ao vivo (Supabase)",
      "grupos":{"Indeferido":{"aberto":ab(G_INDEFERIDO),"cumprido":cu(G_INDEFERIDO)},
        "Deferidos":{"aberto":ab(G_DEFERIDOS),"cumprido":cu(G_DEFERIDOS)},
        "Pré-Acordo":{"aberto":ab(G_PRE_ACORDO),"cumprido":cu(G_PRE_ACORDO)},
        "Acordo Agendado":{"aberto":ab(G_ACORDO_AGENDADO),"cumprido":cu(G_ACORDO_AGENDADO)},
        "Acordo Realizado":{"aberto":ab(G_ACORDO_REALIZADO),"cumprido":cu(G_ACORDO_REALIZADO)}},
      "deferidos_det":[{"nome":s,"aberto":ab([s]),"cumprido":cu([s])} for s in G_DEFERIDOS]}

def _bloco_tok(g):
    a=int(g["aberto"]); c=int(g["cumprido"]); tot=a+c
    ap=round(a/tot*100) if tot else 0; return str(a),str(c),str(ap),str(100-ap if tot else 0)

def render_t2():
    d=carregar_t2(); gr=d["grupos"]; det=d["deferidos_det"]
    maxseg=max((x["aberto"]+x["cumprido"] for x in det), default=1) or 1
    rows=""
    for x in det:
        nome=LABELS.get(x["nome"],x["nome"]); a=int(x["aberto"]); c=int(x["cumprido"])
        aw=round(a/maxseg*100); cw=round(c/maxseg*100)
        rows+=f'<div class="drow"><div class="top"><div class="who">{nome}</div><div class="nums"><b class="a">{a}</b><b class="c">{c}</b></div></div><div class="segbar"><span class="sa" style="width:{aw}%"></span><span class="sc" style="width:{cw}%"></span></div></div>'
    ind=_bloco_tok(gr["Indeferido"]); pre=_bloco_tok(gr["Pré-Acordo"]); age=_bloco_tok(gr["Acordo Agendado"]); rea=_bloco_tok(gr["Acordo Realizado"]); dfe=_bloco_tok(gr["Deferidos"])
    def_tot=int(gr["Deferidos"]["aberto"])+int(gr["Deferidos"]["cumprido"]); def_donut=round(int(gr["Deferidos"]["cumprido"])/(def_tot or 1)*100)
    tpl=TEMPLATE_T2
    repl={"{{COMPETENCIA}}":d["competencia"],"{{STATUS_FONTE}}":d["fonte"],
      "{{IND_AB}}":ind[0],"{{IND_CU}}":ind[1],"{{IND_AP}}":ind[2],"{{IND_CP}}":ind[3],
      "{{PRE_AB}}":pre[0],"{{PRE_CU}}":pre[1],"{{PRE_AP}}":pre[2],"{{PRE_CP}}":pre[3],
      "{{AGE_AB}}":age[0],"{{AGE_CU}}":age[1],"{{AGE_AP}}":age[2],"{{AGE_CP}}":age[3],
      "{{REA_AB}}":rea[0],"{{REA_CU}}":rea[1],"{{REA_AP}}":rea[2],"{{REA_CP}}":rea[3],
      "{{DEF_AB}}":dfe[0],"{{DEF_CU}}":dfe[1],"{{DEF_AB_PCT}}":dfe[2],"{{DEF_CU_PCT}}":dfe[3],
      "{{DEF_TOTAL}}":str(def_tot),"{{DEF_DONUT}}":str(def_donut),"{{DEF_ROWS}}":rows,
      "{{RODAPE}}":f"atualizado {datetime.now():%d/%m %H:%M}"}
    for k,v in repl.items(): tpl=tpl.replace(k,v)
    return tpl

TEMPLATE_T3 = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tela 3 — Alvará & Levantamento</title>
<style>
  :root{
    --bg:#0b1220; --panel:#141d2e; --panel2:#1b2740; --line:#26324d;
    --ink:#f2f6ff; --muted:#93a1bd; --dim:#6b7a99;
    --accent:#5b8cff; --warn:#f5a524; --ok:#2fce8f;
    --crit:#ef7a7a; --roxo:#8b7bff; --azul:#4fb0e8; --teal:#2fce8f;
    --rosa:#f472b6; --ciano:#22d3ee; --dourado:#e3b341;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%}
  body{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,Arial,sans-serif;
    background:radial-gradient(1300px 800px at 12% -12%,#17253e 0%,var(--bg) 55%);
    color:var(--ink);min-height:100%;padding:26px clamp(16px,3vw,50px) 28px;
    display:flex;flex-direction:column;gap:18px;
  }
  header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px}
  .htitle{display:flex;align-items:center;gap:16px}
  .badge-num{width:50px;height:50px;border-radius:14px;background:linear-gradient(135deg,var(--dourado),#b3852a);
    display:grid;place-items:center;font-weight:800;font-size:22px;color:#1a1405;box-shadow:0 10px 26px -10px var(--dourado)}
  h1{font-size:clamp(20px,2.5vw,32px);font-weight:800;letter-spacing:-.02em;line-height:1.05}
  .htitle .sub{color:var(--muted);font-size:14px;margin-top:3px}
  .meta{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
  .pill{font-size:12.5px;font-weight:700;padding:8px 14px;border-radius:999px;border:1px solid var(--line);
    background:var(--panel2);color:var(--muted);display:inline-flex;align-items:center;gap:8px}
  .pill .live{width:8px;height:8px;border-radius:50%;background:var(--ok);box-shadow:0 0 0 4px rgba(47,206,143,.2)}
  .pill.scope{background:rgba(91,140,255,.12);border-color:rgba(91,140,255,.4);color:#b7c9ff}
  .legend{display:flex;gap:18px;font-size:12px;color:var(--muted);font-weight:600}
  .legend i{width:11px;height:11px;border-radius:3px;display:inline-block;margin-right:6px;vertical-align:middle}

  /* stack: Alvará em cima + 6 cards embaixo (metade cada) */
  .stack{flex:1;min-height:0;display:flex;flex-direction:column;gap:18px}
  /* 6 KPI cards — 3 x 2, metade de baixo */
  .kpirow{display:grid;grid-template-columns:repeat(3,1fr);grid-auto-rows:1fr;gap:16px;flex:1;min-height:0;order:2}
  @media(max-width:700px){.kpirow{grid-template-columns:1fr 1fr}}
  .kcard{background:linear-gradient(180deg,var(--panel) 0%,var(--panel2) 100%);
    border:1px solid var(--line);border-radius:18px;padding:20px 24px;display:flex;flex-direction:column;justify-content:space-between;gap:14px}
  .ktitle{font-size:14px;font-weight:800;letter-spacing:.01em;display:flex;align-items:center;gap:8px;line-height:1.2}
  .ktitle i{width:12px;height:12px;border-radius:50%;flex:0 0 auto}
  .kduo{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:auto 0}
  .kstat .kn{font-size:clamp(34px,3.2vw,54px);font-weight:800;line-height:.9;letter-spacing:-.03em}
  .kstat .kn.open{color:var(--warn)} .kstat .kn.done{color:var(--ok)}
  .kstat .kl{font-size:12px;color:var(--muted);margin-top:6px;font-weight:600}
  .segbar{height:11px;border-radius:6px;background:#0e1728;overflow:hidden;display:flex;border:1px solid var(--line)}
  .segbar>span{display:block;height:100%}
  .segbar .sa{background:var(--warn)} .segbar .sc{background:var(--ok)}

  /* Alvará (consolidado + subtipos) — metade de cima */
  .section{background:linear-gradient(180deg,var(--panel) 0%,var(--panel2) 100%);
    border:1px solid var(--line);border-radius:20px;padding:18px 22px;display:flex;flex-direction:column;gap:14px;flex:1;min-height:0;order:1}
  .section .donut{width:150px;height:150px}
  .section .defsum{padding:24px 22px}
  .section .defrows{display:flex;flex-direction:column;justify-content:space-evenly;gap:6px}
  .section .drow .who{font-size:14.5px}
  .section .drow .nums b{font-size:17px}
  .stitle{font-size:12.5px;font-weight:800;letter-spacing:.11em;text-transform:uppercase;color:var(--muted);
    display:flex;align-items:center;gap:9px}
  .stitle .sq{width:11px;height:11px;border-radius:3px}
  .stitle .n{margin-left:auto;font-size:11px;font-weight:800;color:var(--dim);letter-spacing:.04em;text-transform:none}
  .defwrap{display:grid;grid-template-columns:0.9fr 1.6fr;gap:22px;flex:1;min-height:0}
  @media(max-width:1000px){.defwrap{grid-template-columns:1fr}}
  .defsum{background:#0e1728;border:1px solid var(--line);border-radius:16px;padding:20px;
    display:flex;flex-direction:column;gap:16px;justify-content:center}
  .defsum .donutrow{display:flex;align-items:center;gap:18px}
  .donut{width:120px;height:120px;border-radius:50%;flex:0 0 auto;
    background:conic-gradient(var(--ok) calc(var(--p)*1%),#26324d 0);display:grid;place-items:center;position:relative}
  .donut::before{content:"";position:absolute;inset:13px;border-radius:50%;background:#0e1728}
  .donut .c{position:relative;text-align:center}
  .donut .c b{font-size:26px;font-weight:800;color:var(--ok)}
  .donut .c small{display:block;font-size:10px;color:var(--muted);letter-spacing:.06em;text-transform:uppercase}
  .defsum .duo{display:flex;flex-direction:column;gap:4px}
  .defsum .duo .who{font-size:13px;font-weight:700;color:var(--muted);display:flex;align-items:center;gap:8px}
  .defsum .duo .who i{width:11px;height:11px;border-radius:50%}
  .defsum .duo .v{font-size:40px;font-weight:800;line-height:1;letter-spacing:-.02em}
  .defsum .splitbar{height:15px;border-radius:8px;overflow:hidden;display:flex;border:1px solid var(--line)}
  .defsum .splitbar>span{display:block;height:100%}
  .defsum .foot{color:var(--dim);font-size:12px}

  .defrows{display:grid;grid-template-columns:1fr 1fr;gap:11px 22px;align-content:start}
  .drow{display:flex;flex-direction:column;gap:5px}
  .drow .top{display:flex;align-items:baseline;justify-content:space-between;gap:10px}
  .drow .who{font-size:13.5px;font-weight:600;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .drow .nums{display:flex;gap:9px}
  .drow .nums b{font-size:16px;font-weight:800;line-height:1}
  .drow .nums .a{color:var(--warn)} .drow .nums .c{color:var(--ok)}

  footer{color:var(--dim);font-size:12px;text-align:center}
</style>
</head>
<body>
  <header>
    <div class="htitle">
      <div class="badge-num">3</div>
      <div>
        <h1>Alvará &amp; Levantamento</h1>
        <div class="sub">Painel Rodrigo · pagamento ao cliente · em aberto + cumpridos no mês</div>
      </div>
    </div>
    <div class="meta">
      <span class="legend"><span><i style="background:var(--warn)"></i>Em aberto</span><span><i style="background:var(--ok)"></i>Cumprido no mês</span></span>
      <span class="pill scope">● unidades do Rodrigo</span>
      <span class="pill">Competência · {{COMPETENCIA}}</span>
      <span class="pill"><span class="live"></span> {{STATUS_FONTE}}</span>
    </div>
  </header>

  <div class="stack">
  <!-- 6 etapas -->
  <div class="kpirow">
    <div class="kcard">
      <div class="ktitle"><i style="background:var(--azul)"></i> Acomp. Cliente ao Banco</div>
      <div class="kduo">
        <div class="kstat"><div class="kn open">{{AC_AB}}</div><div class="kl">Em aberto</div></div>
        <div class="kstat"><div class="kn done">{{AC_CU}}</div><div class="kl">Cumpr. / mês</div></div>
      </div>
      <div class="segbar"><span class="sa" style="width:{{AC_AP}}%"></span><span class="sc" style="width:{{AC_CP}}%"></span></div>
    </div>
    <div class="kcard">
      <div class="ktitle"><i style="background:var(--roxo)"></i> Enviado ao Banco</div>
      <div class="kduo">
        <div class="kstat"><div class="kn open">{{EB_AB}}</div><div class="kl">Em aberto</div></div>
        <div class="kstat"><div class="kn done">{{EB_CU}}</div><div class="kl">Cumpr. / mês</div></div>
      </div>
      <div class="segbar"><span class="sa" style="width:{{EB_AP}}%"></span><span class="sc" style="width:{{EB_CP}}%"></span></div>
    </div>
    <div class="kcard">
      <div class="ktitle"><i style="background:var(--teal)"></i> Alvará Levantado</div>
      <div class="kduo">
        <div class="kstat"><div class="kn open">{{AL_AB}}</div><div class="kl">Em aberto</div></div>
        <div class="kstat"><div class="kn done">{{AL_CU}}</div><div class="kl">Cumpr. / mês</div></div>
      </div>
      <div class="segbar"><span class="sa" style="width:{{AL_AP}}%"></span><span class="sc" style="width:{{AL_CP}}%"></span></div>
    </div>
    <div class="kcard">
      <div class="ktitle"><i style="background:var(--accent)"></i> Agend. Recibo RPV/Alvará</div>
      <div class="kduo">
        <div class="kstat"><div class="kn open">{{AR_AB}}</div><div class="kl">Em aberto</div></div>
        <div class="kstat"><div class="kn done">{{AR_CU}}</div><div class="kl">Cumpr. / mês</div></div>
      </div>
      <div class="segbar"><span class="sa" style="width:{{AR_AP}}%"></span><span class="sc" style="width:{{AR_CP}}%"></span></div>
    </div>
    <div class="kcard">
      <div class="ktitle"><i style="background:var(--rosa)"></i> Agend. Ofício RPV</div>
      <div class="kduo">
        <div class="kstat"><div class="kn open">{{AO_AB}}</div><div class="kl">Em aberto</div></div>
        <div class="kstat"><div class="kn done">{{AO_CU}}</div><div class="kl">Cumpr. / mês</div></div>
      </div>
      <div class="segbar"><span class="sa" style="width:{{AO_AP}}%"></span><span class="sc" style="width:{{AO_CP}}%"></span></div>
    </div>
    <div class="kcard">
      <div class="ktitle"><i style="background:var(--ciano)"></i> Pagar Cliente</div>
      <div class="kduo">
        <div class="kstat"><div class="kn open">{{PC_AB}}</div><div class="kl">Em aberto</div></div>
        <div class="kstat"><div class="kn done">{{PC_CU}}</div><div class="kl">Cumpr. / mês</div></div>
      </div>
      <div class="segbar"><span class="sa" style="width:{{PC_AP}}%"></span><span class="sc" style="width:{{PC_CP}}%"></span></div>
    </div>
  </div>

  <!-- Alvará -->
  <div class="section">
    <div class="stitle"><span class="sq" style="background:var(--dourado)"></span> Alvará <span class="n">consolidado + 5 subtipos · em aberto + cumpridos no mês</span></div>
    <div class="defwrap">
      <div class="defsum">
        <div class="donutrow">
          <div class="donut" style="--p:{{ALV_DONUT}}"><div class="c"><b>{{ALV_DONUT}}%</b><small>cumprido</small></div></div>
          <div style="display:flex;flex-direction:column;gap:14px">
            <div class="duo">
              <div class="who"><i style="background:var(--warn)"></i> Em aberto</div>
              <div class="v" style="color:var(--warn)">{{ALV_AB}}</div>
            </div>
            <div class="duo">
              <div class="who"><i style="background:var(--ok)"></i> Cumpridos / mês</div>
              <div class="v" style="color:var(--ok)">{{ALV_CU}}</div>
            </div>
          </div>
        </div>
        <div class="splitbar">
          <span style="width:{{ALV_AB_PCT}}%;background:var(--warn)"></span>
          <span style="width:{{ALV_CU_PCT}}%;background:var(--ok)"></span>
        </div>
        <div class="foot">Total no mês: <b style="color:var(--ink)">{{ALV_TOTAL}}</b> (5 subtipos somados)</div>
      </div>
      <div class="defrows">
        {{ALV_ROWS}}
      </div>
    </div>
  </div>
  </div>

  <footer>Painel Rodrigo · Tela 3 de 6 · {{RODAPE}}</footer>
</body>
</html>
"""

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def carregar_t3():
    competencia, ym=_mes_atual()
    df=_pull(ASSUNTOS_T3)
    keys=["Acomp","Enviado","Levantado","Recibo","Ofício","Pagar","Alvará"]
    if df.empty:
        return {"competencia":competencia,"fonte":"ao vivo (Supabase)",
            "grupos":{k:{"aberto":0,"cumprido":0} for k in keys},
            "alvara_det":[{"nome":s,"aberto":0,"cumprido":0} for s in G_ALVARA]}
    stt=df[COL_STATUS].fillna("")
    aberto=df[stt.isin(STATUS_ABERTO)]; cumpr=df[(stt==STATUS_CUMPRIDO)&(df[COL_MES_CONCL].astype(str)==ym)]
    ab=lambda subs:int(aberto[COL_ASSUNTO].isin(subs).sum()); cu=lambda subs:int(cumpr[COL_ASSUNTO].isin(subs).sum())
    return {"competencia":competencia,"fonte":"ao vivo (Supabase)",
      "grupos":{
        "Acomp":{"aberto":ab([A_ACOMP_BANCO]),"cumprido":cu([A_ACOMP_BANCO])},
        "Enviado":{"aberto":ab([A_ENVIADO_BANCO]),"cumprido":cu([A_ENVIADO_BANCO])},
        "Levantado":{"aberto":ab([A_ALVARA_LEVANTADO]),"cumprido":cu([A_ALVARA_LEVANTADO])},
        "Recibo":{"aberto":ab([A_AGEND_RECIBO]),"cumprido":cu([A_AGEND_RECIBO])},
        "Ofício":{"aberto":ab([A_AGEND_OFICIO]),"cumprido":cu([A_AGEND_OFICIO])},
        "Pagar":{"aberto":ab([A_PAGAR_CLIENTE]),"cumprido":cu([A_PAGAR_CLIENTE])},
        "Alvará":{"aberto":ab(G_ALVARA),"cumprido":cu(G_ALVARA)}},
      "alvara_det":[{"nome":s,"aberto":ab([s]),"cumprido":cu([s])} for s in G_ALVARA]}

def render_t3():
    d=carregar_t3(); gr=d["grupos"]; det=d["alvara_det"]
    maxseg=max((x["aberto"]+x["cumprido"] for x in det), default=1) or 1
    rows=""
    for x in det:
        nome=LABELS_T3.get(x["nome"],x["nome"]); a=int(x["aberto"]); c=int(x["cumprido"])
        aw=round(a/maxseg*100); cw=round(c/maxseg*100)
        rows+=f'<div class="drow"><div class="top"><div class="who">{nome}</div><div class="nums"><b class="a">{a}</b><b class="c">{c}</b></div></div><div class="segbar"><span class="sa" style="width:{aw}%"></span><span class="sc" style="width:{cw}%"></span></div></div>'
    ac=_bloco_tok(gr["Acomp"]); eb=_bloco_tok(gr["Enviado"]); al=_bloco_tok(gr["Levantado"])
    ar=_bloco_tok(gr["Recibo"]); ao=_bloco_tok(gr["Ofício"]); pc=_bloco_tok(gr["Pagar"]); alv=_bloco_tok(gr["Alvará"])
    alv_tot=int(gr["Alvará"]["aberto"])+int(gr["Alvará"]["cumprido"]); alv_donut=round(int(gr["Alvará"]["cumprido"])/(alv_tot or 1)*100)
    tpl=TEMPLATE_T3
    repl={"{{COMPETENCIA}}":d["competencia"],"{{STATUS_FONTE}}":d["fonte"],
      "{{AC_AB}}":ac[0],"{{AC_CU}}":ac[1],"{{AC_AP}}":ac[2],"{{AC_CP}}":ac[3],
      "{{EB_AB}}":eb[0],"{{EB_CU}}":eb[1],"{{EB_AP}}":eb[2],"{{EB_CP}}":eb[3],
      "{{AL_AB}}":al[0],"{{AL_CU}}":al[1],"{{AL_AP}}":al[2],"{{AL_CP}}":al[3],
      "{{AR_AB}}":ar[0],"{{AR_CU}}":ar[1],"{{AR_AP}}":ar[2],"{{AR_CP}}":ar[3],
      "{{AO_AB}}":ao[0],"{{AO_CU}}":ao[1],"{{AO_AP}}":ao[2],"{{AO_CP}}":ao[3],
      "{{PC_AB}}":pc[0],"{{PC_CU}}":pc[1],"{{PC_AP}}":pc[2],"{{PC_CP}}":pc[3],
      "{{ALV_AB}}":alv[0],"{{ALV_CU}}":alv[1],"{{ALV_AB_PCT}}":alv[2],"{{ALV_CU_PCT}}":alv[3],
      "{{ALV_TOTAL}}":str(alv_tot),"{{ALV_DONUT}}":str(alv_donut),"{{ALV_ROWS}}":rows,
      "{{RODAPE}}":f"atualizado {datetime.now():%d/%m %H:%M}"}
    for k,v in repl.items(): tpl=tpl.replace(k,v)
    return tpl

# ───────── ROTATIVO ─────────
def _esc(h):
    return (h.replace("\\","\\\\").replace("`","\\`").replace("${","\\${").replace("</script","<\\/script"))

try:
    h2=_esc(render_t2()); h3=_esc(render_t3())
    combined=("<!DOCTYPE html><html><head><meta charset='UTF-8'><style>"
      "html,body{margin:0;padding:0;height:100%;background:#0b1220;overflow:hidden}"
      "#tv{position:fixed;inset:0;width:100%;height:100%;border:0}"
      "#nav{position:fixed;bottom:14px;left:16px;"
      "display:flex;gap:10px;z-index:9;padding:8px 12px;border-radius:999px;"
      "background:rgba(11,18,32,.55);backdrop-filter:blur(6px);border:1px solid rgba(38,50,77,.7)}"
      ".seg{width:66px;height:10px;display:flex;align-items:center;cursor:pointer}"
      ".seg .bar{width:100%;height:6px;border-radius:999px;background:#26324d;overflow:hidden}"
      ".seg .bar>span{display:block;height:100%;width:0;border-radius:999px;"
      "background:linear-gradient(90deg,#5b8cff,#2fce8f)}"
      ".seg:hover .bar{background:#31405f}"
      "</style></head><body><iframe id='tv'></iframe><div id='nav'></div><script>"
      "const TELAS=[`"+h2+"`,`"+h3+"`];const DUR="+str(SEG_POR_TELA)+";"
      "const f=document.getElementById('tv');const nav=document.getElementById('nav');"
      "let i=0,tmr=null;"
      "const segs=TELAS.map(function(_,k){var s=document.createElement('div');s.className='seg';"
      "s.title='Tela '+(k+1);s.addEventListener('click',function(){show(k);});"
      "var bar=document.createElement('div');bar.className='bar';"
      "var b=document.createElement('span');bar.appendChild(b);s.appendChild(bar);nav.appendChild(s);return b;});"
      "function show(idx){clearTimeout(tmr);i=idx;f.srcdoc=TELAS[i];const d=DUR[i%DUR.length];"
      "segs.forEach(function(b,k){b.style.transition='none';b.style.width=(k<i?'100%':'0');});"
      "const cur=segs[i];void cur.offsetWidth;"
      "requestAnimationFrame(function(){cur.style.transition='width '+d+'ms linear';cur.style.width='100%';});"
      "tmr=setTimeout(function(){show((i+1)%TELAS.length);},d);}show(0);"
      "</script></body></html>")
    st.components.v1.html(combined, height=1040, scrolling=False)
except Exception as e:
    st.error(f"Falha ao carregar o painel rotativo: {e}")
