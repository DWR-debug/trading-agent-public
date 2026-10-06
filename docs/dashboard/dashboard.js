(function(){
"use strict";
var WORKFLOW_URL="https://github.com/DWR-debug/trading-agent-public/actions/workflows/resource-dashboard-update.yml";
function $(id){return document.getElementById(id);}
function esc(v){
  var s=String(v==null?"":v);
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;");
}
function badge(label,value,klass){
  return "<span class='badge "+(klass||"")+"'><strong>"+esc(label)+"</strong> = "+esc(value)+"</span>";
}
function stateClass(v){
  var x=String(v||"").toUpperCase();
  if(["SUCCESS","COMPLETED","ONLINE","IN_PROGRESS","READY","SOURCE_COMPONENT_READY"].some(function(k){return x.indexOf(k)>=0;})) return "good";
  if(["QUEUED","PENDING","WAITING","PROVISIONAL","PIT_READINESS_PENDING"].some(function(k){return x.indexOf(k)>=0;})) return "warn";
  if(["FAILURE","OFFLINE","BLOCKED","FALSIFIED","NO RECENT"].some(function(k){return x.indexOf(k)>=0;})) return "bad";
  return "info";
}
function ts(v){
  if(!v) return "—";
  try{return new Date(v).toLocaleString(undefined,{dateStyle:"short",timeStyle:"medium"});}catch(e){return String(v);}
}
function link(url,text){
  return url ? "<a href='"+esc(url)+"' target='_blank' rel='noopener'>"+esc(text)+"</a>" : esc(text);
}
function render(data){
  var s=data.dashboard_summary||{};
  var rb=(data.current_research&&data.current_research.research_board)||[];
  var top4=(data.current_research&&data.current_research.top4)||rb.filter(function(x){return ["Q218","Q219","Q220","Q221"].indexOf(x.code)>=0;});
  var lm=data.lane_map||{};
  var work=data.workload||[];
  var runners=data.runner_live_snapshot||[];
  var activity=data.recent_activity_24h||[];
  var safety=data.scientific_boundary||{};
  $("meta").innerHTML="Snapshot <code>"+esc(data.generated_at_utc)+"</code> · master <code>"+esc(data.master_sha)+"</code> · operational status <code>"+esc(data.operational_snapshot_sha)+"</code>";
  $("overview").innerHTML=[
    ["Active work",s.active_work_items==null?0:s.active_work_items],
    ["Configured resources",s.configured_resources==null?0:s.configured_resources],
    ["Visible runners",s.runner_api_visible==null?"n/a":s.runner_api_visible],
    ["Busy runners",s.busy_runners==null?"n/a":s.busy_runners],
    ["Research tracks",s.research_tracks==null?0:s.research_tracks],
    ["AI providers",s.ai_providers==null?0:s.ai_providers]
  ].map(function(x){return "<div class='stat'><div class='n'>"+esc(x[1])+"</div><div class='l'>"+esc(x[0])+"</div></div>";}).join("");
  $("work").innerHTML=work.length ? "<table><thead><tr><th>Resource / worker</th><th>Lane</th><th>Task</th><th>Job</th><th>Status</th><th>Started</th><th>Actor</th></tr></thead><tbody>"+work.map(function(x){return "<tr><td><div class='rowtitle'>"+esc(x.resource)+"</div><div class='small'>"+esc(x.worker)+"</div></td><td>"+badge("lane",x.lane,stateClass(x.lane))+"</td><td>"+link(x.run_url,x.task)+"<div class='small'>Run "+esc(x.run_id)+"</div></td><td>"+esc(x.job||"—")+"</td><td>"+badge("status",x.status,stateClass(x.status))+"</td><td>"+esc(ts(x.started_at))+"</td><td>"+esc(x.actor||"—")+"</td></tr>";}).join("")+"</tbody></table>" : "<div class='empty'>No active GitHub Actions work was visible in this snapshot.</div>";
  var pipeline=data.capacity_pipeline||[];
  $("pipeline").innerHTML=pipeline.length ? "<table><thead><tr><th>Slot</th><th>Capacity</th><th>Current</th><th>Next planned job</th><th>Next gate / trigger</th><th>Basis</th><th>Mode</th></tr></thead><tbody>"+pipeline.map(function(x){return "<tr><td>"+esc(x.slot_order)+"</td><td><div class='rowtitle'>"+esc(x.resource)+"</div></td><td>"+esc(x.current||"—")+(x.current_active?badge("active","true","good"):"")+"</td><td>"+esc(x.planned_next||"—")+"</td><td>"+esc(x.next_gate||"—")+"</td><td class='small'>"+esc(x.basis||"—")+"</td><td>"+badge("mode",x.mode||"—",stateClass(x.mode))+"</td></tr>";}).join("")+"</tbody></table>" : "<div class='empty'>No deterministic capacity pipeline was published in this snapshot.</div>";
  $("top4").innerHTML=top4.length ? "<table><thead><tr><th>Candidate</th><th>Stage</th><th>Next gate</th><th>Performance authorization</th></tr></thead><tbody>"+top4.map(function(x){return "<tr><td class=\"rowtitle\">"+esc(x.code)+"</td><td>"+badge("stage",x.state,stateClass(x.state))+"</td><td>"+esc(x.next_gate||"—")+"</td><td>"+badge("allowed",x.performance_authorization_allowed?"true":"false",x.performance_authorization_allowed?"bad":"good")+"</td></tr>";}).join("")+"</tbody></table>" : "<div class=\"empty\">Top-4 candidate board is not available in this snapshot.</div>";
  $("resources").innerHTML="<table><thead><tr><th>Resource</th><th>Type</th><th>Role</th><th>Configured identity</th><th>Live state</th><th>Current assignments</th><th>Authority</th></tr></thead><tbody>"+(data.resources||[]).map(function(x){return "<tr><td><div class='rowtitle'>"+esc(x.name)+"</div></td><td>"+esc(x.type)+"</td><td>"+esc(x.role)+"</td><td><code>"+esc(x.configured_runner)+"</code></td><td>"+badge("state",x.live_status,stateClass(x.live_status))+(x.busy===true?badge("busy","true","good"):"")+"</td><td>"+esc(x.current_assignments==null?0:x.current_assignments)+"</td><td class='small'>"+esc(x.authority)+"</td></tr>";}).join("")+"</tbody></table>";
  $("lanes").innerHTML="<h3>Lane A — "+esc(lm.lane_a&&lm.lane_a.name||"FORMAL READINESS")+"</h3><div class='small'>Resource: "+esc(lm.lane_a&&lm.lane_a.slot||"Windows self-hosted A")+"</div><div>"+((lm.lane_a&&lm.lane_a.focus)||[]).map(function(x){return badge("focus",x);}).join("")+"</div><hr style='border:0;border-top:1px solid var(--border);margin:14px 0'><h3>Lane B — "+esc(lm.lane_b&&lm.lane_b.name||"FRONTIER DISCOVERY")+"</h3><div class='small'>Resource: "+esc(lm.lane_b&&lm.lane_b.slot||"Windows self-hosted B")+"</div><div>"+((lm.lane_b&&lm.lane_b.focus)||[]).map(function(x){return badge("focus",x);}).join("")+"</div><p class='small muted'>Separate candidate/trial identity, branches/workflows and immutable receipts are required.</p>";
  $("ai").innerHTML="<table><thead><tr><th>Provider</th><th>Status</th><th>Task</th><th>Observed</th><th>Mode</th><th>Model</th></tr></thead><tbody>"+(data.ai_fabric||[]).map(function(x){return "<tr><td class='rowtitle'>"+esc(x.provider)+"</td><td>"+badge("status",x.status,stateClass(x.status))+"</td><td>"+esc(x.task||"—")+"</td><td>"+esc(ts(x.observed_at_utc))+"</td><td>"+badge("free",x.free_only?"true":"false",x.free_only?"good":"bad")+"</td><td class='small'>"+esc(x.response_model||"—")+"</td></tr>";}).join("")+"</tbody></table>";
  $("research").innerHTML="<table><thead><tr><th>Code</th><th>Lane</th><th>Stage</th><th>Next gate / constraint</th><th>Perf auth</th><th>Issue</th></tr></thead><tbody>"+rb.map(function(x){return "<tr><td class='rowtitle'>"+esc(x.code)+"</td><td>"+esc(x.lane)+"</td><td>"+badge("stage",x.state,stateClass(x.state))+"</td><td>"+esc(x.next_gate)+"</td><td>"+badge("allowed",x.performance_authorization_allowed?"true":"false",x.performance_authorization_allowed?"bad":"good")+"</td><td>"+esc(x.issue_number==null?"—":x.issue_number)+"</td></tr>";}).join("")+"</tbody></table>";
  var runnerNote=s.runner_api_note||"";
  $("runners").innerHTML=runners.length ? "<table><thead><tr><th>Runner</th><th>OS / Arch</th><th>Status</th><th>Busy</th><th>Labels</th></tr></thead><tbody>"+runners.map(function(x){return "<tr><td class='rowtitle'>"+esc(x.name)+"</td><td>"+esc(x.os||"—")+" / "+esc(x.architecture||"—")+"</td><td>"+badge("status",x.status,stateClass(x.status))+"</td><td>"+badge("busy",x.busy?"true":"false",x.busy?"warn":"")+"</td><td>"+(x.labels||[]).map(function(l){return badge("label",l);}).join("")+"</td></tr>";}).join("")+"</tbody></table>" : "<div class='empty'>Actions runner API data was unavailable for this snapshot. Configured resource identities remain shown above. "+esc(runnerNote)+"</div>";
  $("activity").innerHTML=activity.length ? "<table><thead><tr><th>Task</th><th>Result</th><th>Completed</th><th>Actor</th><th>Run</th></tr></thead><tbody>"+activity.map(function(x){return "<tr><td>"+link(x.run_url,x.task)+"</td><td>"+badge("result",x.status,stateClass(x.status))+"</td><td>"+esc(ts(x.completed_at))+"</td><td>"+esc(x.actor||"—")+"</td><td>"+esc(x.run_id)+"</td></tr>";}).join("")+"</tbody></table>" : "<div class='empty'>No completed activity from the last 24 hours was included.</div>";
  $("safety").innerHTML=Object.keys(safety).map(function(k){var v=safety[k];return badge(k,String(v),String(v).toLowerCase()==="false"?"good":"warn");}).join("")+"<p class='small muted' style='margin-top:10px'>Latest formal result: "+esc(data.current_research&&data.current_research.latest_formal_result||"not recorded")+"</p>";
  $("app").hidden=false;
}
function renderEmbeddedSnapshot(){
  var snapshot=window.__TRADING_AGENT_SNAPSHOT__;
  if(snapshot && typeof snapshot==="object"){render(snapshot);return true;}
  return false;
}
function load(){
  $("error").hidden=true;
  var rendered=renderEmbeddedSnapshot();
  if(!rendered){$("meta").textContent="Operational snapshot is not embedded; requesting the published data file…";}
  var url=new URL("dashboard_data.json",document.baseURI);
  url.searchParams.set("ts",String(Date.now()));
  var controller=typeof AbortController==="function" ? new AbortController() : null;
  var timeoutId=controller ? setTimeout(function(){controller.abort();},6000) : null;
  var requestOptions={cache:"no-store"};
  if(controller){requestOptions.signal=controller.signal;}
  fetch(url.toString(),requestOptions).then(function(r){
    if(!r.ok)throw new Error("HTTP "+r.status);
    return r.json();
  }).then(function(data){
    render(data);
  }).catch(function(e){
    if(!rendered){
      $("error").textContent="Dashboard snapshot could not be loaded: "+(e&&e.message||String(e));
      $("error").hidden=false;
    }else{
      $("meta").insertAdjacentHTML("beforeend"," · <span class='warn'>fresh refresh unavailable: "+esc(e&&e.message||String(e))+"; embedded snapshot shown</span>");
    }
  }).then(function(){
    if(timeoutId!==null)clearTimeout(timeoutId);
  });
}
document.addEventListener("DOMContentLoaded",function(){
  $("refresh").addEventListener("click",load);
  $("update").href=WORKFLOW_URL;
  $("update").addEventListener("click",function(){
    $("updateStatus").textContent="GitHub Actions geöffnet. Dort Start/Run workflow ausführen; der Workflow generiert den Snapshot und deployt danach GitHub Pages automatisch.";
  });
  load();
});
})();