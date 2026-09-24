"""Trial 028: per-sleeve volatility budgeting control.

Research-only. The fixed 50/50 candidate is preserved except for one
pre-registered risk intervention: apply the existing 63-session/10% volatility
budget independently to the Trend and Cross-Sectional sleeves before the fixed
50/50 aggregation.

No optimization, selection, threshold search, promotion, leverage or orders.
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

TRIAL_ID = "T-2026-09-24-028"
UNIVERSE = "validation_2026_09_24_per_sleeve_vol_budget"

TREND_SYMBOLS = ("SPLV", "SPHQ", "SPYG", "SPYV", "FXI", "GDX", "PFF", "CWB")
CS_SYMBOLS = ("XSD", "IBB", "ITA", "XAR", "XES")
PORTFOLIO_SYMBOLS = TREND_SYMBOLS + CS_SYMBOLS

TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700

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


def _load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    universe = get_universe(UNIVERSE)
    actual = tuple(item["symbol"] for item in manifest.get("datasets", []))

    if manifest.get("universe") != UNIVERSE:
        raise ValueError("Manifest passt nicht zum Trial-028-Universum.")
    if actual != tuple(universe.symbols):
        raise ValueError("Trial-028-Symbole weichen vom Präregister ab.")
    if manifest.get("target_count") != TARGET_COUNT:
        raise ValueError("Unerwartete Trial-028-Zielhistorie.")
    if manifest.get("source") != "yahoo_chart":
        raise ValueError("Unerwartete Trial-028-Datenquelle.")

    safety = manifest.get("safety", {})
    if safety.get("paper_only") is not True:
        raise RuntimeError("PAPER_ONLY muss True sein.")
    if safety.get("live_trading_enabled") is not False:
        raise RuntimeError("LIVE_TRADING_ENABLED muss False sein.")
    if safety.get("orders_enabled") is not False:
        raise RuntimeError("orders_enabled muss False sein.")
    return manifest


def _load_assets(data_dir: Path, manifest: dict) -> dict[str, tuple]:
    assets: dict[str, tuple] = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        bars = load_bars(
            data_dir / symbol / "1d.csv",
            expected_count=int(item["candle_count"]),
        )
        if len(bars) != TARGET_COUNT:
            raise ValueError(f"{symbol}: {len(bars)} statt {TARGET_COUNT}.")
        if dataset_fingerprint(bars) != item["fingerprint"]:
            raise ValueError(f"{symbol}: Dataset-Fingerprint stimmt nicht.")
        assets[symbol] = bars

    if set(assets) != set(PORTFOLIO_SYMBOLS):
        raise ValueError("Trial-028-Symbolmenge stimmt nicht.")
    common = set.intersection(
        *[{bar.timestamp for bar in bars} for bars in assets.values()]
    )
    if len(common) < TARGET_COUNT:
        raise ValueError(f"Zu wenig gemeinsame Candles: {len(common)}.")

    selected = sorted(common)[-TARGET_COUNT:]
    return {
        symbol: tuple(
            {bar.timestamp: bar for bar in bars}[timestamp]
            for timestamp in selected
        )
        for symbol, bars in assets.items()
    }


def _vol(history: list[float]) -> float | None:
    if len(history) < VOL_WINDOW:
        return None
    sample = history[-VOL_WINDOW:]
    mean = sum(sample) / len(sample)
    variance = sum((value - mean) ** 2 for value in sample) / len(sample)
    return math.sqrt(variance) * math.sqrt(252.0)


def _simulate_sleeve(
    rows: tuple[dict, ...],
    multiplier: float,
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

        turnover = (
            scale * float(row["turnover"])
            + abs(scale - previous_scale)
        )
        gross = float(row["gross_open"])
        net = scale * gross - cost_rate * turnover

        output.append(
            {
                "timestamp": row["timestamp"],
                "gross_return": gross,
                "net_return": net,
                "turnover": float(row["turnover"]),
                "scaled_turnover": turnover,
                "scale": scale,
                "realized_vol_estimate": realized_vol,
            }
        )

        previous_scale = scale
        history.append(
            gross - (FEE_RATE + SLIPPAGE_RATE) * float(row["turnover"])
        )

    return output


def _combine_sleeves(
    trend_rows: tuple[dict, ...],
    cs_rows: tuple[dict, ...],
    multiplier: float,
) -> dict[str, list[dict]]:
    trend = _simulate_sleeve(trend_rows, multiplier)
    cross_sectional = _simulate_sleeve(cs_rows, multiplier)

    if len(trend) != len(cross_sectional):
        raise ValueError("Sleeve-Return-Längen stimmen nicht.")

    combined = []
    fixed = []
    for trend_row, cs_row in zip(trend, cross_sectional):
        timestamp = trend_row["timestamp"]
        if timestamp != cs_row["timestamp"]:
            raise ValueError("Sleeve-Timestamps sind nicht identisch.")

        intervention_net = (
            0.5 * trend_row["net_return"]
            + 0.5 * cs_row["net_return"]
        )
        fixed_gross = (
            0.5 * trend_row["gross_return"]
            + 0.5 * cs_row["gross_return"]
        )

        combined.append(
            {
                "timestamp": timestamp,
                "net_return": intervention_net,
                "gross_return": (
                    0.5 * trend_row["scale"] * trend_row["gross_return"]
                    + 0.5 * cs_row["scale"] * cs_row["gross_return"]
                ),
                "scale": (
                    0.5 * trend_row["scale"]
                    + 0.5 * cs_row["scale"]
                ),
            }
        )
        fixed.append(
            {
                "timestamp": timestamp,
                "gross_return": fixed_gross,
            }
        )

    return {
        "intervention": combined,
        "fixed_unscaled": fixed,
        "trend": trend,
        "cross_sectional": cross_sectional,
    }


def _portfolio_budget(
    rows: tuple[dict, ...],
    multiplier: float,
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

        turnover = scale * float(row["turnover"]) + abs(scale - previous_scale)
        net = scale * float(row["gross_open"]) - cost_rate * turnover

        output.append(
            {
                "timestamp": row["timestamp"],
                "net_return": net,
                "gross_return": scale * float(row["gross_open"]),
                "scale": scale,
            }
        )

        previous_scale = scale
        history.append(
            float(row["gross_open"])
            - (FEE_RATE + SLIPPAGE_RATE) * float(row["turnover"])
        )
    return output


def _summarize(rows: list[dict]) -> dict:
    research = _stats(rows, 0, RESEARCH_COUNT)
    holdout = _stats(rows, RESEARCH_COUNT, RESEARCH_COUNT + HOLDOUT_COUNT)

    width = RESEARCH_COUNT // 5
    windows = []
    start = 0
    for index in range(5):
        end = RESEARCH_COUNT if index == 4 else start + width
        windows.append(
            {"window_index": index + 1, **_stats(rows, start, end)}
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


def _scale_summary(rows: list[dict]) -> dict:
    research = rows[:RESEARCH_COUNT]
    holdout = rows[RESEARCH_COUNT:]
    return {
        "research_median_scale": sorted(
            row["scale"] for row in research
        )[len(research) // 2],
        "research_min_scale": min(row["scale"] for row in research),
        "holdout_median_scale": sorted(
            row["scale"] for row in holdout
        )[len(holdout) // 2],
        "holdout_min_scale": min(row["scale"] for row in holdout),
    }


def _delta(challenger: dict, fixed: dict) -> dict:
    return {
        "research_return_delta_percentage_points": (
            challenger["research"]["period_return"]
            - fixed["research"]["period_return"]
        ) * 100.0,
        "research_drawdown_delta_percentage_points": (
            challenger["research"]["max_drawdown_percent"]
            - fixed["research"]["max_drawdown_percent"]
        ),
        "research_profit_factor_delta": (
            _pf(challenger["research"]["profit_factor"])
            - _pf(fixed["research"]["profit_factor"])
        ),
        "holdout_return_delta_percentage_points": (
            challenger["holdout"]["period_return"]
            - fixed["holdout"]["period_return"]
        ) * 100.0,
        "holdout_drawdown_delta_percentage_points": (
            challenger["holdout"]["max_drawdown_percent"]
            - fixed["holdout"]["max_drawdown_percent"]
        ),
        "holdout_profit_factor_delta": (
            _pf(challenger["holdout"]["profit_factor"])
            - _pf(fixed["holdout"]["profit_factor"])
        ),
    }


def _gates(
    scenarios: dict,
    config: ResearchGateConfig,
) -> dict:
    base = scenarios["base"]["per_sleeve_vol_budget"]
    fixed = scenarios["base"]["fixed_candidate"]
    stress15 = scenarios["stress_1_5x_cost"]["per_sleeve_vol_budget"]
    stress2 = scenarios["stress_2x_cost"]["per_sleeve_vol_budget"]

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
            base["total_return_sensitivity"]["holdout"]["period_return"]
            >= 0.0
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
        "all_checks_passed": (
            all(absolute.values()) and all(non_worsening.values())
        ),
    }


def run_validation(
    data_dir: Path,
    manifest_path: Path,
    output_path: Path,
) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only Sicherheitsvertrag verletzt.")

    manifest = _load_manifest(manifest_path)
    expected = set(PORTFOLIO_SYMBOLS)

    for universe in list_universes():
        if universe.name == UNIVERSE:
            continue
        if expected.intersection(universe.symbols):
            raise ValueError(f"Symbol-Overlap mit bestehendem Universum: {universe.name}")

    assets = _load_assets(data_dir, manifest)
    adjusted = {
        symbol: _yahoo_adjclose(
            symbol,
            bars[0].timestamp,
            bars[-1].timestamp,
        )
        for symbol, bars in assets.items()
    }

    trend_assets = {symbol: assets[symbol] for symbol in TREND_SYMBOLS}
    cs_assets = {symbol: assets[symbol] for symbol in CS_SYMBOLS}

    trend_weights = _build_weight_path(
        trend_assets,
        "sma_50_200_inverse_vol",
    )
    cs_weights = _cs_weights(cs_assets)

    trend_rows = _return_rows(
        trend_assets,
        trend_weights,
        {symbol: adjusted[symbol] for symbol in TREND_SYMBOLS},
    )
    cs_rows = _return_rows(
        cs_assets,
        cs_weights,
        {symbol: adjusted[symbol] for symbol in CS_SYMBOLS},
    )

    trend_by_ts = {row["timestamp"]: row for row in trend_rows}
    cs_by_ts = {row["timestamp"]: row for row in cs_rows}
    common = sorted(set(trend_by_ts) & set(cs_by_ts))

    expected_returns = RESEARCH_COUNT + HOLDOUT_COUNT
    if len(common) != expected_returns:
        raise ValueError(
            f"{len(common)} Returns statt {expected_returns}."
        )

    trend_aligned = tuple(trend_by_ts[ts] for ts in common)
    cs_aligned = tuple(cs_by_ts[ts] for ts in common)

    # Fixed portfolio before the existing aggregate risk layer.
    fixed_rows = tuple(
        {
            "timestamp": ts,
            "gross_open": (
                0.5 * trend_by_ts[ts]["gross_open"]
                + 0.5 * cs_by_ts[ts]["gross_open"]
            ),
            "turnover": (
                0.5 * trend_by_ts[ts]["turnover"]
                + 0.5 * cs_by_ts[ts]["turnover"]
            ),
        }
        for ts in common
    )

    scenario_reports = {}
    for scenario_name, multiplier in COST_SCENARIOS:
        fixed_budget = _portfolio_budget(fixed_rows, multiplier)

        sleeve_parts = _combine_sleeves(
            trend_aligned,
            cs_aligned,
            multiplier,
        )
        intervention = sleeve_parts["intervention"]
        intervention_total = [
            dict(row)
            for row in intervention
        ]

        # Dividend/split sensitivity uses the same sleeve scales but adjusted-close
        # returns. This remains diagnostic and cannot alter the decision rule.
        trend_total = _simulate_sleeve(
            tuple({
                "timestamp": row["timestamp"],
                "gross_open": row["gross_open"],
                "turnover": row["turnover"],
            } for row in trend_aligned),
            multiplier,
        )
        cs_total = _simulate_sleeve(
            tuple({
                "timestamp": row["timestamp"],
                "gross_open": row["gross_open"],
                "turnover": row["turnover"],
            } for row in cs_aligned),
            multiplier,
        )

        total_return_sensitivity = []
        for tr, cr, ts, cs in zip(
            trend_total,
            cs_total,
            trend_aligned,
            cs_aligned,
        ):
            trend_adjusted = float(ts["gross_adjusted_close"])
            cs_adjusted = float(cs["gross_adjusted_close"])
            trend_scale = tr["scale"]
            cs_scale = cr["scale"]

            net = (
                0.5 * trend_scale * trend_adjusted
                + 0.5 * cs_scale * cs_adjusted
                - (FEE_RATE + SLIPPAGE_RATE) * (
                    0.5 * tr["scaled_turnover"]
                    + 0.5 * cr["scaled_turnover"]
                )
            )
            total_return_sensitivity.append({
                "timestamp": tr["timestamp"],
                "net_return": net,
                "gross_return": (
                    0.5 * trend_scale * trend_adjusted
                    + 0.5 * cs_scale * cs_adjusted
                ),
                "scale": 0.5 * (trend_scale + cs_scale),
            })

        scenario_reports[scenario_name] = {
            "fixed_candidate": _summarize(fixed_budget),
            "per_sleeve_vol_budget": _summarize(intervention_total),
            "total_return_sensitivity": _summarize(
                total_return_sensitivity
            ),
            "trend_scale": _scale_summary(sleeve_parts["trend"]),
            "cross_sectional_scale": _scale_summary(
                sleeve_parts["cross_sectional"]
            ),
        }

    gates = _gates(scenario_reports, ResearchGateConfig())
    report = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "status": "COMPLETED",
        "research_only": True,
        "candidate_status": (
            "VALIDATED_PASS"
            if gates["all_checks_passed"]
            else "BLOCKED"
        ),
        "hypothesis": (
            "Applying the existing 63-session/10% volatility budget independently "
            "to the Trend and Cross-Sectional sleeves before the fixed 50/50 "
            "aggregation reduces the concentration of drawdown risk without "
            "reducing holdout performance versus the fixed candidate."
        ),
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
            "baseline": (
                "fixed 50/50 SMA 50/200 inverse-volatility trend + "
                "12-1 CS Top-2 + aggregate 63-session/10% volatility budget"
            ),
            "intervention": (
                "same sleeves and same signals; existing 63-session/10% "
                "volatility budget applied independently within each sleeve, "
                "then fixed 50/50 aggregation"
            ),
            "risk_budget_order": (
                "sleeve-level 10% budget first, fixed 50/50 aggregation second"
            ),
            "costs": {
                "fee_rate": FEE_RATE,
                "slippage_rate": SLIPPAGE_RATE,
            },
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
        "scenarios": scenario_reports,
        "gate_contract": gates,
        "deltas_vs_fixed": _delta(
            scenario_reports["base"]["per_sleeve_vol_budget"],
            scenario_reports["base"]["fixed_candidate"],
        ),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_validation(
        Path(args.data_dir),
        Path(args.manifest),
        Path(args.output),
    )
    print("TRIAL_028_STATUS:", report["status"])
    print("TRIAL_028_CANDIDATE_STATUS:", report["candidate_status"])
    print("TRIAL_028_REPORT_FINGERPRINT:", report["report_fingerprint"])
    print(
        "TRIAL_028_CHECKS:",
        json.dumps(report["gate_contract"], sort_keys=True),
    )


if __name__ == "__main__":
    main()
