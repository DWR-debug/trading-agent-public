"""Plan downstream research-wave dispatches from the Temporal/Identity/State Spine.

This is an orchestration helper only. It reads GitHub run metadata supplied by the
workflow and never reads market outcomes, ranks candidates, or authorizes research.
"""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone

DEFAULTS = [
    {"workflow": ".github/workflows/q224-edgar-modern-source-gate.yml", "label": "Q224", "min_success_age_minutes": 360},
    {"workflow": ".github/workflows/q229-historical-release-census.yml", "label": "Q229-HIST", "min_success_age_minutes": 360},
    {"workflow": ".github/workflows/q229-q230-source-feasibility.yml", "label": "Q229-Q230-SOURCE", "min_success_age_minutes": 360},
    {"workflow": ".github/workflows/q230-windows-trace-connectivity.yml", "label": "Q230-WINDOWS", "min_success_age_minutes": 360},
    {"workflow": ".github/workflows/q231-sec-foia-source-gate.yml", "label": "Q231", "min_success_age_minutes": 360},
]

def iso(s):
    return datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(timezone.utc)

def plan_dispatches(runs, now=None, max_dispatches=5):
    now = now or datetime.now(timezone.utc)
    active_by = {}
    latest_by = {}
    for r in runs:
        wf = r.get("path") or r.get("workflow_url","").rsplit("/",1)[-1]
        if not wf.endswith(".yml"):
            wf = r.get("workflow_path") or wf
        name = r.get("workflow_name") or r.get("name")
        status = r.get("status")
        created = r.get("created_at")
        item = (wf, name)
        if created:
            rec = dict(r)
            rec["_parsed_created"] = iso(created)
        else:
            rec = r
            rec["_parsed_created"] = now
        key = r.get("workflow_path") or r.get("workflow_name") or name
        if status != "completed":
            active_by[key] = True
        prev = latest_by.get(key)
        if prev is None or rec["_parsed_created"] > prev["_parsed_created"]:
            latest_by[key] = rec
    decisions=[]
    dispatches=[]
    for target in DEFAULTS:
        key = target["workflow"]
        active = any(
            (r.get("status") != "completed") and (
                r.get("path")==key or r.get("workflow_path")==key or r.get("name")==target["label"] or
                r.get("workflow_name")==target["label"]
            )
            for r in runs
        )
        latest = None
        candidates=[]
        for r in runs:
            if r.get("path")==key or r.get("workflow_path")==key or r.get("name")==target["label"] or r.get("workflow_name")==target["label"]:
                try:
                    created=iso(r["created_at"])
                except Exception:
                    continue
                candidates.append((created,r))
        if candidates:
            latest=max(candidates,key=lambda x:x[0])[1]
        reason="READY_NO_PRIOR_RUN"
        eligible=not active
        if active:
            reason="SKIP_ACTIVE_DUPLICATE"
            eligible=False
        elif latest:
            age=(now-iso(latest["created_at"])).total_seconds()/60
            if latest.get("conclusion")=="success" and age < target["min_success_age_minutes"]:
                reason=f"SKIP_FRESH_SUCCESS_{int(age)}MIN"
                eligible=False
            else:
                reason=f"READY_LAST={latest.get('conclusion')}_AGE_{int(age)}MIN"
        if eligible and len(dispatches)<max_dispatches:
            dispatches.append(target["workflow"])
        decisions.append({"label":target["label"],"workflow":target["workflow"],"eligible":eligible,"reason":reason})
    return {
        "schema_version":1,
        "record_type":"spine_next_gate_dispatch_plan",
        "generated_at_utc":now.isoformat(),
        "dispatches":dispatches,
        "decisions":decisions,
        "max_dispatches":max_dispatches,
        "scientific_evidence":False,
        "performance_authorization":False,
        "holdout_selection":False,
        "ranking":False,
        "tuning":False,
        "promotion":False,
        "live_execution":False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-dispatches", type=int, default=5)
    args=ap.parse_args()
    data=json.loads(open(args.runs,encoding="utf-8").read())
    runs=data.get("workflow_runs",data if isinstance(data,list) else [])
    out=plan_dispatches(runs,max_dispatches=args.max_dispatches)
    import pathlib
    pathlib.Path(args.output).write_text(json.dumps(out,indent=2)+"
",encoding="utf-8")
    print(json.dumps(out,sort_keys=True))
if __name__=="__main__":
    main()
