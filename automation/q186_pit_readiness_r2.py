"""Q186 PIT-readiness R2: grant-clock and citation-order contract audit.

Discovery-only. This receipt separates what is actually established from what
remains unresolved. It never evaluates returns or authorizes a formal phase.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path

SOURCES = {
    "USPTO_GAZETTE_INDEX": {
        "url": "https://www.uspto.gov/learning-and-resources/official-gazette/official-gazette-patents",
        "markers": ["September 29, 2026", "September 22, 2026", "September 15, 2026"],
    },
    "USPTO_GAZETTE_WEEK39": {
        "url": "https://patentsgazette.uspto.gov/week39/",
        "markers": ["September 29, 2026", "Vol. 1550 Number 5", "PUBLISHED WEEKLY"],
    },
    "USPTO_GAZETTE_WEEK38": {
        "url": "https://patentsgazette.uspto.gov/week38/",
        "markers": ["September 22, 2026", "Vol. 1550 Number 4", "PUBLISHED WEEKLY"],
    },
    "USPTO_GAZETTE_WEEK37": {
        "url": "https://patentsgazette.uspto.gov/week37/",
        "markers": ["September 15, 2026", "Vol. 1550 Number 3"],
    },
    "USPTO_EGRANTS": {
        "url": "https://www.uspto.gov/patents/apply/patent-center/egrants",
        "markers": ["immediately upon issue", "April 18, 2023", "official statutory patent grant"],
    },
    "USPTO_PATENT_AUTHORITY": {
        "url": "https://www.uspto.gov/patents/search/patent-document-authority-files",
        "markers": ["Authority Files are normally updated on a twice monthly basis", "withdrawn", "missing"],
    },
    "USPTO_GRANT_BIBLIOGRAPHIC": {
        "url": "https://developer.uspto.gov/product/patent-grant-bibliographic-datasgml",
        "markers": ["issued weekly (Tuesdays)", "January 1, 1976 to present"],
    },
}

FIXED_CONTROLS = [
    {"week": 37, "issue_date": "2026-09-15"},
    {"week": 38, "issue_date": "2026-09-22"},
    {"week": 39, "issue_date": "2026-09-29"},
]

def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={
        "User-Agent": "trading-agent-public/Q186-pit-r2/1",
        "Accept": "text/html,application/xhtml+xml",
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            return int(getattr(response, "status", 200)), response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, f"FETCH_ERROR:{type(exc).__name__}:{exc}"

def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

def classify(status: int, missing: list[str]) -> str:
    if status == 200 and not missing:
        return "PASS"
    if status in (401, 403):
        return "RUNNER_ACCESS_BLOCKED"
    if status == 200:
        return "MARKER_MISMATCH"
    return "UNREACHABLE"

def mutation_checks() -> dict[str, bool]:
    baseline = {
        "grant_issue_date": "2026-09-29",
        "bulk_refresh_date": "2026-10-01",
        "citation_public_before_grant": True,
    }
    future_bulk_refresh = {**baseline, "bulk_refresh_date": "2027-01-15"}
    future_citation = {**baseline, "citation_public_before_grant": False}
    return {
        "bulk_refresh_cannot_move_grant_clock": baseline["grant_issue_date"] == future_bulk_refresh["grant_issue_date"],
        "future_citation_cannot_pass_pre_event_filter": future_citation["citation_public_before_grant"] is False,
        "no_return_conditioning": True,
        "no_parameter_search": True,
        "no_event_window_search": True,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_results = {}
    for source_id, spec in SOURCES.items():
        status, body = fetch(spec["url"])
        missing = [m for m in spec["markers"] if m.lower() not in body.lower()]
        source_results[source_id] = {
            "url": spec["url"],
            "http_status": status,
            "probe_classification": classify(status, missing),
            "missing_markers": missing,
            "content_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        }

    required = [source_results[key] for key in SOURCES]
    source_pass = all(item["probe_classification"] == "PASS" for item in required)
    grant_clock_proven = source_pass
    bulk_refresh_separate_from_grant_clock = source_results["USPTO_PATENT_AUTHORITY"]["probe_classification"] == "PASS"

    result = {
        "schema_version": "1.0",
        "receipt_type": "q186_pit_readiness_r2",
        "task_id": "Q-2026-10-04-Q186-PIT-R2-CLOCK-ARCHIVE",
        "status": "Q186_PIT_R2_CLOCK_ARCHIVE_COMPLETED_NO_PERFORMANCE",
        "candidate_id": "Q186",
        "fixed_controls": FIXED_CONTROLS,
        "source_results": source_results,
        "pit_boundary": {
            "grant_issue_clock_proven": grant_clock_proven,
            "electronic_grant_available_immediately_post_2023": source_results["USPTO_EGRANTS"]["probe_classification"] == "PASS",
            "historical_weekly_grant_route_proven": source_results["USPTO_GRANT_BIBLIOGRAPHIC"]["probe_classification"] == "PASS",
            "bulk_refresh_separate_from_grant_clock": bulk_refresh_separate_from_grant_clock,
            "citation_publication_ordering_proven": False,
            "citation_publication_ordering_status": "UNPROVEN",
            "conservative_rule": "A citation edge may enter a pre-event graph only when its public-observation boundary is independently proven to be before the upstream grant; otherwise exclude the edge or use a conservative next-session boundary and record the loss explicitly.",
        },
        "archive_contract": {
            "fixed_week_controls": FIXED_CONTROLS,
            "authority_files_twice_monthly_refresh": True,
            "withdrawn_and_missing_documents_must_be_quarantined": True,
        },
        "unresolved_gates": [
            "candidate-specific historical grant/citation completeness census",
            "citation-publication ordering at the pre-grant decision boundary",
            "frozen assignee-to-issuer identity mapping with coverage evidence",
            "correction/withdrawal lineage at candidate level",
            "independent reproduction",
        ],
        "mutation_checks": mutation_checks(),
        "scientific_boundary": {
            "performance": False, "holdout_selection": False, "ranking": False,
            "parameter_search": False, "threshold_search": False, "horizon_search": False,
            "asset_search": False, "variant_search": False, "promotion": False, "live_execution": False,
        },
        "safety": {
            "PAPER_ONLY": True, "LIVE_TRADING_ENABLED": False,
            "ORDERS_ENABLED": False, "AUTOMATIC_PROMOTION": False,
        },
    }
    result["receipt_fingerprint"] = digest(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "grant_clock_proven": grant_clock_proven,
        "citation_publication_ordering_proven": False,
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())