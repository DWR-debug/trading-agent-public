(function(){
"use strict";
var lastSnapshotIso=null;
var FOCUS=["Q104:I19","Q218"];

function $(id){return document.getElementById(id);}
function esc(v){
  return String(v==null?"":v)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;").replace(/'/g,"&#39;");
}
function ts(v){
  if(!v)return "—";
  try{return new Date(v).toLocaleString("de-DE",{dateStyle:"short",timeStyle:"medium"});}
  catch(e){return String(v);}
}
function fmtSnapshotAge(sec){
  if(sec==null||Number.isNaN(Number(sec)))return "Alter: —";
  sec=Math.max(0,Math.round(Number(sec)));
  if(sec<60)return "Alter: "+sec+" s";
  var min=Math.floor(sec/60), rem=sec%60;
  if(min<60)return "Alter: "+min+" min "+rem+" s";
  var h=Math.floor(min/60), m=min%60;
  return "Alter: "+h+" h "+m+" min";
}
function updateSnapshotAge(){
  if(!lastSnapshotIso)return;
  var t=Date.parse(lastSnapshotIso);
  if(!Number.isFinite(t))return;
  $("snapshotAge").textContent=fmtSnapshotAge(Math.max(0,(Date.now()-t)/1000));
}
function updateClock(){
  var now=new Date();
  try{
    $("clockTime").textContent=new Intl.DateTimeFormat("de-DE",{
      timeZone:"Europe/Berlin",hour:"2-digit",minute:"2-digit",second:"2-digit",hour12:false
    }).format(now);
    $("clockDate").textContent=new Intl.DateTimeFormat("de-DE",{
      timeZone:"Europe/Berlin",weekday:"long",year:"numeric",month:"long",day:"numeric"
    }).format(now);
  }catch(e){
    $("clockTime").textContent=now.toLocaleTimeString("de-DE");
    $("clockDate").textContent=now.toLocaleDateString("de-DE");
  }
}
function candidateFrom(text){
  text=String(text||"");
  for(var i=0;i<FOCUS.length;i++)if(text.indexOf(FOCUS[i])>=0)return FOCUS[i];
  return "—";
}
function pct(v){return Math.max(0,Math.min(100,Number(v)||0));}
function progressBar(v,large){
  v=pct(v);
  return "<div class='meter "+(large?"large":"")+"'><div class='meter-fill' style='width:"+v+"%'></div></div>";
}
function capacityState(x,data){
  var plannedRows=(data.planned_capacity||[]).filter(function(p){return p.resource===x.name;});
  var items=plannedRows.reduce(function(a,p){return a.concat(p.planned_assignments||[]);},[]);
  var dispatchable=items.some(function(p){return p.scheduled&&p.dispatchable;});
  var active=Number(x.current_assignments||0)>0;
  var runnerBusy=Boolean(x.runner_busy);
  var runnerOnline=String(x.runner_status||"").toLowerCase()==="online";
  if(active)return {cls:"operating",label:"ARBEITET"};
  if(runnerBusy)return {cls:"unknown",label:"RUNNER BESETZT"};
  if(dispatchable)return {
    cls:"planned",
    label:(x.type==="physical"&&!runnerOnline)?"AUTO-DISPATCH GEPLANT":"AUTO-DISPATCH BEREIT"
  };
  if(String(x.capacity_state||"") === "available")return {cls:"available",label:"VERFÜGBAR"};
  return {cls:"unknown",label:"NICHT VERIFIZIERT"};
}
function render(data){
  var s=data.dashboard_summary||{};
  var resources=(data.resources||[]).filter(function(x){
    return ["Windows self-hosted A","Windows self-hosted B","Windows self-hosted C","GitHub-hosted Ubuntu x64","GitHub-hosted ARM64","Free AI pool"].indexOf(x.name)>=0;
  });
  var pipeline=(data.pipeline||[]).filter(function(x){return FOCUS.indexOf(x.code)>=0;});
  var work=(data.work_assignments||[]).filter(function(x){return FOCUS.indexOf(candidateFrom((x.task||"")+" "+(x.job||"")))>=0;});
  var planned=(data.planned_capacity||[]).filter(function(x){
    return (x.planned_assignments||[]).some(function(p){return FOCUS.indexOf(p.candidate)>=0;});
  });
  var queue=(data.planned_research_queue||[]).filter(function(x){return FOCUS.indexOf(x.candidate)>=0;}).slice(0,2);
  var cr=data.current_research||{};
  lastSnapshotIso=data.generated_at_utc||null;

  $("meta").innerHTML="Snapshot <code>"+esc(data.generated_at_utc)+"</code> · master <code>"+esc(data.master_sha)+"</code> · Status-Quelle <code>"+esc(data.operational_snapshot_sha||"nicht synchron")+"</code>"+
    ((data.dashboard_policy||{}).runner_status_ui_url?" · <a href='"+esc(data.dashboard_policy.runner_status_ui_url)+"' target='_blank' rel='noopener'>Runner-Status</a>":"");

  try{
    var snapDate=data.generated_at_utc?new Date(data.generated_at_utc):null;
    if(snapDate&&!Number.isNaN(snapDate.getTime())){
      $("snapshotTime").textContent=new Intl.DateTimeFormat("de-DE",{timeZone:"Europe/Berlin",hour:"2-digit",minute:"2-digit",second:"2-digit",hour12:false}).format(snapDate);
      $("snapshotDate").textContent=new Intl.DateTimeFormat("de-DE",{timeZone:"Europe/Berlin",weekday:"long",year:"numeric",month:"long",day:"numeric"}).format(snapDate);
    }
  }catch(e){}
  updateSnapshotAge();

  var overallAvg=pipeline.length?Math.round(pipeline.reduce(function(a,x){return a+pct(x.overall_progress_percent);},0)/pipeline.length):0;
  var activeCount=pipeline.reduce(function(a,x){return a+Number(x.active_jobs||0);},0);
  $("focusSummary").innerHTML=
    "<div class='focus-kpi'><span class='eyebrow'>Fokus</span><strong>Q104:I19 + Q218</strong><span>Automatische Kandidatenbeschickung ist auf diese zwei Tracks begrenzt.</span></div>"+
    "<div class='focus-kpi'><span class='eyebrow'>Gesamtentwicklung</span><strong>"+overallAvg+"%</strong><span>arithmetischer Überblick der zwei Entwicklungsstände</span></div>"+
    "<div class='focus-kpi'><span class='eyebrow'>Aktive Candidate-Jobs</span><strong>"+activeCount+"</strong><span>sichtbar in der aktuellen Actions-Telemetrie</span></div>";

  $("candidateFocus").innerHTML=pipeline.length?pipeline.map(function(x){
    var active=Boolean(x.active);
    var overall=pct(x.overall_progress_percent), next=pct(x.next_milestone_progress_percent);
    var state=active?"ARBEIT LÄUFT":"WARTET AUF GATE-START";
    var badge=active?"active-badge":"planned-badge";
    return "<article class='candidate-card'>"+
      "<div class='candidate-head'><div><div class='candidate-code'>"+esc(x.code)+"</div><div class='candidate-stage'>"+esc(x.stage)+"</div></div><span class='badge "+badge+"'>"+state+"</span></div>"+
      "<div class='candidate-main'>"+
        "<div class='ring-wrap'><div class='progress-ring' style='--pct:"+overall+"'><div><strong>"+overall+"%</strong><span>Gesamt</span></div></div></div>"+
        "<div class='candidate-detail'>"+
          "<div class='metric-title'>Nächster Milestone</div><div class='milestone'>"+esc(x.next_gate||"nicht aufgezeichnet")+"</div>"+
          "<div class='metric-row'><span>Fortschritt zum Milestone</span><strong>"+next+"%</strong></div>"+
          progressBar(next,true)+
          "<div class='small muted'>"+esc(x.next_milestone_progress_basis||"keine aktive Workflow-Basis")+"</div>"+
        "</div>"+
      "</div>"+
      "<div class='candidate-foot'><span>"+esc(x.overall_progress_basis||"Entwicklungsindex")+"</span><span>"+(x.performance_authorization_allowed?"AUTORISIERUNG ERLAUBT":"NICHT AUTORISIERT")+"</span></div>"+
    "</article>";
  }).join(""):"<div class='empty'>Kein Fokus-Kandidat im Snapshot.</div>";

  var order={"Windows self-hosted A":0,"Windows self-hosted B":1,"Windows self-hosted C":2,"GitHub-hosted Ubuntu x64":3,"GitHub-hosted ARM64":4,"Free AI pool":5};
  resources.sort(function(a,b){return order[a.name]-order[b.name];});
  $("capacity").innerHTML="<div class='capacity-grid'>"+resources.map(function(x){
    var st=capacityState(x,data);
    var role=esc(x.role||"");
    var active=Number(x.current_assignments||0);
    var free=Number(x.research_slots_free||0);
    return "<div class='capacity "+st.cls+"'>"+
      "<div class='name'>"+esc(x.name)+"</div>"+
      "<div class='state'>"+st.label+"</div>"+
      "<div class='role'>"+role+"</div>"+
      "<div class='capacity-numbers'><strong>"+active+"</strong> aktiv <span>·</span> <strong>"+free+"</strong> frei</div>"+
      "<div class='small muted'>Slots "+esc(x.research_slots_in_use||0)+"/"+esc(x.research_capacity_slots||1)+" · Runner "+esc(x.runner_status||"nicht sichtbar")+"</div>"+
      "</div>";
  }).join("")+"</div>";

  var s10=data.s10_support||{};
  var s10Good=String(s10.status||"") === "S10_UTILITY_ACCEPTED" && s10.eligible===true;
  $("s10").innerHTML=
    "<div class='support-card "+(s10Good?"support-ok":"support-unknown")+"'>"+
      "<div><div class='eyebrow'>Technische Support-Kapazität</div><div class='support-title'>S10 · Android / Termux</div><div class='support-role'>"+esc(s10.role||"bounded support")+"</div></div>"+
      "<div class='support-status'><span class='badge "+(s10Good?"active-badge":"unknown")+"'>"+esc(s10.status||"UNVERIFIED")+"</span><strong>"+(s10Good?"einsatzfähig":"nicht verifiziert")+"</strong></div>"+
      "<div class='support-grid'><div><span>Runner</span><strong>"+esc(s10.runner_name||"S10-TERMUX")+"</strong></div><div><span>Architektur</span><strong>"+esc(s10.architecture||"ARM64")+"</strong></div><div><span>Mode</span><strong>"+esc(s10.mode||"mechanical QA")+"</strong></div><div><span>Letztes Receipt</span><strong>"+esc(s10.latest_workflow_run_id||"—")+"</strong></div></div>"+
      "<div class='small muted'>Mechanische/provenance-/capacity-QA nur. Keine wissenschaftliche Evidenz und keine Performance-Autorisierung.</div>"+
    "</div>";

  $("work").innerHTML=work.length?
    "<table><thead><tr><th>Kapazität</th><th>Candidate</th><th>Job</th><th>Status</th><th>Start</th><th>Run</th></tr></thead><tbody>"+
    work.map(function(x){
      return "<tr><td class='rowtitle'>"+esc(x.resource)+"<div class='small muted'>"+esc(x.worker||"")+"</div></td>"+
        "<td class='rowtitle'>"+esc(candidateFrom((x.task||"")+" "+(x.job||"")))+"</td>"+
        "<td>"+esc(x.job||x.task||"—")+"</td>"+
        "<td><span class='badge active-badge'>"+esc(x.status||"—")+"</span></td>"+
        "<td>"+esc(ts(x.started_at))+"</td>"+
        "<td>"+esc(x.run_id||"—")+"</td></tr>";
    }).join("")+"</tbody></table>":"<div class='empty'>Keine aktiven Fokus-Jobs im Snapshot sichtbar.</div>";

  $("plannedQueue").innerHTML=queue.length?
    "<div class='queue-grid'>"+queue.map(function(x){
      return "<div class='queue-item'><span class='queue-rank'>"+esc(x.queue_rank)+"</span><div><strong>"+esc(x.candidate)+"</strong><div class='small'>"+esc(x.next_gate)+"</div><div class='small muted'>"+esc(x.execution_workflow)+"</div></div></div>";
    }).join("")+"</div>":"<div class='empty'>Kein bounded Next-Gate für den Fokus bereitgestellt.</div>";

  $("planned").innerHTML=planned.length?
    "<table><thead><tr><th>Kapazität</th><th>Candidate</th><th>Nächste Arbeit</th><th>Status</th></tr></thead><tbody>"+
    planned.map(function(x){
      var items=(x.planned_assignments||[]).filter(function(p){return FOCUS.indexOf(p.candidate)>=0;});
      return items.map(function(p){
        var status=p.dispatchable?"READY / AUTO-DISPATCH":(p.scheduled?"GEPLANT / NICHT GESTARTET":"BLOCKIERT / KEINE DISPOSITION");
        var cls=p.dispatchable?"planned-badge":(p.scheduled?"planned-badge":"blocked-badge");
        return "<tr><td class='rowtitle'>"+esc(x.resource)+"</td><td>"+esc(p.candidate)+"</td><td>"+esc(p.task)+"<div class='small muted'>"+esc(p.basis||"")+"</div></td><td><span class='badge "+cls+"'>"+status+"</span></td></tr>";
      }).join("");
    }).join("")+"</tbody></table>":"<div class='empty'>Kein fokussierter Plan-Slot im Snapshot.</div>";

  var milestones=data.milestone_history_12h||[];
  $("milestones12h").innerHTML=milestones.length?
    "<table><thead><tr><th>Zeit</th><th>Typ</th><th>Meilenstein</th><th>Ergebnis</th></tr></thead><tbody>"+
    milestones.map(function(x){
      var title=x.url?"<a href='"+esc(x.url)+"' target='_blank' rel='noopener'>"+esc(x.title||"Meilenstein")+"</a>":esc(x.title||"Meilenstein");
      return "<tr><td>"+esc(ts(x.timestamp))+"</td><td>"+esc(x.kind||"—")+"</td><td class='rowtitle'>"+title+"<div class='small muted'>"+esc(x.detail||"")+"</div></td><td>"+esc(x.status||"—")+"</td></tr>";
    }).join("")+"</tbody></table>":"<div class='empty'>Keine passenden abgeschlossenen Meilensteine in den letzten 12 Stunden.</div>";

  var highlights=(cr.highlights||[]).slice(-6);
  $("achieved").innerHTML=
    "<div class='formal-result'><span class='eyebrow'>Letztes formales Ergebnis</span><strong>"+esc(cr.latest_formal_result||"nicht aufgezeichnet")+"</strong></div>"+
    "<div class='highlight-list'>"+(highlights.length?highlights.map(function(x){return "<div>"+esc(x)+"</div>";}).join(""):"<div class='empty'>Keine Highlights im Snapshot.</div>")+"</div>"+
    "<div class='scientific-lock'>Performance, Holdout, Ranking, Tuning, Promotion und Live-Ausführung bleiben fail-closed.</div>";

  $("opsSummary").innerHTML=
    "<span><strong>"+esc(s.research_capacity_slots_total||0)+"</strong> Research-Slots</span>"+
    "<span><strong>"+esc(s.research_capacity_slots_free||0)+"</strong> frei</span>"+
    "<span><strong>"+esc(s.planned_research_queue_items||0)+"/"+esc(s.planned_research_queue_target||2)+"</strong> Fokus-Backlog</span>"+
    "<span><strong>"+esc((data.dashboard_summary||{}).runner_api_status||"unverified")+"</strong> Runner-Telemetrie</span>";

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
    else{$("meta").insertAdjacentHTML("beforeend"," · <span class='unknown'>Netzwerk-Refresh nicht verfügbar; eingebetteter Snapshot bleibt sichtbar.</span>");}
  }).then(function(){if(timeoutId!==null)clearTimeout(timeoutId);});
}
document.addEventListener("DOMContentLoaded",function(){
  updateClock();
  setInterval(updateClock,1000);
  setInterval(updateSnapshotAge,1000);
  $("refresh").addEventListener("click",load);
  load();
  setInterval(load,180000);
});
})();