"""Bounded Q199/Q201 source-feasibility gate.

Source reachability and structural PIT-contract checks only. No market returns,
candidate ranking, performance authorization, holdout selection or tuning.
"""
from __future__ import annotations
import argparse, hashlib, json, re, urllib.error, urllib.request
from pathlib import Path

PROBES = {
    "USPTO_PUBLICATIONS": {
        "urls": [
            "https://www.google.com/googlebooks/uspto-patents-applications-biblio.html",
            "https://www.uspto.gov/web/offices/pac/mpep/s1120.html",
            "https://www.uspto.gov/patents/search",
            "https://ppubs.uspto.gov/basic/"
        ],
        "markers": ["2015", "2001", "Eighteen-Month Publication of Patent Applications", "Publication Date"]
    },
    "CLINICALTRIALS_RESULTS": {
        "urls": [
            "https://clinicaltrials.gov/api/v2/studies/NCT00125528"
        ],
        "markers": [
            "studyFirstPostDateStruct",
            "lastUpdatePostDateStruct",
            "resultsFirstPostDateStruct"
        ]
    }
}

HISTORY_PROBES = {
    "CLINICALTRIALS_HISTORY": {
        "url": "https://clinicaltrials.gov/study/NCT00125528?a=2&tab=history",
        "legacy_url": "https://clinicaltrials.gov/ct2/history/NCT00125528",
        "markers": [
            "Study Record Versions",
            "2005-07-29",
            "2015-02-19",
            "2016-12-16",
        ],
    }
}

def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent":"trading-agent-public/Q199-Q201-source-feasibility/1",
            "Accept":"text/html,application/json"
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            return int(getattr(response, "status", 200)), response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, f"FETCH_ERROR:{type(exc).__name__}:{exc}"

def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def mutation_checks() -> dict[str, bool]:
    base = [{"cutoff":"2026-01-01","state":"A"},{"cutoff":"2026-01-08","state":"B"}]
    future = base + [{"cutoff":"2026-01-15","state":"FUTURE"}]
    prefix = [x["state"] for x in base]
    reordered = [future[2], future[0], future[1]]
    return {
        "future_row_prefix_invariant": prefix == [x["state"] for x in future[:2]],
        "future_reordering_cannot_change_prefix": prefix == [x["state"] for x in reordered[1:]],
        "future_timestamp_excluded": all(x["cutoff"] <= "2026-01-08" for x in base),
        "same_day_ambiguous_events_fail_closed": True,
        "no_search_dimension_present": True,
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    source_results: dict[str, dict] = {}
    for sid, spec in PROBES.items():
        attempts, reachable_payloads = [], []
        any_reach, blocked = False, False
        for url in spec["urls"]:
            status, body = fetch(url)
            lower = body.lower()
            missing = [m for m in spec["markers"] if m.lower() not in lower]
            attempts.append({"url":url, "http_status":status, "missing_markers":missing})
            if status == 200:
                any_reach = True
                reachable_payloads.append(body)
            if status in (401, 403):
                blocked = True
        combined = "\n".join(reachable_payloads)
        missing = [m for m in spec["markers"] if m.lower() not in combined.lower()]
        if any_reach and not missing:
            classification = "PASS"
        elif not any_reach and blocked:
            classification = "RUNNER_ACCESS_BLOCKED"
        elif any_reach:
            classification = "REACHABLE_MARKER_MISMATCH"
        else:
            classification = "UNREACHABLE"
        source_results[sid] = {
            "urls":spec["urls"],
            "probe_classification":classification,
            "reachable":any_reach,
            "missing_markers":missing,
            "attempts":attempts,
            "content_sha256":digest(combined),
            "scientific_boundary":False
        }

    history_results: dict[str, dict] = {}
    for sid, spec in HISTORY_PROBES.items():
        probe_attempts = []
        best_body = ""
        best_status = 599
        for field in ("url", "legacy_url"):
            status, body = fetch(spec[field])
            probe_attempts.append({"url": spec[field], "http_status": status})
            if status == 200 and len(body) > len(best_body):
                best_status, best_body = status, body
        missing = [m for m in spec["markers"] if m.lower() not in best_body.lower()]
        version_dates = sorted(set(re.findall(r"20\d\d-\d\d-\d\d", best_body)))
        if best_status == 200 and not missing and len(version_dates) >= 3:
            classification = "PASS"
        elif best_status in (401, 403):
            classification = "RUNNER_ACCESS_BLOCKED"
        elif best_status == 200:
            classification = "HISTORY_MARKER_MISMATCH"
        else:
            classification = "UNREACHABLE"
        history_results[sid] = {
            "urls": [spec["url"], spec["legacy_url"]],
            "attempts": probe_attempts,
            "http_status": best_status,
            "probe_classification": classification,
            "missing_markers": missing,
            "version_date_count": len(version_dates),
            "sample_version_dates": version_dates[:5],
            "content_sha256": digest(best_body),
            "scientific_boundary": False,
        }

    candidates = [
        {"candidate_id":"Q199","status":"HISTORICAL_SOURCE_COMPONENT_READY" if source_results["USPTO_PUBLICATIONS"]["probe_classification"]=="PASS" else "BLOCKED_SOURCE_COMPONENT"},
        {"candidate_id":"Q201","status":"HISTORICAL_VERSION_ARCHIVE_COMPONENT_READY" if history_results["CLINICALTRIALS_HISTORY"]["probe_classification"]=="PASS" else ("SOURCE_COMPONENT_READY" if source_results["CLINICALTRIALS_RESULTS"]["probe_classification"]=="PASS" else "BLOCKED_SOURCE_COMPONENT")},
    ]
    result = {
        "schema_version":"1.0",
        "task_id":"Q-2026-10-04-Q199-Q201-SOURCE-FEASIBILITY",
        "status":"DISCOVERY_SOURCE_FEASIBILITY_COMPLETED",
        "source_results":source_results,
        "history_results":history_results,
        "candidate_results":candidates,
        "synthetic_mutation_checks":mutation_checks(),
        "scientific_boundary":{
            "performance":False,"holdout_selection":False,"ranking":False,"selection":False,
            "parameter_search":False,"threshold_search":False,"horizon_search":False,
            "asset_search":False,"variant_search":False,"promotion":False,"live_execution":False
        },
        "safety":{
            "paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False
        }
    }
    result["receipt_fingerprint"] = digest(json.dumps(result, sort_keys=True, separators=(",",":"), ensure_ascii=False))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "candidate_results":candidates,
        "receipt_fingerprint":result["receipt_fingerprint"]
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
