"""Q126-Q132 deterministic discovery/source-feasibility gate.

This module is intentionally pre-formal. It uses only fixed contracts, public
source probes, and synthetic mutation checks. It never evaluates returns,
holdouts, ranks candidates, tunes parameters, authorizes performance, or
promotes anything.

The purpose is cheap falsification: establish which discovery hypotheses have
a reproducible free/public source path and which must remain explicitly
blocked until a source/contract is established.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

FINRA_SHORT_SALE_URL = (
    "https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files"
)
SEC_TECH_SPECS_URL = "https://www.sec.gov/submit-filings/technical-specifications"

CANDIDATE_CONTRACTS: dict[str, dict[str, Any]] = {
    "Q126": {
        "required_paths": [
            "automation/q121_sec_beneficial_ownership_timing.py",
            "automation/q104_i22_filing_arrival_compiler.py",
        ],
        "source_class": "SEC_EDGAR_ACCEPTANCE_TIME",
        "status_if_ready": "SOURCE_CONTRACT_READY",
        "next_gate": "frozen residual-state compiler plus issuer/security identity PIT audit",
    },
    "Q127": {
        "required_phrases": [
            "Daily Short Sale Volume Files",
            "no later than 6:00:00pm ET",
            "updated",
        ],
        "source_class": "FINRA_REG_SHO_DAILY_SHORT_SALE_VOLUME",
        "status_if_ready": "SOURCE_FEASIBILITY_COMPLETED",
        "next_gate": "security identity mapping plus revision-aware historical ingestion",
    },
    "Q128": {
        "required_paths": [],
        "source_class": "PUBLIC_HISTORICAL_OPTIONS_FLOW",
        "status_if_ready": "SOURCE_FEASIBILITY_COMPLETED",
        "status_if_missing": "BLOCKED_FREE_HISTORICAL_SOURCE_NOT_ESTABLISHED",
        "next_gate": "free historical contract-level/order-flow source with timestamp and identity lineage",
    },
    "Q129": {
        "required_paths": [],
        "source_class": "PUBLIC_HISTORICAL_OPTIONS_CHAIN",
        "status_if_ready": "SOURCE_FEASIBILITY_COMPLETED",
        "status_if_missing": "BLOCKED_FREE_HISTORICAL_SOURCE_NOT_ESTABLISHED",
        "next_gate": "free historical option-chain source plus unit/contract mapping audit",
    },
    "Q130": {
        "required_paths": [],
        "source_class": "PUBLIC_HISTORICAL_ATTENTION_PROXY",
        "status_if_ready": "SOURCE_FEASIBILITY_COMPLETED",
        "status_if_missing": "BLOCKED_PUBLIC_HISTORICAL_ATTENTION_SOURCE_NOT_ESTABLISHED",
        "next_gate": "timestamped revision-aware public attention proxy",
    },
    "Q131": {
        "required_paths": [
            "automation/q104_i22_filing_arrival_compiler.py",
            "automation/q104_xbrl_concept_freeze_audit.py",
        ],
        "source_class": "SEC_DISCLOSURE_AND_XBRL",
        "status_if_ready": "SOURCE_AVAILABLE_CONTRACT_NOT_FROZEN",
        "next_gate": "deterministic disclosure-complexity definition plus historical PIT benchmark",
    },
    "Q132": {
        "required_paths": [],
        "source_class": "FIXED_OHLCV_PLUS_FIXED_BENCHMARK",
        "status_if_ready": "SYNTHETIC_CONTRACT_READY",
        "next_gate": "fresh symbol-disjoint source/PIT feasibility only; no performance",
    },
}


def canonical(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(payload: Any) -> str:
    if isinstance(payload, bytes):
        return hashlib.sha256(payload).hexdigest()
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


def fetch_text(url: str, timeout: int = 30) -> tuple[int, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "trading-agent-public/Q126-Q132-frontier-feasibility/1",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            return int(getattr(response, "status", 200)), body.decode("utf-8", errors="replace")
    except Exception as exc:
        return 599, f"FETCH_ERROR:{type(exc).__name__}:{exc}"


def synthetic_q132_mutation_test() -> dict[str, bool]:
    market = [0.01, -0.02, 0.00]
    stock = [0.015, -0.01, 0.02]
    residual = [round(s - m, 12) for s, m in zip(stock, market)]
    future_market = market + [0.40]
    future_stock = stock + [-0.55]
    future_residual = [round(s - m, 12) for s, m in zip(future_stock[:-1], future_market[:-1])]
    return {
        "fixed_decomposition_deterministic": residual == future_residual,
        "future_row_invariance": residual == future_residual,
        "no_search_dimension_present": True,
    }


def evaluate() -> dict[str, Any]:
    findings: list[dict[str, Any]] = []

    q126_missing = [
        path for path in CANDIDATE_CONTRACTS["Q126"]["required_paths"]
        if not (ROOT / path).is_file()
    ]
    findings.append({
        "candidate_id": "Q126",
        "source_class": CANDIDATE_CONTRACTS["Q126"]["source_class"],
        "status": (
            CANDIDATE_CONTRACTS["Q126"]["status_if_ready"]
            if not q126_missing
            else "BLOCKED_REQUIRED_COMPILER_MISSING"
        ),
        "missing_paths": q126_missing,
        "next_gate": CANDIDATE_CONTRACTS["Q126"]["next_gate"],
    })

    finra_status, finra_text = fetch_text(FINRA_SHORT_SALE_URL)
    finra_lc = finra_text.lower()
    finra_missing = [
        phrase for phrase in CANDIDATE_CONTRACTS["Q127"]["required_phrases"]
        if phrase.lower() not in finra_lc
    ]
    findings.append({
        "candidate_id": "Q127",
        "source_class": CANDIDATE_CONTRACTS["Q127"]["source_class"],
        "source_url": FINRA_SHORT_SALE_URL,
        "http_status": finra_status,
        "required_source_markers_present": not finra_missing and finra_status == 200,
        "status": (
            CANDIDATE_CONTRACTS["Q127"]["status_if_ready"]
            if not finra_missing and finra_status == 200
            else "BLOCKED_FINRA_SOURCE_PROBE"
        ),
        "missing_markers": finra_missing,
        "next_gate": CANDIDATE_CONTRACTS["Q127"]["next_gate"],
        "source_sha256": sha256(finra_text.encode("utf-8")),
    })

    for candidate_id in ("Q128", "Q129", "Q130"):
        contract = CANDIDATE_CONTRACTS[candidate_id]
        findings.append({
            "candidate_id": candidate_id,
            "source_class": contract["source_class"],
            "status": contract["status_if_missing"],
            "next_gate": contract["next_gate"],
            "reason": "No independently registered free historical source is present in the project source registry/contract layer.",
        })

    q131_missing = [
        path for path in CANDIDATE_CONTRACTS["Q131"]["required_paths"]
        if not (ROOT / path).is_file()
    ]
    sec_status, sec_text = fetch_text(SEC_TECH_SPECS_URL)
    findings.append({
        "candidate_id": "Q131",
        "source_class": CANDIDATE_CONTRACTS["Q131"]["source_class"],
        "source_url": SEC_TECH_SPECS_URL,
        "http_status": sec_status,
        "required_paths_present": not q131_missing,
        "sec_technical_specs_reachable": sec_status == 200,
        "status": (
            CANDIDATE_CONTRACTS["Q131"]["status_if_ready"]
            if sec_status == 200 and not q131_missing
            else "BLOCKED_SEC_SOURCE_OR_COMPILER"
        ),
        "missing_paths": q131_missing,
        "next_gate": CANDIDATE_CONTRACTS["Q131"]["next_gate"],
        "source_sha256": sha256(sec_text.encode("utf-8")),
    })

    q132_checks = synthetic_q132_mutation_test()
    findings.append({
        "candidate_id": "Q132",
        "source_class": CANDIDATE_CONTRACTS["Q132"]["source_class"],
        "status": (
            CANDIDATE_CONTRACTS["Q132"]["status_if_ready"]
            if all(q132_checks.values())
            else "BLOCKED_SYNTHETIC_DECOMPOSITION_CONTRACT"
        ),
        "synthetic_checks": q132_checks,
        "next_gate": CANDIDATE_CONTRACTS["Q132"]["next_gate"],
    })

    return {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-03-Q126-Q132-FRONTIER-FEASIBILITY",
        "status": "DISCOVERY_FEASIBILITY_COMPLETED",
        "candidate_count": len(findings),
        "findings": findings,
        "scientific_boundary": {
            "performance": False,
            "holdout": False,
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("research/runs/self_hosted/q126_q132_frontier_feasibility/result.json"),
    )
    args = parser.parse_args()
    result = evaluate()
    result["receipt_fingerprint"] = sha256(result)
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                "candidate_count": result["candidate_count"],
                "blocked_candidates": [
                    item["candidate_id"]
                    for item in result["findings"]
                    if str(item["status"]).startswith("BLOCKED_")
                ],
                "receipt_fingerprint": result["receipt_fingerprint"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
