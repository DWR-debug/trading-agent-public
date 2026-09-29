"""Q091 coverage and PIT preparation. No performance is executed."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
from pathlib import Path

from data.canonical_snapshot import load_frozen_snapshot, snapshot_from_preregistration
from data.yahoo_loader import load_yahoo_history
from automation.fixed_window_candidate_discovery import run_discovery
from portfolio.q091_fixed_ensemble import q091_targets_at

ROOT = Path(__file__).resolve().parents[1]
TRIAL_ID = "T-2026-09-29-091"
COVERAGE_ID = "T-2026-09-29-091-COVERAGE"
PIT_ID = "T-2026-09-29-091-PIT"
REQUESTED = 5000
TARGET = 3500
SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}
CANDIDATE_POOL = (
    "AAPL","ABT","ACGL","ACN","ADBE","ADI","AFL","AMAT","AMD","AMGN","AMT",
    "APA","APD","APH","AVGO","AZO","BAC","BALL","BBY","BLK","BRO","BSX",
    "BXP","CAT","CB","CDW","CE","CF","CI","CME","CMCSA","COST","CPRT",
    "CSCO","CSX","CTSH","CVS","DE","DG","DHR","DIS","DOW","EA","EBAY",
    "EIX","ELV","EMR","ENPH","EOG","EPAM","EQIX","ETN","EXC","FANG","FAST",
    "FDX","FL","FOX","FOXA","GD","GE","GILD","GIS","GLW","GM","GPN","GS",
    "HAL","HD","HES","HLT","HON","HPQ","HRL","HUM","IBM","ICE","INTC","INVH",
    "IPG","ISRG","JNJ","JPM","KDP","KEYS","KO","LOW","MA","MAR","MCHP",
)


def _fp(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _resilient_loader(symbol, interval, requested_candles, **kwargs):
    last_error = None
    for attempt in range(3):
        try:
            return load_yahoo_history(symbol, interval, requested_candles, **kwargs)
        except Exception as exc:
            last_error = exc
            print(f"Q091_SOURCE_RETRY symbol={symbol} attempt={attempt + 1} error={exc}")
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Q091 source acquisition failed after 3 attempts for {symbol}: {last_error}")


def coverage() -> dict:
    prereg = json.loads(
        (ROOT / "research/preregistrations/q091_fixed_portfolio_architecture_2026_09_29.json").read_text(
            encoding="utf-8"
        )
    )
    if prereg["trial_id"] != TRIAL_ID or prereg["status"] != "PREREGISTERED_DESIGN_ONLY":
        raise RuntimeError("Q091 preregistration identity/status mismatch")

    discovery_path = ROOT / "research/runs/q091_coverage" / COVERAGE_ID / "discovery.json"
    discovery = run_discovery(
        output=discovery_path,
        symbol_limit=len(CANDIDATE_POOL),
        workers=8,
        candidate_pool=CANDIDATE_POOL,
    )
    selected = tuple(discovery["selected_coverage_batch"][:8])
    if len(selected) != 8:
        raise RuntimeError("Q091 did not obtain eight coverage-valid fresh symbols")

    spec = {
        "trial_id": COVERAGE_ID,
        "universe": "validation_2026_09_29_q091_fixed_portfolio_architecture",
        "symbols": list(selected),
        "interval": "1d",
        "requested_candles": REQUESTED,
        "raw_fetch_candles": REQUESTED,
        "target_common_candles": TARGET,
        "study_window": {"start": "2011-01-01", "end": "2025-09-24"},
    }
    snap = snapshot_from_preregistration(
        spec,
        output_root=ROOT / "research/runs/q091_coverage",
        loader=_resilient_loader,
    )
    if snap["status"] != "COVERAGE_PASSED":
        raise RuntimeError(
            "Q091 coverage failed: "
            + json.dumps(snap.get("coverage", {}).get("errors", {}), sort_keys=True)
        )

    evidence = ROOT / "research/evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    coverage_receipt = {
        "schema_version": "1.0",
        "trial_id": COVERAGE_ID,
        "research_family": "fixed_portfolio_architecture_after_q090_diagnosis",
        "status": "COVERAGE_PASSED",
        "symbols": list(selected),
        "universe": spec["universe"],
        "common_calendar_count": snap["coverage"]["common_calendar_count"],
        "snapshot_fingerprint": snap["snapshot_fingerprint"],
        "source_discovery_fingerprint": discovery["fingerprint"],
        "selection_used": False,
        "performance_evaluation": False,
        "holdout_evaluation": False,
        "safety": SAFETY,
    }
    coverage_receipt["result_fingerprint"] = _fp(coverage_receipt)
    (evidence / "q091_coverage_result.json").write_text(
        json.dumps(coverage_receipt, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    freeze = {
        "schema_version": "1.0",
        "trial_id": COVERAGE_ID,
        "status": "COVERAGE_PASSED",
        "universe": spec["universe"],
        "symbols": list(selected),
        "requested_candles": REQUESTED,
        "target_common_candles": TARGET,
        "snapshot_fingerprint": snap["snapshot_fingerprint"],
        "source_discovery_fingerprint": discovery["fingerprint"],
        "selection_used": False,
        "performance_evaluation": False,
        "holdout_evaluation": False,
        "safety": SAFETY,
    }
    freeze["asset_freeze_fingerprint"] = _fp(freeze)
    (evidence / "q091_asset_freeze.json").write_text(
        json.dumps(freeze, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return coverage_receipt


def _mutate_future(assets, index: int, mode: str):
    out = {symbol: list(bars) for symbol, bars in assets.items()}
    start = index + 1
    stop = len(next(iter(out.values()))) if mode == "future" else min(len(next(iter(out.values()))), index + 2)
    for bars in out.values():
        for i in range(start, stop):
            bar = bars[i]
            bars[i] = type(bar)(
                timestamp=bar.timestamp,
                open=bar.open * 11.0,
                high=bar.high * 11.0,
                low=bar.low * 0.05,
                close=bar.close * 0.05,
                volume=bar.volume * 13.0,
            )
    return {symbol: tuple(bars) for symbol, bars in out.items()}


def pit() -> dict:
    coverage = json.loads((ROOT / "research/evidence/q091_coverage_result.json").read_text(encoding="utf-8"))
    freeze = json.loads((ROOT / "research/evidence/q091_asset_freeze.json").read_text(encoding="utf-8"))
    manifest = ROOT / "research/runs/q091_coverage" / COVERAGE_ID / "snapshot_manifest.json"
    assets = load_frozen_snapshot(manifest)
    symbols = tuple(freeze["symbols"])
    if set(assets) != set(symbols):
        raise RuntimeError("Q091 snapshot symbol set mismatch")
    if any(len(assets[s]) != TARGET for s in symbols):
        raise RuntimeError("Q091 snapshot geometry mismatch")

    indices = (21, 63, 146, 273, 756, 1200, 1800, 2400, 3000, 3496)
    checks = 0
    for index in indices:
        if index >= TARGET - 1:
            continue
        original = q091_targets_at(assets, index, symbols)
        for mode in ("future", "next"):
            mutated = _mutate_future(assets, index, mode)
            if q091_targets_at(mutated, index, symbols) != original:
                raise AssertionError(f"Q091 PIT mutation changed targets at {index}/{mode}")
            checks += 1
        for variant, weights in original.items():
            gross = sum(abs(float(v)) for v in weights.values())
            net = sum(float(v) for v in weights.values())
            if gross > 1.0 + 1e-12:
                raise AssertionError(f"{variant}: gross exposure exceeded 1.0")
            if variant == "E2_CROSS_SECTIONAL_RESIDUALIZED_Q069_5SLEEVE" and abs(net) > 1e-12:
                raise AssertionError("Q091 residualized variant is not net-neutral")

    receipt = {
        "schema_version": "1.0",
        "trial_id": PIT_ID,
        "status": "PIT_PASSED",
        "coverage_trial_id": COVERAGE_ID,
        "symbols": list(symbols),
        "variants": [
            "E1_EQUAL_WEIGHT_Q069_5SLEEVE",
            "E2_CROSS_SECTIONAL_RESIDUALIZED_Q069_5SLEEVE",
        ],
        "checked_decision_points": len(indices),
        "mutation_cases": checks,
        "future_mutation_checks_passed": True,
        "next_session_mutation_checks_passed": True,
        "performance_evaluation": False,
        "selection_used": False,
        "holdout_used_for_selection": False,
        "performance_trial_authorized": False,
        "asset_freeze_fingerprint": freeze["asset_freeze_fingerprint"],
        "safety": SAFETY,
    }
    receipt["result_fingerprint"] = _fp(receipt)
    (ROOT / "research/evidence/q091_pit_result.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("coverage", "pit", "all"), default="all")
    args = parser.parse_args()
    if args.mode in ("coverage", "all"):
        coverage()
    if args.mode in ("pit", "all"):
        pit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
