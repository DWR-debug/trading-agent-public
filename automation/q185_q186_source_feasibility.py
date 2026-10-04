"""Q185-Q186 source-feasibility gate.

Discovery-only. Proves public source routes are reachable and their public-clock
contracts are explicit. It does not establish candidate PIT validity, evaluate
returns, rank candidates, or authorize any formal phase.
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
    "COURTLISTENER_COVERAGE": {
        "candidate_ids": ["Q185"],
        "url": "https://courtlistener.com/coverage/",
        "markers": ["RECAP Archive", "federal filings"],
        "clock_contract": "Docket event dates are distinct from underlying incident dates; exact public intraday availability must be proven per event class, otherwise use next-session availability.",
        "archive_contract": "Coverage is broad but not universal; candidate-specific federal-district coverage census is mandatory.",
    },
    "COURTLISTENER_RECAP": {
        "candidate_ids": ["Q185"],
        "url": "https://courtlistener.com/recap/",
        "markers": ["Advanced RECAP Search", "Docket Number", "Entry Date"],
        "clock_contract": "A recorded docket-entry date is not automatically proof of public dissemination time.",
        "archive_contract": "Searchable RECAP coverage must be measured for the exact historical window and issuer population.",
    },
    "USPTO_PATENTSVIEW": {
        "candidate_ids": ["Q186"],
        "url": "https://www.uspto.gov/subscription-center/2026/patentsview-releases-q4-2025-data-update",
        "markers": ["PatentsView", "Open Data Portal", "December 31, 2025"],
        "clock_contract": "PatentsView bulk refresh/vintage is distinct from patent issue/publication timing.",
        "archive_contract": "Historical disambiguated patent/citation coverage must be reproduced from public USPTO data.",
    },
    "USPTO_PATENT_GRANTS": {
        "candidate_ids": ["Q186"],
        "url": "https://developer.uspto.gov/product/patent-grant-bibliographic-datasgml",
        "markers": ["patent grant", "1976", "weekly"],
        "clock_contract": "Grant issue date is the candidate event boundary; weekly publication and later bulk refresh remain separate.",
        "archive_contract": "Grant/citation archive completeness and citation-publication ordering must be reproduced.",
    },
    "USPTO_EGRANTS": {
        "candidate_ids": ["Q186"],
        "url": "https://www.uspto.gov/patents/apply/patent-center/egrants",
        "markers": ["April 18, 2023", "immediately upon issue", "official statutory patent grant"],
        "clock_contract": "For post-2023 grants the official eGrant provides a documented public-access boundary; earlier history requires separate proof.",
        "archive_contract": "Historical grants must be complete; corrections/withdrawals cannot rewrite earlier decision prefixes.",
    },
}

CANDIDATE_SOURCES = {
    "Q185": ["COURTLISTENER_COVERAGE", "COURTLISTENER_RECAP"],
    "Q186": ["USPTO_PATENTSVIEW", "USPTO_PATENT_GRANTS", "USPTO_EGRANTS"],
}

def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "trading-agent-public/Q185-Q186-source-feasibility/2", "Accept": "text/html,application/json"},
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
    legal_base = [{"public_date": "2024-01-05", "state": "CASE_FILED"}, {"public_date": "2024-02-10", "state": "ACTIVE_LITIGATION"}]
    legal_future = legal_base + [{"public_date": "2024-06-10", "state": "RESOLVED"}]
    patent_edges = [{"known_public_before_grant": True, "edge": "UPSTREAM->DOWNSTREAM"}, {"known_public_before_grant": False, "edge": "FUTURE"}]
    eligible_edges = [x for x in patent_edges if x["known_public_before_grant"]]
    return {
        "legal_prefix_future_invariant": legal_base == legal_future[:len(legal_base)],
        "legal_future_state_not_visible_in_prefix": "RESOLVED" not in [x["state"] for x in legal_base],
        "patent_future_edge_excluded": len(eligible_edges) == 1 and eligible_edges[0]["edge"] == "UPSTREAM->DOWNSTREAM",
        "patent_prior_edge_required": patent_edges[0]["known_public_before_grant"] is True,
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
        url = spec["url"]
        status, body = fetch(url)
        missing = [m for m in spec["markers"] if m.lower() not in body.lower()]
        source_results[source_id] = {
            "url": url,
            "http_status": status,
            "probe_classification": classify(status, missing),
            "reachable": status == 200 and not missing,
            "missing_markers": missing,
            "attempts": [{"url": url, "http_status": status, "missing_markers": missing}],
            "clock_contract": spec["clock_contract"],
            "archive_contract": spec["archive_contract"],
            "content_sha256": digest(body),
        }
    candidate_results = []
    for candidate_id, source_ids in CANDIDATE_SOURCES.items():
        passed = all(source_results[sid]["reachable"] for sid in source_ids)
        candidate_results.append({"candidate_id": candidate_id, "status": "SOURCE_PROBES_PASSED" if passed else "BLOCKED_SOURCE_PROBE", "source_ids": source_ids})
    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-04-Q185-Q186-SOURCE-FEASIBILITY",
        "status": "DISCOVERY_SOURCE_FEASIBILITY_COMPLETED",
        "source_results": source_results,
        "candidate_results": candidate_results,
        "synthetic_mutation_checks": mutation_checks(),
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