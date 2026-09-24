"""Seventh validation: fixed multi-strategy complementarity control.

Research-only. No optimization, selection, production mutation or orders.
The control compares fixed trend-only, fixed cross-sectional-only and a fixed
50/50 blend on a new fully symbol-disjoint validation set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from automation.candidate_validation_50_50_vol_budget import (
    COST_SCENARIOS,
    FEE_RATE,
    HOLDOUT_COUNT,
    RESEARCH_COUNT,
    SLIPPAGE_RATE,
    TARGET_VOL,
    VOL_WINDOW,
    _build_weight_path,
    _cs_weights,
    _pf,
    _return_rows,
    _simulate,
    _stats,
    _summary,
    _yahoo_adjclose,
    load_bars,
)
from config import settings
from research.asset_universes import get_universe, list_universes
from research.protocol import dataset_fingerprint

TREND_UNIVERSE = "validation_2026_09_24_seventh_trend"
CS_UNIVERSE = "validation_2026_09_24_seventh_cs"
TARGET_COUNT = 3500
EXPECTED_COMMON_RETURNS = 3498


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _manifest(path: Path, universe_name: str) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    universe = get_universe(universe_name)
    symbols = tuple(item["symbol"] for item in data.get("datasets", []))
    if data.get("universe") != universe_name or symbols != universe.symbols:
        raise ValueError(f"Manifest passt nicht zu {universe_name}.")
    if data.get("target_count") != TARGET_COUNT or data.get("source") != "yahoo_chart":
        raise ValueError(f"Unerwartete Datenbasis für {universe_name}.")
    safety = data.get("safety", {})
    if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False:
        raise RuntimeError("Manifest-Sicherheitsvertrag verletzt.")
    return data


def _assets(data_dir: Path, manifest: dict) -> dict[str, tuple]:
    out = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        bars = load_bars(data_dir / symbol / "1d.csv", expected_count=int(item["candle_count"]))
        if len(bars) != TARGET_COUNT or dataset_fingerprint(bars) != item["fingerprint"]:
            raise ValueError(f"{symbol}: Dataset-Identität/Fingerprint nicht verifiziert.")
        out[symbol] = bars
    common = set.intersection(*[{bar.timestamp for bar in bars} for bars in out.values()])
    if len(common) != TARGET_COUNT:
        raise ValueError(f"Erwarte exakt {TARGET_COUNT} gemeinsame Candles, erhalten: {len(common)}")
    ordered = sorted(common)
    return {symbol: tuple({bar.timestamp: bar for bar in bars}[ts] for ts in ordered) for symbol, bars in out.items()}


def _blend_rows(trend_rows: dict, cs_rows: dict) -> tuple[dict, ...]:
    common = sorted(set(trend_rows) & set(cs_rows))
    return tuple(
        {
            "timestamp": ts,
            "gross_open": 0.5 * trend_rows[ts]["gross_open"] + 0.5 * cs_rows[ts]["gross_open"],
            "gross_close": 0.5 * trend_rows[ts]["gross_close"] + 0.5 * cs_rows[ts]["gross_close"],
            "gross_adjusted_close": 0.5 * trend_rows[ts]["gross_adjusted_close"] + 0.5 * cs_rows[ts]["gross_adjusted_close"],
            "turnover": 0.5 * trend_rows[ts]["turnover"] + 0.5 * cs_rows[ts]["turnover"],
        }
        for ts in common
    )


def _families(rows_by_family: dict[str, tuple[dict, ...]], multiplier: float) -> dict:
    result = {}
    for family, rows in rows_by_family.items():
        simulated_price = _simulate(list(rows), multiplier, True, False)
        simulated_total = _simulate(list(rows), multiplier, True, True)
        research = _stats(simulated_price, 0, RESEARCH_COUNT)
        holdout = _stats(simulated_price, RESEARCH_COUNT, RESEARCH_COUNT + HOLDOUT_COUNT)
        rolling = _rolling_summary(simulated_price)
        result[family] = {
            "research": research,
            "holdout": holdout,
            "rolling_summary": rolling,
            "total_return_sensitivity": {
                "research": _stats(simulated_total, 0, RESEARCH_COUNT),
                "holdout": _stats(simulated_total, RESEARCH_COUNT, RESEARCH_COUNT + HOLDOUT_COUNT),
            },
        }
    return result


def _rolling_summary(rows: list[dict]) -> dict:
    width = RESEARCH_COUNT // 5
    windows = []
    start = 0
    for index in range(5):
        end = RESEARCH_COUNT if index == 4 else start + width
        windows.append({"window_index": index + 1, **_stats(rows, start, end)})
        start = end
    summary = _summary(rows[:RESEARCH_COUNT], windows)
    return {
        "window_count": len(windows),
        "profitable_windows": summary["profitable_windows"],
        "profitable_window_ratio": summary["profitable_window_ratio"],
        "total_net_return": summary["total_net_return"],
        "overall_profit_factor": summary["overall_profit_factor"],
        "average_drawdown_percent": summary["average_drawdown_percent"],
        "windows": windows,
    }


def _complementarity_diagnostics(families: dict[str, dict]) -> dict:
    trend = families["trend"]
    cs = families["cross_sectional"]
    blend = families["blend_50_50"]
    return {
        "research_drawdown_not_worse_than_both": (
            blend["research"]["max_drawdown_percent"]
            <= min(trend["research"]["max_drawdown_percent"], cs["research"]["max_drawdown_percent"])
        ),
        "research_rolling_pf_not_worse_than_both": (
            _pf(blend["rolling_summary"]["overall_profit_factor"])
            >= max(_pf(trend["rolling_summary"]["overall_profit_factor"]), _pf(cs["rolling_summary"]["overall_profit_factor"]))
        ),
        "holdout_drawdown_not_worse_than_both": (
            blend["holdout"]["max_drawdown_percent"]
            <= min(trend["holdout"]["max_drawdown_percent"], cs["holdout"]["max_drawdown_percent"])
        ),
        "holdout_pf_not_worse_than_both": (
            _pf(blend["holdout"]["profit_factor"])
            >= max(_pf(trend["holdout"]["profit_factor"]), _pf(cs["holdout"]["profit_factor"]))
        ),
        "blend_positive_research": blend["research"]["period_return"] > 0.0,
        "blend_positive_holdout": blend["holdout"]["period_return"] > 0.0,
    }


def run_validation(trend_dir: Path, trend_manifest_path: Path, cs_dir: Path, cs_manifest_path: Path, output_path: Path) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only Sicherheitsvertrag verletzt.")
    trend_manifest = _manifest(trend_manifest_path, TREND_UNIVERSE)
    cs_manifest = _manifest(cs_manifest_path, CS_UNIVERSE)

    trend_universe = set(get_universe(TREND_UNIVERSE).symbols)
    cs_universe = set(get_universe(CS_UNIVERSE).symbols)
    assert trend_universe.isdisjoint(cs_universe)
    combined = trend_universe | cs_universe
    for universe in list_universes():
        if universe.name in {TREND_UNIVERSE, CS_UNIVERSE}:
            continue
        if combined & set(universe.symbols):
            raise ValueError(f"Symbol overlap with {universe.name}")

    trend = _assets(trend_dir, trend_manifest)
    cs = _assets(cs_dir, cs_manifest)
    common = set.intersection(*[{bar.timestamp for bar in bars} for bars in {**trend, **cs}.values()])
    if len(common) != TARGET_COUNT:
        raise ValueError(f"Erwarte exakt {TARGET_COUNT} gemeinsame Candles, erhalten: {len(common)}")

    trend_weights = _build_weight_path(trend, "sma_50_200_inverse_vol")
    cs_weights = _cs_weights(cs)
    all_assets = {**trend, **cs}
    adjusted = {symbol: _yahoo_adjclose(symbol, bars[0].timestamp, bars[-1].timestamp) for symbol, bars in all_assets.items()}

    trend_rows = {row["timestamp"]: row for row in _return_rows(trend, trend_weights, {s: adjusted[s] for s in trend})}
    cs_rows = {row["timestamp"]: row for row in _return_rows(cs, cs_weights, {s: adjusted[s] for s in cs})}
    if set(trend_rows) != set(cs_rows):
        raise ValueError("Trend- und Cross-Sectional-Returnkalender sind nicht identisch.")
    rows_by_family = {
        "trend": tuple(trend_rows.values()),
        "cross_sectional": tuple(cs_rows.values()),
        "blend_50_50": _blend_rows(trend_rows, cs_rows),
    }
    scenarios = {name: _families(rows_by_family, multiplier) for name, multiplier in COST_SCENARIOS}
    base = scenarios["base"]
    report = {
        "schema_version": 1,
        "diagnostic_type": "seventh_multi_strategy_complementarity_validation",
        "status": "COMPLETED",
        "source": {
            "trend_universe": TREND_UNIVERSE,
            "trend_symbols": list(get_universe(TREND_UNIVERSE).symbols),
            "trend_manifest_fingerprint": trend_manifest["manifest_fingerprint"],
            "cs_universe": CS_UNIVERSE,
            "cs_symbols": list(get_universe(CS_UNIVERSE).symbols),
            "cs_manifest_fingerprint": cs_manifest["manifest_fingerprint"],
            "raw_candle_count_per_asset": TARGET_COUNT,
            "common_candle_count": TARGET_COUNT,
            "common_return_count": EXPECTED_COMMON_RETURNS,
            "research_return_count": RESEARCH_COUNT,
            "holdout_return_count": HOLDOUT_COUNT,
            "fully_symbol_disjoint_validation_set": True,
        },
        "methodology": {
            "trend_strategy": "sma_50_200_inverse_vol",
            "cross_sectional_strategy": "12-1 top-2 long-only",
            "portfolio_variants": ["trend", "cross_sectional", "blend_50_50"],
            "vol_budget_target_annualized": TARGET_VOL,
            "vol_budget_window_sessions": VOL_WINDOW,
            "execution_model": "close(t) decision -> next-session open -> following-open return",
            "cost_scenarios": [name for name, _ in COST_SCENARIOS],
            "optimization_used": False,
            "selection_used": False,
            "holdout_used_for_selection": False,
            "orders_enabled": False,
        },
        "scenarios": scenarios,
        "complementarity_diagnostics": _complementarity_diagnostics(base),
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False},
    }
    report["report_fingerprint"] = _fp(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trend-data-dir", required=True)
    parser.add_argument("--trend-manifest", required=True)
    parser.add_argument("--cs-data-dir", required=True)
    parser.add_argument("--cs-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run_validation(Path(args.trend_data_dir), Path(args.trend_manifest), Path(args.cs_data_dir), Path(args.cs_manifest), Path(args.output))
    print("COMPLEMENTARITY_STATUS: COMPLETED")
    print("REPORT_FINGERPRINT:", report["report_fingerprint"])
    print("COMPLEMENTARITY_DIAGNOSTICS:", report["complementarity_diagnostics"])


if __name__ == "__main__":
    main()
