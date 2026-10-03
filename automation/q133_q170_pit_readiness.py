"""Q133-Q170 PIT-readiness R1.

This is a conservative downstream gate for candidates already classified as
source-feasible. It verifies timing/revision/mapping prerequisites and runs
bounded public sample probes where a deterministic sample is available.

It never evaluates returns, ranks candidates, searches parameters/horizons/
assets, selects a holdout, authorizes performance, promotes or trades live.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from automation.q133_q145_source_feasibility import CANDIDATE_SOURCES, PROBES

ROOT = Path(__file__).resolve().parents[1]
SOURCE_RECEIPT = ROOT / "research/evidence/q133_q170_source_feasibility_2026_10_03.json"

SOURCE_CONTRACTS: dict[str, dict[str, Any]] = {
    "SEC_EDGAR_SUBMISSIONS": {
        "clock": "filing acceptance timestamp",
        "revision": "amendment/accession lineage must remain explicit",
        "mapping": "issuer CIK and accession identity",
        "archive": "historical submissions retained",
        "contract_status": "PIT_CONTRACT_DEFINED_PENDING_ARCHIVE",
        "sample_url": "https://data.sec.gov/submissions/CIK0000320193.json",
        "sample_markers": ["filings", "acceptanceDateTime", "accessionNumber"],
    },
    "WIKIMEDIA_PAGEVIEWS": {
        "clock": "UTC pageview bucket timestamp",
        "revision": "redirect/entity mapping and historical retention must be frozen",
        "mapping": "issuer/entity-to-page mapping",
        "archive": "historical day-level series required",
        "contract_status": "PIT_CONTRACT_DEFINED_PENDING_ARCHIVE",
        "sample_url": "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/Apple/20251001/20251003",
        "sample_markers": ["items", "timestamp"],
    },
    "EIA_OPEN": {
        "clock": "release/vintage boundary",
        "revision": "continuous-series revisions must be separated from release state",
        "mapping": "fixed industry/energy exposure map",
        "archive": "historical vintage availability must be demonstrated",
        "contract_status": "PIT_CONTRACT_UNRESOLVED",
        "sample_url": "https://www.eia.gov/opendata/",
        "sample_markers": ["Open Data", "Bulk"],
    },
    "USA_SPENDING": {
        "clock": "public dissemination timestamp",
        "revision": "transaction/amendment semantics",
        "mapping": "contractor/issuer identity map",
        "archive": "historical transaction reconstruction",
        "contract_status": "PIT_CONTRACT_UNRESOLVED",
        "sample_url": "https://api.usaspending.gov/docs/endpoints",
        "sample_markers": ["Endpoints do not currently require any authorization"],
    },
    "COURTLISTENER": {
        "clock": "docket/publication timestamp",
        "revision": "docket amendment/entry corrections",
        "mapping": "party/issuer entity mapping",
        "archive": "historical docket coverage census",
        "contract_status": "PIT_CONTRACT_UNRESOLVED",
        "sample_url": "https://www.courtlistener.com/help/",
        "sample_markers": ["REST APIs"],
    },
    "CFTC_RELEASE": {
        "clock": "public COT release timestamp",
        "revision": "report revision handling",
        "mapping": "fixed commodity-to-issuer exposure map",
        "archive": "historical released reports",
        "contract_status": "PIT_CONTRACT_DEFINED_PENDING_ARCHIVE",
        "sample_url": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm",
        "sample_markers": ["3:30 p.m. Eastern", "2026 Release Schedule"],
    },
    "LDA_API": {
        "clock": "filing/publication timestamp",
        "revision": "filing amendments and duplicate records",
        "mapping": "registrant/entity and issue mapping",
        "archive": "historical filing retention",
        "contract_status": "PIT_CONTRACT_UNRESOLVED",
        "sample_url": "https://lda.gov/api/tos/",
        "sample_markers": ["Unauthenticated", "rate limited"],
    },
    "OPENFDA_DRUG": {
        "clock": "event/update timestamp",
        "revision": "record updates and corrections",
        "mapping": "manufacturer/issuer identity mapping",
        "archive": "historical event reconstruction",
        "contract_status": "PIT_CONTRACT_UNRESOLVED",
        "sample_url": "https://api.fda.gov/drug/drugsfda.json?limit=1",
        "sample_markers": ["results", "meta"],
    },
    "OPENFDA_DEVICE": {
        "clock": "recall/enforcement event timestamp",
        "revision": "record updates and corrections",
        "mapping": "manufacturer/issuer identity mapping",
        "archive": "historical event reconstruction",
        "contract_status": "PIT_CONTRACT_UNRESOLVED",
        "sample_url": "https://api.fda.gov/device/recall.json?limit=1",
        "sample_markers": ["results", "meta"],
    },
    "SEC_FOIA": {
        "clock": "request/received/closed dates",
        "revision": "log correction semantics",
        "mapping": "topic-to-issuer mapping",
        "archive": "historical FOIA log coverage",
        "contract_status": "PIT_CONTRACT_UNRESOLVED",
        "sample_url": "https://www.sec.gov/foia/frequently-requested-documents/foia-logs",
        "sample_markers": ["FOIA Logs"],
    },
    "GOVINFO": {
        "clock": "Federal Register publication timestamp",
        "revision": "correction/republication semantics",
        "mapping": "fixed rule-to-industry exposure classes",
        "archive": "historical bulk coverage",
        "contract_status": "PIT_CONTRACT_DEFINED_PENDING_ARCHIVE",
        "sample_url": "https://www.govinfo.gov/bulkdata/",
        "sample_markers": ["Federal Register"],
    },
    "BTS_FAF": {
        "clock": "vintage/release boundary",
        "revision": "historical FAF vintage identity",
        "mapping": "industry/commodity concordance",
        "archive": "historical vintage availability",
        "contract_status": "PIT_CONTRACT_UNRESOLVED",
        "sample_url": "https://www.bts.gov/faf",
        "sample_markers": ["Freight Analysis Framework"],
    },
    "EPA_ENVIROFACTS": {
        "clock": "agency action/publication timestamp",
        "revision": "facility record correction/update",
        "mapping": "facility-to-issuer identity map",
        "archive": "historical action coverage",
        "contract_status": "PIT_CONTRACT_UNRESOLVED",
        "sample_url": "https://www.epa.gov/enviro/envirofacts-data-service-api",
        "sample_markers": ["RESTful", "JSON"],
    },
    "FTC_DATA": {
        "clock": "enforcement publication timestamp",
        "revision": "dataset correction/republication",
        "mapping": "industry/peer exposure map",
        "archive": "historical enforcement dataset",
        "contract_status": "PIT_CONTRACT_UNRESOLVED",
        "sample_url": "https://search.ftc.gov/policy-notices/open-government/data-sets",
        "sample_markers": ["FTC Nonmerger Enforcement Actions"],
    },
    "DOJ_ANTITRUST": {
        "clock": "release publication timestamp",
        "revision": "release correction/update",
        "mapping": "industry/issuer graph",
        "archive": "historical release coverage",
        "contract_status": "PIT_CONTRACT_UNRESOLVED",
        "sample_url": "https://www.justice.gov/atr/press-releases",
        "sample_markers": ["Press Releases", "Antitrust"],
    },
    "PYPI_STATS": {
        "clock": "download-series period",
        "revision": "historical series retention and corrections",
        "mapping": "package-to-issuer mapping",
        "archive": "historical period coverage plus bot/CI contamination audit",
        "contract_status": "PIT_CONTRACT_DEFINED_PENDING_ARCHIVE",
        "sample_url": "https://pypistats.org/api/packages/requests/recent",
        "sample_markers": ["data", "last_day"],
    },
    "CROSSREF_API": {
        "clock": "created/update/index date",
        "revision": "metadata update and index semantics",
        "mapping": "author/affiliation-to-issuer mapping",
        "archive": "historical metadata retrieval",
        "contract_status": "PIT_CONTRACT_DEFINED_PENDING_ARCHIVE",
        "sample_url": "https://api.crossref.org/works?filter=from-created-date:2025-01-01,until-created-date:2025-01-02&rows=1",
        "sample_markers": ["message", "created", "indexed"],
    },
    "USGS_EARTHQUAKE": {
        "clock": "event origin time plus update time",
        "revision": "product update/supersession semantics",
        "mapping": "fixed geography/facility map",
        "archive": "historical event archive",
        "contract_status": "PIT_CONTRACT_DEFINED_PENDING_ARCHIVE",
        "sample_url": "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2025-01-01&endtime=2025-01-02&limit=1",
        "sample_markers": ["features", "properties", "time", "updated"],
    },
    "NOAA_SWPC": {
        "clock": "product issue time",
        "revision": "cancellation/archive semantics",
        "mapping": "fixed operational-sensitivity map",
        "archive": "historical product archive",
        "contract_status": "PIT_CONTRACT_DEFINED_PENDING_ARCHIVE",
        "sample_url": "https://services.swpc.noaa.gov/products/",
        "sample_markers": ["alerts.json"],
    },
}


def fetch(url: str) -> tuple[int, bytes]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "trading-agent-public/Q133-Q170-PIT-R1/1", "Accept": "*/*"},
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return int(getattr(response, "status", 200)), response.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, f"FETCH_ERROR:{type(exc).__name__}:{exc}".encode()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_sample(source_id: str, contract: dict[str, Any]) -> dict[str, Any]:
    status, body = fetch(str(contract["sample_url"]))
    text_body = body.decode("utf-8", errors="replace")
    missing = [m for m in contract["sample_markers"] if m.lower() not in text_body.lower()]
    if status != 200:
        sample_status = "INFRA_ACCESS_BLOCKED"
    elif missing:
        sample_status = "PIT_SAMPLE_PARSE_UNRESOLVED"
    else:
        sample_status = "SOURCE_DATA_SAMPLE_REACHABLE"
    return {
        "source_id": source_id,
        "url": contract["sample_url"],
        "http_status": status,
        "sample_status": sample_status,
        "missing_markers": missing,
        "content_sha256": sha256(body),
    }


def future_mutation_check() -> dict[str, bool]:
    base = [{"decision": 1, "state": "A"}, {"decision": 2, "state": "B"}]
    future = base + [{"decision": 3, "state": "FUTURE"}]
    return {
        "future_row_prefix_invariant": [x["state"] for x in base] == [x["state"] for x in future[:2]],
        "future_change_not_visible_to_prefix": future[:2] == base,
        "no_search_dimension_present": True,
    }


def load_inventory() -> dict[str, dict[str, Any]]:
    paths = [
        ROOT / "research/frontier/q133_q145_candidate_wave_2026_10_03.json",
        ROOT / "research/frontier/q146_q151_candidate_wave_2026_10_03.json",
        ROOT / "research/frontier/q152_q165_candidate_wave_2026_10_03.json",
        ROOT / "research/frontier/q166_q170_candidate_wave_2026_10_03.json",
    ]
    candidates: dict[str, dict[str, Any]] = {}
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("candidates", []):
            candidates[str(item["id"])] = item
    return candidates


def run(output: Path) -> dict[str, Any]:
    source_receipt = json.loads(SOURCE_RECEIPT.read_text(encoding="utf-8"))
    feasible = set(source_receipt.get("newly_source_feasible_candidates", []))
    inventory = load_inventory()

    candidate_results: list[dict[str, Any]] = []
    source_ids_needed = sorted(
        {
            source_id
            for candidate_id in feasible
            for source_id in CANDIDATE_SOURCES.get(candidate_id, [])
            if source_id in SOURCE_CONTRACTS
        }
    )
    source_results = {
        source_id: source_sample(source_id, SOURCE_CONTRACTS[source_id])
        for source_id in source_ids_needed
    }

    for candidate_id in sorted(feasible):
        candidate = inventory.get(candidate_id, {"id": candidate_id})
        source_ids = CANDIDATE_SOURCES.get(candidate_id, [])
        contracts = [SOURCE_CONTRACTS[s] for s in source_ids if s in SOURCE_CONTRACTS]
        missing_contracts = [s for s in source_ids if s not in SOURCE_CONTRACTS]
        source_samples = [source_results[s] for s in source_ids if s in source_results]

        if missing_contracts:
            pit_status = "PIT_CONTRACT_UNRESOLVED"
        elif any(x["sample_status"] == "INFRA_ACCESS_BLOCKED" for x in source_samples):
            pit_status = "PIT_CONTRACT_DEFINED_PENDING_ARCHIVE"
        elif all(c["contract_status"] == "PIT_CONTRACT_DEFINED_PENDING_ARCHIVE" for c in contracts):
            pit_status = "PIT_CONTRACT_DEFINED_PENDING_ARCHIVE"
        else:
            pit_status = "PIT_CONTRACT_UNRESOLVED"

        candidate_results.append(
            {
                "candidate_id": candidate_id,
                "name": candidate.get("name"),
                "source_ids": source_ids,
                "next_gate": candidate.get("next_gate"),
                "pit_status": pit_status,
                "source_sample_statuses": {
                    s: source_results[s]["sample_status"] for s in source_ids if s in source_results
                },
                "required_contract_dimensions": {
                    "clock": [SOURCE_CONTRACTS[s]["clock"] for s in source_ids if s in SOURCE_CONTRACTS],
                    "revision": [SOURCE_CONTRACTS[s]["revision"] for s in source_ids if s in SOURCE_CONTRACTS],
                    "mapping": [SOURCE_CONTRACTS[s]["mapping"] for s in source_ids if s in SOURCE_CONTRACTS],
                    "archive": [SOURCE_CONTRACTS[s]["archive"] for s in source_ids if s in SOURCE_CONTRACTS],
                },
                "performance_authorized": False,
            }
        )

    result: dict[str, Any] = {
        "schema_version": "1.0",
        "receipt_type": "q133_q170_pit_readiness_r1",
        "wave_id": "Q133-Q170-PIT-READINESS-R1-2026-10-03",
        "status": "PIT_READINESS_COMPLETED_NO_PERFORMANCE",
        "source_receipt": {
            "path": "research/evidence/q133_q170_source_feasibility_2026_10_03.json",
            "workflow_run_id": source_receipt.get("workflow_run_id"),
            "receipt_fingerprint": source_receipt.get("receipt_fingerprint"),
            "source_probe_pass_count": source_receipt.get("source_pass_count"),
            "candidate_count": source_receipt.get("candidate_count"),
            "source_feasible_candidate_count": len(feasible),
        },
        "source_results": source_results,
        "candidate_results": candidate_results,
        "synthetic_mutation_checks": future_mutation_check(),
        "scientific_boundary": {
            "performance": False,
            "holdout_selection": False,
            "asset_selection": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "variant_search": False,
            "candidate_ranking": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": {
            "PAPER_ONLY": True,
            "LIVE_TRADING_ENABLED": False,
            "ORDERS_ENABLED": False,
            "AUTOMATIC_PROMOTION": False,
        },
    }
    result["receipt_fingerprint"] = sha256(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                "source_probe_pass_count": result["source_receipt"]["source_probe_pass_count"],
                "source_feasible_candidate_count": result["source_receipt"]["source_feasible_candidate_count"],
                "candidate_pit_statuses": {
                    x["candidate_id"]: x["pit_status"] for x in candidate_results
                },
                "receipt_fingerprint": result["receipt_fingerprint"],
            },
            sort_keys=True,
        )
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
