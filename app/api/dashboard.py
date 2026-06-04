"""Layer 4 — Framework: live metrics dashboard at /dashboard and JSON stats at /api/stats."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CK Bot — Dashboard</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0f1117;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-height:100vh;font-size:14px}
.header{padding:16px 24px;border-bottom:1px solid #1e2436;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.header h1{font-size:16px;font-weight:600;color:#f1f5f9;letter-spacing:.02em}
.status-row{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.dot{width:8px;height:8px;border-radius:50%;background:#22c55e;flex-shrink:0;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.status-label{font-size:13px;color:#22c55e;font-weight:500}
.uptime-label{font-size:12px;color:#475569}
.refresh-label{font-size:11px;color:#334155}
.container{max-width:1120px;margin:0 auto;padding:20px 16px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:16px}
.card{background:#161b2e;border:1px solid #1e2a45;border-radius:10px;padding:18px 20px}
.card .val{font-size:34px;font-weight:700;line-height:1;margin-bottom:5px;font-variant-numeric:tabular-nums}
.card .lbl{font-size:11px;color:#475569;text-transform:uppercase;letter-spacing:.06em}
.card .sub{font-size:11px;color:#334155;margin-top:3px}
.blue .val{color:#60a5fa}
.green .val{color:#4ade80}
.orange .val{color:#fb923c}
.purple .val{color:#a78bfa}
.section{background:#161b2e;border:1px solid #1e2a45;border-radius:10px;padding:18px 20px;margin-bottom:12px}
.section-title{font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:.07em;margin-bottom:14px}
.chart-wrap{display:flex;align-items:flex-end;gap:3px;height:72px;overflow:hidden}
.bar-col{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:3px;height:100%}
.bar-fill{width:100%;background:#2563eb;border-radius:2px 2px 0 0;min-height:2px;transition:height .3s}
.bar-fill.now{background:#60a5fa}
.bar-lbl{font-size:9px;color:#334155;line-height:1}
table{width:100%;border-collapse:collapse}
th{text-align:left;padding:6px 0;color:#334155;font-weight:500;font-size:11px;text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid #1e2a45}
td{padding:9px 0;border-bottom:1px solid #111827;color:#94a3b8;font-size:13px;vertical-align:top}
td.ts{color:#334155;white-space:nowrap;padding-right:16px;font-size:12px}
td.qt{color:#cbd5e1}
.empty{color:#1e2a45;font-style:italic;padding:12px 0;font-size:13px}
.intent-item{margin-bottom:10px}
.intent-header{display:flex;justify-content:space-between;font-size:12px;color:#64748b;margin-bottom:4px}
.intent-name{color:#94a3b8}
.intent-count{color:#475569}
.intent-track{height:5px;background:#0d1220;border-radius:3px}
.intent-fill{height:100%;background:#4f46e5;border-radius:3px;transition:width .4s}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:640px){
  .cards{grid-template-columns:repeat(2,1fr)}
  .card .val{font-size:26px}
  .two-col{grid-template-columns:1fr}
}
</style>
</head>
<body>
<div class="header">
  <h1>Centr Krasok Bot</h1>
  <div class="status-row">
    <div class="dot" id="dot"></div>
    <span class="status-label" id="status-label">Online</span>
    <span class="uptime-label" id="uptime"></span>
    <span class="refresh-label" id="last-refresh"></span>
  </div>
</div>
<div class="container">
  <div class="cards">
    <div class="card blue">
      <div class="val" id="c-total">—</div>
      <div class="lbl">Total Requests</div>
      <div class="sub" id="c-det"></div>
    </div>
    <div class="card green">
      <div class="val" id="c-llm">—</div>
      <div class="lbl">LLM Calls</div>
      <div class="sub" id="c-llmrate"></div>
    </div>
    <div class="card orange">
      <div class="val" id="c-tokens">—</div>
      <div class="lbl">Tokens Used</div>
    </div>
    <div class="card purple">
      <div class="val" id="c-rt">—</div>
      <div class="lbl">Avg Response, ms</div>
      <div class="sub" id="c-errors"></div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Запросы по часам (24 ч)</div>
    <div class="chart-wrap" id="chart"></div>
  </div>

  <div class="two-col">
    <div class="section">
      <div class="section-title">Топ-5 интентов</div>
      <div id="intents"><div class="empty">Нет данных</div></div>
    </div>
    <div class="section">
      <div class="section-title">Последние 5 вопросов без ответа</div>
      <table>
        <thead><tr><th>Время</th><th>Вопрос</th></tr></thead>
        <tbody id="unanswered"><tr><td colspan="2" class="empty">Нет данных</td></tr></tbody>
      </table>
    </div>
  </div>
</div>

<script>
function fmtUptime(s){
  const h=Math.floor(s/3600),m=Math.floor((s%3600)/60);
  if(h>0) return h+'ч '+m+'м';
  return m+'м '+Math.floor(s%60)+'с';
}
function fmtNum(n){
  if(n>=1000000) return (n/1000000).toFixed(1)+'M';
  if(n>=1000) return (n/1000).toFixed(1)+'k';
  return String(n);
}
function buildChart(data){
  const el=document.getElementById('chart');
  el.innerHTML='';
  const nowH=new Date().getHours();
  const hours=[];
  for(let i=23;i>=0;i--) hours.push((nowH-i+24)%24);
  const counts=hours.map(h=>data[String(h)]||0);
  const mx=Math.max(...counts,1);
  hours.forEach((h,i)=>{
    const pct=Math.max(Math.round(counts[i]/mx*100),counts[i]>0?3:0);
    const col=document.createElement('div');
    col.className='bar-col';
    col.innerHTML='<div class="bar-fill'+(h===nowH?' now':'')+'" style="height:'+pct+'%"></div>'
      +'<div class="bar-lbl">'+h+'</div>';
    el.appendChild(col);
  });
}
function buildIntents(data){
  const el=document.getElementById('intents');
  const entries=Object.entries(data).sort((a,b)=>b[1]-a[1]).slice(0,5);
  if(!entries.length){el.innerHTML='<div class="empty">Нет данных</div>';return;}
  const total=entries.reduce((s,[,v])=>s+v,0)||1;
  el.innerHTML=entries.map(([k,v])=>{
    const pct=Math.round(v/total*100);
    return '<div class="intent-item">'
      +'<div class="intent-header"><span class="intent-name">'+k+'</span>'
      +'<span class="intent-count">'+v+' ('+pct+'%)</span></div>'
      +'<div class="intent-track"><div class="intent-fill" style="width:'+pct+'%"></div></div>'
      +'</div>';
  }).join('');
}
function buildUnanswered(items){
  const tbody=document.getElementById('unanswered');
  const last5=[...items].reverse().slice(0,5);
  if(!last5.length){
    tbody.innerHTML='<tr><td colspan="2" class="empty">Нет вопросов без ответа</td></tr>';
    return;
  }
  tbody.innerHTML=last5.map(q=>
    '<tr><td class="ts">'+q.timestamp+'</td><td class="qt">'+q.text+'</td></tr>'
  ).join('');
}
async function refresh(){
  try{
    const r=await fetch('/api/stats');
    if(!r.ok) throw new Error(r.status);
    const d=await r.json();
    document.getElementById('c-total').textContent=fmtNum(d.total_requests);
    document.getElementById('c-det').textContent=d.deterministic_answers+' детерм.';
    document.getElementById('c-llm').textContent=fmtNum(d.llm_calls);
    document.getElementById('c-llmrate').textContent=d.llm_rate+'% от всех';
    document.getElementById('c-tokens').textContent=fmtNum(d.total_tokens_used);
    document.getElementById('c-rt').textContent=d.avg_response_time_ms;
    document.getElementById('c-errors').textContent=d.errors_count+' ошиб.';
    document.getElementById('uptime').textContent='uptime '+fmtUptime(d.uptime_seconds);
    document.getElementById('dot').style.background='#22c55e';
    document.getElementById('status-label').textContent='Online';
    document.getElementById('last-refresh').textContent='обновлено '+new Date().toLocaleTimeString();
    buildChart(d.requests_per_hour);
    buildIntents(d.requests_by_intent);
    buildUnanswered(d.unanswered_questions);
  }catch(e){
    document.getElementById('dot').style.background='#ef4444';
    document.getElementById('status-label').textContent='Offline';
  }
}
refresh();
setInterval(refresh,10000);
</script>
</body>
</html>"""


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> str:
    return _HTML


@router.get("/api/stats")
async def api_stats(request: Request) -> dict:
    return request.app.state.metrics.get_stats()
