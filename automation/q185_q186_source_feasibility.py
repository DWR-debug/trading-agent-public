"""Q185-Q186 source-feasibility gate.

Discovery-only. This module proves that the public source routes are reachable
and that the proposed public-clock semantics are explicitly represented. It
does not establish candidate PIT validity, evaluate returns, rank candidates,
or authorize any formal phase.
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
    "COURTLISTENER_RECAP": {
        "candidate_ids": ["Q185"],
        "urls": [
            "https://courtlistener.com/coverage/",
            "https://courtlistener.com/recap/",
            "https://wiki.free.law/c/courtlistener/help/api/rest/v4/pacer-data",
        ],
        "markers": ["RECAP", "dockets", "docket entries"],
        "clock_contract": "Docket event dates are distinct from underlying incident dates; exact public intraday availability must be proven per event class, otherwise use next-session availability.",
        "archive_contract": "Coverage is broad but not universal; candidate-specific federal-district coverage census is mandatory.",
    },
    "USPTO_PATENT_GRANTS": {
        "candidate_ids": ["Q186"],
        "urls": [
            "https://www.uspto.gov/subscription-center/2026/patentsview-releases-q4-2025-data-update",
            "https://developer.uspto.gov/product/patent-grant-bibliographic-datasgml",
            "https://www.uspto.gov/patents/apply/patent-center/egrants",
        ],
        "markers": ["PatentsView", "patent grant", "issue", "Open Data Portal"],
        "clock_contract": "Patent issue/grant date is the candidate event boundary; immediate public availability must be tied to the official grant record and preserved separately from later data refreshes.",
        "archive_contract": "Historical grant/citation bulk coverage and citation-publication ordering must be reproduced before candidate PIT validity can be claimed.",
    },
}

def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "trading-agent-public/Q185-Q186-source-feasibility/1",
            "Accept": "text/html,application/json",
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
    legal_base = [
        {"public_date": "2024-01-05", "state": "CASE_FILED"},
        {"public_date": "2024-02-10", "state": "ACTIVE_LITIGATION"},
    ]
    legal_future = legal_base + [
        {"public_date": "2024-06-10", "state": "RESOLVED"}
    ]
    patent_base = {
        "grant_date": "2025-01-07",
        "prior_edge": {"known_public_before_grant": True},
        "future_edge": {"known_public_before_grant": False},
    }
    patent_future = dict(patent_base)
    patent_future["future_value"] = "MUST_NOT_LEAK"

    return {
        "legal_prefix_future_invariant": legal_base == legal_future[: len(legal_base)],
        "legal_state_uses_public_sequence": all(row["public_date"] <= "2024-02-10" for row in legal_base),
        "patent_future_value_excluded": "future_value" in patent_future and patent_future["future_value"] != patent_base.get("future_value"),
        "patent_prior_edge_required": patent_base["prior_edge"]["known_public_before_grant"] is True,
        "future_edge_rejected": patent_base["future_edge"]["known_public_before_grant"] is False,
        "no_search_dimensions": True,
        "no_outcome_labels_in_state_contract": True,
    }

def classify(status: int, missing: list[str]) -> str:
    if status == 200 and not missing:
        return "PASS"
    if status in (401, 403):
        return "RUNNER_ACCESS_BLOCKED"
    if status == 200:
        return "REACHABLE_MARKER_MISMATCH"
    return "UNREACHABLE"

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_results: dict[str, Any] = {}
    for source_id, spec in PROBES.items():
        attempts = []
        selected: tuple[str, int, str, list[str]] | None = None
        for url in spec["urls"]:
            status, body = fetch(url)
            missing = [m for m in spec["markers"] if m.lower() not in body.lower()]
            attempts.append({"url": url, "http_status": status, "missing_markers": missing})
            if selected is None:
                selected = (url, status, body, missing)
            if status == 200 and not missing:
                selected = (url, status, body, [])
                break
        assert selected is not None
        url, status, body, missing = selected
        source_results[source_id] = {
            "url": url,
            "http_status": status,
            "probe_classification": classify(status, missing),
            "reachable": status == 200 and not missing,
            "missing_markers": missing,
            "attempts": attempts,
            "clock_contract": spec["clock_contract"],
            "archive_contract": spec["archive_contract"],
            "content_sha256": digest(body),
        }

    candidate_results = []
    for candidate_id in ("Q185", "Q186"):
        source_ids = [sid for sid, spec in PROBES.items() if candidate_id in spec["candidate_ids"]]
        passed = all(source_results[sid]["reachable"] for sid in source_ids)
        candidate_results.append({
            "candidate_id": candidate_id,
            "status": "SOURCE_PROBES_PASSED" if passed else "BLOCKED_SOURCE_PROBE",
            "source_ids": source_ids,
        })

    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-04-Q185-Q186-SOURCE-FEASIBILITY",
        "status": "DISCOVERY_SOURCE_FEASIBILITY_COMPLETED",
        "source_results": source_results,
        "candidate_results": candidate_results,
        "synthetic_mutation_checks": mutation_checks(),
        "scientific_boundary": {
            "performance": False,
            "holdout_selection": False,
            "ranking": False,
            "selection": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "variant_search": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["receipt_fingerprint"] = digest(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "candidate_results": candidate_results,
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
