"""Trial 029: fixed inverse-volatility parity between the two sleeves.

Research-only. Existing Trend and Cross-Sectional signals remain unchanged.
Only the capital allocation between the two sleeves changes from fixed 50/50
to monthly inverse-volatility parity based on the preceding 63 completed returns.

No optimization, selection, threshold search, leverage or orders.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
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

TRIAL_ID = "T-2026-09-24-030"
UNIVERSE = "validation_2026_09_24_sleeve_volatility_parity_confirmation"
TREND_SYMBOLS = ("IWB", "IEFA", "BIV", "BSV", "VGIT", "JNK", "HDV", "DBE")
CS_SYMBOLS = ("IYF", "IYE", "IYG", "DJP", "EPHE")
PORTFOLIO_SYMBOLS = TREND_SYMBOLS + CS_SYMBOLS

TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700
SLEEVE_VOL_WINDOW = 63
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
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode()).hexdigest()


def _pf(value: float | str) -> float:
    return float("inf") if value == "inf" else float(value)


def _load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    universe = get_universe(UNIVERSE)
    actual = tuple(item["symbol"] for item in manifest.get("datasets", []))
    if manifest.get("universe") != UNIVERSE:
        raise ValueError("Manifest passt nicht zum Trial-029-Universum.")
    if actual != tuple(universe.symbols):
        raise ValueError("Trial-029-Symbole weichen vom Präregister ab.")
    if manifest.get("target_count") != TARGET_COUNT or manifest.get("source") != "yahoo_chart":
        raise ValueError("Unerwartete Trial-029-Datenbasis.")
    safety = manifest.get("safety", {})
    if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False or safety.get("orders_enabled") is not False:
        raise RuntimeError("Paper-only-Sicherheitsvertrag verletzt.")
    return manifest


def _load_assets(data_dir: Path, manifest: dict) -> dict[str, tuple]:
    assets = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        bars = load_bars(data_dir / symbol / "1d.csv", expected_count=int(item["candle_count"]))
        if len(bars) != TARGET_COUNT or dataset_fingerprint(bars) != item["fingerprint"]:
            raise ValueError(f"{symbol}: Dataset-Identität/Fingerprint stimmt nicht.")
        assets[symbol] = bars
    if set(assets) != set(PORTFOLIO_SYMBOLS):
        raise ValueError("Trial-029-Symbolmenge stimmt nicht.")
    common = set.intersection(*[{bar.timestamp for bar in bars} for bars in assets.values()])
    if len(common) < TARGET_COUNT:
        raise ValueError(f"Zu wenig gemeinsame Candles: {len(common)}.")
    selected = sorted(common)[-TARGET_COUNT:]
    return {
        symbol: tuple({bar.timestamp: bar for bar in bars}[ts] for ts in selected)
        for symbol, bars in assets.items()
    }


def _vol(values: list[float]) -> float | None:
    if len(values) < SLEEVE_VOL_WINDOW:
        return None
    sample = values[-SLEEVE_VOL_WINDOW:]
    mean = sum(sample) / len(sample)
    variance = sum((value - mean) ** 2 for value in sample) / len(sample)
    return math.sqrt(variance) * math.sqrt(252.0)


def _sleeve_parity_weights(
    trend_history: list[float], cs_history: list[float]
) -> tuple[float, float]:
    trend_vol = _vol(trend_history)
    cs_vol = _vol(cs_history)
    if trend_vol is None or cs_vol is None or trend_vol <= 0.0 or cs_vol <= 0.0:
        return 0.5, 0.5
    inv_trend = 1.0 / trend_vol
    inv_cs = 1.0 / cs_vol
    total = inv_trend + inv_cs
    return inv_trend / total, inv_cs / total


def _aggregate_sleeves(
    trend_rows: tuple[dict, ...], cs_rows: tuple[dict, ...]
) -> tuple[dict, ...]:
    if len(trend_rows) != len(cs_rows):
        raise ValueError("Sleeve-Return-Längen stimmen nicht.")
    trend_history: list[float] = []
    cs_history: list[float] = []
    trend_weight = 0.5
    rows = []
    for index, (trend_row, cs_row) in enumerate(zip(trend_rows, cs_rows)):
        if trend_row["timestamp"] != cs_row["timestamp"]:
            raise ValueError("Sleeve-Timestamps stimmen nicht.")
        new_month = index > 0 and (
            trend_row["timestamp"].year,
            trend_row["timestamp"].month,
        ) != (
            trend_rows[index - 1]["timestamp"].year,
            trend_rows[index - 1]["timestamp"].month,
        )
        previous_trend = 0.5 if index == 0 else previous_trend_weight
        previous_cs = 1.0 - previous_trend
        if new_month:
            trend_weight, cs_weight = _sleeve_parity_weights(
                trend_history, cs_history
            )
        elif index == 0:
            trend_weight, cs_weight = 0.5, 0.5
        else:
            cs_weight = 1.0 - trend_weight

        allocation_turnover = (
            abs(trend_weight - previous_trend)
            + abs(cs_weight - previous_cs)
        )

        rows.append(
            {
                "timestamp": trend_row["timestamp"],
                "trend_weight": trend_weight,
                "cs_weight": cs_weight,
                "gross_open": (
                    trend_weight * float(trend_row["gross_open"])
                    + cs_weight * float(cs_row["gross_open"])
                ),
                "gross_close": (
                    trend_weight * float(trend_row["gross_close"])
                    + cs_weight * float(cs_row["gross_close"])
                ),
                "gross_adjusted_close": (
                    trend_weight * float(trend_row["gross_adjusted_close"])
                    + cs_weight * float(cs_row["gross_adjusted_close"])
                ),
                "turnover": (
                    trend_weight * float(trend_row["turnover"])
                    + cs_weight * float(cs_row["turnover"])
                    + allocation_turnover
                ),
                "allocation_turnover": allocation_turnover,
            }
        )

        trend_history.append(float(trend_row["gross_open"]))
        cs_history.append(float(cs_row["gross_open"]))
        previous_trend_weight = trend_weight

    return tuple(rows)


def _fixed_rows(
    trend_rows: tuple[dict, ...], cs_rows: tuple[dict, ...]
) -> tuple[dict, ...]:
    return tuple(
        {
            "timestamp": tr["timestamp"],
            "trend_weight": 0.5,
            "cs_weight": 0.5,
            "gross_open": 0.5 * float(tr["gross_open"]) + 0.5 * float(cr["gross_open"]),
            "gross_close": 0.5 * float(tr["gross_close"]) + 0.5 * float(cr["gross_close"]),
            "gross_adjusted_close": 0.5 * float(tr["gross_adjusted_close"]) + 0.5 * float(cr["gross_adjusted_close"]),
            "turnover": 0.5 * float(tr["turnover"]) + 0.5 * float(cr["turnover"]),
            "allocation_turnover": 0.0,
        }
        for tr, cr in zip(trend_rows, cs_rows)
    )


def _portfolio_budget(
    rows: tuple[dict, ...], multiplier: float, total_return: bool
) -> list[dict]:
    history: list[float] = []
    previous_scale = 1.0
    cost_rate = (FEE_RATE + SLIPPAGE_RATE) * multiplier
    output = []
    for row in rows:
        realized_vol = _vol(history)
        scale = 1.0
        if realized_vol is not None and realized_vol > TARGET_VOL:
            scale = min(1.0, TARGET_VOL / realized_vol)
        gross = float(row["gross_open"])
        if total_return:
            gross += float(row["gross_adjusted_close"]) - float(row["gross_close"])
        turnover = scale * float(row["turnover"]) + abs(scale - previous_scale)
        output.append(
            {
                "timestamp": row["timestamp"],
                "net_return": scale * gross - cost_rate * turnover,
                "gross_return": scale * gross,
                "turnover": float(row["turnover"]),
                "scaled_turnover": turnover,
                "scale": scale,
                "trend_weight": row["trend_weight"],
                "cs_weight": row["cs_weight"],
                "allocation_turnover": row["allocation_turnover"],
                "realized_vol_estimate": realized_vol,
            }
        )
        previous_scale = scale
        history.append(gross - (FEE_RATE + SLIPPAGE_RATE) * float(row["turnover"]))
    return output


def _summarize(rows: list[dict]) -> dict:
    research = _stats(rows, 0, RESEARCH_COUNT)
    holdout = _stats(rows, RESEARCH_COUNT, RESEARCH_COUNT + HOLDOUT_COUNT)
    width = RESEARCH_COUNT // 5
    windows = []
    start = 0
    for index in range(5):
        end = RESEARCH_COUNT if index == 4 else start + width
        windows.append({"window_index": index + 1, **_stats(rows, start, end)})
        start = end
    return {
        "research": research,
        "holdout": holdout,
        "rolling_windows": windows,
        "rolling_summary": _summary(rows[:RESEARCH_COUNT], windows),
        "oos_to_is_return_ratio": holdout["period_return"] / research["period_return"] if research["period_return"] > 0.0 else 0.0,
    }


def _weight_summary(rows: tuple[dict, ...]) -> dict:
    research = rows[:RESEARCH_COUNT]
    holdout = rows[RESEARCH_COUNT:]
    def median(values: list[float]) -> float:
        ordered = sorted(values)
        return ordered[len(ordered) // 2]
    return {
        "research_median_trend_weight": median([r["trend_weight"] for r in research]),
        "research_min_trend_weight": min(r["trend_weight"] for r in research),
        "research_max_trend_weight": max(r["trend_weight"] for r in research),
        "holdout_median_trend_weight": median([r["trend_weight"] for r in holdout]),
        "holdout_min_trend_weight": min(r["trend_weight"] for r in holdout),
        "holdout_max_trend_weight": max(r["trend_weight"] for r in holdout),
    }


def _gates(scenarios: dict, config: ResearchGateConfig) -> dict:
    base = scenarios["base"]["parity_candidate"]
    fixed = scenarios["base"]["fixed_candidate"]
    stress15 = scenarios["stress_1_5x_cost"]["parity_candidate"]
    stress2 = scenarios["stress_2x_cost"]["parity_candidate"]
    roll = base["rolling_summary"]
    absolute = {
        "research_return_positive": base["research"]["period_return"] > 0.0,
        "research_drawdown": base["research"]["max_drawdown_percent"] <= config.maximum_drawdown_percent,
        "research_profit_factor": _pf(base["research"]["profit_factor"]) >= config.minimum_profit_factor,
        "rolling_profit_factor": _pf(roll["overall_profit_factor"]) >= config.minimum_profit_factor,
        "rolling_profitable_window_ratio": roll["profitable_window_ratio"] >= config.minimum_profitable_window_ratio,
        "rolling_average_drawdown": roll["average_drawdown_percent"] <= config.maximum_drawdown_percent,
        "oos_to_is_return_ratio": base["oos_to_is_return_ratio"] >= config.minimum_oos_to_is_return_ratio,
        "holdout_return_positive": base["holdout"]["period_return"] > 0.0,
        "holdout_profit_factor": _pf(base["holdout"]["profit_factor"]) >= config.minimum_profit_factor,
        "holdout_drawdown": base["holdout"]["max_drawdown_percent"] <= config.maximum_drawdown_percent,
        "stress_1_5x_nonnegative": stress15["holdout"]["period_return"] >= 0.0,
        "stress_2x_nonnegative": stress2["holdout"]["period_return"] >= 0.0,
        "total_return_sensitivity_nonnegative": scenarios["base"]["total_return_sensitivity"]["holdout"]["period_return"] >= 0.0,
    }
    non_worsening = {
        "research_return_not_below_fixed": base["research"]["period_return"] >= fixed["research"]["period_return"],
        "research_drawdown_not_worse_vs_fixed": base["research"]["max_drawdown_percent"] <= fixed["research"]["max_drawdown_percent"],
        "research_profit_factor_not_below_fixed": _pf(base["research"]["profit_factor"]) >= _pf(fixed["research"]["profit_factor"]),
        "rolling_pf_not_below_fixed": _pf(roll["overall_profit_factor"]) >= _pf(fixed["rolling_summary"]["overall_profit_factor"]),
        "rolling_profitable_ratio_not_below_fixed": roll["profitable_window_ratio"] >= fixed["rolling_summary"]["profitable_window_ratio"],
        "rolling_average_drawdown_not_worse_vs_fixed": roll["average_drawdown_percent"] <= fixed["rolling_summary"]["average_drawdown_percent"],
        "oos_to_is_not_below_fixed": base["oos_to_is_return_ratio"] >= fixed["oos_to_is_return_ratio"],
        "holdout_return_not_below_fixed": base["holdout"]["period_return"] >= fixed["holdout"]["period_return"],
        "holdout_pf_not_below_fixed": _pf(base["holdout"]["profit_factor"]) >= _pf(fixed["holdout"]["profit_factor"]),
        "holdout_drawdown_not_worse_vs_fixed": base["holdout"]["max_drawdown_percent"] <= fixed["holdout"]["max_drawdown_percent"],
    }
    return {
        "absolute": absolute,
        "non_worsening_vs_fixed_candidate": non_worsening,
        "all_absolute_passed": all(absolute.values()),
        "all_non_worsening_passed": all(non_worsening.values()),
        "all_checks_passed": all(absolute.values()) and all(non_worsening.values()),
    }


def run_validation(data_dir: Path, manifest_path: Path, output_path: Path) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only Sicherheitsvertrag verletzt.")
    manifest = _load_manifest(manifest_path)
    expected = set(PORTFOLIO_SYMBOLS)
    for universe in list_universes():
        if universe.name != UNIVERSE and expected.intersection(universe.symbols):
            raise ValueError(f"Symbol-Overlap mit bestehendem Universum: {universe.name}")

    assets = _load_assets(data_dir, manifest)
    adjusted = {
        symbol: _yahoo_adjclose(symbol, bars[0].timestamp, bars[-1].timestamp)
        for symbol, bars in assets.items()
    }

    trend_assets = {symbol: assets[symbol] for symbol in TREND_SYMBOLS}
    cs_assets = {symbol: assets[symbol] for symbol in CS_SYMBOLS}
    trend_rows = _return_rows(
        trend_assets,
        _build_weight_path(trend_assets, "sma_50_200_inverse_vol"),
        {symbol: adjusted[symbol] for symbol in TREND_SYMBOLS},
    )
    cs_rows = _return_rows(
        cs_assets,
        _cs_weights(cs_assets),
        {symbol: adjusted[symbol] for symbol in CS_SYMBOLS},
    )

    trend_map = {row["timestamp"]: row for row in trend_rows}
    cs_map = {row["timestamp"]: row for row in cs_rows}
    common = sorted(set(trend_map) & set(cs_map))
    if len(common) != RESEARCH_COUNT + HOLDOUT_COUNT:
        raise ValueError(f"{len(common)} Returns statt {RESEARCH_COUNT + HOLDOUT_COUNT}.")

    trend_aligned = tuple(trend_map[ts] for ts in common)
    cs_aligned = tuple(cs_map[ts] for ts in common)
    fixed_rows = _fixed_rows(trend_aligned, cs_aligned)
    parity_rows = _aggregate_sleeves(trend_aligned, cs_aligned)

    scenarios = {}
    for name, multiplier in COST_SCENARIOS:
        fixed = _portfolio_budget(fixed_rows, multiplier, total_return=False)
        parity = _portfolio_budget(parity_rows, multiplier, total_return=False)
        parity_total = _portfolio_budget(parity_rows, multiplier, total_return=True)
        scenarios[name] = {
            "fixed_candidate": _summarize(fixed),
            "parity_candidate": _summarize(parity),
            "total_return_sensitivity": _summarize(parity_total),
        }

    gates = _gates(scenarios, ResearchGateConfig())
    report = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "status": "COMPLETED",
        "research_only": True,
        "candidate_status": "VALIDATED_PASS" if gates["all_checks_passed"] else "BLOCKED",
        "hypothesis": "Replacing fixed 50/50 capital allocation between unchanged Trend and Cross-Sectional sleeves with monthly inverse-volatility parity based only on the preceding 63 completed sleeve returns can reduce risk concentration without reducing holdout performance.",
        "source": {
            "universe": UNIVERSE,
            "trend_symbols": list(TREND_SYMBOLS),
            "cross_sectional_symbols": list(CS_SYMBOLS),
            "portfolio_symbols": list(PORTFOLIO_SYMBOLS),
            "target_candles": TARGET_COUNT,
            "common_returns": len(common),
            "research_count": RESEARCH_COUNT,
            "holdout_count": HOLDOUT_COUNT,
            "fully_symbol_disjoint": True,
            "signal_variant_count": 1,
            "manifest_fingerprint": manifest["manifest_fingerprint"],
        },
        "methodology": {
            "baseline": "fixed 50/50 SMA 50/200 inverse-volatility trend + 12-1 CS Top-2 + aggregate 63-session/10% volatility budget",
            "intervention": "only sleeve capital weights change: monthly inverse-volatility parity from preceding 63 completed Trend/CS returns",
            "rebalance": "first trading row of each new month",
            "risk_estimation_window": SLEEVE_VOL_WINDOW,
            "warmup": "equal 50/50 until 63 completed common sleeve returns exist",
            "weight_constraint": "0 <= each sleeve weight <= 1; weights sum to 1",
            "aggregate_risk_budget": "existing 63-session/10% budget unchanged after sleeve allocation",
            "allocation_turnover_costed": True,
            "point_in_time": "current return uses only sleeve rows strictly before the current row for allocation",
            "costs": {"fee_rate": FEE_RATE, "slippage_rate": SLIPPAGE_RATE},
            "cost_scenarios": [name for name, _ in COST_SCENARIOS],
            "optimization_used": False,
            "selection_used": False,
            "holdout_used_for_selection": False,
            "parameter_search": False,
            "threshold_search": False,
            "variant_search": False,
            "shorting": False,
            "leverage_above_one": False,
            "orders_enabled": False,
        },
        "scenarios": scenarios,
        "weight_summary": _weight_summary(parity_rows),
        "gate_contract": gates,
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False},
    }
    report["report_fingerprint"] = _fp(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    return report


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--data-dir",required=True)
    p.add_argument("--manifest",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    r=run_validation(Path(a.data_dir),Path(a.manifest),Path(a.output))
    print("TRIAL_029_STATUS:",r["status"])
    print("TRIAL_029_CANDIDATE_STATUS:",r["candidate_status"])
    print("TRIAL_029_REPORT_FINGERPRINT:",r["report_fingerprint"])
    print("TRIAL_029_CHECKS:",json.dumps(r["gate_contract"],sort_keys=True))
