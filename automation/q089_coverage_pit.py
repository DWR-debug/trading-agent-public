"""Q089 clean fresh coverage, snapshot, PIT and preregistration harness."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from automation.fixed_window_candidate_discovery import run_discovery
from automation.q069_candidate_bank import CANDIDATES, candidate_targets_at
from data.canonical_snapshot import load_frozen_snapshot, snapshot_from_preregistration

ROOT = Path(__file__).resolve().parents[1]
COVERAGE_ID = "T-2026-09-28-089-COVERAGE"
PIT_ID = "T-2026-09-28-089-PIT"
INPUT_ID = "T-2026-09-28-089-INPUT-FREEZE"
PERFORMANCE_ID = "T-2026-09-28-089-PERFORMANCE"
UNIVERSE = "validation_2026_09_28_q089_clean_q069"
REQUESTED, RAW, TARGET = 5000, 5000, 3500
RESEARCH, HOLDOUT, N = 2798, 700, 3500

# Fixed source-order reserve pool. Global prior-research exclusion is applied
# by fixed_window_candidate_discovery before any coverage selection.
CANDIDATE_POOL = (
    "AEE","AEP","AES","AFL","AIZ","ATO","AVY","BBY","BDX","BEN","BK","BKH",
    "BMY","CAG","CAH","CHD","CHRW","CINF","CMA","CMS","CNP","COF","CPB","CPT",
    "CTRA","CTSH","CUBE","D","DHI","DOV","DPZ","DRI","DTE","DUK","DXC","ECL",
    "ED","EFX","EIX","EL","EMN","EMR","EPAM","ETN","ETR","EVRG","EXPD","EXR",
    "FAST","FBHS","FCX","FE","FITB","FMC","FRT","FTV","GPC","HAS","HBAN","HIG",
    "HOLX","HSIC","HST","IFF","IP","IRM","ITW","J","JBHT","JCI","KEY","KHC",
    "KIM","KMB","KMI","L","LDOS","LEN","LH","LNT","LUV","LVS","MAS","MCD","MDT",
    "MET","MKC","MLM","MOH","MOS","MRO","MSI","MTB","NDSN","NEM","NKE","NLOK",
    "NOC","NRG","NTRS","NUE","NVR","OMC","OKE","ORLY","OTIS","OXY","PAYX","PFG",
    "PHM","PKG","PNC","PNW","PPG","PPL","PRGO","PVH","RSG","RTX","ROL","ROST",
    "RRC","SJM","SLB","STT","STX","SWK","SWKS","SYY","TAP","TFX","TGT",
    "TJX","TMO","TPR","TSCO","TSN","TT","TROW","TRV","TTEK","TXT","UDR","UHS",
    "USB","VLO","VMC","VRSK","VTR","WEC","WELL","WMB","WRB","WST","WY","XEL"
)
SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


def _canonical(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def _fp(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _coverage_paths() -> tuple[Path, Path]:
    root = ROOT / "research" / "runs" / "q089_coverage" / COVERAGE_ID
    return root / "snapshot_manifest.json", root


def coverage() -> dict:
    discovery = run_discovery(
        output=ROOT / "research" / "runs" / "q089_discovery" / "discovery.json",
        symbol_limit=96,
        workers=8,
        candidate_pool=CANDIDATE_POOL,
    )
    selected = tuple(discovery["selected_coverage_batch"][:8])
    if len(selected) != 8:
        raise RuntimeError("Q089 did not obtain eight coverage-valid disjoint symbols")

    spec = {
        "trial_id": COVERAGE_ID,
        "universe": UNIVERSE,
        "symbols": list(selected),
        "interval": "1d",
        "requested_candles": REQUESTED,
        "raw_fetch_candles": RAW,
        "target_common_candles": TARGET,
        "study_window": {"start": "2011-01-01", "end": "2025-09-24"},
        "governance": {
            "coverage_only": True,
            "performance_evaluation": False,
            "selection_used": False,
            "asset_selection_by_performance": False,
        },
        "safety": SAFETY,
    }
    snap = snapshot_from_preregistration(
        spec, output_root=ROOT / "research" / "runs" / "q089_coverage"
    )
    if snap["status"] != "COVERAGE_PASSED":
        raise RuntimeError("Q089 coverage failed")

    freeze = {
        "schema_version": "1.0",
        "trial_id": COVERAGE_ID,
        "status": "COVERAGE_PASSED",
        "universe": UNIVERSE,
        "symbols": list(selected),
        "requested_candles": REQUESTED,
        "raw_fetch_candles": RAW,
        "target_common_candles": TARGET,
        "study_window": spec["study_window"],
        "source_discovery_fingerprint": discovery["fingerprint"],
        "snapshot_fingerprint": snap["snapshot_fingerprint"],
        "selection_used": False,
        "holdout_selection_used": False,
        "performance_evaluation": False,
        "safety": SAFETY,
    }

    evidence = ROOT / "research" / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "q089_coverage_result.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "trial_id": COVERAGE_ID,
                "research_family": "q089_clean_fresh_q069_validation",
                "status": "COVERAGE_PASSED",
                "symbols": list(selected),
                "universe": UNIVERSE,
                "common_calendar_count": snap["coverage"]["common_calendar_count"],
                "snapshot_fingerprint": snap["snapshot_fingerprint"],
                "selection_used": False,
                "performance_evaluation": False,
                "holdout_evaluation": False,
                "source_discovery": discovery,
                "safety": SAFETY,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    coverage_path = evidence / "q089_coverage_result.json"
    coverage_data = json.loads(coverage_path.read_text(encoding="utf-8"))
    coverage_data["result_fingerprint"] = _fp(coverage_data)
    coverage_path.write_text(
        json.dumps(coverage_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    (evidence / "q089_asset_freeze.json").write_text(
        json.dumps(freeze, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print("Q089_COVERAGE_PASS", ",".join(selected))
    print("Q089_SNAPSHOT_FP", snap["snapshot_fingerprint"])
    print("Q089_INPUT_BUNDLE_FP", input_freeze["bundle_fingerprint"])
    return {
        "coverage": freeze,
        "selected": selected,
    }


def _mutate(assets, index: int, mode: str):
    out = {s: list(bars) for s, bars in assets.items()}
    for bars in out.values():
        start = index + 1
        stop = len(bars) if mode == "future" else min(len(bars), index + 2)
        for i in range(start, stop):
            bar = bars[i]
            bars[i] = type(bar)(
                timestamp=bar.timestamp,
                open=bar.open * 9.0,
                high=bar.high * 9.0,
                low=bar.low * 0.1,
                close=bar.close * 0.1,
                volume=bar.volume * 10.0,
            )
    return {s: tuple(b) for s, b in out.items()}


def pit() -> dict:
    freeze = json.loads((ROOT / "research" / "evidence" / "q089_asset_freeze.json").read_text())
    if freeze.get("trial_id") != COVERAGE_ID or freeze.get("status") != "COVERAGE_PASSED":
        raise ValueError("Q089 coverage receipt invalid")
    manifest, _ = _coverage_paths()
    assets = load_frozen_snapshot(manifest)
    symbols = tuple(freeze["symbols"])
    if tuple(assets) != symbols:
        raise ValueError("Q089 snapshot symbol order mismatch")
    if any(len(assets[s]) != N for s in symbols):
        raise ValueError("Q089 snapshot geometry mismatch")

    checks = []
    for index in range(757, N - 1, 113):
        original = candidate_targets_at(assets, index, symbols=symbols)
        for mode in ("future", "next"):
            changed = candidate_targets_at(
                _mutate(assets, index, mode), index, symbols=symbols
            )
            if changed != original:
                raise AssertionError(f"Q089 PIT mutation changed candidate targets at {index}/{mode}")
            for name in CANDIDATES:
                weights = original[name]
                if sum(weights.values()) > 1.0 + 1e-12:
                    raise AssertionError(f"Q089 gross cap breached by {name}")
            checks.append({"index": index, "mode": mode})

    result = {
        "schema_version": "1.0",
        "trial_id": PIT_ID,
        "status": "PIT_PASSED",
        "coverage_trial_id": COVERAGE_ID,
        "input_bundle_trial_id": INPUT_ID,
        "symbols": list(symbols),
        "candidates": list(CANDIDATES),
        "checked_decision_points": len(checks),
        "future_mutation_checks_passed": True,
        "next_session_mutation_checks_passed": True,
        "performance_evaluation": False,
        "oos_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "holdout_used_for_selection": False,
        "performance_trial_authorized": False,
        "checks_fingerprint": _fp(checks),
        "asset_freeze_fingerprint": _fp(freeze),
        "safety": SAFETY,
    }
    result["result_fingerprint"] = _fp(result)
    path = ROOT / "research" / "evidence" / "q089_pit_result.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Q089_PIT_PASS", len(checks))
    print("Q089_PIT_FP", result["result_fingerprint"])
    return result


def preregister() -> dict:
    coverage = json.loads((ROOT / "research" / "evidence" / "q089_coverage_result.json").read_text())
    pit_result = json.loads((ROOT / "research" / "evidence" / "q089_pit_result.json").read_text())
    input_freeze = json.loads((ROOT / "research" / "evidence" / "q089_input_freeze_result.json").read_text())
    freeze = json.loads((ROOT / "research" / "evidence" / "q089_asset_freeze.json").read_text())
    if pit_result.get("trial_id") != PIT_ID or pit_result.get("status") != "PIT_PASSED":
        raise ValueError("Q089 PIT receipt is not complete")
    prereg = {
        "schema_version": "1.0",
        "trial_id": PERFORMANCE_ID,
        "research_family": "q089_clean_fresh_q069_validation",
        "status": "PREREGISTERED_PERFORMANCE",
        "universe": UNIVERSE,
        "symbols": list(freeze["symbols"]),
        "requested_candles": REQUESTED,
        "target_common_candles": TARGET,
        "research_periods": RESEARCH,
        "holdout_periods": HOLDOUT,
        "initial_capital_eur": 2000,
        "candidate_source": "Q069 fixed candidate bank",
        "candidates": list(CANDIDATES),
        "data_contract": {
            "coverage_trial_id": COVERAGE_ID,
            "coverage_result_fingerprint": coverage["result_fingerprint"],
            "snapshot_fingerprint": coverage["snapshot_fingerprint"],
            "pit_trial_id": PIT_ID,
            "pit_result_fingerprint": pit_result["result_fingerprint"],
            "input_bundle_trial_id": INPUT_ID,
            "input_bundle_fingerprint": input_freeze["bundle_fingerprint"],
        },
        "identity_contract": {
            "trial_id": PERFORMANCE_ID,
            "expected_trial_code": "089",
            "mode": "fresh_trial",
            "reused_source_trials": [],
            "required_receipts": [
                {
                    "role": "coverage",
                    "path": "research/evidence/q089_coverage_result.json",
                    "trial_id": COVERAGE_ID,
                    "fingerprint_key": "snapshot_fingerprint",
                    "expected_data_contract_key": "coverage_result_fingerprint",
                },
                {
                    "role": "pit",
                    "path": "research/evidence/q089_pit_result.json",
                    "trial_id": PIT_ID,
                    "fingerprint_key": "result_fingerprint",
                    "expected_data_contract_key": "pit_result_fingerprint",
                },
                {
                    "role": "input_bundle",
                    "path": "research/evidence/q089_input_freeze_result.json",
                    "trial_id": INPUT_ID,
                    "fingerprint_key": "bundle_fingerprint",
                    "expected_data_contract_key": "input_bundle_fingerprint",
                },
            ],
        },
        "governance_contract_version": 2,
        "governance": {
            "performance_trial_authorized": False,
            "selection": False,
            "holdout_used_for_selection": False,
            "parameter_search": False,
            "threshold_search": False,
            "asset_search": False,
            "horizon_search": False,
            "variant_search": False,
            "family_ranking": False,
            "promotion_decision": False,
            "automatic_promotion": False,
        },
        "source_discovery_fingerprint": coverage["source_discovery"]["fingerprint"],
        "asset_freeze_fingerprint": _fp(freeze),
        "source_scope": {
            "candidate_definitions": "automation/q069_candidate_bank.py",
            "candidate_definitions_frozen": True,
            "fresh_symbol_disjointness": True,
            "global_prior_research_exclusion": True,
        },
        "safety": SAFETY,
    }
    prereg["source_contract"] = {
        "performance_runner_path": "automation/q089_performance.py",
        "performance_runner_sha256": hashlib.sha256(
            (ROOT / "automation/q089_performance.py").read_bytes()
        ).hexdigest(),
        "candidate_bank_path": "automation/q069_candidate_bank.py",
        "candidate_bank_sha256": hashlib.sha256(
            (ROOT / "automation/q069_candidate_bank.py").read_bytes()
        ).hexdigest(),
        "cost_contract_path": "execution/cost_contract.py",
        "cost_contract_sha256": hashlib.sha256(
            (ROOT / "execution/cost_contract.py").read_bytes()
        ).hexdigest(),
        "settings_path": "config/settings.py",
        "settings_sha256": hashlib.sha256(
            (ROOT / "config/settings.py").read_bytes()
        ).hexdigest(),
    }
    path = ROOT / "research" / "preregistrations" / "q089_performance_2026_09_28.json"
    path.write_text(json.dumps(prereg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    registry_path = ROOT / "research" / "governance" / "active_research_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for entry in registry.get("active_trials", []):
        if entry.get("code") == "089":
            entry.update(
                {
                    "trial_id": PERFORMANCE_ID,
                    "class": "fresh_validation",
                    "state": "PREREGISTERED_WAITING_PREFLIGHT",
                    "issue_number": 589,
                    "preregistration_path": "research/preregistrations/q089_performance_2026_09_28.json",
                    "performance_authorization_allowed": False,
                }
            )
    registry_path.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("Q089_PREREGISTERED", PERFORMANCE_ID)
    return prereg


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("coverage", "pit", "preregister"))
    args = parser.parse_args()
    if args.mode == "coverage":
        coverage()
    elif args.mode == "pit":
        pit()
    else:
        preregister()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
