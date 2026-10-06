(function(){
"use strict";
var WORKFLOW_URL="https://github.com/DWR-debug/trading-agent-public/actions/workflows/resource-dashboard-update.yml";
function $(id){return document.getElementById(id);}
function esc(v){return String(v==null?"":v).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;");}
function ts(v){if(!v)return "—";try{return new Date(v).toLocaleString(undefined,{dateStyle:"short",timeStyle:"medium"});}catch(e){return String(v);}}
function fmtDuration(sec){
  if(sec==null||Number.isNaN(Number(sec)))return "—";
  sec=Math.max(0,Math.round(Number(sec)));
  var h=Math.floor(sec/3600), m=Math.floor((sec%3600)/60), s=sec%60;
  if(h)return h+" h "+m+" min";
  if(m)return m+" min "+s+" s";
  return s+" s";
}
function relativeRemaining(sec){
  if(sec==null)return "—";
  return sec>0 ? "noch ca. "+fmtDuration(sec) : "voraussichtlich fertig";
}
function candidateFrom(text){
  text=String(text||"");
  return ["Q104:I19","Q218","Q220","Q221","Q219"].find(function(c){return text.indexOf(c)>=0;})||"—";
}
function updateClock(){
  var now=new Date();
  try{
    $("clockTime").textContent=new Intl.DateTimeFormat("de-DE",{timeZone:"Europe/Berlin",hour:"2-digit",minute:"2-digit",second:"2-digit",hour12:false}).format(now);
    $("clockDate").textContent=new Intl.DateTimeFormat("de-DE",{timeZone:"Europe/Berlin",weekday:"long",year:"numeric",month:"long",day:"numeric"}).format(now);
  }catch(e){
    $("clockTime").textContent=now.toLocaleTimeString("de-DE");
    $("clockDate").textContent=now.toLocaleDateString("de-DE");
  }
}
function capacityClass(x){
  var s=String(x.capacity_state||"unknown");
  return ["operating","available"].indexOf(s)>=0?s:"unknown";
}
function stateBadge(status){
  var s=String(status||"");
  var active=["queued","in_progress","waiting","pending"].indexOf(s)>=0;
  var cls=active?"active-badge":(["success","completed","ready"].some(function(k){return s.toLowerCase().indexOf(k)>=0;})?"good":"unknown");
  return "<span class='badge "+cls+"'>"+esc(s||"—")+"</span>";
}
function render(data){
  var s=data.dashboard_summary||{};
  var resources=(data.resources||[]).filter(function(x){
    return ["Windows self-hosted A","Windows self-hosted B","Windows self-hosted C","GitHub-hosted Ubuntu x64","GitHub-hosted ARM64","Free AI pool"].indexOf(x.name)>=0;
  });
  var work=data.work_assignments||[];
  var pipeline=data.pipeline||[];
  var cr=data.current_research||{};
  $("meta").innerHTML="Snapshot <code>"+esc(data.generated_at_utc)+"</code> · master <code>"+esc(data.master_sha)+"</code> · Status-Quelle <code>"+esc(data.operational_snapshot_sha||"nicht synchron")+"</code>";

  var order={"Windows self-hosted A":0,"Windows self-hosted B":1,"Windows self-hosted C":2,"GitHub-hosted Ubuntu x64":3,"GitHub-hosted ARM64":4,"Free AI pool":5};
  resources.sort(function(a,b){return order[a.name]-order[b.name];});
  $("capacity").innerHTML="<div class='capacity-grid'>"+resources.map(function(x){
    var cls=capacityClass(x);
    var state=cls==="operating"?"ARBEITET":cls==="available"?"VERFÜGBAR":"NICHT SICHTBAR";
    var plannedCount=(data.planned_capacity||[]).filter(function(p){return p.resource===x.name;}).reduce(function(n,p){return n+Number(p.planned_count||0);},0);
    return "<div class='capacity "+cls+"'>"+
      "<div class='name'>"+esc(x.name)+"</div>"+
      "<div class='state'>"+state+"</div>"+
      "<div class='role'>"+esc(x.role)+"</div>"+
      "<div class='jobs'>"+esc(x.current_assignments||0)+" aktiver Job"+((x.current_assignments||0)===1?"":"s")+"</div>"+
      "<div class='small muted'>Slots: "+esc(x.research_slots_in_use||0)+"/"+esc(x.research_capacity_slots||1)+" belegt · "+esc(x.research_slots_free||0)+" frei</div>"+
      "<div class='small muted'>"+esc(plannedCount)+" geplant</div>"+
      "</div>";
  }).join("")+"</div>";

  $("work").innerHTML=work.length ? "<table><thead><tr><th>Kapazität</th><th>Candidate</th><th>Job</th><th>Status</th><th>Start</th><th>Erwartete Dauer</th><th>ETA / Rest</th></tr></thead><tbody>"+work.map(function(x){
    return "<tr><td class='rowtitle'>"+esc(x.resource)+"<div class='small muted'>"+esc(x.worker)+"</div></td>"+
      "<td>"+esc(candidateFrom((x.task||"")+" "+(x.job||"")))+"<div class='small'>"+esc(x.task||"")+"</div></td>"+
      "<td>"+esc(x.job||"—")+"<div class='small'>Run "+esc(x.run_id||"—")+"</div></td>"+
      "<td>"+stateBadge(x.status)+"</td>"+
      "<td>"+esc(ts(x.started_at))+"</td>"+
      "<td>"+fmtDuration(x.expected_duration_seconds)+"<div class='small muted'>n="+esc(x.duration_sample_count||0)+"</div></td>"+
      "<td>"+relativeRemaining(x.remaining_seconds)+"<div class='small'>"+(x.expected_finish_at?esc(ts(x.expected_finish_at)):"—")+"</div></td></tr>";
  }).join("")+"</tbody></table>" : "<div class='empty'>Aktuell ist kein aktiver GitHub-Actions-Job im Snapshot sichtbar.</div>";

  var planned=data.planned_capacity||[];
  $("planned").innerHTML=planned.length ? "<table><thead><tr><th>Kapazität</th><th>Aktuell</th><th>Geplante nächste Arbeit</th><th>Bereitschaft</th><th>Erwartete Dauer</th><th>Planstatus</th></tr></thead><tbody>"+planned.map(function(x){
    var p=(x.planned_assignments||[])[0];
    var label=p ? (esc(p.candidate)+" — "+esc(p.task)) : "keine unabhängige Ready-Arbeit";
    var readiness=p ? esc(p.readiness) : "—";
    var dur=p ? fmtDuration(p.expected_duration_seconds) : "—";
    var status=p ? (p.scheduled ? "<span class='badge planned-badge'>GEPLANT / NICHT GESTARTET</span>" : "<span class='badge blocked-badge'>BLOCKIERT / KEINE DISPOSITION</span>") : "<span class='badge unknown'>nicht zugewiesen</span>";
    var basis=p ? "<div class='small muted'>"+esc(p.basis)+"</div>" : "<div class='small muted'>"+esc(x.unallocated_reason||"")+"</div>";
    return "<tr><td class='rowtitle'>"+esc(x.resource)+"</td><td>"+esc(x.current_assignments||0)+" aktiver Job"+((x.current_assignments||0)===1?"":"s")+"</td><td>"+label+basis+"</td><td>"+readiness+"</td><td>"+dur+(p?"<div class='small muted'>n="+esc(p.duration_sample_count||0)+"</div>":"")+"</td><td>"+status+"</td></tr>";
  }).join("")+"</tbody></table>" : "<div class='empty'>Kein bounded Plan im Snapshot.</div>";

  $("pipeline").innerHTML=pipeline.length ? "<table><thead><tr><th>Candidate</th><th>Stage</th><th>Nächster Gate</th><th>Aktuell</th><th>Erwartete Jobdauer</th><th>Samples</th></tr></thead><tbody>"+pipeline.map(function(x){
    var active=x.active;
    return "<tr><td class='rowtitle'>"+esc(x.code)+"</td>"+
      "<td>"+esc(x.stage)+"</td>"+
      "<td>"+esc(x.next_gate||"—")+"</td>"+
      "<td>"+(active?"<span class='badge active-badge'>ARBEIT LÄUFT ("+esc(x.active_jobs)+")</span>":"<span class='badge unknown'>kein aktiver Job sichtbar</span>")+"</td>"+
      "<td>"+fmtDuration(x.expected_duration_seconds)+"<div class='small muted'>P90 "+fmtDuration(x.duration_p90_seconds)+"</div></td>"+
      "<td>"+esc(x.duration_sample_count||0)+"</td></tr>";
  }).join("")+"</tbody></table>" : "<div class='empty'>Keine Top-4-Pipeline im Snapshot.</div>";

  var milestones=data.milestone_history_12h||[];
  $("milestones12h").innerHTML=milestones.length ? "<table><thead><tr><th>Zeit</th><th>Typ</th><th>Meilenstein</th><th>Ergebnis</th></tr></thead><tbody>"+milestones.map(function(x){
    var link=x.url ? "<a href='"+esc(x.url)+"' target='_blank' rel='noopener'>"+esc(x.title||"Meilenstein")+"</a>" : esc(x.title||"Meilenstein");
    return "<tr><td>"+esc(ts(x.timestamp))+"</td><td>"+esc(x.kind||"—")+"</td><td class='rowtitle'>"+link+"<div class='small muted'>"+esc(x.detail||"")+"</div></td><td>"+esc(x.status||"—")+"</td></tr>";
  }).join("")+"</tbody></table>" : "<div class='empty'>In den letzten 12 Stunden wurden keine passenden abgeschlossenen Research-/Evidence-Meilensteine aufgezeichnet.</div>";

  var highlights=(cr.highlights||[]).slice(-6);
  $("achieved").innerHTML=
    "<div class='small'><strong>Letztes formales Ergebnis:</strong> "+esc(cr.latest_formal_result||"nicht aufgezeichnet")+"</div>"+
    "<div style='margin-top:10px'>"+(highlights.length?highlights.map(function(x){return "<div style='margin:7px 0'>"+esc(x)+"</div>";}).join(""):"<div class='empty'>Keine Highlights im Snapshot.</div>")+"</div>"+
    "<div class='small muted' style='margin-top:10px'>Performance, Holdout, Ranking, Tuning, Promotion und Live-Ausführung bleiben fail-closed.</div>";

  var pcs=s.planned_capacity_items||0, pbs=s.blocked_planned_items||0, urs=s.unallocated_routable_items||0;
  $("plannedSummary").textContent="Geplant: "+pcs+" · Blockiert auf Prerequisite: "+pbs+" · Nicht zugewiesen: "+urs;
  $("app").hidden=false;
}
function renderEmbedded(){
  var snap=window.__TRADING_AGENT_SNAPSHOT__;
  if(snap&&typeof snap==="object"){render(snap);return true;}
  return false;
}
function load(){
  $("error").hidden=true;
  var rendered=renderEmbedded();
  var url=new URL("dashboard_data.json",document.baseURI);
  url.searchParams.set("ts",String(Date.now()));
  var controller=typeof AbortController==="function"?new AbortController():null;
  var timeoutId=controller?setTimeout(function(){controller.abort();},6000):null;
  var opts={cache:"no-store"}; if(controller)opts.signal=controller.signal;
  fetch(url.toString(),opts).then(function(r){if(!r.ok)throw new Error("HTTP "+r.status);return r.json();}).then(render).catch(function(e){
    if(!rendered){$("error").textContent="Snapshot konnte nicht geladen werden: "+(e&&e.message||String(e));$("error").hidden=false;}
    else{$("meta").insertAdjacentHTML("beforeend"," · <span class='unknown'>Netzwerk-Refresh nicht verfügbar; eingebetteter Snapshot wird angezeigt.</span>");}
  }).then(function(){if(timeoutId!==null)clearTimeout(timeoutId);});
}
document.addEventListener("DOMContentLoaded",function(){
  updateClock();
  setInterval(updateClock,1000);
  $("refresh").addEventListener("click",load);
  $("update").addEventListener("click",function(){});
  load();
});
})();
