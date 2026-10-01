"""CPU-only Verdict/OpenJev 1.4 benchmark against the isolated ECL corpus.

Model output is shadow metadata only; it cannot affect project evidence, gates,
authorization, candidate selection, promotion, or live execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import statistics
import time
from pathlib import Path

LABELS=("SUPPORTED","REFUTED","INSUFFICIENT")
LABEL_DESCRIPTIONS={
    "SUPPORTED":"It is supported by the supplied evidence.",
    "REFUTED":"It is refuted by the supplied evidence.",
}
CAL_TEMPERATURE_BY_K={"3":5.0069,"4":4.0314,"5":3.0560}

def load_cases(path:Path)->list[dict]:
    rows=[json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    if len(rows)!=36 or {x.get("gold_label") for x in rows}!=set(LABELS):
        raise ValueError("unexpected ECL corpus")
    return rows

def softmax(xs):
    m=max(xs)
    ex=[math.exp(x-m) for x in xs]
    s=sum(ex)
    return [v/s for v in ex]

def build_prompt(question:str,context:str,labels:list[str])->str:
    prefix="".join("<<LABEL>>"+x for x in labels)
    return prefix+"<<SEP>>"+"Question: "+question+"\n\nContext:\n"+context

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--model-dir",type=Path,required=True)
    ap.add_argument("--corpus",type=Path,default=Path("research/benchmarks/evidence_critic_pilot_2026_10_01.jsonl"))
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    cases=load_cases(args.corpus)

    import numpy as np
    import onnxruntime as ort
    from transformers import AutoTokenizer

    tok=AutoTokenizer.from_pretrained(args.model_dir,local_files_only=True)
    sess=ort.InferenceSession(
        str(args.model_dir/"model.onnx"),
        providers=["CPUExecutionProvider"],
    )
    input_names={x.name for x in sess.get_inputs()}
    if not {"input_ids","attention_mask"}.issubset(input_names):
        raise RuntimeError(f"unexpected ONNX inputs: {sorted(input_names)}")

    rows=[]
    started=time.perf_counter()
    orders=[["SUPPORTED","REFUTED"],["REFUTED","SUPPORTED"]]
    for case in cases:
        q="Classify the claim using only the supplied evidence."
        context=f"Claim: {case['claim']}\nEvidence: {case['evidence']}"
        labels=[f"It is {LABEL_DESCRIPTIONS[x].removeprefix('It is ').rstrip('.') }." for x in orders[0]]
        labels.append("insufficient evidence")
        prompt=build_prompt(q,context,labels)
        t0=time.perf_counter()
        encoded=tok(prompt,max_length=512,truncation=True,return_tensors="np")
        outputs=sess.run(None,{"input_ids":encoded["input_ids"],"attention_mask":encoded["attention_mask"]})
        logits=np.asarray(outputs[0])[0][:3].astype(float).tolist()
        temp=CAL_TEMPERATURE_BY_K["3"]
        probs=softmax([x/temp for x in logits])
        ids=["SUPPORTED","REFUTED","INSUFFICIENT"]
        idx=max(range(3),key=lambda i:probs[i])
        pred=ids[idx]
        rows.append({
            "id":case["id"],
            "gold_label":case["gold_label"],
            "predicted_label":pred,
            "probabilities":{ids[i]:float(probs[i]) for i in range(3)},
            "confidence":float(probs[idx]),
            "brier":sum((probs[i]-float(ids[i]==case["gold_label"]))**2 for i in range(3)),
            "latency_ms":round((time.perf_counter()-t0)*1000,3),
        })

    scored=rows
    accuracy=sum(x["predicted_label"]==x["gold_label"] for x in scored)/len(scored)
    brier=statistics.mean(x["brier"] for x in scored)
    lat=[x["latency_ms"] for x in rows]
    result={
        "schema_version":1,
        "task_id":"ECL-2026-10-01-001",
        "status":"BENCHMARK_COMPLETED",
        "model":"verdict-1.4",
        "implementation":"Heman10x-NGU/Verdict-open-jev v1.4 inference engine",
        "model_artifact_sha256":hashlib.sha256((args.model_dir/"model.onnx").read_bytes()).hexdigest(),
        "environment":{"python":platform.python_version(),"platform":platform.platform()},
        "corpus":{"cases":len(cases),"labels":LABELS},
        "metrics":{
            "n_total":len(rows),
            "accuracy":accuracy,
            "brier_mean":brier,
            "insufficient_recall":sum(x["predicted_label"]=="INSUFFICIENT" and x["gold_label"]=="INSUFFICIENT" for x in rows)/sum(x["gold_label"]=="INSUFFICIENT" for x in rows),
            "insufficient_precision":sum(x["predicted_label"]=="INSUFFICIENT" and x["gold_label"]=="INSUFFICIENT" for x in rows)/max(1,sum(x["predicted_label"]=="INSUFFICIENT" for x in rows)),
            "malformed_or_no_decision":0,
        },
        "latency_ms":{"median":statistics.median(lat),"p95":sorted(lat)[max(0,math.ceil(.95*len(lat))-1)]},
        "option_order_sensitivity":"not run in this direct ONNX adapter; separate implementation parity remains required",
        "worker_output_is_scientific_evidence":False,
        "governance":{"performance_evaluation":False,"holdout_selection":False,"candidate_selection":False,"candidate_ranking":False,"parameter_search":False,"promotion":False,"live_execution":False},
        "raw_predictions":rows,
        "duration_seconds":round(time.perf_counter()-started,2),
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"model":result["model"],"accuracy":accuracy,"brier_mean":brier,"insufficient_recall":result["metrics"]["insufficient_recall"],"median_latency_ms":result["latency_ms"]["median"]}))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
