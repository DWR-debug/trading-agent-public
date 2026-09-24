"""Research-only validation of the fixed four-day Turn-of-Month alpha."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

from config import settings
from research.asset_universes import get_universe
from research.protocol import dataset_fingerprint

TARGET_UNIVERSE = "validation_2026_09_24_turn_of_month"
TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700
ASSETS = ("EWS", "EWM", "EZA", "ECH", "EPU", "EIDO", "THD", "EPHE")
FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    universe = get_universe(TARGET_UNIVERSE)
    symbols = tuple(item["symbol"] for item in manifest.get("datasets", []))
    if (
        manifest.get("universe") != TARGET_UNIVERSE
        or manifest.get("target_count") != TARGET_COUNT
        or symbols != ASSETS
        or manifest.get("source") != "yahoo_chart"
    ):
        raise ValueError("Turn-of-Month market manifest contract mismatch.")
    safety = manifest.get("safety", {})
    if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False:
        raise RuntimeError("Manifest safety contract violated.")
    if tuple(universe.symbols) != ASSETS:
        raise ValueError("Turn-of-Month universe registration mismatch.")
    return manifest


def _load_assets(data_dir: Path, manifest: dict) -> dict[str, tuple]:
    from automation.candidate_validation_50_50_vol_budget import load_bars

    assets = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        bars = load_bars(data_dir / symbol / "1d.csv", expected_count=int(item["candle_count"]))
        if len(bars) != TARGET_COUNT or dataset_fingerprint(bars) != item["fingerprint"]:
            raise ValueError(f"{symbol}: market dataset fingerprint mismatch.")
        assets[symbol] = tuple(bars)

    timestamps = [tuple(bar.timestamp for bar in bars) for bars in assets.values()]
    if any(values != timestamps[0] for values in timestamps[1:]):
        raise ValueError("Turn-of-Month assets must share an identical timestamp calendar.")
    return assets


def _tom_days(days: tuple[date, ...]) -> set[date]:
    flags: set[date] = set()
    months: dict[tuple[int, int], list[date]] = {}
    for day in days:
        months.setdefault((day.year, day.month), []).append(day)
    for month_days in months.values():
        flags.update(month_days[:3])
        flags.add(month_days[-1])
    return flags


def _return_rows(assets: dict[str, tuple]) -> tuple[dict, ...]:
    reference = next(iter(assets.values()))
    days = tuple(bar.timestamp.astimezone(timezone.utc).date() for bar in reference)
    active_days = _tom_days(days)
    rows = []
    previous_weight = 0.0

    for index in range(2, TARGET_COUNT):
        target_day = reference[index].timestamp.astimezone(timezone.utc).date()
        gross = sum(
            bars[index].close / bars[index - 1].close - 1.0
            for bars in assets.values()
        ) / len(assets)
        weight = 1.0 if target_day in active_days else 0.0
        turnover = abs(weight - previous_weight)
        rows.append(
            {
                "timestamp": reference[index].timestamp.isoformat(),
                "previous_timestamp": reference[index - 1].timestamp.isoformat(),
                "target_day": target_day.isoformat(),
                "tom_active": weight > 0.0,
                "basket_gross_return": gross,
                "strategy_gross_return": weight * gross,
                "turnover": turnover,
            }
        )
        previous_weight = weight

    if len(rows) != RESEARCH_COUNT + HOLDOUT_COUNT:
        raise ValueError(f"Unexpected return count: {len(rows)}")
    return tuple(rows)


def _simulate(rows: tuple[dict, ...], cost_multiplier: float) -> list[dict]:
    cost_rate = (FEE_RATE + SLIPPAGE_RATE) * cost_multiplier
    output = []
    for row in rows:
        item = dict(row)
        item["net_return"] = float(row["strategy_gross_return"]) - cost_rate * float(row["turnover"])
        output.append(item)
    return output


def _stats(rows: list[dict]) -> dict:
    equity = peak = 1.0
    gp = gl = 0.0
    max_dd = 0.0
    tom_values: list[float] = []
    non_tom_values: list[float] = []
    turnover = 0.0

    for row in rows:
        value = float(row["net_return"])
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = max(max_dd, 1.0 - equity / peak)
        if value > 0.0:
            gp += value
        elif value < 0.0:
            gl -= value
        turnover += float(row["turnover"])
        (tom_values if row["tom_active"] else non_tom_values).append(
            float(row["basket_gross_return"])
        )

    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": gp / gl if gl > 0.0 else ("inf" if gp > 0.0 else 0.0),
        "day_count": len(rows),
        "turnover": turnover,
        "tom_day_count": len(tom_values),
        "non_tom_day_count": len(non_tom_values),
        "tom_mean_gross_daily_return": sum(tom_values) / len(tom_values) if tom_values else None,
        "non_tom_mean_gross_daily_return": sum(non_tom_values) / len(non_tom_values) if non_tom_values else None,
        "tom_minus_non_tom_mean_daily_return": (
            sum(tom_values) / len(tom_values) - sum(non_tom_values) / len(non_tom_values)
            if tom_values and non_tom_values else None
        ),
    }


def _rolling(rows: list[dict]) -> list[dict]:
    width = RESEARCH_COUNT // 5
    windows = []
    start = 0
    for index in range(5):
        end = RESEARCH_COUNT if index == 4 else start + width
        windows.append({"window_index": index + 1, **_stats(rows[start:end])})
        start = end
    return windows


def _rolling_summary(windows: list[dict]) -> dict:
    profitable = sum(item["period_return"] > 0.0 for item in windows)
    return {
        "window_count": len(windows),
        "profitable_windows": profitable,
        "profitable_window_ratio": profitable / len(windows),
        "total_window_return": sum(item["period_return"] for item in windows),
        "average_drawdown_percent": sum(item["max_drawdown_percent"] for item in windows) / len(windows),
    }


def _scenario(rows: tuple[dict, ...], multiplier: float) -> dict:
    simulated = _simulate(rows, multiplier)
    research = _stats(simulated[:RESEARCH_COUNT])
    holdout = _stats(simulated[RESEARCH_COUNT:])
    rolling = _rolling(simulated)
    return {
        "research": research,
        "holdout": holdout,
        "rolling_windows": rolling,
        "rolling_summary": _rolling_summary(rolling),
        "oos_to_is_return_ratio": (
            holdout["period_return"] / research["period_return"]
            if research["period_return"] > 0.0 else 0.0
        ),
    }


def _pf_value(value: float | str) -> float:
    return float("inf") if value == "inf" else float(value)


def run_validation(*, data_dir: Path, market_manifest: Path, output: Path) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")

    manifest = _load_manifest(market_manifest)
    assets = _load_assets(data_dir, manifest)
    rows = _return_rows(assets)

    scenarios = {
        "base": _scenario(rows, 1.0),
        "stress_1_5x_cost": _scenario(rows, 1.5),
        "stress_2x_cost": _scenario(rows, 2.0),
    }

    base = scenarios["base"]
    checks = {
        "research_tom_mean_gt_non_tom": base["research"]["tom_mean_gross_daily_return"] > base["research"]["non_tom_mean_gross_daily_return"],
        "holdout_tom_mean_gt_non_tom": base["holdout"]["tom_mean_gross_daily_return"] > base["holdout"]["non_tom_mean_gross_daily_return"],
        "research_drawdown": base["research"]["max_drawdown_percent"] <= 10.0,
        "research_profit_factor": _pf_value(base["research"]["profit_factor"]) >= 1.10,
        "rolling_profitable_window_ratio": base["rolling_summary"]["profitable_window_ratio"] >= 0.50,
        "oos_to_is_return_ratio": base["oos_to_is_return_ratio"] >= 0.25,
        "holdout_return_positive": base["holdout"]["period_return"] > 0.0,
        "holdout_profit_factor": _pf_value(base["holdout"]["profit_factor"]) >= 1.10,
        "holdout_drawdown": base["holdout"]["max_drawdown_percent"] <= 10.0,
        "stress_1_5x_nonnegative": scenarios["stress_1_5x_cost"]["holdout"]["period_return"] >= 0.0,
        "stress_2x_nonnegative": scenarios["stress_2x_cost"]["holdout"]["period_return"] >= 0.0,
    }

    report = {
        "schema_version": 1,
        "trial_id": "T-2026-09-24-017",
        "status": "COMPLETED",
        "research_only": True,
        "selection_used": False,
        "parameter_search_used": False,
        "data_scope": {
            "market_assets": list(ASSETS),
            "market_candles_per_asset": TARGET_COUNT,
            "market_manifest_fingerprint": manifest["manifest_fingerprint"],
            "research_return_count": RESEARCH_COUNT,
            "holdout_return_count": HOLDOUT_COUNT,
            "fully_symbol_disjoint_validation_set": True,
        },
        "policy": {
            "window": "last trading day of month + first three trading days of following month",
            "weights": {symbol: 1.0 / len(ASSETS) for symbol in ASSETS},
            "gross_exposure": 1.0,
            "net_exposure": 1.0,
            "price_field": "unadjusted close",
        },
        "methodology": {
            "execution": "previous_close -> target_close",
            "cost_scenarios": ["base", "stress_1_5x_cost", "stress_2x_cost"],
            "holdout_used_for_selection": False,
            "strategy_variants": 1,
            "parameter_search": False,
            "tom_window_definition": "target_day is one of the first three or the last trading day of its calendar month",
        },
        "scenarios": scenarios,
        "decision": {"checks": checks, "all_checks_passed": all(checks.values())},
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False},
    }
    report["report_fingerprint"] = _fp(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--market-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run_validation(
        data_dir=Path(args.data_dir),
        market_manifest=Path(args.market_manifest),
        output=Path(args.output),
    )
    print("TURN_OF_MONTH_STATUS:", report["status"])
    print("TURN_OF_MONTH_DECISION:", json.dumps(report["decision"], sort_keys=True))
    print("TURN_OF_MONTH_SCENARIOS:", json.dumps(report["scenarios"], sort_keys=True))
    print("TURN_OF_MONTH_REPORT_FINGERPRINT:", report["report_fingerprint"])


if __name__ == "__main__":
    main()
