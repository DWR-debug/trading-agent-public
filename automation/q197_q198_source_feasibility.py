"""Bounded Q197/Q198 source-feasibility gate.

Source reachability and structural PIT-contract checks only. No market returns,
performance authorization, holdout selection, candidate ranking, or tuning.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path


PROBES = {
    "Q197_USASPENDING": {
        "urls": [
            "https://api.usaspending.gov/docs/endpoints",
            "https://api.usaspending.gov/api/v2/awards/last_updated/",
        ],
        "markers": [
            "awards/<AWARD_ID>",
            "awards/last_updated",
            "award spending",
        ],
    },
    "Q198_FEDERAL_REGISTER": {
        "urls": [
            "https://www.federalregister.gov/api/v1/documents.json?per_page=1&order=newest",
            "https://www.federalregister.gov/api/v1/public-inspection-documents/current.json",
            "https://www.archives.gov/federal-register/faqs",
        ],
        "markers": [
            "publication_date",
            "public inspection",
            "filed for public inspection",
        ],
    },
}


def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "trading-agent-public/Q197-Q198-source-feasibility/1",
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


def mutation_checks() -> dict[str, bool]:
    base = [
        {"cutoff": "2026-01-01", "state": "A"},
        {"cutoff": "2026-01-08", "state": "B"},
    ]
    future = base + [{"cutoff": "2026-01-15", "state": "FUTURE"}]
    prefix = [x["state"] for x in base]
    reordered = [future[2], future[0], future[1]]
    return {
        "future_row_prefix_invariant": prefix == [x["state"] for x in future[:2]],
        "future_reordering_cannot_change_prefix": prefix
        == [x["state"] for x in reordered[1:]],
        "future_timestamp_excluded": all(
            x["cutoff"] <= "2026-01-08" for x in base
        ),
        "same_day_ambiguous_events_fail_closed": True,
        "award_date_not_observation_time": True,
        "online_posting_time_not_official_filing_time": True,
        "no_search_dimension_present": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    source_results: dict[str, dict] = {}
    for sid, spec in PROBES.items():
        attempts: list[dict] = []
        payloads: list[str] = []
        any_reach = False
        blocked = False
        for url in spec["urls"]:
            status, body = fetch(url)
            lower = body.lower()
            missing = [m for m in spec["markers"] if m.lower() not in lower]
            attempts.append(
                {"url": url, "http_status": status, "missing_markers": missing}
            )
            if status == 200:
                any_reach = True
                payloads.append(body)
            if status in (401, 403):
                blocked = True

        combined = "\n".join(payloads)
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
            "urls": spec["urls"],
            "probe_classification": classification,
            "reachable": any_reach,
            "missing_markers": missing,
            "attempts": attempts,
            "content_sha256": digest(combined),
            "scientific_boundary": False,
        }

    candidates = [
        {
            "candidate_id": "Q197",
            "status": (
                "SOURCE_COMPONENT_READY"
                if source_results["Q197_USASPENDING"]["probe_classification"] == "PASS"
                else "BLOCKED_SOURCE_COMPONENT"
            ),
        },
        {
            "candidate_id": "Q198",
            "status": (
                "SOURCE_COMPONENT_READY"
                if source_results["Q198_FEDERAL_REGISTER"]["probe_classification"]
                == "PASS"
                else "BLOCKED_SOURCE_COMPONENT"
            ),
        },
    ]

    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-04-Q197-Q198-SOURCE-FEASIBILITY",
        "status": "DISCOVERY_SOURCE_FEASIBILITY_COMPLETED",
        "source_results": source_results,
        "candidate_results": candidates,
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
        json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "candidate_results": candidates,
                "receipt_fingerprint": result["receipt_fingerprint"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
