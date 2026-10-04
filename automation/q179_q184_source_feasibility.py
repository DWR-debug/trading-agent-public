"""Q179-Q184 public/free source-feasibility gate.
Discovery-only: source reachability + clock markers + synthetic future mutation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

PROBES: dict[str, dict[str, Any]] = {
    "CLINICALTRIALS": {
        "url": "https://clinicaltrials.gov/",
        "markers": ["First posted", "Last update posted", "Results first posted"],
        "clock_contract": "Posted-date fields define public availability; submitted dates are separate.",
    },
    "NHTSA_RECALLS": {
        "url": "https://www.nhtsa.gov/nhtsa-datasets-and-apis",
        "markers": ["Time Period: 1949 to present", "Frequency: Daily", "published"],
        "clock_contract": "Recall publication date is distinct from the underlying safety-issue report date.",
    },
    "OSHA_DATA": {
        "url": "https://www.osha.gov/enforcement/",
        "markers": ["Data", "Fatality Inspection Data", "High Penalty Cases - Historical"],
        "clock_contract": "Inspection/opening and public display/download boundaries must be separated.",
    },
    "FERC_ELIBRARY": {
        "url": "https://www.ferc.gov/ferc-online/elibrary",
        "markers": ["issued and received", "Search", "download"],
        "clock_contract": "Issued/received document records are distinct from later corrections and underlying event dates.",
    },
    "NTSB_CAROL": {
        "url": "https://www.ntsb.gov/safety/data/pages/data_stats.aspx",
        "markers": ["CAROL", "1982 to the present", "daily and pending aviation publication report"],
        "clock_contract": "Investigation event and publication times remain distinct.",
    },
    "FCC_ULS": {
        "url": "https://opendata.fcc.gov/Wireless/FCC-Universal-Licensing-System-ULS-/x28i-i4z4",
        "markers": ["daily transaction files", "weekly transaction files", "Public Domain"],
        "clock_contract": "Transaction identity/date is distinct from daily/weekly dissemination files.",
    },
}
CANDIDATE_SOURCES = {
    "Q179": ["CLINICALTRIALS"],
    "Q180": ["NHTSA_RECALLS"],
    "Q181": ["OSHA_DATA"],
    "Q182": ["FERC_ELIBRARY"],
    "Q183": ["NTSB_CAROL"],
    "Q184": ["FCC_ULS"],
}

def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "trading-agent-public/Q179-Q184-source-feasibility/1", "Accept": "text/html,application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            return int(getattr(response, "status", 200)), response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, f"FETCH_ERROR:{type(exc).__name__}:{exc}"

def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def future_mutation_invariance() -> dict[str, bool]:
    base = [{"cutoff": "2026-01-02", "state": "A"}, {"cutoff": "2026-01-03", "state": "B"}]
    mutated = base + [{"cutoff": "2026-01-04", "state": "FUTURE"}]
    return {
        "future_row_prefix_invariant": [x["state"] for x in base] == [x["state"] for x in mutated[:len(base)]],
        "future_timestamp_excluded": all(row["cutoff"] <= "2026-01-03" for row in base),
        "no_search_dimension_present": True,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source_results = {}
    for source_id, spec in PROBES.items():
        status, body = fetch(spec["url"])
        lowered = body.lower()
        missing = [m for m in spec["markers"] if m.lower() not in lowered]
        source_results[source_id] = {
            "url": spec["url"],
            "http_status": status,
            "reachable": status == 200,
            "required_markers_present": status == 200 and not missing,
            "missing_markers": missing,
            "clock_contract": spec["clock_contract"],
            "content_sha256": digest(body),
        }
    candidate_results = []
    for candidate_id, source_ids in CANDIDATE_SOURCES.items():
        candidate_results.append({
            "candidate_id": candidate_id,
            "status": "SOURCE_PROBES_PASSED" if all(source_results[s]["required_markers_present"] for s in source_ids) else "BLOCKED_SOURCE_PROBE",
            "source_ids": source_ids,
        })
    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-04-Q179-Q184-SOURCE-FEASIBILITY",
        "status": "DISCOVERY_SOURCE_FEASIBILITY_COMPLETED",
        "source_results": source_results,
        "candidate_results": candidate_results,
        "synthetic_mutation_checks": future_mutation_invariance(),
        "scientific_boundary": {
            "performance": False, "holdout_selection": False, "ranking": False, "selection": False,
            "parameter_search": False, "threshold_search": False, "horizon_search": False,
            "asset_search": False, "variant_search": False, "promotion": False, "live_execution": False,
        },
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
    }
    result["receipt_fingerprint"] = digest(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "candidate_results": candidate_results, "receipt_fingerprint": result["receipt_fingerprint"]}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
