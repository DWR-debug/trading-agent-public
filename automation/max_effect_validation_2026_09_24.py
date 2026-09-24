"""Pre-registered Trial 023: monthly low-MAX cross-sectional control.

Research-only. No optimization, selection, leverage, shorting, or production mutation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from backtesting.models import Candle
from config import settings
from data.market_store import MarketDataStore
from execution.cost_contract import ResearchExecutionCostContract, validate_research_cost_compatibility
from research.fixed_max_effect import daily_close_returns, low_max_assets, previous_month_max

TRIAL_ID = "T-2026-09-24-023"
UNIVERSE = "validation_2026_09_24_max_effect_us_stocks"
SYMBOLS = ("ORCL", "CSCO", "TXN", "ADP", "UPS", "ABT", "GILD", "AMGN")
TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700
SELECT_COUNT = 4
COST_CONTRACT = ResearchExecutionCostContract()
BASE_COST = COST_CONTRACT.total_one_way_bps / 10_000.0


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


def _load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("universe") != UNIVERSE:
        raise ValueError("Unexpected Trial 023 universe.")
    if manifest.get("target_count") != TARGET_COUNT:
        raise ValueError("Unexpected Trial 023 target count.")
    datasets = manifest.get("datasets") or []
    if tuple(item["symbol"] for item in datasets) != SYMBOLS:
        raise ValueError("Manifest symbols do not match Trial 023 preregistration.")
    if not all(item["candle_count"] == TARGET_COUNT for item in datasets):
        raise ValueError("Not every Trial 023 asset has the target candle count.")
    alignment = manifest.get("calendar_alignment", {})
    if alignment.get("mode") != "timestamp_intersection_tail":
        raise ValueError("Trial 023 requires timestamp-intersection alignment.")
    if alignment.get("aligned_candle_count") != TARGET_COUNT:
        raise ValueError("Trial 023 common calendar length is not 3500.")
    safety = manifest.get("safety", {})
    if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False:
        raise ValueError("Trial 023 paper-only safety contract missing.")
    return manifest


def _load_assets(data_dir: Path, manifest: dict) -> dict[str, list[Candle]]:
    assets: dict[str, list[Candle]] = {}
    store = MarketDataStore(data_dir)
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        candles = store.load(symbol, "1d")
        if len(candles) != TARGET_COUNT:
            raise ValueError(f"{symbol}: expected {TARGET_COUNT} candles.")
        assets[symbol] = list(candles)

    common = set(c.timestamp for c in assets[SYMBOLS[0]])
    for symbol in SYMBOLS[1:]:
        common &= {c.timestamp for c in assets[symbol]}
    common_tail = sorted(common)[-TARGET_COUNT:]
    if len(common_tail) != TARGET_COUNT:
        raise ValueError("Trial 023 common timestamp intersection is too short.")

    for symbol in SYMBOLS:
        by_ts = {c.timestamp: c for c in assets[symbol]}
        assets[symbol] = [by_ts[ts] for ts in common_tail]
    return assets


def _selections(
    timestamps: list,
    returns_by_symbol: dict[str, tuple[float, ...]],
) -> dict[tuple[int, int], tuple[tuple[str, ...], tuple[str, ...]]]:
    max_by_symbol = {
        symbol: previous_month_max(timestamps, returns_by_symbol[symbol])
        for symbol in SYMBOLS
    }
    selections: dict[tuple[int, int], tuple[tuple[str, ...], tuple[str, ...]]] = {}
    months = sorted({_month_key(ts) for ts in timestamps})
    for month in months:
        values = {
            symbol: max_by_symbol[symbol][month]
            for symbol in SYMBOLS
            if month in max_by_symbol[symbol]
        }
        if len(values) != len(SYMBOLS):
            continue
        low = low_max_assets(SYMBOLS, values, select_count=SELECT_COUNT)
        high = tuple(
            symbol
            for symbol, _value in sorted(
                ((symbol, values[symbol]) for symbol in SYMBOLS),
                key=lambda item: (-item[1], item[0]),
            )[:SELECT_COUNT]
        )
        selections[month] = (low, high)
    return selections


def _month_key(timestamp) -> tuple[int, int]:
    return timestamp.year, timestamp.month


def _portfolio_returns(
    assets: dict[str, list[Candle]],
    *,
    cost_multiplier: float,
) -> tuple[list[float], list[float | None], int, float]:
    timestamps = [c.timestamp for c in assets[SYMBOLS[0]]]
    returns_by_symbol = {
        symbol: daily_close_returns([c.close for c in assets[symbol]])
        for symbol in SYMBOLS
    }
    selections = _selections(timestamps, returns_by_symbol)

    portfolio_returns: list[float] = []
    edge_by_row: list[float | None] = []
    previous_target = {symbol: 0.0 for symbol in SYMBOLS}
    turnover_total = 0.0

    for row in range(TARGET_COUNT - 2):
        month = _month_key(timestamps[row])
        selected = selections.get(month)
        if selected is None:
            target = {symbol: 0.0 for symbol in SYMBOLS}
            edge_by_row.append(None)
        else:
            low_assets, high_assets = selected
            target = {
                symbol: (1.0 / SELECT_COUNT if symbol in low_assets else 0.0)
                for symbol in SYMBOLS
            }
            realized = {
                symbol: (
                    assets[symbol][row + 2].close
                    / assets[symbol][row + 1].close
                    - 1.0
                )
                for symbol in SYMBOLS
            }
            low_return = sum(realized[symbol] for symbol in low_assets) / SELECT_COUNT
            high_return = sum(realized[symbol] for symbol in high_assets) / SELECT_COUNT
            edge_by_row.append(low_return - high_return)

        realized = {
            symbol: (
                assets[symbol][row + 2].close
                / assets[symbol][row + 1].close
                - 1.0
            )
            for symbol in SYMBOLS
        }
        turnover = sum(
            abs(target[symbol] - previous_target[symbol])
            for symbol in SYMBOLS
        )
        turnover_total += turnover
        gross_return = sum(target[symbol] * realized[symbol] for symbol in SYMBOLS)
        portfolio_returns.append(
            gross_return - BASE_COST * cost_multiplier * turnover
        )
        previous_target = target

    return portfolio_returns, edge_by_row, len(selections), turnover_total


def _metrics(values: list[float], split: int) -> dict:
    def segment(series: list[float]) -> dict:
        equity = 1.0
        peak = 1.0
        max_dd = 0.0
        gains = 0.0
        losses = 0.0
        for value in series:
            if not -1.0 < value:
                raise ValueError("Return at or below -100% is invalid.")
            equity *= 1.0 + value
            peak = max(peak, equity)
            max_dd = max(max_dd, 1.0 - equity / peak)
            if value > 0.0:
                gains += value
            elif value < 0.0:
                losses += -value
        return {
            "return": equity - 1.0,
            "max_drawdown_percent": max_dd * 100.0,
            "profit_factor": gains / losses if losses else None,
            "count": len(series),
        }

    boundaries = [round(i * split / 5) for i in range(6)]
    rolling = [
        segment(values[boundaries[i] : boundaries[i + 1]])
        for i in range(5)
    ]
    research = segment(values[:split])
    holdout = segment(values[split : split + HOLDOUT_COUNT])
    oos = holdout["return"] / research["return"] if research["return"] > 0 else 0.0
    return {
        "research": research,
        "holdout": {**holdout, "oos_to_research_return_ratio": oos},
        "rolling_research": rolling,
        "rolling_profitable_window_ratio": sum(
            item["return"] > 0 for item in rolling
        ) / len(rolling),
    }


def _edge_metrics(edge_by_row: list[float | None], split: int) -> dict:
    if len(edge_by_row) != TARGET_COUNT - 2:
        raise ValueError("MAX edge series length must equal the 3498 PIT return rows.")

    research_values = [
        value for value in edge_by_row[:split] if value is not None
    ]
    holdout_values = [
        value for value in edge_by_row[split : split + HOLDOUT_COUNT]
        if value is not None
    ]
    if not research_values or not holdout_values:
        raise ValueError("MAX edge has no observations in one of the required splits.")

    return {
        "research_mean_low_minus_high_daily_return": sum(research_values) / len(research_values),
        "holdout_mean_low_minus_high_daily_return": sum(holdout_values) / len(holdout_values),
        "research_edge_observation_count": len(research_values),
        "holdout_edge_observation_count": len(holdout_values),
    }


def run(data_dir: Path, manifest_path: Path, output_path: Path) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")
    COST_CONTRACT.validate()
    validate_research_cost_compatibility(
        fee_rate=COST_CONTRACT.fee_bps / 10_000.0,
        slippage_rate=COST_CONTRACT.slippage_bps / 10_000.0,
        contract=COST_CONTRACT,
    )

    manifest = _load_manifest(manifest_path)
    assets = _load_assets(data_dir, manifest)

    scenarios: dict[str, dict] = {}
    edge_by_row: list[float | None] = []
    selection_month_count = 0
    turnover_base = 0.0

    for name, multiplier in (
        ("base", 1.0),
        ("stress_1_5x_cost", 1.5),
        ("stress_2x_cost", 2.0),
    ):
        values, current_edge, selections, turnover = _portfolio_returns(
            assets,
            cost_multiplier=multiplier,
        )
        if not edge_by_row:
            edge_by_row = current_edge
            selection_month_count = selections
            turnover_base = turnover
        elif current_edge != edge_by_row or selections != selection_month_count:
            raise ValueError("Signal path changed between cost scenarios.")
        scenarios[name] = _metrics(values, RESEARCH_COUNT)

    edge = _edge_metrics(edge_by_row, RESEARCH_COUNT)
    checks = {
        "research_return_positive": scenarios["base"]["research"]["return"] > 0.0,
        "research_drawdown": scenarios["base"]["research"]["max_drawdown_percent"] <= 10.0,
        "research_profit_factor": (
            scenarios["base"]["research"]["profit_factor"] is not None
            and scenarios["base"]["research"]["profit_factor"] >= 1.10
        ),
        "rolling_profitable_window_ratio": scenarios["base"]["rolling_profitable_window_ratio"] >= 0.50,
        "oos_to_is_return_ratio": scenarios["base"]["holdout"]["oos_to_research_return_ratio"] >= 0.25,
        "holdout_return_positive": scenarios["base"]["holdout"]["return"] > 0.0,
        "holdout_drawdown": scenarios["base"]["holdout"]["max_drawdown_percent"] <= 10.0,
        "holdout_profit_factor": (
            scenarios["base"]["holdout"]["profit_factor"] is not None
            and scenarios["base"]["holdout"]["profit_factor"] >= 1.10
        ),
        "stress_1_5x_nonnegative": scenarios["stress_1_5x_cost"]["holdout"]["return"] >= 0.0,
        "stress_2x_nonnegative": scenarios["stress_2x_cost"]["holdout"]["return"] >= 0.0,
        "research_max_effect_edge_positive": edge["research_mean_low_minus_high_daily_return"] > 0.0,
        "holdout_max_effect_edge_positive": edge["holdout_mean_low_minus_high_daily_return"] > 0.0,
    }
    decision = "VALIDATED_PASS" if all(checks.values()) else "NO_SUPPORT"

    report = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "status": "COMPLETED",
        "research_only": True,
        "code_version": os.getenv("GITHUB_SHA") or "UNVERIFIED_LOCAL_CODE",
        "preregistration": {
            "document": "docs/trial_023_max_effect_preregistration_2026_09_24.md",
            "strategy_variants": 1,
            "selection_after_results": False,
            "parameter_search": False,
            "threshold_search": False,
            "holdout_selection": False,
        },
        "source": {
            "universe": UNIVERSE,
            "symbols": list(SYMBOLS),
            "target_candles": TARGET_COUNT,
            "common_returns": TARGET_COUNT - 2,
            "research_count": RESEARCH_COUNT,
            "holdout_count": HOLDOUT_COUNT,
            "fully_symbol_disjoint": True,
            "manifest_fingerprint": manifest["manifest_fingerprint"],
        },
        "methodology": {
            "signal": "maximum daily close-to-close return within the immediately preceding completed calendar month",
            "direction": "long four lowest-MAX assets",
            "select_count": SELECT_COUNT,
            "portfolio_gross_exposure": 1.0,
            "rebalance": "calendar-month transition",
            "execution": "decision timestamp t -> realized close-to-close return t+1 to t+2",
            "fee_bps": COST_CONTRACT.fee_bps,
            "slippage_bps": COST_CONTRACT.slippage_bps,
            "cost_stress_multipliers": [1.5, 2.0],
            "leverage": 1.0,
            "shorting": False,
        },
        "edge_measure": edge,
        "selection_month_count": selection_month_count,
        "base_total_turnover": turnover_base,
        "scenarios": scenarios,
        "decision": {
            "checks": checks,
            "all_checks_passed": all(checks.values()),
            "result": decision,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    report["report_fingerprint"] = _fp(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run(Path(args.data_dir), Path(args.manifest), Path(args.output))
    print("MAX_EFFECT_STATUS:", report["status"])
    print("MAX_EFFECT_DECISION:", json.dumps(report["decision"], sort_keys=True))
    print("MAX_EFFECT_REPORT_FINGERPRINT:", report["report_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
