"""Q090 diagnostic-only decomposition of the immutable Q089 performance result."""
from __future__ import annotations
import argparse, hashlib, json, math, statistics, subprocess
from pathlib import Path
from typing import Iterable
from automation.q069_candidate_bank import CANDIDATES, candidate_targets_at
from data.canonical_snapshot import load_frozen_snapshot

TRIAL_ID="T-2026-09-29-090"
PARENT_TRIAL_ID="T-2026-09-28-089-PERFORMANCE"
Q089_RESULT="research/evidence/q089_performance_result.json"
Q089_MANIFEST="research/runs/q089_coverage/T-2026-09-28-089-COVERAGE/snapshot_manifest.json"
Q089_RESULT_FP="0eee84e44a12b9f4a606aebb63afe50990dfa0f6e6009afcf926f525e3c8e8d1"
Q089_SNAPSHOT_FP="bb82aeaed86411a8675be7f8ecb1c99e9c144f017466a836b8cafeb9d3b55e1d"
Q089_RUNNER_SHA="0546bebae018acb0b530f094462b3c9cd79d96aba7ed66c8b17dc720ab13057b"
Q069_BANK_SHA="84e008a6152cbea128e5e5f2ac0dfdde0b0172310fe4c510241c60edfd3ff617"
N=3500; RESEARCH=2798; HOLDOUT=700; COST_RATE=0.0015
SAFETY={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}

def canonical(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False)
def fingerprint(v): return hashlib.sha256(canonical(v).encode()).hexdigest()
def mean(v:Iterable[float]): v=list(v); return statistics.fmean(v) if v else 0.0
def hhi(v:Iterable[float]):
    a=[abs(float(x)) for x in v]; t=sum(a); return sum((x/t)**2 for x in a) if t else 0.0
def pearson(a,b):
    n=min(len(a),len(b))
    if n<2:return 0.0
    x=a[:n]; y=b[:n]; ax=mean(x); ay=mean(y)
    vx=sum((z-ax)**2 for z in x); vy=sum((z-ay)**2 for z in y)
    return sum((xx-ax)*(yy-ay) for xx,yy in zip(x,y))/math.sqrt(vx*vy) if vx>0 and vy>0 else 0.0
def jaccard(a,b):
    u=a|b; return len(a&b)/len(u) if u else 1.0
def stats(values):
    if not values:return {"period_return":0.0,"max_drawdown_percent":0.0,"profit_factor":0.0,"positive_day_ratio":0.0,"day_count":0}
    eq=peak=1.0; gain=loss=0.0; pos=0; dd=0.0
    for v in values:
        eq*=1.0+v; peak=max(peak,eq); dd=max(dd,1.0-eq/peak if eq>0 else 1.0)
        if v>0:gain+=v;pos+=1
        elif v<0:loss-=v
    return {"period_return":eq-1.0,"max_drawdown_percent":dd*100.0,"profit_factor":gain/loss if loss else ("inf" if gain else 0.0),"positive_day_ratio":pos/len(values),"day_count":len(values)}
def rolling_stats(values):
    width=RESEARCH//5; out=[]
    for i in range(5):
        start=i*width; end=RESEARCH if i==4 else (i+1)*width
        x=stats(values[start:end]); x.update(window_index=i+1,start_index=start,end_index_exclusive=end); out.append(x)
    return out
def max_drawdown_interval(values):
    eq=peak=1.0; peak_idx=-1; best=0.0; start=end=0
    for i,v in enumerate(values):
        eq*=1.0+v
        if eq>peak:peak=eq;peak_idx=i
        cur=1.0-eq/peak if eq>0 else 1.0
        if cur>best:best=cur;start=peak_idx+1;end=i
    return {"start_index":start,"end_index":end,"length":end-start+1,"max_drawdown_percent":best*100.0}
def market_returns(assets,symbols):
    return [mean([assets[s][i+2].open/assets[s][i+1].open-1.0 for s in symbols]) for i in range(N-2)]
def classify_regime(values):
    labels=[]; vols=[None]*len(values)
    for i in range(len(values)):
        if i>=21:vols[i]=statistics.pstdev(values[i-21:i])
        if i<273 or vols[i] is None:labels.append("UNDEFINED_EARLY");continue
        threshold=statistics.median([v for v in vols[i-252:i] if v is not None])
        trend=math.prod(1.0+x for x in values[i-63:i])-1.0
        labels.append(("UPTREND" if trend>=0 else "DOWNTREND")+"_"+("HIGHVOL" if vols[i]>=threshold else "LOWVOL"))
    return labels
def verify_q089_result(root):
    r=json.loads((root/Q089_RESULT).read_text())
    if r.get("trial_id")!=PARENT_TRIAL_ID or r.get("status")!="COMPLETED":raise RuntimeError("Q089 result identity/status invalid")
    actual=r.get("report_fingerprint");p=dict(r);p.pop("report_fingerprint",None)
    if actual!=Q089_RESULT_FP or fingerprint(p)!=Q089_RESULT_FP:raise RuntimeError("Q089 result fingerprint mismatch")
    if r.get("safety")!=SAFETY or r.get("selection_used") is not False or r.get("holdout_used_for_selection") is not False:raise RuntimeError("Q089 governance/safety mismatch")
    return r
def verify_sources(root):
    for rel,exp in (("automation/q089_performance.py",Q089_RUNNER_SHA),("automation/q069_candidate_bank.py",Q069_BANK_SHA)):
        act=subprocess.check_output(["git","hash-object",str(root/rel)],text=True).strip()
        if act!=exp:raise RuntimeError(f"source blob mismatch: {rel}")
def verify_snapshot(root,q089):
    m=json.loads((root/Q089_MANIFEST).read_text())
    if m.get("status")!="COVERAGE_PASSED" or m.get("snapshot_fingerprint")!=Q089_SNAPSHOT_FP:raise RuntimeError("Q089 snapshot manifest invalid")
    if tuple(m.get("symbols",()))!=tuple(q089["symbols"]) or int(m.get("target_common_candles",-1))!=N:raise RuntimeError("Q089 snapshot geometry invalid")
    assets=load_frozen_snapshot(root/Q089_MANIFEST); symbols=tuple(m["symbols"])
    if tuple(assets)!=symbols or any(len(assets[s])!=N for s in symbols):raise RuntimeError("Q089 frozen snapshot invalid")
    return assets,symbols
def build_paths(assets,symbols):
    weights={name:tuple(candidate_targets_at(assets,i,symbols=symbols)[name] for i in range(N)) for name in CANDIDATES}; paths={}
    for arm in CANDIDATES:
        prev={s:0.0 for s in symbols}; gross=[];net=[];turn=[];symbol_net={s:[] for s in symbols};exposure=[];hs=[];t1=[];t2=[]
        for i in range(N-2):
            w=weights[arm][i];rets=[assets[s][i+2].open/assets[s][i+1].open-1.0 for s in symbols];t=sum(abs(float(w.get(s,0))-prev[s]) for s in symbols);g=sum(float(w.get(s,0))*rets[k] for k,s in enumerate(symbols));n=g-COST_RATE*t
            gross.append(g);net.append(n);turn.append(t);a=[abs(float(w.get(s,0))) for s in symbols];exposure.append(sum(a));hs.append(hhi(a));o=sorted(a,reverse=True);t1.append(o[0] if o else 0.0);t2.append(sum(o[:2]))
            for k,s in enumerate(symbols):
                d=abs(float(w.get(s,0))-prev[s]);symbol_net[s].append(float(w.get(s,0))*rets[k]-COST_RATE*d)
            prev={s:float(w.get(s,0)) for s in symbols}
        paths[arm]={"weights":weights[arm],"gross":gross,"net":net,"turnover":turn,"symbol_net":symbol_net,"exposure":exposure,"hhi":hs,"top1":t1,"top2":t2}
    return weights,paths
def reconstruct_summary(path):
    v=path["net"];r=stats(v[:RESEARCH]);h=stats(v[RESEARCH:RESEARCH+HOLDOUT]);rw=rolling_stats(v);gp=sum(max(x["period_return"],0) for x in rw);lp=-sum(min(x["period_return"],0) for x in rw)
    return {"research":r,"holdout":h,"rolling_windows":rw,"rolling_profit_factor":gp/lp if lp else ("inf" if gp else 0.0),"rolling_profitable_window_ratio":sum(x["period_return"]>0 for x in rw)/5.0,"rolling_average_drawdown_percent":mean(x["max_drawdown_percent"] for x in rw),"oos_to_is_return_ratio":h["period_return"]/r["period_return"] if r["period_return"]>0 else 0.0}
def close(a,b):return a==b if isinstance(a,str) or isinstance(b,str) else math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-12)
def verify_exact(q089,paths):
    for arm in CANDIDATES:
        rec=reconstruct_summary(paths[arm]);st=q089["arms"][arm]["base"]
        for p in ("research","holdout"):
            for k in ("period_return","max_drawdown_percent","positive_day_ratio","day_count"):
                if not close(st[p][k],rec[p][k]):raise RuntimeError(f"aggregate mismatch {arm} {p} {k}")
            if not close(st[p]["profit_factor"],rec[p]["profit_factor"]):raise RuntimeError(f"aggregate mismatch {arm} {p} profit_factor")
        for k in ("rolling_profit_factor","rolling_profitable_window_ratio","rolling_average_drawdown_percent","oos_to_is_return_ratio"):
            if not close(st[k],rec[k]):raise RuntimeError(f"aggregate mismatch {arm} {k}")
def underwater(values):
    eq=peak=1.0;mask=[]
    for v in values:
        eq*=1.0+v;peak=max(peak,eq);mask.append(eq<peak)
    return mask
def symbol_diag(path,symbols):
    dd=max_drawdown_interval(path["net"]);out={}
    for s in symbols:
        vals=path["symbol_net"][s]
        out[s]={"mean_weight":mean(path["weights"][i].get(s,0.0) for i in range(N-2)),"max_abs_weight":max(abs(path["weights"][i].get(s,0.0)) for i in range(N-2)),"research_net_contribution":sum(vals[:RESEARCH]),"holdout_net_contribution":sum(vals[RESEARCH:RESEARCH+HOLDOUT]),"global_net_contribution":sum(vals),"worst_drawdown_interval_net_contribution":sum(vals[dd["start_index"]:dd["end_index"]+1])}
    return out
def regime_diag(values,regimes):
    grouped={}
    for label,v in zip(regimes,values):grouped.setdefault(label,[]).append(v)
    return {label:{"day_count":len(v),"compound_return":math.prod(1+x for x in v)-1.0,"simple_return_sum":sum(v),"mean_daily_return":mean(v),"negative_day_fraction":mean([1.0 if x<0 else 0.0 for x in v])} for label,v in grouped.items()}
def pairwise(weights,paths):
    out={}
    for i,left in enumerate(CANDIDATES):
        for right in CANDIDATES[i+1:]:
            wl=weights[left];wr=weights[right];nl=paths[left]["net"];nr=paths[right]["net"];ul=underwater(nl);ur=underwater(nr);ov=[];adv=[];al=[];ar=[]
            for t in range(N-2):
                a={s for s,w in wl[t].items() if abs(float(w))>1e-12};b={s for s,w in wr[t].items() if abs(float(w))>1e-12};ov.append(jaccard(a,b))
                if ul[t] or ur[t]:adv.append(jaccard(a,b));al.append(nl[t]);ar.append(nr[t])
            out[f"{left}__{right}"]={"mean_active_set_jaccard_all_days":mean(ov),"mean_active_set_jaccard_either_underwater":mean(adv),"either_underwater_day_count":len(adv),"net_return_correlation_all_days":pearson(nl,nr),"net_return_correlation_either_underwater":pearson(al,ar)}
    return out
def market_diag(paths,market):
    out={}
    for arm in CANDIDATES:
        u=underwater(paths[arm]["net"]);idx=[i for i,x in enumerate(u) if x]
        out[arm]={"net_market_correlation_all_days":pearson(paths[arm]["net"],market),"net_market_correlation_while_underwater":pearson([paths[arm]["net"][i] for i in idx],[market[i] for i in idx]),"underwater_fraction":mean([1.0 if x else 0.0 for x in u]),"worst_drawdown_interval":max_drawdown_interval(paths[arm]["net"])}
    return out
def run(root,output,markdown_path):
    q=verify_q089_result(root);verify_sources(root);assets,symbols=verify_snapshot(root,q);weights,paths=build_paths(assets,symbols);verify_exact(q,paths);market=market_returns(assets,symbols);regimes=classify_regime(market);arms={}
    for arm in CANDIDATES:
        p=paths[arm];dd=max_drawdown_interval(p["net"]);u=underwater(p["net"])
        arms[arm]={"q089_gates_passed":q["arms"][arm]["gates_passed"],"q089_gates_total":q["arms"][arm]["gates_total"],"q089_base":q["arms"][arm]["base"],"reconstructed_summary":reconstruct_summary(p),
          "exposure":{"mean_gross_exposure":mean(p["exposure"]),"max_gross_exposure":max(p["exposure"]),"mean_hhi":mean(p["hhi"]),"max_hhi":max(p["hhi"]),"mean_top1_share":mean(p["top1"]),"mean_top2_share":mean(p["top2"]),"active_day_fraction":mean([1.0 if x>0 else 0.0 for x in p["exposure"]])},
          "turnover":{"turnover_sum":sum(p["turnover"]),"turnover_mean":mean(p["turnover"]),"base_cost_drag_simple":COST_RATE*sum(p["turnover"])},
          "drawdown":{**dd,"start_timestamp":str(assets[symbols[0]][dd["start_index"]+2].timestamp),"end_timestamp":str(assets[symbols[0]][dd["end_index"]+2].timestamp),"research_window":next((x["window_index"] for x in rolling_stats(p["net"]) if x["start_index"]<=dd["start_index"]<x["end_index_exclusive"]),None),"underwater_fraction":mean([1.0 if x else 0.0 for x in u]),"negative_day_fraction":mean([1.0 if x<0 else 0.0 for x in p["net"]])},
          "symbols":symbol_diag(p,symbols),"regimes":regime_diag(p["net"],regimes)}
    summary=[{"arm":arm,"gates_passed":q["arms"][arm]["gates_passed"],"research_drawdown_percent":q["arms"][arm]["base"]["research"]["max_drawdown_percent"],"holdout_return_percent":100*q["arms"][arm]["base"]["holdout"]["period_return"],"holdout_drawdown_percent":q["arms"][arm]["base"]["holdout"]["max_drawdown_percent"],"rolling_profitable_window_ratio":q["arms"][arm]["base"]["rolling_profitable_window_ratio"],"rolling_average_drawdown_percent":q["arms"][arm]["base"]["rolling_average_drawdown_percent"],"mean_hhi":arms[arm]["exposure"]["mean_hhi"],"mean_top2_share":arms[arm]["exposure"]["mean_top2_share"],"turnover_sum":arms[arm]["turnover"]["turnover_sum"]} for arm in CANDIDATES]
    result={"schema_version":"1.0","trial_id":TRIAL_ID,"parent_trial_id":PARENT_TRIAL_ID,"status":"COMPLETED_DIAGNOSTIC_ONLY","research_family":"q090_q089_failure_mechanism_diagnosis",
      "source":{"parent_report_fingerprint":Q089_RESULT_FP,"parent_workflow_run_id":"36543296042","parent_code_version":q["code_version"],"snapshot_fingerprint":Q089_SNAPSHOT_FP,"symbols":list(symbols),"requested_candles":q["requested_candles"],"target_common_candles":q["target_common_candles"],"research_periods":q["research_periods"],"holdout_periods":q["holdout_periods"],"candidate_bank_sha256":Q069_BANK_SHA,"performance_runner_sha256":Q089_RUNNER_SHA},
      "reconstruction":{"aggregate_reconstruction_exact":True,"no_new_market_data":True,"no_new_performance_trial":True,"source_result_immutable":True},
      "diagnostic_scope":{"symbol_concentration":True,"exposure_path":True,"regime_decomposition":True,"signal_overlap":True,"return_correlation":True,"market_correlation":True,"turnover_and_cost_drag":True,"drawdown_interval_attribution":True,"research_holdout_descriptive_breakdown":True},
      "arms":arms,"pairwise":pairwise(weights,paths),"market":market_diag(paths,market),"executive_summary":{"arms":summary},
      "governance":{"diagnostic_evaluation":True,"new_performance_evaluation":False,"selection":False,"holdout_used_for_selection":False,"parameter_search":False,"threshold_search":False,"asset_search":False,"horizon_search":False,"variant_search":False,"family_ranking":False,"promotion_decision":False,"automatic_promotion":False},"safety":SAFETY}
    result["diagnostic_fingerprint"]=fingerprint(result);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    markdown_path.parent.mkdir(parents=True,exist_ok=True)
    lines=["# Q090 — Q089 Failure-Mechanism Diagnosis","","Status: COMPLETED_DIAGNOSTIC_ONLY","","Immutable-result reconstruction only; no new market data, candidate selection, parameter search, new performance trial or promotion.","","## Executive summary","","| Arm | Q089 gates | Research DD | Holdout return | Holdout DD | Rolling positive windows | Rolling avg DD | Mean HHI | Mean top-2 share | Turnover sum |","|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for x in summary:lines.append(f"| {x['arm']} | {x['gates_passed']}/13 | {x['research_drawdown_percent']:.2f}% | {x['holdout_return_percent']:.2f}% | {x['holdout_drawdown_percent']:.2f}% | {x['rolling_profitable_window_ratio']:.0%} | {x['rolling_average_drawdown_percent']:.2f}% | {x['mean_hhi']:.4f} | {x['mean_top2_share']:.4f} | {x['turnover_sum']:.2f} |")
    lines += ["","","## Interpretation boundary","","Findings are descriptive decompositions, not causal proof or arm selection.",f"- Exact aggregate reconstruction: {result['reconstruction']['aggregate_reconstruction_exact']}",f"- Parent report fingerprint: {Q089_RESULT_FP}",f"- Snapshot fingerprint: {Q089_SNAPSHOT_FP}",""]
    for arm in CANDIDATES:
        x=arms[arm];d=x["drawdown"];lines += [f"## {arm}","",f"- Worst drawdown: {d['start_timestamp']} to {d['end_timestamp']} ({d['length']} days), {d['max_drawdown_percent']:.2f}%.",f"- Mean/max HHI: {x['exposure']['mean_hhi']:.4f}/{x['exposure']['max_hhi']:.4f}.",f"- Mean top-1/top-2 share: {x['exposure']['mean_top1_share']:.4f}/{x['exposure']['mean_top2_share']:.4f}.",f"- Turnover sum / simple base-cost drag: {x['turnover']['turnover_sum']:.2f}/{x['turnover']['base_cost_drag_simple']:.6f}",""]
    lines += ["## Governance","","Diagnostic only. No selection, tuning, new performance trial or promotion.","Safety remains paper-only."]
    markdown_path.write_text("\n".join(lines)+"\n",encoding="utf-8");return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--repo-root",required=True);p.add_argument("--output",required=True);p.add_argument("--markdown",required=True);a=p.parse_args();run(Path(a.repo_root),Path(a.output),Path(a.markdown))
