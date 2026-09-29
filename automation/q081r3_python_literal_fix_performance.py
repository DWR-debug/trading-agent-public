"""Q081-R3 corrective replication for Q081/Q079 fixed E1/E2 evaluation.

Q079 produced no scientific performance result because the E2 hysteresis output
violated its already-preregistered gross-exposure cap before evaluation. Q081
keeps the Q079 data, PIT contract, candidate arms, costs and 13-gate evaluation
unchanged, and adds only a deterministic execution-layer pro-rata cap
enforcement required by the existing gross-cap contract.

No parameter, threshold, asset, horizon, variant or family selection is done.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import automation.q079_e1_e2_performance as q079

q079.datetime = datetime

from automation.q067_alpha_mechanisms import (
    GROSS_EXPOSURE_CAP,
    GROSS_EXPOSURE_TOLERANCE,
    apply_common_mode_throttle,
    apply_turnover_hysteresis,
    build_alpha_sleeves,
    equal_weight_ensemble,
    sleeve_period_returns,
    validate_gross_exposure_cap,
)
from config import settings
from execution.cost_contract import validate_research_cost_compatibility

TRIAL_ID = "T-2026-09-30-081R3-PERFORMANCE"
Q079_TRIAL_ID = "T-2026-09-28-079-PERFORMANCE"
Q079_COVERAGE_TRIAL_ID = "T-2026-09-28-079-COVERAGE"
Q079_PIT_TRIAL_ID = "T-2026-09-28-079-PIT"
Q079_INPUT_BUNDLE_TRIAL_ID = "T-2026-09-28-079-INPUT-FREEZE"
SYMBOLS = q079.Q079_SYMBOLS
N = q079.N
RESEARCH = q079.RESEARCH
HOLDOUT = q079.HOLDOUT
FEE = q079.FEE
SLIPPAGE = q079.SLIPPAGE
COSTS = q079.COSTS


def _load_json(path: Path) -> dict:
    return q079._load_json(path)


def _fp(value: object) -> str:
    return q079._fp(value)


def apply_execution_gross_cap(
    row: dict[str, float],
    *,
    symbols: tuple[str, ...] = SYMBOLS,
    cap: float = GROSS_EXPOSURE_CAP,
    tolerance: float = GROSS_EXPOSURE_TOLERANCE,
) -> dict[str, float]:
    """Apply the fixed gross-cap execution envelope pro-rata, with no tunable threshold."""
    if cap < 0.0 or tolerance < 0.0:
        raise ValueError("cap and tolerance must be non-negative")
    values = {symbol: float(row.get(symbol, 0.0)) for symbol in symbols}
    for symbol, value in values.items():
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError(f"non-finite portfolio weight: {symbol}")
        if value < -tolerance:
            raise ValueError(f"negative long-only weight: {symbol}")
    gross = sum(abs(value) for value in values.values())
    if gross <= cap + tolerance:
        return values
    if gross <= 0.0:
        return values
    scale = cap / gross
    return {symbol: value * scale for symbol, value in values.items()}


def correct_e2_execution_envelope(
    weights,
    *,
    symbols: tuple[str, ...] = SYMBOLS,
) -> tuple[dict[str, float], ...]:
    return tuple(
        apply_execution_gross_cap(row, symbols=symbols)
        for row in weights
    )


def run(preregistration: Path, repo_root: Path, output: Path) -> dict:
    prereg = _load_json(preregistration)
    if prereg.get("trial_id") != TRIAL_ID:
        raise ValueError("Q081R3 performance preregistration trial id mismatch")
    if prereg.get("status") != "PREREGISTERED_PERFORMANCE":
        raise ValueError("Q081R3 preregistration status mismatch")

    safety = {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    if prereg.get("safety") != safety:
        raise RuntimeError("Q081R3 performance safety mismatch")
    governance = prereg.get("governance", {})
    for key in (
        "parameter_search",
        "threshold_search",
        "asset_search",
        "horizon_search",
        "variant_search",
        "family_ranking",
        "selection",
        "holdout_used_for_selection",
        "promotion_decision",
        "automatic_promotion",
    ):
        if governance.get(key) is not False:
            raise RuntimeError(f"forbidden governance flag is true: {key}")

    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("runtime safety flags invalid")
    if settings.ORDERS_ENABLED is not False or settings.AUTOMATIC_PROMOTION is not False:
        raise RuntimeError("runtime order/promotion flags invalid")
    validate_research_cost_compatibility(fee_rate=FEE, slippage_rate=SLIPPAGE)

    assets, coverage_result, pit_result = q079._assert_preflight(repo_root)
    if coverage_result.get("trial_id") != Q079_COVERAGE_TRIAL_ID:
        raise RuntimeError("Q079 coverage identity mismatch")
    if pit_result.get("trial_id") != Q079_PIT_TRIAL_ID:
        raise RuntimeError("Q079 PIT identity mismatch")

    sleeves = build_alpha_sleeves(assets, symbols=SYMBOLS)
    aggregate = equal_weight_ensemble(sleeves, symbols=SYMBOLS)
    sleeve_returns = sleeve_period_returns(
        assets,
        sleeves,
        symbols=SYMBOLS,
    )
    e1 = apply_common_mode_throttle(
        aggregate,
        sleeve_returns,
        symbols=SYMBOLS,
    )
    e2_raw = apply_turnover_hysteresis(
        aggregate,
        symbols=SYMBOLS,
    )
    e2 = correct_e2_execution_envelope(e2_raw, symbols=SYMBOLS)

    bundle_manifest, adjusted = q079._load_adjusted_bundle(repo_root)
    if bundle_manifest.get("trial_id") != Q079_INPUT_BUNDLE_TRIAL_ID:
        raise RuntimeError("Q079 input bundle identity mismatch")
    if bundle_manifest.get("bundle_fingerprint") != prereg["data_contract"]["input_bundle_fingerprint"]:
        raise RuntimeError("Q081R3 input bundle fingerprint mismatch")

    arms = {
        "CONTROL_6SLEEVE_ENSEMBLE": aggregate,
        "E1_ALPHA_COMMON_MODE_THROTTLE": e1,
        "E2_TURNOVER_HYSTERESIS": e2,
    }
    for weights in arms.values():
        validate_gross_exposure_cap(weights, symbols=SYMBOLS)

    reports = {
        name: q079._evaluate(assets, weights, adjusted)
        for name, weights in arms.items()
    }
    result = {
        "schema_version": "1.0",
        "trial_id": TRIAL_ID,
        "status": "COMPLETED",
        "code_version": __import__("os").getenv("GITHUB_SHA", "UNVERIFIED"),
        "universe": prereg["universe"],
        "symbols": list(SYMBOLS),
        "requested_candles": prereg["requested_candles"],
        "target_common_candles": prereg["target_common_candles"],
        "research_periods": RESEARCH,
        "holdout_periods": HOLDOUT,
        "initial_capital_eur": 2000.0,
        "corrective_basis": {
            "prior_trial_id": Q079_TRIAL_ID,
            "prior_trial_status": "IMPLEMENTATION_INVALID_NO_SCIENTIFIC_OUTCOME",
            "prior_execution_incident": {
                "workflow_run_id": 36426000120,
                "job_id": 108939981712,
                "row_index": 294,
                "observed_gross_exposure": 1.005555555556,
                "preregistered_gross_exposure_cap": 1.0
            },
            "correction": "deterministic pro-rata enforcement of the already-preregistered gross exposure cap after the unchanged E2 hysteresis transformation",
            "new_tunable_parameters": False
        },
        "coverage_prerequisite": {
            "trial_id": Q079_COVERAGE_TRIAL_ID,
            "result_fingerprint": coverage_result["result_fingerprint"],
            "snapshot_fingerprint": coverage_result["snapshot_fingerprint"]
        },
        "pit_prerequisite": {
            "trial_id": Q079_PIT_TRIAL_ID,
            "result_fingerprint": pit_result["result_fingerprint"]
        },
        "input_bundle_prerequisite": {
            "trial_id": Q079_INPUT_BUNDLE_TRIAL_ID,
            "bundle_fingerprint": bundle_manifest["bundle_fingerprint"]
        },
        "arms": reports,
        "performance_evaluation": true,
        "oos_evaluation": true,
        "holdout_evaluation": true,
        "selection_used": false,
        "holdout_used_for_selection": false,
        "parameter_search": false,
        "threshold_search": false,
        "asset_search": false,
        "horizon_search": false,
        "variant_search": false,
        "family_ranking": false,
        "governance": {
            "performance_trial_authorized": true,
            "selection": false,
            "holdout_used_for_selection": false,
            "promotion_decision": false,
            "automatic_promotion": false
        },
        "safety": safety
    }
    result["report_fingerprint"] = _fp(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        __import__("json").dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.preregistration, args.repo_root, args.output)
