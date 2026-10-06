from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime
from pathlib import Path

def parse_acceptance(value, label):
    if value is None or not isinstance(value, str) or len(value) != 14 or not value.isdigit():
        raise SystemExit(f"Q218_INVALID_ACCEPTANCE:{label}:{value!r}")
    try:
        return datetime.strptime(value, "%Y%m%d%H%M%S")
    except ValueError as exc:
        raise SystemExit(f"Q218_INVALID_ACCEPTANCE:{label}:{value!r}") from exc

def pair_issuer(issuer):
    selected, unpaired, seen = [], [], {}
    events = sorted(
        issuer.get("paired_10k_events", []),
        key=lambda e: (e.get("ten_k_acceptance_datetime") or "", e.get("ten_k_accession") or ""),
    )
    for event in events:
        target_raw = event.get("ten_k_acceptance_datetime")
        pair_acc = event.get("paired_8k_accession")
        if not target_raw:
            raise SystemExit(f"Q218_MISSING_TARGET_ACCEPTANCE:{issuer.get('cik')}:{event.get('ten_k_accession')}")
        target_dt = parse_acceptance(target_raw, "target_10k")
        if pair_acc is None:
            unpaired.append({"ten_k_accession": event.get("ten_k_accession"), "status": "NO_ELIGIBLE_PAIR"})
            continue
        pair_raw = event.get("paired_8k_acceptance_datetime")
        pair_dt = parse_acceptance(pair_raw, "paired_8k")
        lower_raw = event.get("pair_lower_bound_acceptance")
        lower_dt = parse_acceptance(lower_raw, "lower_bound") if lower_raw else None
        if event.get("paired_8k_form", "8-K") != "8-K" or event.get("paired_8k_is_amendment") is True:
            raise SystemExit(f"Q218_AMENDED_OR_INVALID_PAIR:{issuer.get('cik')}:{pair_acc}")
        if pair_dt >= target_dt:
            reason = "EQUAL_TARGET_TIMESTAMP" if pair_dt == target_dt else "PAIR_AFTER_TARGET"
            raise SystemExit(f"Q218_{reason}:{issuer.get('cik')}:{pair_acc}")
        if lower_dt is not None and pair_dt <= lower_dt:
            raise SystemExit(f"Q218_PAIR_NOT_AFTER_LOWER:{issuer.get('cik')}:{pair_acc}")
        if pair_acc in seen:
            raise SystemExit(f"Q218_DUPLICATE_PAIR_ASSIGNMENT:{pair_acc}:{seen[pair_acc]}:{event.get('ten_k_accession')}")
        seen[pair_acc] = str(event.get("ten_k_accession"))
        selected.append({
            "ten_k_accession": event.get("ten_k_accession"),
            "ten_k_acceptance_datetime": target_raw,
            "paired_8k_accession": pair_acc,
            "paired_8k_acceptance_datetime": pair_raw,
            "pair_lower_bound_acceptance": lower_raw,
            "status": "PAIR_VALIDATED",
        })
    return selected + unpaired, {
        "target_count": len(events),
        "paired_count": len(selected),
        "unpaired_count": len(unpaired),
        "duplicate_pair_assignments": 0,
    }

def run(census_path, output):
    census = json.loads(Path(census_path).read_text(encoding="utf-8"))
    issuers = census.get("q218_sec_pair_census", {}).get("issuer_results", {})
    if not isinstance(issuers, dict) or len(issuers) != 8:
        raise SystemExit("Q218_EXPECTED_EIGHT_ISSUERS")
    results = {}
    for symbol in sorted(issuers):
        rows, summary = pair_issuer(issuers[symbol])
        results[symbol] = {"summary": summary, "events": rows}
    out = {
        "schema_version": 1,
        "record_type": "q218_event_pair_pit_gate",
        "task_id": "Q-2026-10-06-218-EVENT-PAIR-PIT-GATE",
        "candidate_id": "Q218",
        "fixed_window": census.get("fixed_window", census.get("fixed_control_window", {})),
        "issuer_results": results,
        "issuer_count": 8,
        "target_10k_count": sum(x["summary"]["target_count"] for x in results.values()),
        "paired_10k_count": sum(x["summary"]["paired_count"] for x in results.values()),
        "unpaired_10k_count": sum(x["summary"]["unpaired_count"] for x in results.values()),
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
        "paper_only": True,
        "pit_policy":"strictly_before_target_acceptance; equal-second timestamps fail closed",
    }
    out["receipt_fingerprint"] = hashlib.sha256(json.dumps(out, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    r = run(args.census, args.output)
    print(json.dumps({
        "status":"Q218_EVENT_PAIR_PIT_GATE_COMPLETED",
        "target_10k_count":r["target_10k_count"],
        "paired_10k_count":r["paired_10k_count"],
        "unpaired_10k_count":r["unpaired_10k_count"],
        "receipt_fingerprint":r["receipt_fingerprint"],
    }, sort_keys=True))
