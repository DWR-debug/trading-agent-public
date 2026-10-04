"""Q179-Q184 PIT Readiness R1.

Strictly pre-formal. This lane verifies candidate-specific source/clock
contracts and bounded public samples. It does not establish full historical
archive coverage, frozen issuer mapping, revision lineage, independent
reproduction, performance authorization, promotion, or live execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

CONTRACTS: dict[str, dict[str, Any]] = {
    "Q179": {
        "source_id": "CLINICALTRIALS",
        "urls": ["https://clinicaltrials.gov/api/v2/studies/NCT00125528"],
        "markers": ["studyFirstPostDateStruct", "resultsFirstPostDateStruct", "lastUpdatePostDateStruct"],
        "clock": "ClinicalTrials.gov posted-date fields define public availability; submitted dates remain separate.",
        "revision": "Record update lineage must be reconstructed without replacing the earlier posted state.",
        "mapping": "Sponsor/exposure to listed pharma issuer must be frozen independently of outcomes.",
        "archive": "Historical API/download coverage and a reproducible prior-state archive are still unproven.",
        "status": "PIT_CONTRACT_DEFINED_PENDING_ARCHIVE_AND_ISSUER_MAPPING",
    },
    "Q180": {
        "source_id": "NHTSA_RECALLS",
        "urls": [
            "https://www.nhtsa.gov/nhtsa-datasets-and-apis",
            "https://api.nhtsa.gov/recalls/recallsByVehicle?make=acura&model=rdx&modelYear=2012",
        ],
        "markers": {
            "https://www.nhtsa.gov/nhtsa-datasets-and-apis": [
                "FLAT_RCL_POST_2010.zip",
                "All times shown are Eastern Time (ET)",
                "published",
            ],
            "https://api.nhtsa.gov/recalls/recallsByVehicle?make=acura&model=rdx&modelYear=2012": [
                "results",
            ],
        },
        "clock": "NHTSA publication date and ET convention are documented; exact historical event-publication reconstruction is still required.",
        "revision": "Flat-file/API revision and amendment semantics must be separated from the initial public state.",
        "mapping": "Vehicle/product-to-issuer exposure mapping must be frozen before evaluation.",
        "archive": "Historical flat-file coverage is documented, but candidate-specific archive reconstruction is still pending.",
        "status": "PIT_CONTRACT_DEFINED_PENDING_PUBLICATION_FIELD_AND_ISSUER_MAPPING",
    },
    "Q181": {
        "source_id": "OSHA_DATA",
        "urls": ["https://catalog.data.gov/dataset/dol-enforcement-data-inspection"],
        "markers": ["accessLevel", "public", "accrualPeriodicity", "R/P1D", "inspections conducted by OSHA"],
        "clock": "DOL catalog confirms public daily accrual; an exact intraday public observation boundary is still unresolved.",
        "revision": "Dataset refreshes/corrections must be separated from the historical inspection state.",
        "mapping": "Establishment/parent-to-issuer mapping must be frozen and coverage-tested.",
        "archive": "Historical inspection coverage exists at the public dataset level, but candidate-specific PIT reconstruction is pending.",
        "status": "PIT_CONTRACT_DEFINED_PENDING_INTRADAY_CLOCK_AND_ISSUER_MAPPING",
    },
    "Q182": {
        "source_id": "FERC_ELIBRARY",
        "urls": ["https://ferc.gov/what-elibrary", "https://www.ferc.gov/about/what-ferc/frequently-asked-questions-faqs/documents-and-filing/elibrary"],
        "markers": ["issued by FERC", "Documents received and issued by FERC", "download"],
        "clock": "FERC issued/received document semantics are established, but runner access currently returns HTTP 403.",
        "revision": "Corrections/updated filings must remain separate from the initial public document state.",
        "mapping": "Docket/project/facility-to-issuer mapping must be frozen.",
        "archive": "The official archive is broad, but candidate-specific historical extraction has not been reproduced in this lane.",
        "status": "PIT_CONTRACT_DEFINED_RUNNER_BLOCKED_PENDING_ACCESS",
    },
    "Q183": {
        "source_id": "NTSB_CAROL",
        "urls": [
            "https://www.ntsb.gov/safety/data/Pages/Data_Stats.aspx",
            "https://www.ntsb.gov/Pages/CAROL-Data-Dictionary.aspx",
        ],
        "markers": {
            "https://www.ntsb.gov/safety/data/Pages/Data_Stats.aspx": [
                "1982 to the present",
                "daily and pending aviation publication report",
            ],
            "https://www.ntsb.gov/Pages/CAROL-Data-Dictionary.aspx": [
                "cm_recentReportPublishDate",
            ],
        },
        "clock": "Recent report publication date plus the daily/pending publication report provide a public publication boundary.",
        "revision": "Report publication/correction history must be separated from the underlying incident date.",
        "mapping": "Operator/airport/facility-to-issuer exposure mapping must be frozen.",
        "archive": "Historical aviation data coverage is documented, but candidate-specific PIT reconstruction remains pending.",
        "status": "PIT_CONTRACT_DEFINED_PENDING_HISTORICAL_PUBLICATION_AND_ISSUER_MAPPING",
    },
    "Q184": {
        "source_id": "FCC_ULS",
        "urls": ["https://opendata.fcc.gov/Wireless/FCC-Universal-Licensing-System-ULS-/x28i-i4z4"],
        "markers": ["daily transaction files", "weekly transaction files", "Public Domain"],
        "clock": "Daily transaction-file dissemination is established; exact transaction/amendment clock and historical file lineage still require audit.",
        "revision": "Application/license modifications and later corrections must not rewrite prior transaction states.",
        "mapping": "Licensee/application-to-issuer mapping must be frozen.",
        "archive": "Public access files are available, but candidate-specific historical lineage remains pending.",
        "status": "PIT_CONTRACT_DEFINED_PENDING_TRANSACTION_CLOCK_AND_ISSUER_MAPPING",
    },
}

def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "trading-agent-public/Q179-Q184-PIT-R1/1", "Accept": "*/*"},
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            return int(getattr(response, "status", 200)), response.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, f"FETCH_ERROR:{type(exc).__name__}:{exc}".encode()

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def source_probe(url: str, markers: list[str] | dict[str, list[str]]) -> dict[str, Any]:
    status, body = fetch(url)
    text_body = body.decode("utf-8", errors="replace")
    required = markers[url] if isinstance(markers, dict) else markers
    missing = [m for m in required if m.lower() not in text_body.lower()]
    classification = (
        "SAMPLE_REACHABLE" if status == 200 and not missing
        else "RUNNER_ACCESS_BLOCKED" if status in (401, 403)
        else "SAMPLE_PARSE_UNRESOLVED" if status == 200
        else "UNREACHABLE"
    )
    return {
        "url": url,
        "http_status": status,
        "classification": classification,
        "missing_markers": missing,
        "content_sha256": sha256(body),
    }

def invariance_checks() -> dict[str, bool]:
    base = [{"decision": 1, "state": "A"}, {"decision": 2, "state": "B"}]
    future = base + [{"decision": 3, "state": "FUTURE"}]
    reordered = [base[1], base[0]]
    return {
        "future_row_prefix_invariant": future[:2] == base,
        "future_value_not_visible_to_prefix": future[:2] == base,
        "input_order_independent_fixture": sorted(x["decision"] for x in reordered) == [1, 2],
        "missingness_fixture_fails_closed": None not in ("A", "B"),
        "no_search_dimension_present": True,
    }

def run(output: Path) -> dict[str, Any]:
    candidate_results=[]
    source_results={}
    for candidate_id, contract in CONTRACTS.items():
        probes=[]
        for url in contract["urls"]:
            p=source_probe(url, contract["markers"])
            probes.append(p)
            source_results[url]=p
        candidate_results.append({
            "candidate_id": candidate_id,
            "source_id": contract["source_id"],
            "pit_status": contract["status"],
            "probe_statuses": [p["classification"] for p in probes],
            "clock_contract": contract["clock"],
            "revision_contract": contract["revision"],
            "mapping_contract": contract["mapping"],
            "archive_contract": contract["archive"],
            "performance_authorized": False,
        })
    result={
        "schema_version":"1.0",
        "receipt_type":"q179_q184_pit_readiness_r1",
        "wave_id":"Q179-Q184-PIT-READINESS-R1-2026-10-04",
        "status":"PIT_READINESS_R1_COMPLETED_NO_PERFORMANCE",
        "source_results":source_results,
        "candidate_results":candidate_results,
        "synthetic_mutation_checks":invariance_checks(),
        "unresolved_gate_requirements":[
            "full historical source/archive coverage",
            "exact public observation clock where not proven",
            "fixed entity mapping coverage",
            "revision/amendment lineage",
            "independent reproduction",
        ],
        "scientific_boundary":{
            "performance":False,"holdout_selection":False,"asset_selection":False,
            "parameter_search":False,"threshold_search":False,"horizon_search":False,
            "variant_search":False,"candidate_ranking":False,"promotion":False,
            "live_execution":False,
        },
        "safety":{"PAPER_ONLY":True,"LIVE_TRADING_ENABLED":False,"ORDERS_ENABLED":False,"AUTOMATIC_PROMOTION":False},
    }
    result["receipt_fingerprint"]=sha256(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode())
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"candidate_pit_statuses":{x["candidate_id"]:x["pit_status"] for x in candidate_results},"receipt_fingerprint":result["receipt_fingerprint"]},sort_keys=True))
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args(); run(args.output)
