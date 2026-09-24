"""Formal T042 volatility-managed time-series momentum experiment.

Research-only. No live trading, no order execution, no automatic promotion.

The preregistered challenger uses:
- 252-session long/short time-series momentum
- monthly rebalancing
- asset-level de-risk-only inverse-variance scaling
- target annualized variance 0.01 (10% annualized volatility)
- gross-exposure cap 1.0

The fixed control uses the same signal with equal 1/N absolute weights.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from automation.literature_strategy_lab import load_bars
from config import settings
from research.asset_universes import get_universe
from research.protocol import dataset_fingerprint

ROOT = Path(__file__).resolve().parents[1]

TRIAL_ID = "T-2026-09-24-042"
UNIVERSE = "validation_2026_09_24_volatility_managed_tsm"
TARGET_COUNT = 3500
EVALUATION_COUNT = 3498
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700

TSM_LOOKBACK = 252
VOL_LOOKBACK = 21
TARGET_VARIANCE = 0.01
REBALANCE_MONTHLY = True

FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
COST_RATE = FEE_RATE + SLIPPAGE_RATE

COST_SCENARIOS = (
    ("base", 1.0),
    ("stress_1_5x_cost", 1.5),
    ("stress_2x_cost", 2.0),
)

SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _sign(value: float) -> int:
    if value > 0.0:
        return 1
    if value < 0.0:
        return -1
    return 0


def _inverse_variance_scale(annualized_variance: float) -> float:
    if annualized_variance <= 0.0:
        return 1.0
    return min(1.0, TARGET_VARIANCE / annualized_variance)


def _annualized_realized_variance(closes: list[float], end_index: int) -> float:
    if end_index < VOL_LOOKBACK:
        return 0.0
    returns = [
        closes[index] / closes[index - 1] - 1.0
        for index in range(end_index - VOL_LOOKBACK + 1, end_index + 1)
    ]
    if len(returns) != VOL_LOOKBACK:
        return 0.0
    mean = sum(returns) / len(returns)
    denominator = len(returns) - 1
    if denominator <= 0:
        return 0.0
    variance = sum((value - mean) ** 2 for value in returns) / denominator
    return variance * 252.0


def _tsm_signal(closes: list[float], decision_index: int) -> int:
    anchor = decision_index - 1
    origin = anchor - TSM_LOOKBACK
    if origin < 0:
        return 0
    return _sign(closes[anchor] / closes[origin] - 1.0)


def _target_weights(
    closes_by_symbol: dict[str, list[float]],
    decision_index: int,
    challenger: bool,
) -> dict[str, float]:
    symbols = tuple(closes_by_symbol)
    n = len(symbols)
    if n == 0:
        return {}

    output: dict[str, float] = {}
    for symbol in symbols:
        signal = _tsm_signal(
            closes_by_symbol[symbol],
            decision_index,
        )
        base_weight = signal / n
        if not challenger:
            output[symbol] = base_weight
            continue

        variance = _annualized_realized_variance(
            closes_by_symbol[symbol],
            decision_index - 1,
        )
        scale = _inverse_variance_scale(variance)
        output[symbol] = base_weight * scale

    gross = sum(abs(value) for value in output.values())
    if gross > 1.0 + 1e-12:
        output = {
            symbol: value / gross
            for symbol, value in output.items()
        }
    return output


def _load_coverage(
    coverage_path: Path,
    preregistration: dict,
) -> tuple[dict, dict[str, tuple]]:
    payload = json.loads(coverage_path.read_text(encoding="utf-8"))
    if payload.get("trial_id") != TRIAL_ID:
        raise ValueError("Coverage artifact belongs to another trial.")
    if payload.get("status") != "coverage_passed":
        raise ValueError("T042 formal performance requires coverage_passed.")
    if payload.get("universe") != preregistration["universe"]:
        raise ValueError("Coverage universe does not match preregistration.")
    counts = payload.get("per_symbol_counts", {})
    if set(counts) != set(preregistration["symbols"]):
        raise ValueError("Coverage symbol set does not match preregistration.")
    if any(int(count) != TARGET_COUNT for count in counts.values()):
        raise ValueError("Coverage contains a symbol below target history.")

    snapshots = payload.get("data_snapshot", {}).get("datasets", [])
    if len(snapshots) != len(preregistration["symbols"]):
        raise ValueError("Coverage data snapshot is incomplete.")

    assets: dict[str, tuple] = {}
    for item in snapshots:
        symbol = item["symbol"]
        if symbol not in preregistration["symbols"]:
            raise ValueError(f"Unexpected snapshot symbol: {symbol}.")
        dataset_path = Path(item["path"])
        if not dataset_path.is_absolute():
            dataset_path = ROOT / dataset_path
        bars = tuple(load_bars(dataset_path, expected_count=TARGET_COUNT))
        if dataset_fingerprint(bars) != item["fingerprint"]:
            raise ValueError(f"Dataset fingerprint mismatch for {symbol}.")
        assets[symbol] = bars

    if tuple(assets) != tuple(preregistration["symbols"]):
        raise ValueError("Coverage symbol order does not match preregistration.")

    common = set.intersection(
        *(set(bar.timestamp for bar in bars) for bars in assets.values())
    )
    if len(common) != TARGET_COUNT:
        raise ValueError(
            f"Common calendar mismatch: {len(common)} != {TARGET_COUNT}"
        )
    return payload, assets


def _verify_preregistration(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("trial_id") != TRIAL_ID:
        raise ValueError("Unexpected T042 trial id.")
    if payload.get("universe") != UNIVERSE:
        raise ValueError("Unexpected T042 universe.")
    if payload.get("requested_candles") != TARGET_COUNT:
        raise ValueError("Unexpected T042 candle target.")
    if payload.get("search_scope", {}).get("parameter_search") is not False:
        raise ValueError("Parameter search must remain disabled.")
    if payload.get("search_scope", {}).get("variant_search") is not False:
        raise ValueError("Variant search must remain disabled.")
    if payload.get("search_scope", {}).get("holdout_used_for_selection") is not False:
        raise ValueError("Holdout selection must remain disabled.")
    if payload.get("coverage_gate", {}).get("performance_allowed_before_coverage_pass") is not False:
        raise ValueError("Coverage gate is invalid.")
    if payload.get("safety") != SAFETY:
        raise ValueError("Safety contract is invalid.")
    universe = get_universe(UNIVERSE)
    if tuple(payload.get("symbols", [])) != tuple(universe.symbols):
        raise ValueError("Preregistered symbols do not match reserved universe.")
    return payload


def _evaluation_rows(
    assets: dict[str, tuple],
    challenger: bool,
) -> tuple[dict, ...]:
    symbols = tuple(assets)
    lengths = {len(bars) for bars in assets.values()}
    if lengths != {TARGET_COUNT}:
        raise ValueError("All T042 assets must contain exactly 3500 candles.")

    timestamps = [bar.timestamp for bar in assets[symbols[0]]]
    for index, bars in enumerate(assets.values()):
        if [bar.timestamp for bar in bars] != timestamps:
            raise ValueError("T042 asset calendars are not aligned at evaluation.")
    closes_by_symbol = {
        symbol: [bar.close for bar in assets[symbol]]
        for symbol in symbols
    }

    previous_weights = {symbol: 0.0 for symbol in symbols}
    current_weights = {symbol: 0.0 for symbol in symbols}
    rows = []
    previous_month = None

    for decision_index in range(2, TARGET_COUNT):
        timestamp = timestamps[decision_index]
        month = (timestamp.year, timestamp.month)
        if REBALANCE_MONTHLY and month != previous_month:
            if decision_index <= TSM_LOOKBACK:
                current_weights = {
                    symbol: 0.0
                    for symbol in symbols
                }
            else:
                current_weights = _target_weights(
                    closes_by_symbol,
                    decision_index,
                    challenger,
                )
            previous_month = month

        gross_return = 0.0
        daily_turnover = 0.0
        for symbol in symbols:
            market_return = (
                closes_by_symbol[symbol][decision_index]
                / closes_by_symbol[symbol][decision_index - 1]
                - 1.0
            )
            weight = current_weights[symbol]
            gross_return += weight * market_return
            daily_turnover += abs(weight - previous_weights[symbol])

        rows.append(
            {
                "timestamp": timestamp,
                "gross_return": gross_return,
                "turnover": daily_turnover,
                "gross_exposure": sum(abs(value) for value in current_weights.values()),
                "weights": dict(current_weights),
            }
        )
        previous_weights = dict(current_weights)

    if len(rows) != EVALUATION_COUNT:
        raise ValueError(
            f"Unexpected evaluation count: {len(rows)} != {EVALUATION_COUNT}"
        )
    return tuple(rows)


def _with_cost(rows: tuple[dict, ...], multiplier: float) -> list[dict]:
    output = []
    for row in rows:
        net = row["gross_return"] - COST_RATE * multiplier * row["turnover"]
        output.append({**row, "net_return": net})
    return output


def _stats(values: list[float], start: int, end: int) -> dict:
    segment = values[start:end]
    if not segment:
        return {
            "period_return": 0.0,
            "max_drawdown_percent": 0.0,
            "profit_factor": 0.0,
            "day_count": 0,
        }

    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    gross_profit = 0.0
    gross_loss = 0.0

    for value in segment:
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_drawdown = max(
            max_drawdown,
            1.0 - equity / peak if peak > 0.0 else 1.0,
        )
        if value > 0.0:
            gross_profit += value
        elif value < 0.0:
            gross_loss -= value

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0.0
        else ("inf" if gross_profit > 0.0 else 0.0)
    )
    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_drawdown * 100.0,
        "profit_factor": profit_factor,
        "day_count": len(segment),
    }


def _rolling(values: list[float], research_end: int) -> list[dict]:
    width = research_end // 5
    windows = []
    start = 0
    for index in range(5):
        end = research_end if index == 4 else start + width
        windows.append(
            {
                "window_index": index + 1,
                **_stats(values, start, end),
            }
        )
        start = end
    return windows


def _summary(values: list[float], research_end: int) -> dict:
    development_end = int(research_end * 0.80)
    research = _stats(values, 0, research_end)
    development = _stats(values, 0, development_end)
    oos = _stats(values, development_end, research_end)
    holdout = _stats(values, research_end, len(values))
    rolling = _rolling(values, research_end)
    rolling_pf = min(
        math.inf if row["profit_factor"] == "inf" else float(row["profit_factor"])
        for row in rolling
    )
    return {
        "research": research,
        "development": development,
        "oos": oos,
        "holdout": holdout,
        "oos_to_is_return_ratio": (
            oos["period_return"] / development["period_return"]
            if development["period_return"] > 0.0
            else 0.0
        ),
        "rolling": rolling,
        "rolling_min_profit_factor": rolling_pf,
        "rolling_profitable_window_ratio": (
            sum(row["period_return"] > 0.0 for row in rolling) / len(rolling)
        ),
        "rolling_average_drawdown_percent": (
            sum(row["max_drawdown_percent"] for row in rolling) / len(rolling)
        ),
    }


def _metric_pf(value: object) -> float:
    return math.inf if value == "inf" else float(value)


def _gates(challenger: dict, control: dict, stress15: dict, stress2: dict) -> dict:
    r = challenger["research"]
    h = challenger["holdout"]
    rolling_checks = challenger

    absolute = {
        "positive_research_return": r["period_return"] > 0.0,
        "research_drawdown_lte_10pct": r["max_drawdown_percent"] <= 10.0,
        "research_profit_factor_gte_1_10": _metric_pf(r["profit_factor"]) >= 1.10,
        "rolling_profit_factor_gte_1_10": rolling_checks["rolling_min_profit_factor"] >= 1.10,
        "profitable_rolling_windows_gte_50pct": rolling_checks["rolling_profitable_window_ratio"] >= 0.50,
        "average_rolling_drawdown_lte_10pct": rolling_checks["rolling_average_drawdown_percent"] <= 10.0,
        "oos_to_is_return_ratio_gte_0_25": challenger["oos_to_is_return_ratio"] >= 0.25,
        "positive_holdout_return": h["period_return"] > 0.0,
        "holdout_profit_factor_gte_1_10": _metric_pf(h["profit_factor"]) >= 1.10,
        "holdout_drawdown_lte_10pct": h["max_drawdown_percent"] <= 10.0,
        "holdout_stress_1_5x_nonnegative": stress15["holdout"]["period_return"] >= 0.0,
        "holdout_stress_2x_nonnegative": stress2["holdout"]["period_return"] >= 0.0,
    }
    non_deterioration = {
        "research_return_not_below_control": (
            r["period_return"] >= control["research"]["period_return"]
        ),
        "research_drawdown_not_worse": (
            r["max_drawdown_percent"] <= control["research"]["max_drawdown_percent"]
        ),
        "research_profit_factor_not_below_control": (
            _metric_pf(r["profit_factor"]) >= _metric_pf(control["research"]["profit_factor"])
        ),
        "rolling_pf_not_below_control": (
            challenger["rolling_min_profit_factor"] >= control["rolling_min_profit_factor"]
        ),
        "rolling_profitable_ratio_not_below_control": (
            challenger["rolling_profitable_window_ratio"]
            >= control["rolling_profitable_window_ratio"]
        ),
        "rolling_average_drawdown_not_worse": (
            challenger["rolling_average_drawdown_percent"]
            <= control["rolling_average_drawdown_percent"]
        ),
        "oos_to_is_not_below_control": (
            challenger["oos_to_is_return_ratio"] >= control["oos_to_is_return_ratio"]
        ),
        "holdout_return_not_below_control": (
            h["period_return"] >= control["holdout"]["period_return"]
        ),
        "holdout_profit_factor_not_below_control": (
            _metric_pf(h["profit_factor"]) >= _metric_pf(control["holdout"]["profit_factor"])
        ),
        "holdout_drawdown_not_worse": (
            h["max_drawdown_percent"] <= control["holdout"]["max_drawdown_percent"]
        ),
    }
    return {
        "absolute": absolute,
        "non_deterioration_vs_equal_weight_control": non_deterioration,
        "all_absolute_passed": all(absolute.values()),
        "all_non_deterioration_passed": all(non_deterioration.values()),
        "all_passed": all(absolute.values()) and all(non_deterioration.values()),
    }


def run_trial(
    coverage_path: str | Path,
    preregistration_path: str | Path,
    output_path: str | Path,
) -> dict:
    if settings.PAPER_ONLY is not True:
        raise RuntimeError("T042 requires PAPER_ONLY=True.")
    if settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("T042 requires LIVE_TRADING_ENABLED=False.")

    prereg = _verify_preregistration(Path(preregistration_path))
    coverage, assets = _load_coverage(Path(coverage_path), prereg)

    coverage_fingerprint = coverage["coverage_fingerprint"]
    expected_coverage_fingerprint = "67a42d1a4832413e4a0a6dc36e1d47dd5c92a25923ea86c8d1c11a1d29e30d24"
    if coverage_fingerprint != expected_coverage_fingerprint:
        raise ValueError("T042 does not use the frozen approved coverage snapshot.")

    challenger_rows = _evaluation_rows(assets, challenger=True)
    control_rows = _evaluation_rows(assets, challenger=False)

    scenarios = {}
    for scenario, multiplier in COST_SCENARIOS:
        challenger_summary = _summary(
            [row["net_return"] for row in _with_cost(challenger_rows, multiplier)],
            RESEARCH_COUNT,
        )
        control_summary = _summary(
            [row["net_return"] for row in _with_cost(control_rows, multiplier)],
            RESEARCH_COUNT,
        )
        scenarios[scenario] = {
            "challenger": challenger_summary,
            "equal_weight_control": control_summary,
        }

    base_challenger = scenarios["base"]["challenger"]
    base_control = scenarios["base"]["equal_weight_control"]
    evaluation = _gates(
        base_challenger,
        base_control,
        scenarios["stress_1_5x_cost"]["challenger"],
        scenarios["stress_2x_cost"]["challenger"],
    )

    report = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "status": "PASSED_NO_AUTO_PROMOTION" if evaluation["all_passed"] else "BLOCKED",
        "scientific_outcome": (
            "EVIDENCE_GATED_PASS" if evaluation["all_passed"] else "NO_PROMOTION_EVIDENCE"
        ),
        "source": {
            "universe": UNIVERSE,
            "coverage_fingerprint": coverage_fingerprint,
            "common_calendar_count": coverage["common_calendar_count"],
            "evaluation_return_count": EVALUATION_COUNT,
            "research_return_count": RESEARCH_COUNT,
            "holdout_return_count": HOLDOUT_COUNT,
        },
        "methodology": {
            "signal": "sign(close[t-1] / close[t-253] - 1)",
            "signal_lookback_sessions": TSM_LOOKBACK,
            "realized_variance_lookback_sessions": VOL_LOOKBACK,
            "target_annualized_variance": TARGET_VARIANCE,
            "target_annualized_volatility": math.sqrt(TARGET_VARIANCE),
            "scaling": "min(1.0, target_variance / trailing_annualized_realized_variance)",
            "de_risk_only": True,
            "gross_exposure_cap": 1.0,
            "rebalance": "first trading session of each calendar month",
            "point_in_time": True,
            "baseline": "same signal with equal 1/N absolute weights",
            "leverage": 1.0,
            "short_allowed": True,
            "parameter_search": False,
            "holdout_used_for_selection": False,
            "costs": {
                "fee_rate": FEE_RATE,
                "slippage_rate": SLIPPAGE_RATE,
                "scenarios": [name for name, _ in COST_SCENARIOS],
                "turnover_costed": True,
            },
        },
        "scenarios": scenarios,
        "evaluation": evaluation,
        "safety": SAFETY,
    }
    report["report_fingerprint"] = _fingerprint(report)

    output = Path(output_path)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", required=True)
    parser.add_argument("--preregistration", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run_trial(args.coverage, args.preregistration, args.output)
    print("T042_STATUS:", report["status"])
    print("T042_REPORT_FINGERPRINT:", report["report_fingerprint"])
    print("T042_RESEARCH_RETURN:", report["scenarios"]["base"]["challenger"]["research"]["period_return"])
    print("T042_HOLDOUT_RETURN:", report["scenarios"]["base"]["challenger"]["holdout"]["period_return"])
    print("T042_HOLDOUT_MAX_DD:", report["scenarios"]["base"]["challenger"]["holdout"]["max_drawdown_percent"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
