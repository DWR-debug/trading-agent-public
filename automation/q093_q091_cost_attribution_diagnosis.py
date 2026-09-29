"""Q093 deterministic gross-vs-net cost attribution diagnosis for Q091."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from automation.q069_candidate_bank import CANDIDATES, candidate_targets_at
from data.canonical_snapshot import load_frozen_snapshot
from portfolio.q091_fixed_ensemble import demean_weights, gross_normalize

TRIAL_ID="T-2026-09-29-093"
PARENT_TRIAL_ID="T-2026-09-29-091"
RESULT_PATH="research/evidence/q091_performance_result.json"
MANIFEST_PATH="research/runs/q091_coverage/T-2026-09-29-091-COVERAGE/snapshot_manifest.json"
RESULT_FP="0816e49774ff901438e046e162e428884f3f67b305cf26e0ebff2451ce38195d"
SNAPSHOT_FP="4f89d5fa954139b0b88d916ce307b1b1a93b61b020dc8b1b4b4296d70df2f4e2"
N=3500
RESEARCH=2798
HOLDOUT=700
COST_RATE=0.0015
SAFETY={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False}


def canonical(v:object)->str:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False)


def fp(v:object)->str:
    return hashlib.sha256(canonical(v).encode()).hexdigest()


def stats(values:list[float])->dict:
    equity=peak=1.0
    gain=loss=0.0
    positive=0
    dd=0.0
    for v in values:
        equity*=1.0+v
        peak=max(peak,equity)
        dd=max(dd,1.0-equity/peak if equity>0 else 1.0)
        if v>0:
            gain+=v
            positive+=1
        elif v<0:
            loss-=v
    return {
        "period_return":equity-1.0,
        "max_drawdown_percent":dd*100.0,
        "profit_factor":gain/loss if loss else ("inf" if gain else 0.0),
        "positive_day_ratio":positive/len(values) if values else 0.0,
        "day_count":len(values),
    }


def parent(root:Path)->dict:
    d=json.loads((root/RESULT_PATH).read_text(encoding="utf-8"))
    if d.get("trial_id")!=PARENT_TRIAL_ID or d.get("status")!="COMPLETED":
        raise RuntimeError("Q091 result identity/status invalid")
    if d.get("report_fingerprint")!=RESULT_FP:
        raise RuntimeError("Q091 report fingerprint mismatch")
    if d.get("safety")!=SAFETY or d.get("selection_used") is not False or d.get("holdout_used_for_selection") is not False:
        raise RuntimeError("Q091 safety/governance mismatch")
    return d


def snapshot(root:Path, p:dict):
    m=json.loads((root/MANIFEST_PATH).read_text(encoding="utf-8"))
    if m.get("status")!="COVERAGE_PASSED" or m.get("snapshot_fingerprint")!=SNAPSHOT_FP:
        raise RuntimeError("Q091 snapshot contract invalid")
    symbols=tuple(m["symbols"])
    if list(symbols)!=p["symbols"] or int(m["target_common_candles"])!=N:
        raise RuntimeError("Q091 snapshot geometry mismatch")
    assets=load_frozen_snapshot(root/MANIFEST_PATH)
    if any(len(assets[s])!=N for s in symbols):
        raise RuntimeError("Q091 snapshot length mismatch")
    return assets,symbols


def weights_for(variant:str,assets,symbols):
    weights=[]; turnover=[]; prev={s:0.0 for s in symbols}
    for i in range(N-2):
        sleeves=candidate_targets_at(assets,i,symbols=symbols)
        if variant=="E1_EQUAL_WEIGHT_Q069_5SLEEVE":
            w={s:sum(float(sleeves[n][s]) for n in CANDIDATES)/5.0 for s in symbols}
        else:
            residuals={n:demean_weights(sleeves[n],symbols) for n in CANDIDATES}
            combined={s:sum(float(residuals[n][s]) for n in CANDIDATES)/5.0 for s in symbols}
            w=gross_normalize(combined,symbols)
        weights.append(w)
        turnover.append(sum(abs(float(w[s])-prev[s]) for s in symbols))
        prev={s:float(w[s]) for s in symbols}
    return weights,turnover


def returns_for(weights,turnover,assets,symbols):
    gross=[]; net=[]
    for i,w in enumerate(weights):
        r=sum(float(w[s])*(assets[s][i+2].open/assets[s][i+1].open-1.0) for s in symbols)
        gross.append(r)
        net.append(r-COST_RATE*turnover[i])
    return gross,net


def split(values:list[float])->dict:
    return {
        "research":stats(values[:RESEARCH]),
        "holdout":stats(values[RESEARCH:RESEARCH+HOLDOUT]),
    }


def reconstruct(root:Path,output:Path,markdown:Path)->dict:
    p=parent(root)
    assets,symbols=snapshot(root,p)
    arms={}
    for variant in ("E1_EQUAL_WEIGHT_Q069_5SLEEVE","E2_CROSS_SECTIONAL_RESIDUALIZED_Q069_5SLEEVE"):
        weights,turnover=weights_for(variant,assets,symbols)
        gross,net=returns_for(weights,turnover,assets,symbols)
        net_summary=split(net)
        expected=p["arms"][variant]["base"]
        for split_name in ("research","holdout"):
            for k in ("period_return","max_drawdown_percent","positive_day_ratio","day_count"):
                a=expected[split_name][k]
                b=net_summary[split_name][k]
                if isinstance(a,str):
                    if a!=b: raise RuntimeError(f"Q093 net reconstruction mismatch {variant} {split_name} {k}")
                elif not math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-12):
                    raise RuntimeError(f"Q093 net reconstruction mismatch {variant} {split_name} {k}")
        gross_summary=split(gross)
        simple_cost_research=COST_RATE*sum(turnover[:RESEARCH])
        simple_cost_holdout=COST_RATE*sum(turnover[RESEARCH:RESEARCH+HOLDOUT])
        arms[variant]={
            "exact_net_reconstruction":True,
            "gross_before_costs":gross_summary,
            "net_after_base_costs":net_summary,
            "cost_attribution":{
                "turnover_sum_research":sum(turnover[:RESEARCH]),
                "turnover_sum_holdout":sum(turnover[RESEARCH:RESEARCH+HOLDOUT]),
                "mean_turnover_research":sum(turnover[:RESEARCH])/RESEARCH,
                "mean_turnover_holdout":sum(turnover[RESEARCH:RESEARCH+HOLDOUT])/HOLDOUT,
                "simple_cost_drag_research":simple_cost_research,
                "simple_cost_drag_holdout":simple_cost_holdout,
                "compound_return_difference_gross_minus_net_research":gross_summary["research"]["period_return"]-net_summary["research"]["period_return"],
                "compound_return_difference_gross_minus_net_holdout":gross_summary["holdout"]["period_return"]-net_summary["holdout"]["period_return"],
                "holdout_sign_flips_after_base_costs":gross_summary["holdout"]["period_return"]>0 and net_summary["holdout"]["period_return"]<=0,
            },
            "stress_sensitivity_from_parent":{
                "base_holdout_return":p["arms"][variant]["base"]["holdout"]["period_return"],
                "stress_1_5x_holdout_return":p["arms"][variant]["stress_1_5x_cost"]["holdout"]["period_return"],
                "stress_2x_holdout_return":p["arms"][variant]["stress_2x_cost"]["holdout"]["period_return"],
            }
        }
    result={
        "schema_version":"1.0",
        "trial_id":TRIAL_ID,
        "status":"COMPLETED_DIAGNOSTIC_ONLY",
        "research_family":"q093_q091_cost_attribution_diagnosis",
        "parent_trial_id":PARENT_TRIAL_ID,
        "source":{
            "parent_report_fingerprint":RESULT_FP,
            "snapshot_fingerprint":SNAPSHOT_FP,
            "symbols":list(symbols),
            "requested_candles":5000,
            "target_common_candles":N,
            "research_periods":RESEARCH,
            "holdout_periods":HOLDOUT,
            "cost_rate":COST_RATE
        },
        "reconstruction":{
            "aggregate_net_reconstruction_exact":True,
            "no_new_market_data":True,
            "no_new_performance_trial":True,
            "parent_result_immutable":True
        },
        "arms":arms,
        "governance":{
            "diagnostic_evaluation":True,
            "new_performance_evaluation":False,
            "selection":False,
            "holdout_used_for_selection":False,
            "parameter_search":False,
            "threshold_search":False,
            "asset_search":False,
            "horizon_search":False,
            "variant_search":False,
            "family_ranking":False,
            "promotion_decision":False,
            "automatic_promotion":False
        },
        "next_question":"After isolating cost drag, determine whether gross pre-cost holdout behavior itself survives independently of the Q091 portfolio architecture on a new preregistered disjoint validation.",
        "safety":SAFETY
    }
    result["diagnostic_fingerprint"]=fp(result)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    lines=[
      "# Q093 — Q091 Cost Attribution Diagnosis","","Status: COMPLETED_DIAGNOSTIC_ONLY","",
      "Immutable Q091 reconstruction; no new market data or performance trial.","",
      "| Variant | Gross research | Gross holdout | Net holdout | Simple holdout cost drag | Holdout sign flip | Turnover research/holdout |",
      "|---|---:|---:|---:|---:|---|---:|"
    ]
    for variant,a in arms.items():
        lines.append(
            f"| {variant} | {100*a['gross_before_costs']['research']['period_return']:.2f}% | "
            f"{100*a['gross_before_costs']['holdout']['period_return']:.2f}% | "
            f"{100*a['net_after_base_costs']['holdout']['period_return']:.2f}% | "
            f"{100*a['cost_attribution']['simple_cost_drag_holdout']:.2f} pp | "
            f"{a['cost_attribution']['holdout_sign_flips_after_base_costs']} | "
            f"{a['cost_attribution']['turnover_sum_research']:.2f}/{a['cost_attribution']['turnover_sum_holdout']:.2f} |"
        )
    lines += ["","","## Governance","",
              "- Exact net reconstruction: true",
              "- New performance evaluation: false",
              "- Selection/holdout selection: false",
              "- Promotion: false",
              f"- Parent result fingerprint: {RESULT_FP}",
              f"- Diagnostic fingerprint: {result['diagnostic_fingerprint']}"]
    markdown.parent.mkdir(parents=True,exist_ok=True)
    markdown.write_text("\n".join(lines)+"\n",encoding="utf-8")
    return result


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--repo-root",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--markdown",type=Path,required=True)
    a=p.parse_args()
    d=reconstruct(a.repo_root,a.output,a.markdown)
    print("Q093_DIAGNOSIS_OK")
    print("Q093_DIAGNOSTIC_FINGERPRINT:",d["diagnostic_fingerprint"])
    return 0


if __name__=="__main__":
    raise SystemExit(main())
