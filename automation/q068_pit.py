"""Q068 point-in-time mutation validation for frozen E1/E2 mechanisms."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from automation.q067_alpha_mechanisms import (
    E1_CORRELATION_LOOKBACK,
    Q067_SLEEVES,
    TARGET_CANDLES,
    alpha_sleeve_targets_at,
    apply_turnover_hysteresis,
    build_alpha_sleeves,
    equal_weight_ensemble,
    mean_pairwise_correlation,
    sleeve_period_returns,
    sleeve_return_history_at,
)
from data.canonical_snapshot import load_frozen_snapshot

Q068_SYMBOLS = ("ETR", "PPL", "WEC", "FE", "D", "EXR", "PSA", "O")
COVERAGE_TRIAL_ID = "T-2026-09-28-068-COVERAGE"
PIT_TRIAL_ID = "T-2026-09-28-068-PIT"
STEP = 113
MIN_HISTORY = E1_CORRELATION_LOOKBACK + 210


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


def _validate(root: Path):
    assets = load_frozen_snapshot(root / "snapshot_manifest.json")
    if tuple(assets) != Q068_SYMBOLS:
        raise ValueError("Q068 symbol order mismatch")
    if any(len(assets[symbol]) != TARGET_CANDLES for symbol in Q068_SYMBOLS):
        raise ValueError("Q068 snapshot geometry mismatch")
    return assets


def _mutate(assets, index: int, mode: str):
    out = {symbol: list(bars) for symbol, bars in assets.items()}
    for symbol, bars in out.items():
        start = index + 1
        stop = len(bars) if mode == "future" else index + 2
        for i in range(start, stop):
            bars[i] = type(bars[i])(
                timestamp=bars[i].timestamp,
                open=bars[i].open * 9.0,
                high=bars[i].high * 9.0,
                low=bars[i].low * 0.1,
                close=bars[i].close * 0.1,
                volume=bars[i].volume,
            )
    return {symbol: tuple(bars) for symbol, bars in out.items()}


def _aggregate_at(assets, index: int):
    sleeves = alpha_sleeve_targets_at(
        assets,
        index,
        symbols=Q068_SYMBOLS,
    )
    return {
        symbol: sum(
            float(sleeves[name].get(symbol, 0.0))
            for name in Q067_SLEEVES
        ) / len(Q067_SLEEVES)
        for symbol in Q068_SYMBOLS
    }


def _assert_history_equal(original_assets, mutated_assets, index: int):
    original = sleeve_return_history_at(
        original_assets,
        index,
        symbols=Q068_SYMBOLS,
    )
    mutated = sleeve_return_history_at(
        mutated_assets,
        index,
        symbols=Q068_SYMBOLS,
    )
    assert original == mutated
    assert abs(
        mean_pairwise_correlation(original)
        - mean_pairwise_correlation(mutated)
    ) < 1e-15


def run(coverage_root: Path, result_path: Path) -> dict:
    assets = _validate(coverage_root)

    sleeves = build_alpha_sleeves(assets, symbols=Q068_SYMBOLS)
    aggregate = equal_weight_ensemble(sleeves, symbols=Q068_SYMBOLS)
    returns = sleeve_period_returns(
        assets,
        sleeves,
        symbols=Q068_SYMBOLS,
    )

    from automation.q067_alpha_mechanisms import common_mode_multipliers

    multipliers = common_mode_multipliers(returns)
    e2_path = apply_turnover_hysteresis(
        aggregate,
        symbols=Q068_SYMBOLS,
    )

    checks = []
    for index in range(MIN_HISTORY, TARGET_CANDLES - 1, STEP):
        original_target = aggregate[index]
        original_prev_target = aggregate[index - 1]
        original_e2 = e2_path[index]

        for mode in ("future", "next"):
            mutated = _mutate(assets, index, mode)
            mutated_target = _aggregate_at(mutated, index)
            mutated_prev_target = _aggregate_at(mutated, index - 1)
            mutated_e2 = apply_turnover_hysteresis(
                (e2_path[index - 1], mutated_target),
                symbols=Q068_SYMBOLS,
            )[1]

            assert original_target == mutated_target
            assert original_prev_target == mutated_prev_target
            assert original_e2 == mutated_e2
            _assert_history_equal(assets, mutated, index)
            assert multipliers[index] in (1.0, 0.5)
            checks.append(
                {
                    "index": index,
                    "mode": mode,
                    "e1_multiplier": multipliers[index],
                }
            )

    result = {
        "schema_version": "1.0",
        "trial_id": PIT_TRIAL_ID,
        "status": "PIT_PASSED",
        "coverage_trial_id": COVERAGE_TRIAL_ID,
        "symbols": list(Q068_SYMBOLS),
        "checked_decision_points": len(checks),
        "mechanisms": [
            "E1_ALPHA_COMMON_MODE_THROTTLE",
            "E2_TURNOVER_HYSTERESIS",
        ],
        "future_mutation_checks_passed": True,
        "next_session_mutation_checks_passed": True,
        "performance_evaluation": False,
        "oos_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "performance_trial_authorized": False,
        "checks_fingerprint": _fp(checks),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["result_fingerprint"] = _fp(result)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print("Q068_PIT_STATUS:", result["status"])
    print("Q068_PIT_FINGERPRINT:", result["result_fingerprint"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage-root", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args()
    run(Path(args.coverage_root), Path(args.result))
