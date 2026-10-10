(function(){
"use strict";
var lastSnapshotIso=null;
var FOCUS=["Q104:I19","Q220","Q218"];

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
    "Q218":{
      name:"SEC disclosure event pairing",
      mechanism:"Mandatory/voluntary 10-K → 8-K Item 2.02 pairing with acceptance-time lineage",
      lane:"FRONTIER DISCOVERY",
      cardClass:"candidate-q218"
    }
  };
  return map[code]||{name:code,mechanism:"",lane:"RESEARCH",cardClass:""};
}
function candidateStatus(x){
  var status=String(x.current_milestone_status||"").toLowerCase();
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
    {
      code:"Q104:I19",cls:"decision-q104",disposition:"Weiter · Single-flight",
      title:"13F-Abdeckung zuerst schließen",
      advance:"Den bereits laufenden Census nicht duplizieren. Nach dessen terminalem Zustand nur fehlgeschlagene Shards nach Behebung des Bootstrap-/Runner-Fehlers gezielt wiederholen; erfolgreiche Receipts bleiben unverändert.",
      stop:"Runner-, Netzwerk- oder Python-Bootstrap-Fehler sind kein wissenschaftlicher Falsifikator. Parken nur, wenn nach begrenzter Reparatur historische Security-Identität, Coverage oder Acceptance-Time-Lineage nicht belegbar ist."
    },
    {
      code:"Q220",cls:"decision-q220",disposition:"Weiter · PIT-Compiler",
      title:"Positive Population in einen PIT-Zustand überführen",
      advance:"Den fixierten As-filed-Pool mit Acceptance-Time und historischem Filing-Präfix kompilieren; Taxonomie-, TextBlock-, XSD- und Presentation-Zuordnung deterministisch einfrieren und anschließend unabhängig reproduzieren.",
      stop:"Fail-closed, falls historische öffentliche Uhr, Schema-/Taxonomie-Drift oder das narrative/strukturierte Mapping nicht eindeutig rekonstruierbar ist. Keine Performance-Auswertung vor erfolgreicher unabhängiger PIT-Reproduktion und separater Autorisierung."
    },
    {
      code:"Q218",cls:"decision-q218",disposition:"Begrenzt · Provenance/PIT",
      title:"Aktuellen Kontext unabhängig abgleichen",
      advance:"Original-Resultat, aktuelle Master-Code-Fingerprints, fixierten Vertrag/Präregistrierung und Quell-/Event-Pair-Receipts reconciliieren; die PIT-Lineage unabhängig reproduzieren. Die abgeschlossenen One-shot- und 8-Paar-Replikationsläufe nicht wiederholen.",
      stop:"Parken, wenn Ergebnis und aktueller Code-Kontext nicht reconciliierbar sind, PIT ungültig/unreproduzierbar ist oder der Mechanismus gegenüber bestehender Disclosure-Divergence-Literatur nicht hinreichend separierbar ist. Kein neuer outcome-bearing Lauf ohne separate exakte formale Autorisierung."
    }
  ];
  var host=$("candidateDecisionRules");
  if(!host)return;
  host.innerHTML=
    "<div class='decision-board-head'><div><div class='section-kicker'>Decision control · receipt-first</div><div class='decision-board-title'>Nächster Schritt, Falsifikator und Wechselregel</div></div><div class='small muted'>Forschungsdisposition — keine Rendite-Rangliste oder Erfolgswahrscheinlichkeit.</div></div>"+
    "<div class='decision-grid'>"+rules.map(function(r){
      var x=byCode[r.code]||{};
      var status=String(x.current_milestone_status||"nicht im Snapshot").replace(/_/g," ").toUpperCase();
      var gate=String(x.current_milestone||x.next_gate||"Kein Gate im Snapshot");
      return "<article class='decision-card "+r.cls+"' data-decision-candidate='"+esc(r.code)+"'>"+
        "<div class='decision-head'><div class='decision-code'>"+esc(r.code)+"</div><span class='decision-disposition'>"+esc(r.disposition)+"</span></div>"+
        "<div class='decision-current'>Snapshot-Gate: <strong>"+esc(status)+"</strong> · "+esc(gate)+"</div>"+
        "<div class='decision-field'><strong>Nächster zulässiger Schritt</strong><b>"+esc(r.title)+".</b> "+esc(r.advance)+"</div>"+
        "<div class='decision-field'><strong>Stop-/Wechselregel</strong>"+esc(r.stop)+"</div>"+
      "</article>";
    }).join("")+"</div>"+
    "<div class='decision-fallback'><strong>Reserve Q221:</strong> erst nach dokumentiertem Park-/Ersatzentscheid für Q218. Vor einer Aufnahme genügt zunächst ein enges Go/No-Go zur historischen USAspending-Veröffentlichungsuhr, Award-vs.-Modification-Semantik, Behördenausnahmen und Recipient-to-Issuer-Zuordnung. Keine automatische Erweiterung der Top-3 oder künstliche Kapazitätsbelegung.</div>";
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
  var queue=(data.planned_research_queue||[]).filter(function(x){return FOCUS.indexOf(x.candidate)>=0;}).slice(0,3);
  var cr=data.current_research||{};
  lastSnapshotIso=data.generated_at_utc||null;

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
    "<div class='focus-kpi'><span class='eyebrow'>Aktive Top-3</span><strong>Q104:I19 · Q220 · Q218</strong><span>Drei getrennte Forschungsaufträge; weitere Kandidaten bleiben pausiert.</span></div>"+
    "<div class='focus-kpi'><span class='eyebrow'>Entwicklungsindex</span><strong>"+overallAvg+"%</strong><span>arithmetischer Index der drei Tracks, keine Erfolgswahrscheinlichkeit</span></div>"+
    "<div class='focus-kpi'><span class='eyebrow'>Aktive Candidate-Jobs</span><strong>"+activeCount+"</strong><span>sichtbar in der aktuellen Actions-Telemetrie</span></div>";

  $("candidateFocus").innerHTML=pipeline.length?pipeline.map(function(x){
    var active=Boolean(x.active);
    var overall=pct(x.overall_progress_percent), next=pct(x.next_milestone_progress_percent);
    var info=candidateInfo(x.code);
    var status=candidateStatus(x);
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
// Forschungsressourcen aktiv = distinct research resources, not raw job count.
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
  load();
  setInterval(load,180000);
});
})();