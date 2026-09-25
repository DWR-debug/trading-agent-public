"""Trial 045: one fixed ATR trailing exit as a position-lifecycle control.
Research-only; no optimization, selection, promotion or orders.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from automation.candidate_validation_50_50_vol_budget import (
    _build_weight_path,
    _cs_weights,
    _return_rows,
    _stats,
    _summary,
    _yahoo_adjclose,
    load_bars,
)
from config import settings
from research.asset_universes import get_universe, list_universes
from research.protocol import dataset_fingerprint
from validation.research_gates import ResearchGateConfig


TRIAL_ID = "T-2026-09-25-045"
UNIVERSE = "validation_2026_09_25_position_lifecycle_exit"
TREND_SYMBOLS = ("WFC", "DUK", "AXP", "BLK", "DHR", "INTU", "MAR", "COP")
CS_SYMBOLS = ("SO", "NEE", "AMGN", "BSX", "CMCSA")
PORTFOLIO_SYMBOLS = TREND_SYMBOLS + CS_SYMBOLS

REQUESTED_COUNT = 3520
TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700

ATR_WINDOW = 20
ATR_MULTIPLE = 3.0
TREND_STRATEGY = "sma_50_200_inverse_vol"
TREND_VOL_WINDOW = 60
MAX_ASSET_WEIGHT = 0.25
VOL_WINDOW = 63
TARGET_VOL = 0.10
FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005

COST_SCENARIOS = (
    ("base", 1.0),
    ("stress_1_5x_cost", 1.5),
    ("stress_2x_cost", 2.0),
)


def _canon(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _pf(value: float | str) -> float:
    return float("inf") if value == "inf" else float(value)


def _manifest(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    universe = get_universe(UNIVERSE)
    symbols = tuple(item["symbol"] for item in data.get("datasets", []))

    if data.get("universe") != UNIVERSE or symbols != tuple(universe.symbols):
        raise ValueError("Manifest passt nicht zum T045-Universum.")

    if (
        data.get("requested_candles") != REQUESTED_COUNT
        or data.get("target_common_calendar") != TARGET_COUNT
    ):
        raise ValueError("Unerwartete T045 Coverage-Datenbasis.")

    safety = data.get("safety", {})
    if (
        safety.get("paper_only") is not True
        or safety.get("live_trading_enabled") is not False
        or safety.get("orders_enabled") is not False
    ):
        raise RuntimeError("Paper-only-Sicherheitsvertrag verletzt.")

    return data


def _assets(data_dir: Path, manifest: dict) -> dict[str, tuple]:
    snapshots = manifest.get("data_snapshot", {}).get("datasets", [])
    if len(snapshots) != len(PORTFOLIO_SYMBOLS):
        raise ValueError("T045 frozen data snapshot is incomplete.")

    assets: dict[str, tuple] = {}
    for item in snapshots:
        symbol = item["symbol"]
        bars = load_bars(
            data_dir / symbol / "1d.csv",
            expected_count=int(item["candle_count"]),
        )
        if (
            len(bars) != REQUESTED_COUNT
            or dataset_fingerprint(bars) != item["fingerprint"]
        ):
            raise ValueError(f"{symbol}: Dataset-Identität/Fingerprint stimmt nicht.")
        assets[symbol] = bars

    if set(assets) != set(PORTFOLIO_SYMBOLS):
        raise ValueError("T045-Symbole fehlen.")

    common = set.intersection(
        *({bar.timestamp for bar in bars} for bars in assets.values())
    )
    if len(common) < TARGET_COUNT:
        raise ValueError(
            f"Zu wenig gemeinsame Candles im T045-Snapshot: {len(common)}"
        )

    selected = sorted(common)[-TARGET_COUNT:]
    return {
        symbol: tuple(
            {bar.timestamp: bar for bar in bars}[timestamp]
            for timestamp in selected
        )
        for symbol, bars in assets.items()
    }


def _month_end_indices(bars: tuple) -> tuple[int, ...]:
    out: list[int] = []
    previous_key = None
    previous_index = None

    for index, bar in enumerate(bars):
        key = (bar.timestamp.year, bar.timestamp.month)
        if previous_key is not None and key != previous_key:
            out.append(previous_index)
        previous_key = key
        previous_index = index

    if previous_index is not None:
        out.append(previous_index)

    return tuple(out)


def _atr_value(bars: tuple, index: int, window: int = ATR_WINDOW) -> float | None:
    """Simple point-in-time ATR from the current bar plus prior closes."""
    if window <= 0:
        raise ValueError("ATR window must be positive.")
    if index < window:
        return None

    true_ranges: list[float] = []
    for cursor in range(index - window + 1, index + 1):
        previous_close = bars[cursor - 1].close
        current = bars[cursor]
        true_ranges.append(
            max(
                current.high - current.low,
                abs(current.high - previous_close),
                abs(current.low - previous_close),
            )
        )

    if len(true_ranges) != window:
        raise ValueError("ATR construction produced an unexpected sample size.")

    return sum(true_ranges) / window


def _stop_triggered(
    highest_close: float | None,
    current_close: float,
    atr: float | None,
) -> bool:
    if highest_close is None or atr is None or atr <= 0.0:
        return False
    return current_close < highest_close - ATR_MULTIPLE * atr


def _atr_trailing_exit_weight_path(
    assets: dict[str, tuple],
) -> tuple[tuple[dict[str, float], ...], dict]:
    """Overlay one fixed ATR trailing exit on the unchanged monthly trend weights.

    Entry occurs only when the baseline monthly trend sleeve has a positive
    allocation. After a close-triggered stop, the asset remains flat until the
    next monthly rebalance. A positive baseline allocation there re-enters and
    resets the trailing high to that day's close. No other trend weights are
    renormalized after an exit.
    """
    baseline = _build_weight_path(assets, TREND_STRATEGY)
    length = len(next(iter(assets.values())))
    month_ends = set(_month_end_indices(next(iter(assets.values()))))

    current = {symbol: 0.0 for symbol in assets}
    active = {symbol: False for symbol in assets}
    stopped = {symbol: False for symbol in assets}
    highest_close: dict[str, float | None] = {symbol: None for symbol in assets}

    stop_events: list[dict[str, str | float]] = []
    output: list[dict[str, float]] = []

    for index in range(length):
        if index in month_ends:
            for symbol, bars in assets.items():
                baseline_weight = baseline[index].get(symbol, 0.0)

                if baseline_weight <= 0.0:
                    active[symbol] = False
                    stopped[symbol] = False
                    highest_close[symbol] = None
                    current[symbol] = 0.0
                    continue

                if not active[symbol] or stopped[symbol]:
                    active[symbol] = True
                    stopped[symbol] = False
                    highest_close[symbol] = bars[index].close

                current[symbol] = baseline_weight

        for symbol, bars in assets.items():
            if not active[symbol] or stopped[symbol]:
                current[symbol] = 0.0
                continue

            close = bars[index].close
            previous_high = highest_close[symbol]
            atr = _atr_value(bars, index)

            if previous_high is None:
                highest_close[symbol] = close
                current[symbol] = baseline[index].get(symbol, 0.0)
                continue

            if _stop_triggered(previous_high, close, atr):
                stopped[symbol] = True
                active[symbol] = False
                current[symbol] = 0.0
                stop_events.append(
                    {
                        "symbol": symbol,
                        "timestamp": bars[index].timestamp.isoformat(),
                        "close": close,
                        "highest_close": previous_high,
                        "atr": float(atr) if atr is not None else 0.0,
                    }
                )
                continue

            highest_close[symbol] = max(previous_high, close)
            current[symbol] = baseline[index].get(symbol, 0.0)

        output.append(dict(current))

    by_symbol = Counter(event["symbol"] for event in stop_events)
    diagnostics = {
        "stop_event_count": len(stop_events),
        "stop_events_by_symbol": dict(sorted(by_symbol.items())),
        "stopped_asset_days": sum(
            1 for row in output for value in row.values() if value == 0.0
        ),
        "position_asset_days": sum(
            1 for row in output for value in row.values() if value > 0.0
        ),
    }
    return tuple(output), diagnostics


def _portfolio_rows(
    trend_assets: dict[str, tuple],
    cs_assets: dict[str, tuple],
    trend_weights: tuple[dict[str, float], ...],
    adjusted: dict[str, dict],
) -> tuple[dict, ...]:
    cs_weights = _cs_weights(cs_assets)

    trend_rows = _return_rows(
        trend_assets,
        trend_weights,
        {symbol: adjusted[symbol] for symbol in trend_assets},
    )
    cs_rows = _return_rows(
        cs_assets,
        cs_weights,
        {symbol: adjusted[symbol] for symbol in cs_assets},
    )

    trend_by_time = {row["timestamp"]: row for row in trend_rows}
    cs_by_time = {row["timestamp"]: row for row in cs_rows}
    common = sorted(set(trend_by_time) & set(cs_by_time))

    expected = RESEARCH_COUNT + HOLDOUT_COUNT
    if len(common) != expected:
        raise ValueError(f"{len(common)} Returns statt {expected}.")

    return tuple(
        {
            "timestamp": timestamp,
            "gross_open": (
                0.5 * trend_by_time[timestamp]["gross_open"]
                + 0.5 * cs_by_time[timestamp]["gross_open"]
            ),
            "gross_close": (
                0.5 * trend_by_time[timestamp]["gross_close"]
                + 0.5 * cs_by_time[timestamp]["gross_close"]
            ),
            "gross_adjusted_close": (
                0.5 * trend_by_time[timestamp]["gross_adjusted_close"]
                + 0.5 * cs_by_time[timestamp]["gross_adjusted_close"]
            ),
            "turnover": (
                0.5 * trend_by_time[timestamp]["turnover"]
                + 0.5 * cs_by_time[timestamp]["turnover"]
            ),
        }
        for timestamp in common
    )


def _vol(history: list[float]) -> float | None:
    if len(history) < VOL_WINDOW:
        return None
    sample = history[-VOL_WINDOW:]
    mean = sum(sample) / len(sample)
    variance = sum((value - mean) ** 2 for value in sample) / len(sample)
    return math.sqrt(variance) * math.sqrt(252.0)


def _simulate(
    rows: tuple[dict, ...],
    multiplier: float,
    total_return: bool = False,
) -> list[dict]:
    history: list[float] = []
    previous_scale = 1.0
    cost_rate = (FEE_RATE + SLIPPAGE_RATE) * multiplier
    output: list[dict] = []

    for row in rows:
        scale = 1.0
        realized_vol = _vol(history)
        if realized_vol is not None and realized_vol > TARGET_VOL:
            scale = min(1.0, TARGET_VOL / realized_vol)

        gross = row["gross_open"]
        if total_return:
            gross += row["gross_adjusted_close"] - row["gross_close"]

        turnover = scale * row["turnover"] + abs(scale - previous_scale)
        net = scale * gross - cost_rate * turnover

        output.append(
            {
                "timestamp": row["timestamp"],
                "scale": scale,
                "net_return": net,
                "gross_return": scale * gross,
                "realized_vol_estimate": realized_vol,
            }
        )
        previous_scale = scale
        history.append(
            row["gross_open"]
            - (FEE_RATE + SLIPPAGE_RATE) * row["turnover"]
        )

    return output


def _summarize(rows: list[dict]) -> dict:
    research = _stats(rows, 0, RESEARCH_COUNT)
    holdout = _stats(rows, RESEARCH_COUNT, RESEARCH_COUNT + HOLDOUT_COUNT)

    width = RESEARCH_COUNT // 5
    windows: list[dict] = []
    start = 0
    for index in range(5):
        end = RESEARCH_COUNT if index == 4 else start + width
        windows.append(
            {
                "window_index": index + 1,
                **_stats(rows, start, end),
            }
        )
        start = end

    return {
        "research": research,
        "holdout": holdout,
        "rolling_windows": windows,
        "rolling_summary": _summary(rows[:RESEARCH_COUNT], windows),
        "oos_to_is_return_ratio": (
            holdout["period_return"] / research["period_return"]
            if research["period_return"] > 0.0
            else 0.0
        ),
    }


def _scenario(
    fixed_rows: tuple[dict, ...],
    challenger_rows: tuple[dict, ...],
    multiplier: float,
) -> dict:
    return {
        "fixed_candidate": {
            "price_only": _summarize(_simulate(fixed_rows, multiplier)),
        },
        "exit_challenger": {
            "price_only": _summarize(_simulate(challenger_rows, multiplier)),
            "total_return_sensitivity": _summarize(
                _simulate(challenger_rows, multiplier, True)
            ),
        },
    }


def _gates(scenarios: dict, config: ResearchGateConfig) -> dict:
    base = scenarios["base"]["exit_challenger"]["price_only"]
    fixed = scenarios["base"]["fixed_candidate"]["price_only"]
    stress15 = scenarios["stress_1_5x_cost"]["exit_challenger"]["price_only"]
    stress2 = scenarios["stress_2x_cost"]["exit_challenger"]["price_only"]
    total = scenarios["base"]["exit_challenger"]["total_return_sensitivity"]
    roll = base["rolling_summary"]

    absolute = {
        "research_return_positive": base["research"]["period_return"] > 0.0,
        "research_drawdown": (
            base["research"]["max_drawdown_percent"]
            <= config.maximum_drawdown_percent
        ),
        "research_profit_factor": (
            _pf(base["research"]["profit_factor"])
            >= config.minimum_profit_factor
        ),
        "rolling_profit_factor": (
            _pf(roll["overall_profit_factor"])
            >= config.minimum_profit_factor
        ),
        "rolling_profitable_window_ratio": (
            roll["profitable_window_ratio"]
            >= config.minimum_profitable_window_ratio
        ),
        "rolling_average_drawdown": (
            roll["average_drawdown_percent"]
            <= config.maximum_drawdown_percent
        ),
        "oos_to_is_return_ratio": (
            base["oos_to_is_return_ratio"]
            >= config.minimum_oos_to_is_return_ratio
        ),
        "holdout_return_positive": base["holdout"]["period_return"] > 0.0,
        "holdout_profit_factor": (
            _pf(base["holdout"]["profit_factor"])
            >= config.minimum_profit_factor
        ),
        "holdout_drawdown": (
            base["holdout"]["max_drawdown_percent"]
            <= config.maximum_drawdown_percent
        ),
        "stress_1_5x_nonnegative": (
            stress15["holdout"]["period_return"] >= 0.0
        ),
        "stress_2x_nonnegative": (
            stress2["holdout"]["period_return"] >= 0.0
        ),
        "total_return_sensitivity_nonnegative": (
            total["holdout"]["period_return"] >= 0.0
        ),
    }

    non_worsening = {
        "research_return_not_below_fixed": (
            base["research"]["period_return"]
            >= fixed["research"]["period_return"]
        ),
        "research_drawdown_not_worse_vs_fixed": (
            base["research"]["max_drawdown_percent"]
            <= fixed["research"]["max_drawdown_percent"]
        ),
        "research_profit_factor_not_below_fixed": (
            _pf(base["research"]["profit_factor"])
            >= _pf(fixed["research"]["profit_factor"])
        ),
        "rolling_pf_not_below_fixed": (
            _pf(roll["overall_profit_factor"])
            >= _pf(fixed["rolling_summary"]["overall_profit_factor"])
        ),
        "rolling_profitable_ratio_not_below_fixed": (
            roll["profitable_window_ratio"]
            >= fixed["rolling_summary"]["profitable_window_ratio"]
        ),
        "rolling_average_drawdown_not_worse_vs_fixed": (
            roll["average_drawdown_percent"]
            <= fixed["rolling_summary"]["average_drawdown_percent"]
        ),
        "oos_to_is_not_below_fixed": (
            base["oos_to_is_return_ratio"]
            >= fixed["oos_to_is_return_ratio"]
        ),
        "holdout_return_not_below_fixed": (
            base["holdout"]["period_return"]
            >= fixed["holdout"]["period_return"]
        ),
        "holdout_pf_not_below_fixed": (
            _pf(base["holdout"]["profit_factor"])
            >= _pf(fixed["holdout"]["profit_factor"])
        ),
        "holdout_drawdown_not_worse_vs_fixed": (
            base["holdout"]["max_drawdown_percent"]
            <= fixed["holdout"]["max_drawdown_percent"]
        ),
    }

    return {
        "absolute": absolute,
        "non_worsening_vs_fixed_candidate": non_worsening,
        "all_absolute_passed": all(absolute.values()),
        "all_non_worsening_passed": all(non_worsening.values()),
        "all_checks_passed": all(absolute.values()) and all(non_worsening.values()),
    }


def run_validation(
    data_dir: Path,
    manifest_path: Path,
    output_path: Path,
) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only-Sicherheitsvertrag verletzt.")

    manifest = _manifest(manifest_path)
    expected = set(PORTFOLIO_SYMBOLS)

    for universe in list_universes():
        if universe.name == UNIVERSE:
            continue
        if expected.intersection(universe.symbols):
            raise ValueError(f"Symbol-Overlap mit bestehendem Universum: {universe.name}")

    assets = _assets(data_dir, manifest)
    all_assets = {**assets}
    adjusted = {
        symbol: _yahoo_adjclose(
            symbol,
            bars[0].timestamp,
            bars[-1].timestamp,
        )
        for symbol, bars in all_assets.items()
    }

    trend_assets = {symbol: assets[symbol] for symbol in TREND_SYMBOLS}
    cs_assets = {symbol: assets[symbol] for symbol in CS_SYMBOLS}

    fixed_trend_weights = _build_weight_path(
        trend_assets,
        TREND_STRATEGY,
    )
    challenger_trend_weights, lifecycle = _atr_trailing_exit_weight_path(
        trend_assets,
    )

    fixed_rows = _portfolio_rows(
        trend_assets,
        cs_assets,
        fixed_trend_weights,
        adjusted,
    )
    challenger_rows = _portfolio_rows(
        trend_assets,
        cs_assets,
        challenger_trend_weights,
        adjusted,
    )

    scenarios = {
        name: _scenario(fixed_rows, challenger_rows, multiplier)
        for name, multiplier in COST_SCENARIOS
    }
    gates = _gates(scenarios, ResearchGateConfig())

    report = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "status": "COMPLETED",
        "research_only": True,
        "candidate_status": "VALIDATED_PASS"
        if gates["all_checks_passed"]
        else "BLOCKED",
        "hypothesis": (
            "Replace only the trend-sleeve position lifecycle with one fixed "
            "ATR trailing exit while preserving the SMA 50/200 signal, the "
            "cross-sectional sleeve, 10% portfolio volatility budget, costs "
            "and point-in-time execution."
        ),
        "source": {
            "universe": UNIVERSE,
            "trend_symbols": list(TREND_SYMBOLS),
            "cross_sectional_symbols": list(CS_SYMBOLS),
            "portfolio_symbols": list(PORTFOLIO_SYMBOLS),
            "target_candles": TARGET_COUNT,
            "common_returns": len(challenger_rows),
            "research_count": RESEARCH_COUNT,
            "holdout_count": HOLDOUT_COUNT,
            "fully_symbol_disjoint": True,
            "coverage_fingerprint": manifest["coverage_fingerprint"],
        },
        "methodology": {
            "baseline": (
                "fixed 50/50 SMA 50/200 inverse-volatility trend sleeve + "
                "12-1 cross-sectional Top-2 + 10% portfolio volatility budget"
            ),
            "intervention": (
                "trend-sleeve-only position lifecycle using a fixed trailing "
                "stop at highest close since entry minus 3x ATR20"
            ),
            "atr_window": ATR_WINDOW,
            "atr_multiple": ATR_MULTIPLE,
            "atr_definition": "simple 20-session true-range average using information available through current close",
            "exit_execution_contract": (
                "close-triggered decision -> next-session open; stopped asset remains flat "
                "until next monthly baseline rebalance; no renormalization of remaining trend weights"
            ),
            "trend_rebalance": "monthly baseline signal",
            "trend_volatility_weighting_window": TREND_VOL_WINDOW,
            "trend_asset_weight_cap": MAX_ASSET_WEIGHT,
            "risk_budget_window": VOL_WINDOW,
            "target_annualized_volatility": TARGET_VOL,
            "point_in_time": "close decision -> next open execution; following open-to-open return",
            "costs": {
                "fee_rate": FEE_RATE,
                "slippage_rate": SLIPPAGE_RATE,
                "scenarios": ["base", "1.5x", "2x"],
            },
            "optimization_used": False,
            "selection_used": False,
            "holdout_used_for_selection": False,
            "parameter_search": False,
            "variant_search": False,
            "shorting": False,
            "leverage_above_one": False,
            "orders_enabled": False,
        },
        "lifecycle_diagnostics": lifecycle,
        "scenarios": scenarios,
        "gate_contract": gates,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }

    report["report_fingerprint"] = _fp(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = run_validation(
        Path(args.data_dir),
        Path(args.manifest),
        Path(args.output),
    )
    print("TRIAL_045_STATUS:", result["status"])
    print("TRIAL_045_CANDIDATE_STATUS:", result["candidate_status"])
    print("TRIAL_045_REPORT_FINGERPRINT:", result["report_fingerprint"])
    print(
        "TRIAL_045_CHECKS:",
        json.dumps(result["gate_contract"], sort_keys=True),
    )
