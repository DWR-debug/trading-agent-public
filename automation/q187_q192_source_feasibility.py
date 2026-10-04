"""Q187-Q192 public/free source-feasibility gate.

Discovery-only: bounded source reachability, required markers and synthetic
chronology invariants. This module never reads returns and cannot authorize
performance, selection, ranking, tuning, promotion or live execution.
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
    "USASPENDING": {
        "urls": [
            "https://api.usaspending.gov/docs/endpoints",
            "https://www.usaspending.gov/keyword_search/2026",
        ],
        "markers": [
            "Endpoints do not currently require any authorization",
            "Action Date",
            "Award ID",
            "Transaction Amount",
        ],
        "clock_contract": (
            "Award action date is distinct from the time the transaction record "
            "becomes publicly retrievable. Formal PIT must prove a public boundary "
            "or conservatively shift use to the next eligible session."
        ),
    },
    "FDA_SRLC": {
        "urls": [
            "https://www.fda.gov/safety/medical-product-safety-information/drug-safety-related-labeling-changes",
            "https://www.fda.gov/drugs/drug-safety-and-availability/drug-safety-related-labeling-changes-srlc-database-overview-updates-safety-information-fda-approved",
        ],
        "markers": [
            "Drug Safety-related Labeling Changes",
            "January 2016",
            "Search Labeling by Drug Name",
            "Search Labeling by Date Range",
        ],
        "clock_contract": (
            "Supplement/date/update fields describe the labeling event and database "
            "state separately. Exact first-public observation and later corrections "
            "must be reconstructed before same-day use."
        ),
    },
    "CPSC_RECALLS": {
        "urls": [
            "https://www.cpsc.gov/Recalls/CPSC-Recalls-Application-Program-Interface-API-Information",
            "https://www.cpsc.gov/Data",
        ],
        "markers": [
            "Recall Data API",
            "machine readable",
            "decades of consumer product recall information",
        ],
        "clock_contract": (
            "Recall publication state is distinct from incident/manufacture dates. "
            "Historical public-observation timing and revisions/withdrawals must be "
            "kept separate."
        ),
    },
    "EPA_ECHO": {
        "urls": [
            "https://echo.epa.gov/tools/data-downloads",
            "https://echo.epa.gov/resources/echo-data/about-the-data",
        ],
        "markers": [
            "Data Downloads",
            "updated weekly",
            "compliance",
            "enforcement",
        ],
        "clock_contract": (
            "Facility/event dates are not interchangeable with the public ECHO "
            "refresh/extraction boundary. Historical PIT must use the documented "
            "refresh clock and prevent later refreshes from rewriting the prefix."
        ),
    },
    "USPTO_PATENT": {
        "urls": [
            "https://www.uspto.gov/products/patent-grant-data",
            "https://www.uspto.gov/learning-and-resources/official-gazette/official-gazette-patents",
        ],
        "markers": [
            "Patent Grant Full Text Data",
            "Official Gazette",
            "patent grants",
        ],
        "clock_contract": (
            "Patent issue/publication date is distinct from later bulk-data refreshes. "
            "For Q191 the science-publication boundary must be separately proven and "
            "same-day ambiguous ordering must be excluded."
        ),
    },
    "CROSSREF": {
        "urls": [
            "https://api.crossref.org/works?rows=1",
        ],
        "markers": [
            "message",
            "status",
        ],
        "clock_contract": (
            "Crossref deposit/publication metadata is not automatically an exact "
            "public-dissemination timestamp; historical stage ordering must be proven."
        ),
    },
    "FDA_SHORTAGES": {
        "urls": [
            "https://www.fda.gov/drug-shortages",
            "https://open.fda.gov/data/drugshortages/",
            "https://api.fda.gov/drug/shortages.json?limit=1",
        ],
        "markers": [
            "Drug Shortages",
            "updated daily",
            "Drug Shortages download information",
        ],
        "clock_contract": (
            "Shortage start/resolution dates are distinct from first public observation. "
            "Historical daily-list state must be reconstructed without allowing current "
            "records to overwrite earlier prefixes."
        ),
    },
}

CANDIDATE_SOURCES = {
    "Q187": ["USASPENDING"],
    "Q188": ["FDA_SRLC"],
    "Q189": ["CPSC_RECALLS"],
    "Q190": ["EPA_ECHO"],
    "Q191": ["USPTO_PATENT", "CROSSREF"],
    "Q192": ["FDA_SHORTAGES"],
}


def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "trading-agent-public/Q187-Q192-source-feasibility/1",
            "Accept": "text/html,application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            return int(getattr(response, "status", 200)), response.read().decode(
                "utf-8", errors="replace"
            )
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, f"FETCH_ERROR:{type(exc).__name__}:{exc}"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def chronology_mutation_invariance() -> dict[str, bool]:
    base = [
        {"cutoff": "2026-02-02", "state": "A"},
        {"cutoff": "2026-02-03", "state": "B"},
    ]
    future = base + [{"cutoff": "2026-02-04", "state": "FUTURE"}]
    reordered = [future[2], future[0], future[1]]
    prefix = [x["state"] for x in base]
    return {
        "future_row_prefix_invariant": prefix
        == [x["state"] for x in future[: len(base)]],
        "future_timestamp_excluded": all(
            row["cutoff"] <= "2026-02-03" for row in base
        ),
        "reordering_future_row_cannot_change_prefix": prefix
        == [x["state"] for x in reordered[1:]],
        "no_search_dimension_present": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_results: dict[str, dict[str, Any]] = {}
    for source_id, spec in PROBES.items():
        attempts: list[dict[str, Any]] = []
        selected: tuple[str, int, str, list[str]] | None = None

        for url in spec["urls"]:
            status, body = fetch(url)
            lowered = body.lower()
            missing = [
                marker for marker in spec["markers"] if marker.lower() not in lowered
            ]
            attempts.append(
                {
                    "url": url,
                    "http_status": status,
                    "missing_markers": missing,
                }
            )
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
            "reachable": status == 200,
            "required_markers_present": status == 200 and not missing,
            "probe_classification": (
                "PASS"
                if status == 200 and not missing
                else (
                    "RUNNER_ACCESS_BLOCKED"
                    if status in (401, 403)
                    else (
                        "REACHABLE_MARKER_MISMATCH"
                        if status == 200
                        else "UNREACHABLE"
                    )
                )
            ),
            "missing_markers": missing,
            "attempts": attempts,
            "clock_contract": spec["clock_contract"],
            "content_sha256": digest(body),
        }

    candidate_results = [
        {
            "candidate_id": candidate_id,
            "status": (
                "SOURCE_PROBES_PASSED"
                if all(
                    source_results[source_id]["required_markers_present"]
                    for source_id in source_ids
                )
                else "BLOCKED_SOURCE_PROBE"
            ),
            "source_ids": source_ids,
        }
        for candidate_id, source_ids in CANDIDATE_SOURCES.items()
    ]

    result: dict[str, Any] = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-04-Q187-Q192-SOURCE-FEASIBILITY",
        "status": "DISCOVERY_SOURCE_FEASIBILITY_COMPLETED",
        "source_results": source_results,
        "candidate_results": candidate_results,
        "synthetic_mutation_checks": chronology_mutation_invariance(),
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
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "candidate_results": candidate_results,
                "source_results": source_results,
                "receipt_fingerprint": result["receipt_fingerprint"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
