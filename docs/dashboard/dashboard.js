(function(){
"use strict";
var lastSnapshotIso=null;
var lastFetchIso=null;
var refreshInFlight=false;
var hasRenderedSnapshot=false;
var refreshIntervalMs=180000;
var lastRenderedSnapshotKey=null;
var FOCUS=["Q104:I19","Q220","Q221"];

function $(id){return document.getElementById(id);}
function esc(v){
  return String(v==null?"":v)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;").replace(/'/g,"&#39;");
}
function safeHttpsUrl(v){
  try{var u=new URL(String(v||""));return u.protocol==="https:"?u.href:"";}
  catch(e){return "";}
}
function ts(v){
  if(!v)return "—";
  try{return new Date(v).toLocaleString("de-DE",{dateStyle:"short",timeStyle:"medium"});}
  catch(e){return String(v);}
}
function fmtDuration(sec){
  if(sec==null||!Number.isFinite(Number(sec)))return "nicht geschätzt";
  sec=Math.max(0,Math.round(Number(sec)));
  if(sec<60)return sec+" s";
  var min=Math.round(sec/60);
  if(min<60)return min+" min";
  var h=Math.floor(min/60),m=min%60;
  if(h<48)return h+" h"+(m?" "+m+" min":"");
  var d=Math.floor(h/24),rh=h%24;
  return d+" d"+(rh?" "+rh+" h":"");
}
function durationBenchmarkLabel(p50,p90,count){
  if(p50==null||!Number.isFinite(Number(p50)))return "Keine belastbare Vergleichsbasis";
  return "P50 "+fmtDuration(p50)+(p90!=null&&Number.isFinite(Number(p90))?" · P90 "+fmtDuration(p90):"")+" · n="+String(count||0);
}
function remainingRunLabel(item){
  if(String(item.status||"")!=="in_progress")return "Run noch nicht gestartet";
  if(item.expected_duration_seconds==null)return "Keine historische Laufzeitbasis";
  if(!item.p50_elapsed_exceeded)return "ca. "+fmtDuration(item.remaining_seconds)+" bis P50";
  if(item.expected_duration_p90_seconds!=null&&!item.p90_elapsed_exceeded)return "P50 überschritten · ca. "+fmtDuration(item.remaining_p90_seconds)+" bis P90";
  return "P"+(item.expected_duration_p90_seconds!=null?"90":"50")+" überschritten · Restlaufzeit offen";
}
function pipelineDurationLabel(item){
  if(!item.scheduled)return "Keine Schätzung · prerequisite blockiert";
  if(item.expected_duration_seconds==null)return "Noch nicht kalibriert";
  return durationBenchmarkLabel(item.expected_duration_seconds,item.expected_duration_p90_seconds,item.duration_sample_count);
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
  if(lastSnapshotIso){
    var t=Date.parse(lastSnapshotIso);
    if(Number.isFinite(t))$("snapshotAge").textContent=fmtSnapshotAge(Math.max(0,(Date.now()-t)/1000));
  }
}
function snapshotKey(data){
  return [data.master_sha||"",data.generated_at_utc||"",data.operational_snapshot_sha||""].join("|");
}
function setRefreshStatus(mode,message){
  var el=$("refreshStatus");
  if(!el)return;
  el.className="refresh-status muted "+mode;
  el.textContent=message;
}
function refreshStatusMessage(mode,error){
  var snapshot=lastSnapshotIso?ts(lastSnapshotIso):"Zeitstempel nicht verfügbar";
  var fetched=lastFetchIso?ts(lastFetchIso):"noch kein erfolgreicher Browser-Abruf";
  if(mode==="loading"){
    return lastFetchIso
      ? "Prüfe auf einen neueren veröffentlichten Snapshot. Letzter erfolgreicher Browser-Abruf: "+fetched+". Der vorhandene Stand bleibt sichtbar."
      : "Lade den zuletzt veröffentlichten Snapshot. Der Browser fragt alle 3 Minuten ab; der Server-Snapshot wird planmäßig etwa alle 5 Minuten neu erzeugt. Dieser Vorgang startet keinen Workflow.";
  }
  if(mode==="success"){
    return "Snapshot verfügbar · Datenstand "+snapshot+" · letzter erfolgreicher Browser-Abruf "+fetched+". Browser-Abruf alle 3 Minuten; neue Server-Snapshots ungefähr alle 5 Minuten.";
  }
  return "Snapshot-Abruf fehlgeschlagen ("+(error||"Netzwerkfehler")+") · letzter sichtbarer Datenstand "+snapshot+" · letzter erfolgreicher Browser-Abruf "+fetched+". Vorhandene Ansicht bleibt erhalten; neuer Versuch folgt automatisch.";
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
  var normalized=String(text||"").toUpperCase().replace(/[^A-Z0-9]/g,"");
  for(var i=0;i<FOCUS.length;i++){
    var key=FOCUS[i].toUpperCase().replace(/[^A-Z0-9]/g,"");
    if(normalized.indexOf(key)>=0)return FOCUS[i];
  }
  return "—";
}
function candidateInfo(code){
  var map={
    "Q104:I19":{
      name:"Institutional demand × accrual state",
      mechanism:"Fixed-concept accrual state × 13F institutional-ownership transitions",
      lane:"FORMAL READINESS",
      cardClass:"candidate-q104"
    },
    "Q220":{
      name:"As-filed XBRL representation gap",
      mechanism:"Narrative TextBlock versus structured XBRL mapping; fixed issuer pool and taxonomy drift",
      lane:"FRONTIER DISCOVERY",
      cardClass:"candidate-q220"
    },
    "Q221":{
      name:"Government R&D → procurement option value",
      mechanism:"Public R&D awards, competition/agency state and pre-event capability; historical USAspending clock and issuer mapping first",
      lane:"FRONTIER DISCOVERY",
      cardClass:"candidate-q221"
    },
    "Q218":{
      name:"SEC disclosure event pairing (archived / outside active focus)",
      mechanism:"Historical evidence retained; no active Top-3 dispatch",
      lane:"ARCHIVED · OUTSIDE ACTIVE FOCUS",
      cardClass:"candidate-q218"
    }
  };
  return map[code]||{name:code,mechanism:"",lane:"RESEARCH",cardClass:""};
}
function candidateStatus(x){
  var status=String(x.current_milestone_status||"").toLowerCase();
  if(x.next_workpack_required)return {label:"WORKPACK OFFEN",cls:"blocked-badge"};
  // Scientific gate outcome outranks ancillary job activity. A route probe can
  // remain queued while the fixed population it supports is already blocked.
  if(status==="blocked"||status.indexOf("blocked")>=0){
    return x.code==="Q218"
      ?{label:"FOLGEGATE GESPERRT",cls:"blocked-badge"}
      :{label:"DATEN-GATE BLOCKIERT",cls:"blocked-badge"};
  }
  if(x.active)return {label:"ARBEIT LÄUFT",cls:"active-badge"};
  if(status==="complete"||status==="completed")return {label:"MEILENSTEIN ERREICHT",cls:"active-badge"};
  if(status==="ready")return {label:"NÄCHSTES GATE BEREIT",cls:"planned-badge"};
  if(status==="running")return {label:"GATE LÄUFT",cls:"active-badge"};
  return {label:"GATE OFFEN",cls:"planned-badge"};
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
  var runnerBusy=x.runner_busy===true;
  var runnerUnknown=x.runner_busy==null;
  var runnerOnline=String(x.runner_status||"").toLowerCase()==="online";
  if(active)return {cls:"operating",label:"ARBEITET"};
  if(runnerBusy)return {cls:"unknown",label:"RUNNER BESETZT"};
  if(x.type==="physical"&&runnerUnknown)return {cls:"unknown",label:"RUNNER-STATUS UNBEKANNT"};
  if(dispatchable)return {
    cls:"planned",
    label:(x.type==="physical"&&!runnerOnline)?"AUTO-DISPATCH GEPLANT":"AUTO-DISPATCH BEREIT"
  };
  if(String(x.capacity_state||"") === "available")return {cls:"available",label:"VERFÜGBAR"};
  return {cls:"unknown",label:"NICHT VERIFIZIERT"};
}
function renderProgressCharts(data,pipeline){
  var byCode={};
  (pipeline||[]).forEach(function(x){byCode[x.code]=x;});
  var overall=pipeline||[];
  $("overallProgressBars").innerHTML=overall.length?overall.map(function(x){
    var v=pct(x.overall_progress_percent);
    return "<div class='bar-row'>"+
      "<div class='bar-meta'><span class='bar-label'>"+esc(x.code)+"</span><span class='bar-value'>"+v+"%</span></div>"+
      "<div class='bar-track'><div class='bar-fill' style='width:"+v+"%'></div></div>"+
      "<div class='bar-sub'>"+esc(x.overall_progress_basis||"Entwicklungsindex")+"</div>"+
    "</div>";
  }).join(""):"<div class='empty'>Keine fokussierten Kandidaten im Snapshot.</div>";

  $("milestoneProgressBars").innerHTML=overall.length?overall.map(function(x){
    var v=pct(x.next_milestone_progress_percent);
    var status=String(x.current_milestone_status||"").toUpperCase();
    return "<div class='bar-row'>"+
      "<div class='bar-meta'><span class='bar-label'>"+esc(x.code)+" · "+esc(x.current_milestone||"aktueller Milestone")+"</span><span class='bar-value'>"+v+"%</span></div>"+
      "<div class='bar-track'><div class='bar-fill milestone' style='width:"+v+"%'></div></div>"+
      "<div class='bar-sub'>"+esc(status)+" · "+esc(x.next_milestone_progress_basis||"Milestone nicht verifiziert")+"</div>"+
    "</div>";
  }).join(""):"<div class='empty'>Kein Milestone-Status verfügbar.</div>";
}


function renderCandidateDecisionRules(pipeline){
  var byCode={};
  (pipeline||[]).forEach(function(x){byCode[x.code]=x;});
  var rules=[
    {code:"Q104:I19",cls:"decision-q104",mode:"Weiter · Single-flight",title:"Historische 13F-Vollständigkeit schließen",
     advance:"Bestehende Census-Ausführung bzw. nützlichen Nachfolger bis zum terminalen Ergebnis verfolgen. Danach nur fehlende Shard-/Header-Belege gezielt wiederherstellen; anschließend den fixierten konzeptspezifischen PIT-Zustand kompilieren und unabhängig reproduzieren.",
     stop:"Runner- oder Bootstrap-Fehler sind kein wissenschaftlicher Falsifikator. Parken, falls begrenzte Reparatur historische Security-Identität, Abdeckung oder SEC-Acceptance-Time-Lineage nicht belastbar rekonstruieren kann."},
    {code:"Q220",cls:"decision-q220",mode:"Weiter · PIT-Compiler",title:"Positive Population historisch kompilieren",
     advance:"Der versiongebundene Populationsbeleg umfasst 55 Filing-Datensätze aus acht fixierten Emittenten ohne Datensatzfehler. Als Nächstes den historischen Filing-Präfix-/Acceptance-Time- und Representation-State-Compiler bauen; TextBlock-, XSD-, Taxonomie- und Presentation-Mapping einfrieren.",
     stop:"Fail-closed, wenn die historische öffentliche Zeitgrenze nicht rekonstruierbar ist, Schema-/Taxonomie-Drift die Zuordnung mehrdeutig macht oder der narrative/strukturierte Gap nicht deterministisch messbar ist. Der Free-AI-CYD-Output war inhaltlich unbrauchbar, keine wissenschaftliche Evidenz."},
    {code:"Q221",cls:"decision-q221",mode:"Weiter · Public clock",title:"USAspending-Veröffentlichungsuhr rekonstruieren",
     advance:"Den begrenzten USAspending-Workpack parallel zu Q220 starten, sobald unabhängige Kapazität frei ist: historische Veröffentlichungsvintages und Transaktionsklassen sichern, DoD/USACE-90-Tage- und FAR-Ausnahmen klassifizieren und Recipient-to-Issuer-Mapping einfrieren. PIT-Validierung folgt erst danach.",
     stop:"Der aktuelle Live-Source-Marker ist kein historischer Nachweis. Fail-closed, wenn Veröffentlichungs-Vintage/Public-Clock, Ausnahmeklassen, Transaktionszustände oder das vorab fixierte Empfänger-zu-Emittent-Mapping nicht belastbar rekonstruierbar sind."}
  ];
  var host=$("candidateDecisionRules");
  if(!host)return;
  host.innerHTML="<div class='decision-board-head'><div><div class='section-kicker'>Receipt-first · aktuelle Gates</div><div class='decision-board-title'>Nächster Schritt und Stop-Regel je aktivem Kandidaten</div></div><div class='small muted'>Ressourcenpriorität, keine Rendite-Rangliste.</div></div><div class='decision-grid'>"+
    rules.map(function(r){var x=byCode[r.code]||{};if(r.code==="Q220"&&x.next_workpack_required){r=Object.assign({},r,{mode:"WORKPACK OFFEN · NICHT AUTO-DISPATCH",title:"Neues begrenztes Robustheits-/Governance-Workpack definieren",advance:"Die 55/55 Population-, PIT-Compiler- und unabhängigen Reproduktionsbelege sind positiv; ein ausführbares nächstes Workpack ist noch nicht definiert. Keine automatische Disposition oder Performancefreigabe."});}else if(r.code==="Q220"&&x.current_milestone){r=Object.assign({},r,{title:String(x.current_milestone),advance:String(x.next_gate||r.advance)});}var status=String(x.current_milestone_status||"nicht im Snapshot").replace(/_/g," ").toUpperCase();var gate=String(x.current_milestone||x.next_gate||"Kein Gate im Snapshot");return "<article class='decision-card "+r.cls+"'><div class='decision-head'><div class='decision-code'>"+esc(r.code)+"</div><span class='decision-disposition'>"+esc(r.mode)+"</span></div><div class='decision-current'>Snapshot-Gate: <strong>"+esc(status)+"</strong> · "+esc(gate)+"</div><div class='decision-field'><strong>Nächster zulässiger Schritt</strong><b>"+esc(r.title)+".</b> "+esc(r.advance)+"</div><div class='decision-field'><strong>Stop-/Falsifikationsregel</strong>"+esc(r.stop)+"</div></article>";}).join("")+"</div>"+
    "<div class='decision-fallback'><strong>Archiviert, nicht aktiv:</strong> Q218 ist aus aktivem Fokus und automatischem Dispatch entfernt. One-shot und Acht-Ereignis-Replikation bleiben deskriptiv archiviert und werden nicht wiederholt. Q219 bleibt pausiert. Keine künstlichen Aufgaben und keine Performance-, Holdout-, Tuning-, Ranking-, Promotion- oder Live-Trading-Autorisierung aus dem Dashboard.</div>";
}

function renderCandidatePortfolio(data){
  var items=data.candidate_portfolio||[];
  var method=data.candidate_portfolio_methodology||{};
  var searchEl=$("portfolioSearch"), tierEl=$("portfolioTier");
  if(!searchEl||!tierEl||!$("candidatePortfolio"))return;
  function tierLabel(x){
    var map={
      VERY_HIGH:"Sehr hoch",
      HIGH_CONDITIONAL:"Hoch · bedingt",
      MEDIUM_HIGH:"Mittel bis hoch",
      MEDIUM:"Mittel",
      MEDIUM_RISK_STATE:"Risikozustand",
      CONDITIONAL:"Quelle zuerst prüfen",
      BLOCKED_SOURCE:"Datenblocker"
    };
    return map[x]||String(x||"Unklassifiziert").replace(/_/g," ");
  }
  function tierClass(x){
    if(x==="VERY_HIGH"||x==="HIGH_CONDITIONAL")return "potential-high";
    if(x==="BLOCKED_SOURCE")return "potential-blocked";
    return "potential-mid";
  }
  function renderRows(){
    var q=String(searchEl.value||"").trim().toLowerCase();
    var filter=String(tierEl.value||"ALL");
    var selected=items.filter(function(x){
      if(filter!=="ALL"&&x.tier!==filter)return false;
      var hay=[x.code,x.name,x.mechanism,x.current_state,x.next_gate,x.blocker,x.why,x.first_falsifier,x.portfolio_action].join(" ").toLowerCase();
      return !q||hay.indexOf(q)>=0;
    });
    $("portfolioCount").textContent=selected.length+" / "+items.length+" Kandidaten";
    if(!selected.length){
      $("candidatePortfolio").innerHTML="<div class='empty'>Keine Kandidaten entsprechen diesem Filter.</div>";
      return;
    }
    $("candidatePortfolio").innerHTML="<table class='portfolio-table'><thead><tr>"+
      "<th>Rang</th><th>Kandidat / Mechanismus</th><th>Forschungs-<br>potenzial</th><th>Aktueller Evidenzstand</th><th>Nächstes hartes Gate / Blocker</th><th>Planungsdauer</th><th>Strategie-Erfolgschance</th>"+
      "</tr></thead><tbody>"+selected.map(function(x){
        var tier=tierLabel(x.tier), cls=tierClass(x.tier);
        var oddsTitle=(method.success_probability||"Erfolgschance nicht schätzbar");
        var action=String(x.portfolio_action||"").replace(/_/g," ");
        var why=x.why||"";
        var falsifier=x.first_falsifier||"";
        var blocker=x.blocker||"";
        return "<tr>"+
          "<td><div class='portfolio-rank'>"+esc(x.rank)+"</div><div class='small muted'>"+(x.separate_workpack_allowed===false?"gebündelt":"Priorität")+"</div></td>"+
          "<td><div class='portfolio-code'>"+esc(x.code)+"</div><div class='portfolio-name'>"+esc(x.name)+"</div>"+
            "<div class='portfolio-mechanism'>"+esc(x.mechanism||"")+"</div>"+
            "<details class='portfolio-details'><summary>Begründung und billiger Falsifikator</summary><div><strong>Warum:</strong> "+esc(why)+"</div><div><strong>Früher Falsifikator:</strong> "+esc(falsifier)+"</div><div><strong>Disposition:</strong> "+esc(action)+"</div></details></td>"+
          "<td class='portfolio-tier'><span class='"+cls+"'>"+esc(tier)+"</span><div class='small muted'>"+esc(x.potential||"")+"</div></td>"+
          "<td>"+esc(x.current_state||"nicht erfasst")+"</td>"+
          "<td><strong>"+esc(x.next_gate||"Nicht dokumentiert")+"</strong><div class='small muted' style='margin-top:4px'><strong>Blocker:</strong> "+esc(blocker)+"</div></td>"+
          "<td class='portfolio-eta'><strong>Nächstes Gate</strong>"+esc(x.next_gate_eta||"nicht geschätzt")+"<div style='margin-top:7px'><strong>Bis unabh. PIT</strong>"+esc(x.independent_pit_eta||"nicht geschätzt")+"</div><div class='small muted'>"+esc(x.duration_estimate_confidence==="LOW_PLANNING_RANGE"?"niedrige Vertrauensstufe":"nicht kalibriert")+"</div></td>"+
          "<td class='portfolio-odds' title='"+esc(oddsTitle)+"'>Nicht schätzbar<div class='small muted'>Keine unabhängige, kostenbereinigte OOS-Basis</div></td>"+
        "</tr>";
      }).join("")+"</tbody></table>";
  }
  if(!searchEl.dataset.bound){
    searchEl.addEventListener("input",renderRows);
    tierEl.addEventListener("change",renderRows);
    searchEl.dataset.bound="1";
  }
  renderRows();
}

function renderCandidateIntake(data){
  var plan=data.candidate_intake_plan||{};
  var summary=plan.summary||{};
  var rows=plan.candidates||[];
  var host=$("candidateIntake");
  if(!host)return;
  var focus=(plan.active_focus_lock||FOCUS).join(" · ");
  host.innerHTML=
    "<div class='ops-strip'>"+
      "<span><strong>"+esc(summary.total_candidates||0)+"</strong> Vorschläge</span>"+
      "<span><strong>"+esc(summary.validated_quarantined||0)+"</strong> validiert, quarantänisiert</span>"+
      "<span><strong>"+esc(summary.blocked||0)+"</strong> blockiert</span>"+
      "<span><strong>"+esc(summary.dispatchable_now||0)+"</strong> automatisch disponiert</span>"+
    "</div>"+
    "<div class='small muted' style='margin:8px 0'>Status: <strong>"+esc(plan.status||"UNBEKANNT")+"</strong> · Fokus gesperrt: "+esc(focus)+" · Plan-Fingerprint: "+esc(plan.plan_fingerprint||"—")+"</div>"+
    (plan.queue_error?"<div class='empty'>Queue-Fehler: "+esc(plan.queue_error)+"</div>":"")+
    (rows.length?
      "<div style='overflow-x:auto'><table><thead><tr><th>Reihenfolge</th><th>Kandidat</th><th>Disposition</th><th>Nächster Falsifikator</th><th>Kapazität</th></tr></thead><tbody>"+
      rows.map(function(x){
        var blocked=String(x.status||"").indexOf("BLOCKED")===0;
        var badgeClass=blocked?"blocked-badge":"planned-badge";
        var falsifier=(x.cheap_falsifiers||[])[0]||x.next_gate||"Falsifikator fehlt";
        return "<tr><td>"+esc(x.queue_position||"—")+"</td>"+
          "<td class='rowtitle'>"+esc(x.candidate_id)+"<div class='small muted'>"+esc(x.candidate_name||"")+"</div></td>"+
          "<td><span class='badge "+badgeClass+"'>"+esc(x.status||"UNBEKANNT")+"</span><div class='small muted'>"+esc(x.reason||"")+"</div></td>"+
          "<td>"+esc(falsifier)+"</td>"+
          "<td>"+(x.dispatchable?"DISPATCHABLE":"KEINE ZUTEILUNG")+"</td></tr>";
      }).join("")+
      "</tbody></table></div>":
      "<div class='empty'>Intake-Queue ist leer. Keine Rechenarbeit, keine Kapazitätsbelegung. Neue Vorschläge in research/candidates/candidate_intake_queue.json eintragen.</div>"
    )+
    "<div class='small muted' style='margin-top:8px'>FIFO statt Rendite-Ranking. Neue Kandidaten bleiben nicht-authorisierende Hypothesen. Explizite Fokusentscheidung vor jeder Kapazitätszuteilung erforderlich.</div>";
}


function operationStatusClass(status){
  var s=String(status||"").toLowerCase();
  if(s==="in_progress"||s==="running"||s.indexOf("aktiv")>=0||s.indexOf("läuft")>=0)return "active-badge";
  if(s==="queued"||s==="pending"||s==="waiting"||s==="ready"||s.indexOf("bereit")>=0||s.indexOf("geplant")>=0||s.indexOf("nächstes")>=0||s.indexOf("erreicht")>=0)return "planned-badge";
  if(s.indexOf("block")>=0||s.indexOf("voraussetzung")>=0||s.indexOf("fail")>=0||s.indexOf("unknown")>=0)return "blocked-badge";
  return "blocked-badge";
}
function nextDurationLabel(item,data,code){
  var pipelineRow=(data.pipeline||[]).filter(function(x){return x.code===code;})[0]||{};
  if(pipelineRow.next_workpack_required)return "Keine ETA · neues Workpack offen";
  if(item&&item.scheduled===false)return "Keine ETA · Voraussetzung blockiert";
  if(item&&item.dispatchable===false)return "Keine ETA · nicht auto-dispatchierbar";
  if(item&&item.expected_duration_seconds!=null&&Number(item.duration_sample_count)>0){
    return durationBenchmarkLabel(item.expected_duration_seconds,item.expected_duration_p90_seconds,item.duration_sample_count);
  }
  var b=(data.job_duration_benchmarks||{})[code]||null;
  if(b&&b.p50_seconds!=null&&Number(b.sample_count)>0){
    return durationBenchmarkLabel(b.p50_seconds,b.p90_seconds,b.sample_count);
  }
  return "Nicht kalibriert";
}
function renderOperationsOverview(data,work,pipeline,planned,queue){
  var kpis=$("opsKpis"), nowTable=$("opsNowTable"), nextTable=$("opsNextTable");
  if(!kpis||!nowTable||!nextTable)return;
  var rows=Array.isArray(work)?work.slice():[];
  var running=rows.filter(function(x){return String(x.status||x.run_status||"")==="in_progress";});
  var waiting=rows.filter(function(x){return ["queued","waiting","pending"].indexOf(String(x.status||x.run_status||""))>=0;});
  var calibrated=rows.filter(function(x){return Number(x.duration_sample_count||0)>0&&x.expected_duration_seconds!=null;});
  kpis.innerHTML=
    "<div class='ops-kpi'><span>JETZT AKTIV</span><strong>"+running.length+"</strong><small>sichtbare Fokus-Jobs</small></div>"+
    "<div class='ops-kpi'><span>WARTET AUF START</span><strong>"+waiting.length+"</strong><small>Queue-Zeit separat erfasst</small></div>"+
    "<div class='ops-kpi'><span>ZEITBASIS</span><strong>"+calibrated.length+"/"+rows.length+"</strong><small>aktive Jobs mit Vergleichslaufzeiten</small></div>";
  nowTable.innerHTML=rows.length?
    "<table class='ops-table ops-compact'><thead><tr><th>Was / Kandidat</th><th>Wer / Runner</th><th>Status · Start</th><th>Bereits</th><th>Historische Dauer</th><th>Restlaufzeit</th><th>Run</th></tr></thead><tbody>"+
    rows.map(function(x){
      var runStatus=String(x.status||x.run_status||"unknown");
      var jobStatus=String(x.job_status||runStatus);
      var isRunning=runStatus==="in_progress";
      var candidate=candidateFrom((x.task||"")+" "+(x.job||""));
      var started=x.run_started_at||(isRunning?x.started_at:(x.queued_at||x.started_at));
      var elapsed=isRunning?fmtDuration(x.elapsed_seconds):"Queue "+fmtDuration(x.queue_elapsed_seconds);
      var benchmark=(Number(x.duration_sample_count||0)>0&&x.expected_duration_seconds!=null)
        ?durationBenchmarkLabel(x.expected_duration_seconds,x.expected_duration_p90_seconds,x.duration_sample_count)
        :"Nicht kalibriert";
      var remaining=isRunning?remainingRunLabel(x):"Run noch nicht gestartet";
      var url=safeHttpsUrl(x.run_url);
      var link=url?"<a href='"+esc(url)+"' target='_blank' rel='noopener'>#"+esc(x.run_id||"—")+"</a>":esc("#"+String(x.run_id||"—"));
      return "<tr>"+
        "<td><strong>"+esc(candidate)+"</strong><div class='ops-clamp'>"+esc(x.job||x.task||"Aufgabe nicht benannt")+"</div><small class='muted'>"+esc(x.task||"")+"</small></td>"+
        "<td><strong>"+esc(x.resource||"Ressource unbekannt")+"</strong><small>"+esc(x.worker||"Runner nicht zugeordnet")+"</small></td>"+
        "<td><span class='badge "+operationStatusClass(jobStatus)+"'>"+esc(jobStatus.replace(/_/g," "))+"</span><small>Run: "+esc(runStatus.replace(/_/g," "))+"</small></td>"+
        "<td><strong>"+esc(elapsed)+"</strong><small>"+esc(ts(started))+"</small></td>"+
        "<td>"+esc(benchmark)+"</td>"+
        "<td>"+esc(remaining)+"</td>"+
        "<td>"+link+"</td></tr>";
    }).join("")+"</tbody></table>"
    :"<div class='empty'>Im aktuellen Snapshot sind keine aktiven Top-3-Jobs sichtbar.</div>";

  var byCode={};(pipeline||[]).forEach(function(x){byCode[x.code]=x;});
  var queuedByCode={};(queue||[]).forEach(function(x){queuedByCode[x.candidate]=x;});
  var assignments=[];
  (planned||[]).forEach(function(r){
    (r.planned_assignments||[]).forEach(function(p){
      if(FOCUS.indexOf(p.candidate)>=0)assignments.push({resource:r.resource,item:p});
    });
  });
  function assignmentScore(rec){
    var p=rec.item;
    return (p.scheduled?4:0)+(p.dispatchable?2:0)+(p.expected_duration_seconds!=null?1:0);
  }
  function plannedFor(code){
    return assignments.filter(function(rec){return rec.item.candidate===code;}).sort(function(a,b){return assignmentScore(b)-assignmentScore(a);})[0]||null;
  }
  function statusFor(code,pipe,rec,activeRows){
    if(activeRows.length)return "AKTIVER RUN LÄUFT · NICHT DUPLIZIEREN";
    if((pipe||{}).next_workpack_required)return "WORKPACK OFFEN · NICHT AUTO-DISPATCH";
    if(rec){
      var p=rec.item;
      var readiness=String(p.readiness||"").toUpperCase();
      if(p.scheduled===false||p.dispatch_condition==="ADVISORY_ONLY"||readiness.indexOf("NEEDS_NEW_WORKPACK")>=0||p.dispatchable===false){
        return "VORAUSSETZUNG OFFEN · NICHT AUTO-DISPATCH";
      }
      if(p.dispatchable)return p.dispatch_condition==="FREE_SLOT"?"BEREIT ZU STARTEN":"BEREIT · SLOT PRÜFEN";
      return "GEPLANT · STATUS NICHT BESTÄTIGT";
    }
    var s=String((pipe||{}).current_milestone_status||"").toLowerCase();
    if(s.indexOf("block")>=0)return "BLOCKIERT";
    if(s==="ready")return "GATE BEREIT";
    if(s==="running"||s==="in_progress")return "GATE LÄUFT";
    if(s==="complete"||s==="completed")return "GATE ERREICHT";
    return "ALS NÄCHSTES ZU PRÜFEN";
  }
  nextTable.innerHTML="<table class='ops-table ops-compact ops-next-table'><thead><tr><th>Reihenfolge</th><th>Status</th><th>Was kommt als Nächstes?</th><th>Wer / Ressource</th><th>Zeitbedarf</th></tr></thead><tbody>"+
    FOCUS.map(function(code,index){
      var pipe=byCode[code]||{};
      var activeRows=rows.filter(function(x){return candidateFrom((x.task||"")+" "+(x.job||""))===code;});
      var rec=plannedFor(code), q=queuedByCode[code]||{};
      var gate=String(pipe.next_gate||pipe.current_milestone||q.next_gate||"Nächstes Gate nicht dokumentiert");
      var p=rec?rec.item:null;
      var task;
      if(activeRows.length&&code==="Q104:I19"){
        task="Nach terminalem Census: sechs Shard-Receipts abgleichen → nur belegte Header-Lücken gezielt reparieren → PIT-Compiler.";
      }else if(activeRows.length){
        task="Nach Abschluss des aktiven Runs: "+gate;
      }else if(pipe.next_workpack_required){
        task="Neues begrenztes Workpack definieren: "+gate;
      }else if(p&&p.dispatchable&&p.scheduled){
        task=String(p.task||gate);
      }else{
        task=String(pipe.next_gate||(p&&p.task)||q.next_gate||gate);
      }
      var owner;
      if(activeRows.length){
        owner="Aktiver Run zuerst · danach Ressource neu disponieren";
      }else if(p&&p.dispatchable&&p.scheduled&&rec.resource){
        owner=String(rec.resource);
      }else if(pipe.next_workpack_required){
        owner="Workpack zuerst spezifizieren · kein Runner zuordnen";
      }else if(p&&(!p.dispatchable||p.scheduled===false)){
        owner="Nicht disponieren · neues Workpack / Voraussetzung offen";
      }else{
        owner=String(q.resource_hint||"Noch nicht zugeordnet");
      }
      var status=statusFor(code,pipe,rec,activeRows);
      var estimate=nextDurationLabel(p,data,code);
      var basis=p?String(p.readiness||p.basis||""):String(pipe.next_milestone_progress_basis||pipe.current_milestone_status||"");
      if(activeRows.length)basis="Keinen Parallel-Run starten; aktiven Lauf abschließen und erst danach Receipts prüfen.";
      if(pipe.next_workpack_required)basis="PIT-Quittungskette positiv; der nächste Robustheits-/Governance-Workpack ist noch nicht definiert.";
      var cls=operationStatusClass(status);
      return "<tr><td><strong>"+(index+1)+". "+esc(code)+"</strong></td>"+
        "<td><span class='badge "+cls+"'>"+esc(status)+"</span></td>"+
        "<td><strong class='ops-clamp'>"+esc(task)+"</strong><small>"+esc(basis)+"</small></td>"+
        "<td>"+esc(owner)+"</td>"+
        "<td><strong>"+esc(estimate)+"</strong><small>Historische Vergleichslaufzeit; Wartezeit nicht enthalten</small></td></tr>";
    }).join("")+"</tbody></table>";
}

function render(data){
  lastRenderedSnapshotKey=snapshotKey(data);
  var s=data.dashboard_summary||{};
  var resources=(data.resources||[]).filter(function(x){
    return ["Windows self-hosted A","Windows self-hosted B","Windows self-hosted C","GitHub-hosted Ubuntu x64","GitHub-hosted ARM64","Free AI pool"].indexOf(x.name)>=0;
  });
  var pipeline=(data.pipeline||[]).filter(function(x){return FOCUS.indexOf(x.code)>=0;});
  var work=(data.work_assignments||[]).filter(function(x){return FOCUS.indexOf(candidateFrom((x.task||"")+" "+(x.job||"")))>=0;});
  var planned=(data.planned_capacity||[]).filter(function(x){
    return (x.planned_assignments||[]).some(function(p){return FOCUS.indexOf(p.candidate)>=0;});
  });
  var queue=(data.planned_research_queue||[]).filter(function(x){return FOCUS.indexOf(x.candidate)>=0;}).slice(0,3);
  var cr=data.current_research||{};
  lastSnapshotIso=data.generated_at_utc||null;
  renderOperationsOverview(data,work,pipeline,planned,queue);

  var handoff=data.chat_handoff||{};
  var handoffText=[
    "TRADING AGENT — CHAT HANDOFF",
    "Dashboard generated UTC: "+String(data.generated_at_utc||"unknown"),
    "Dashboard master SHA: "+String(data.master_sha||"unknown"),
    "Operational status snapshot SHA: "+String(data.operational_snapshot_sha||"unknown"),
    "Handoff generated UTC: "+String(handoff.generated_at_utc||"unknown"),
    "Handoff source master SHA: "+String(handoff.source_master_sha||"unknown"),
    "Active execution focus: "+(handoff.active_execution_focus||FOCUS).join(" | "),
    "Next research focus and decision log:",
    String(handoff.next_research_focus||"Handoff missing; verify docs/CURRENT_STATUS.md and live state before acting."),
    "Resume rule: "+String(handoff.resume_rule||"Read canonical current status first; verify live Actions/runners and immutable receipts."),
    "Safety: PAPER_ONLY="+String((handoff.safety||{}).PAPER_ONLY!==false)
      +"; LIVE_TRADING_ENABLED="+String((handoff.safety||{}).LIVE_TRADING_ENABLED===true)
      +"; ORDERS_ENABLED="+String((handoff.safety||{}).ORDERS_ENABLED===true)
      +"; AUTOMATIC_PROMOTION="+String((handoff.safety||{}).AUTOMATIC_PROMOTION===true)
      +"; paid_usage_usd="+String((handoff.safety||{}).paid_usage_usd==null?0:(handoff.safety||{}).paid_usage_usd)
  ].join("\n");
  if($("chatHandoffText"))$("chatHandoffText").value=handoffText;

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
  renderProgressCharts(data,pipeline);

  $("focusSummary").innerHTML=
    "<div class='focus-kpi'><span class='eyebrow'>Aktive Top-3</span><strong>Q104:I19 · Q220 · Q221</strong><span>Drei getrennte Forschungsaufträge; weitere Kandidaten bleiben pausiert.</span></div>"+
    "<div class='focus-kpi'><span class='eyebrow'>Entwicklungsindex</span><strong>"+overallAvg+"%</strong><span>arithmetischer Index der drei Tracks, keine Erfolgswahrscheinlichkeit</span></div>"+
    "<div class='focus-kpi'><span class='eyebrow'>Aktive Candidate-Jobs</span><strong>"+activeCount+"</strong><span>sichtbar in der aktuellen Actions-Telemetrie</span></div>";

  var decisionLog=data.handoff_decision_log||{};
  var decisions=Array.isArray(decisionLog.entries)?decisionLog.entries.slice(0,6):[];
  var handoff=data.chat_handoff||{};
  var panel=$("handoffPanel");
  if(panel){
    var focus=String(handoff.next_research_focus||"Aktuelle Next-Gate-Anweisung fehlt; kanonischen Status und Live-Läufe prüfen.");
    var sourceSha=String(handoff.source_master_sha||"nicht aufgezeichnet");
    panel.innerHTML=
      "<div class='handoff-meta'>Dashboard-Master <code>"+esc(data.master_sha||"unbekannt")+"</code> · Handoff-Quellstand <code>"+esc(sourceSha)+"</code> · Entscheidungsprotokoll <code>"+esc(decisionLog.updated_at_utc||"nicht aufgezeichnet")+"</code></div>"+
      "<p class='handoff-focus-text'>"+esc(focus)+"</p>"+
      "<h3>Letzte wichtige Entscheidungen und Sicherungspunkte</h3>"+
      "<div class='handoff-decisions'>"+(decisions.length?decisions.map(function(item){
        var url=safeHttpsUrl(item.url);
        var related=safeHttpsUrl(item.related_run_url);
        return "<article class='handoff-entry'>"+
          "<div class='handoff-status'>"+esc(item.date_utc||"")+" · "+esc(item.status||"")+"</div>"+
          "<h4>"+esc(item.title||item.candidate||"Entscheidung")+"</h4>"+
          "<p><strong>Befund / Entscheidung:</strong> "+esc(item.decision||"")+"</p>"+
          "<p><strong>Nächster Schritt:</strong> "+esc(item.next_action||"")+"</p>"+
          (url?"<a href='"+esc(url)+"' target='_blank' rel='noopener'>PR / Referenz öffnen</a> ":"")+
          (related?"<a href='"+esc(related)+"' target='_blank' rel='noopener'>Lauf öffnen</a>":"")+
        "</article>";
      }).join(""):"<div class='empty'>Noch keine gesicherten Entscheidungen.</div>")+"</div>";
  }

  $("candidateFocus").innerHTML=pipeline.length?pipeline.map(function(x){
    var active=Boolean(x.active);
    var overall=pct(x.overall_progress_percent), next=pct(x.next_milestone_progress_percent);
    var info=candidateInfo(x.code);
    var status=candidateStatus(x);
    if(x.next_workpack_required)status={label:"WORKPACK OFFEN",cls:"blocked-badge"};
    return "<article class='candidate-card "+esc(info.cardClass)+"' data-candidate='"+esc(x.code)+"'>"+
      "<div class='candidate-head'><div><div class='candidate-code'>"+esc(x.code)+"</div><div class='candidate-name'>"+esc(info.name)+"</div><div class='candidate-stage'>"+esc(x.stage)+"</div></div><span class='badge "+status.cls+"'>"+status.label+"</span></div>"+
      "<p class='candidate-mechanism'>"+esc(info.mechanism)+"</p>"+
      "<div class='candidate-main'>"+
        "<div class='ring-wrap'><div class='progress-ring' style='--pct:"+overall+"'><div><strong>"+overall+"%</strong><span>Entwicklung</span></div></div></div>"+
        "<div class='candidate-detail'>"+
          "<div class='metric-title'>Nächster Milestone</div><div class='milestone'>"+esc(x.current_milestone||x.next_gate||"nicht aufgezeichnet")+"</div>"+
          "<div class='metric-row'><span>Milestone-Fortschritt</span><strong>"+next+"%</strong></div>"+
          progressBar(next,true)+
          "<div class='gate-context' aria-label='Gate-Status, Befund und nächste Aktion'>"+
            "<div class='gate-context-row'><span class='metric-title'>Gate-Status</span><span class='badge "+(String(x.current_milestone_status||'').toLowerCase().match(/complete|ready|running|next/)?'planned-badge':'blocked-badge')+"'>"+esc(String(x.current_milestone_status||"UNBEKANNT").toUpperCase())+"</span></div>"+
            "<div class='metric-title' style='margin-top:5px'>Gate-Befund / Blocker</div>"+
            "<div class='gate-context-value'>"+esc(x.next_milestone_progress_basis||"Kein receipt-basierter Befund dokumentiert.")+"</div>"+
            "<div class='metric-title' style='margin-top:5px'>Nächste sinnvolle Aktion</div>"+
            "<div class='gate-context-value'><strong>"+esc(x.next_gate||"Keine nächste Aktion dokumentiert.")+"</strong></div>"+
          "</div>"+
          "<div class='capacity-assignment' style='margin-top:12px'>"+
            "<div class='metric-title'>Kapazitäten / Runner</div>"+
            "<div class='small'><strong>Aktiv:</strong> "+esc((x.active_capacity_assignments||[]).map(function(a){return (a.resource||"")+" · "+(a.worker||"");}).join(" | ")||"keine")+"</div>"+
            "<div class='small muted'><strong>Nächste Disposition:</strong> "+esc((x.planned_capacity_assignments||[]).map(function(a){return (a.resource||"")+" · "+(a.task||"");}).join(" | ")||"keine")+"</div>"+
          "</div>"+
          "<div class='milestone-list' style='margin-top:12px'>"+(x.milestones||[]).map(function(m){
            var mv=pct(m.progress);
            var ms=String(m.status||"").toUpperCase();
            return "<div class='milestone-item'>"+
              "<div class='label'>"+esc(m.label)+"</div>"+
              "<div><div class='bar-track'><div class='bar-fill "+(ms==="COMPLETE"?"":"milestone")+"' style='width:"+mv+"%'></div></div></div>"+
              "<div class='state'>"+esc(ms)+" · "+mv+"%</div>"+
            "</div>";
          }).join("")+"</div>"+
          "<div class='metric-title' style='margin-top:14px'>Entwicklungskette bis Abschluss</div>"+
          "<div class='development-roadmap'>"+(x.development_roadmap||[]).map(function(step){
            var rs=String(step.status||"").toUpperCase();
            var cls=rs==="COMPLETED"?"complete":(rs==="READY"?"ready":(rs==="RUNNING"?"running":(rs==="CLOSED"?"closed":"blocked")));
            return "<div class='roadmap-step'>"+
              "<div><strong>"+esc(step.label)+"</strong></div>"+
              "<div class='small "+cls+"'>"+esc(rs)+" · nächstes Kriterium: "+esc(step.next||"")+"</div>"+
            "</div>";
          }).join("")+"</div>"+
        "</div>"+
      "</div>"+
      "<div class='candidate-foot'><span>"+esc(x.overall_progress_basis||"Entwicklungsindex")+"</span><span>"+esc(x.capacity_summary||"Kapazität nicht sichtbar")+"</span><span>"+(x.performance_authorization_allowed?"AUTORISIERUNG ERLAUBT":"NICHT AUTORISIERT")+"</span></div>"+
    "</article>";
  }).join(""):"<div class='empty'>Kein Fokus-Kandidat im Snapshot.</div>";

  renderCandidateDecisionRules(pipeline);
  renderCandidatePortfolio(data);
  renderCandidateIntake(data);

  var order={"Windows self-hosted A":0,"Windows self-hosted B":1,"Windows self-hosted C":2,"GitHub-hosted Ubuntu x64":3,"GitHub-hosted ARM64":4,"Free AI pool":5};
  resources.sort(function(a,b){return order[a.name]-order[b.name];});
  $("capacity").innerHTML="<div class='capacity-grid'>"+resources.map(function(x){
    var st=capacityState(x,data);
    var role=esc(x.role||"");
    var active=Number(x.current_assignments||0);
    var freeLabel=x.research_slots_free==null?"?":String(x.research_slots_free);
    var slotsInUseLabel=x.research_slots_in_use==null?"?":String(x.research_slots_in_use);
    var queuedCount=Number(x.queued_assignments||0);
    var currentRows=work.filter(function(w){return w.resource===x.name;});
    var currentText=currentRows.slice(0,2).map(function(w){
      return candidateFrom((w.task||"")+" "+(w.job||""))+" · "+(w.job||w.task||"Research-Job")+" ["+(w.job_status||w.status||"—")+"]";
    });
    if(currentRows.length>2)currentText.push("+"+(currentRows.length-2)+" weitere aktive Jobs");
    var planRow=planned.filter(function(r){return r.resource===x.name;})[0]||{};
    var nextItems=(planRow.planned_assignments||[]).filter(function(p){return FOCUS.indexOf(p.candidate)>=0;});
    var nextText=nextItems.slice(0,2).map(function(p){
      var state=!p.scheduled?"blockiert":(p.dispatchable?(p.dispatch_condition==="FREE_SLOT"?"bereit für Dispatch":"bereit, wartet auf freien Slot"):"geplant, noch nicht startbar");
      return p.candidate+" · "+p.task+" ["+state+"]";
    });
    if(nextItems.length>2)nextText.push("+"+(nextItems.length-2)+" weitere Pipeline-Schritte");
    return "<div class='capacity "+st.cls+"'>"+
      "<div class='name'>"+esc(x.name)+"</div>"+
      "<div class='state'>"+st.label+"</div>"+
      "<div class='role'>"+role+"</div>"+
      "<div class='capacity-numbers'><strong>"+active+"</strong> aktiv <span>·</span> <strong>"+esc(freeLabel)+"</strong> frei</div>"+
      "<div class='small muted'>Slots "+esc(slotsInUseLabel)+"/"+esc(x.research_capacity_slots||1)+" · Runner "+esc(x.runner_status||"nicht sichtbar")+" · Busy-Basis "+esc(x.runner_busy_basis||"unbekannt")+" · Queue "+queuedCount+"</div>"+
      "<div class='capacity-assignments'><div class='capacity-current'><strong>Arbeitet an</strong>"+(currentText.length?currentText.map(function(v){return "<div>"+esc(v)+"</div>";}).join(""):"<div class='muted'>Keine sichtbare aktive Top-3-Zuordnung</div>")+"</div>"+
      "<div class='capacity-next'><strong>Nächster Pipeline-Schritt</strong>"+(nextText.length?nextText.map(function(v){return "<div>"+esc(v)+"</div>";}).join(""):"<div class='muted'>Kein separater Schritt disponiert</div>")+"</div></div>"+
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
    "<div class='ops-table-scroll'><table class='ops-table'><thead><tr><th>Kapazität / Runner</th><th>Kandidat / Job</th><th>Runner-Jobstatus</th><th>Run-Start / Queue</th><th>Run-Laufzeit</th><th>Historische Run-Dauer</th><th>Restlaufzeit (Run)</th><th>Actions</th></tr></thead><tbody>"+
    work.map(function(x){
      var runStatus=String(x.status||x.run_status||"—");
      var jobStatus=String(x.job_status||runStatus);
      var jobCls=jobStatus==="in_progress"?"active-badge":(jobStatus==="queued"||jobStatus==="waiting"||jobStatus==="pending"?"planned-badge":"blocked-badge");
      var startText=x.run_started_at||((runStatus==="in_progress")?x.started_at:(x.queued_at||x.started_at));
      var elapsedText=runStatus==="in_progress"?fmtDuration(x.elapsed_seconds):"Queue "+fmtDuration(x.queue_elapsed_seconds);
      var p50=durationBenchmarkLabel(x.expected_duration_seconds,x.expected_duration_p90_seconds,x.duration_sample_count);
      var link=x.run_url?"<a href='"+esc(x.run_url)+"' target='_blank' rel='noopener'>Run #"+esc(x.run_id||"—")+"</a>":"#"+esc(x.run_id||"—");
      return "<tr><td class='rowtitle'>"+esc(x.resource)+"<div class='small muted'>"+esc(x.worker||"")+"</div></td>"+
        "<td class='rowtitle'>"+esc(candidateFrom((x.task||"")+" "+(x.job||"")))+"<div class='small'>"+esc(x.job||x.task||"—")+"</div><div class='small muted'>Workflow: "+esc(x.task||"—")+"</div></td>"+
        "<td><span class='badge "+jobCls+"'>"+esc(jobStatus.replace(/_/g," "))+"</span><div class='small muted'>Run: "+esc(runStatus.replace(/_/g," "))+"</div></td>"+
        "<td>"+esc(ts(startText))+"</td>"+
        "<td>"+esc(elapsedText)+"</td>"+
        "<td title='"+esc(x.duration_source||"Keine Datenbasis")+"'>"+esc(p50)+"</td>"+
        "<td>"+esc(remainingRunLabel(x))+"</td>"+
        "<td>"+link+"</td></tr>";
    }).join("")+"</tbody></table></div>":"<div class='empty'>Keine aktiven Fokus-Jobs im Snapshot sichtbar.</div>";

  $("plannedQueue").innerHTML=queue.length?
    "<div class='queue-grid'>"+queue.map(function(x){
      var b=(data.job_duration_benchmarks||{})[x.candidate]||null;
      var estimate=durationBenchmarkLabel(b&&b.p50_seconds,b&&b.p90_seconds,b&&b.sample_count);
      return "<div class='queue-item'><span class='queue-rank'>"+esc(x.queue_rank)+"</span><div><strong>"+esc(x.candidate)+"</strong><div class='small'>"+esc(x.next_gate)+"</div><div class='small muted'>Kapazitätsziel: "+esc(x.resource_hint||"noch nicht zugeordnet")+"</div><div class='small muted'>Geschätzte Jobdauer: "+esc(estimate)+"</div><div class='small muted'>"+esc(x.execution_workflow)+"</div></div></div>";
    }).join("")+"</div>":"<div class='empty'>Kein bounded Next-Gate für den Fokus bereitgestellt.</div>";

  $("planned").innerHTML=planned.length?
    "<div class='ops-table-scroll'><table class='ops-table'><thead><tr><th>Kapazität</th><th>Kandidat</th><th>Nächste Arbeit / Blocker</th><th>Dispatch-Status</th><th>Geschätzte Jobdauer</th></tr></thead><tbody>"+
    planned.map(function(x){
      var items=(x.planned_assignments||[]).filter(function(p){return FOCUS.indexOf(p.candidate)>=0;});
      return items.map(function(p){
        var status=!p.scheduled?"BLOCKIERT / KEINE DISPOSITION":(p.dispatchable?(p.dispatch_condition==="FREE_SLOT"?"BEREIT / AUTO-DISPATCH":"BEREIT / WARTET AUF FREIEN SLOT"):"GEPLANT / VORAUSSETZUNG OFFEN");
        var cls=!p.scheduled?"blocked-badge":(p.dispatchable?"planned-badge":"blocked-badge");
        var duration=pipelineDurationLabel(p);
        return "<tr><td class='rowtitle'>"+esc(x.resource)+"</td>"+
          "<td class='rowtitle'>"+esc(p.candidate)+"<div class='small muted'>"+esc(p.lane||"")+"</div></td>"+
          "<td>"+esc(p.task)+"<div class='small muted'>"+esc(p.basis||"")+"</div><div class='small muted'>Readiness: "+esc(p.readiness||"unbekannt")+"</div></td>"+
          "<td><span class='badge "+cls+"'>"+status+"</span><div class='small muted'>"+esc(p.dispatch_condition||"")+"</div></td>"+
          "<td title='"+esc(p.duration_source||"Keine historische Vergleichsbasis")+"'>"+esc(duration)+"<div class='small muted'>Laufzeitspanne, keine Queue-Wartezeit</div></td></tr>";
      }).join("");
    }).join("")+"</tbody></table></div>":"<div class='empty'>Kein fokussierter Plan-Slot im Snapshot.</div>";

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
// Forschungsressourcen aktiv = distinct research resources, not raw job count.
function load(manual){
  if(refreshInFlight){
    if(manual)setRefreshStatus("loading","Ein Snapshot-Abruf läuft bereits; kein paralleler Abruf wird gestartet.");
    return;
  }
  refreshInFlight=true;
  var button=$("refresh");
  if(manual&&button){
    button.disabled=true;
    button.setAttribute("aria-busy","true");
    button.textContent="Snapshot wird geladen…";
  }
  $("error").hidden=true;
  setRefreshStatus("loading",refreshStatusMessage("loading"));
  if(!hasRenderedSnapshot)hasRenderedSnapshot=renderEmbedded();

  var url=new URL("dashboard_data.json",document.baseURI);
  url.searchParams.set("ts",String(Date.now()));
  var controller=typeof AbortController==="function"?new AbortController():null;
  var timeoutId=controller?setTimeout(function(){controller.abort();},6000):null;
  var opts={cache:"no-store"};
  if(controller)opts.signal=controller.signal;
  fetch(url.toString(),opts)
    .then(function(r){if(!r.ok)throw new Error("HTTP "+r.status);return r.json();})
    .then(function(data){
      if(!hasRenderedSnapshot||snapshotKey(data)!==lastRenderedSnapshotKey)render(data);
      hasRenderedSnapshot=true;
      lastFetchIso=new Date().toISOString();
      setRefreshStatus("success",refreshStatusMessage("success"));
    })
    .catch(function(e){
      var msg=e&&e.message||String(e);
      if(!hasRenderedSnapshot){
        hasRenderedSnapshot=renderEmbedded();
        if(!hasRenderedSnapshot){
          $("error").textContent="Snapshot konnte nicht geladen werden: "+msg;
          $("error").hidden=false;
        }
      }
      setRefreshStatus("warning",refreshStatusMessage("warning",msg));
    })
    .then(function(){
      if(timeoutId!==null)clearTimeout(timeoutId);
      refreshInFlight=false;
      if(manual&&button){
        button.disabled=false;
        button.removeAttribute("aria-busy");
        button.textContent="Snapshot aktualisieren";
      }
      updateSnapshotAge();
    });
}
document.addEventListener("DOMContentLoaded",function(){
  updateClock();
  setInterval(updateClock,1000);
  setInterval(updateSnapshotAge,1000);
  $("refresh").addEventListener("click",function(){load(true);});
  document.addEventListener("visibilitychange",function(){
    if(document.visibilityState==="visible")load(false);
  });
  $("copyHandoff").addEventListener("click",function(){
    var field=$("chatHandoffText");
    var status=$("copyHandoffStatus");
    if(!field)return;
    var payload=field.value;
    if(navigator.clipboard&&typeof navigator.clipboard.writeText==="function"){
      navigator.clipboard.writeText(payload).then(function(){
        if(status)status.textContent="Übergabe kopiert.";
      }).catch(function(){
        field.focus();field.select();
        var copied=false;
        try{copied=document.execCommand("copy");}catch(e){}
        if(status)status.textContent=copied?"Übergabe kopiert.":"Text markiert — bitte manuell kopieren.";
      });
    }else{
      field.focus();field.select();
      var copied=false;
      try{copied=document.execCommand("copy");}catch(e){}
      if(status)status.textContent=copied?"Übergabe kopiert.":"Text markiert — bitte manuell kopieren.";
    }
  });
  load(false);
  setInterval(function(){load(false);},refreshIntervalMs);
});
})();