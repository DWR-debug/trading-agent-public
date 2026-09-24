"""Sixth independent validation of a fixed CS dispersion risk budget.

Keeps the existing 50/50 trend + CS architecture and exact Top-2 signal.
The CS sleeve is scaled down only when 21-session cross-sectional dispersion
is above its prior 63-observation median. The rule can never increase CS
above the original 50% sleeve weight.

No parameter search, threshold search, asset selection or production mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

from automation import candidate_validation_50_50_vol_budget as base
from config import settings
from research.asset_universes import get_universe
from research.protocol import dataset_fingerprint

TREND_UNIVERSE = "validation_2026_09_24_sixth_trend"
CS_UNIVERSE = "validation_2026_09_24_sixth_cs"
TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700

CS_LOOKBACK = base.CS_LOOKBACK
CS_SKIP = base.CS_SKIP
CS_REBALANCE = base.CS_REBALANCE
CS_TOP_N = base.CS_TOP_N
CS_DISPERSION_LOOKBACK = 21
DISPERSION_REFERENCE_WINDOW = 63
TREND_STRATEGY = base.TREND_STRATEGY
TARGET_VOL = base.TARGET_VOL
VOL_WINDOW = base.VOL_WINDOW
FEE_RATE = base.FEE_RATE
SLIPPAGE_RATE = base.SLIPPAGE_RATE
COST_SCENARIOS = base.COST_SCENARIOS


def _canon(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _pf(value: float | str) -> float:
    return float("inf") if value == "inf" else float(value)


def _manifest(path: Path, universe_name: str) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    universe = get_universe(universe_name)
    symbols = tuple(item["symbol"] for item in data.get("datasets", []))
    if (
        data.get("universe") != universe_name
        or symbols != universe.symbols
        or data.get("target_count") != TARGET_COUNT
        or data.get("source") != "yahoo_chart"
    ):
        raise ValueError(f"Manifest passt nicht zu {universe_name}.")
    safety = data.get("safety", {})
    if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False:
        raise RuntimeError("Manifest-Sicherheitsvertrag verletzt.")
    return data


def _assets(data_dir: Path, manifest: dict) -> dict[str, tuple]:
    out = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        bars = base.load_bars(
            data_dir / symbol / "1d.csv",
            expected_count=int(item["candle_count"]),
        )
        if (
            len(bars) != TARGET_COUNT
            or dataset_fingerprint(bars) != item["fingerprint"]
        ):
            raise ValueError(f"{symbol}: Dataset-Fingerprint nicht verifiziert.")
        out[symbol] = bars

    common = set.intersection(
        *[{bar.timestamp for bar in bars} for bars in out.values()]
    )
    if len(common) != TARGET_COUNT:
        raise ValueError(
            f"Erwartet exakt {TARGET_COUNT} gemeinsame Candles, erhalten {len(common)}."
        )
    ordered = sorted(common)
    return {
        symbol: tuple({bar.timestamp: bar for bar in bars}[ts] for ts in ordered)
        for symbol, bars in out.items()
    }


def _dispersion(assets: dict[str, tuple], index: int) -> float | None:
    if index < CS_DISPERSION_LOOKBACK:
        return None
    values = [
        assets[symbol][index].close
        / assets[symbol][index - CS_DISPERSION_LOOKBACK].close
        - 1.0
        for symbol in assets
    ]
    return statistics.pstdev(values)


def _dispersion_state(
    assets: dict[str, tuple],
    index: int,
) -> tuple[float, float] | None:
    current = _dispersion(assets, index)
    if current is None or index < (
        CS_DISPERSION_LOOKBACK + DISPERSION_REFERENCE_WINDOW
    ):
        return None
    history = [
        _dispersion(assets, end_index)
        for end_index in range(
            index - DISPERSION_REFERENCE_WINDOW,
            index,
        )
    ]
    if any(value is None for value in history):
        return None
    reference = statistics.median(
        value for value in history if value is not None
    )
    return current, reference


def _effective_cs_weights(
    assets: dict[str, tuple],
    fixed_weights: tuple[dict[str, float], ...],
) -> tuple[dict[str, float], ...]:
    result = []
    for index, weights in enumerate(fixed_weights):
        state = _dispersion_state(assets, index)
        if state is None:
            scale = 1.0
        else:
            current, reference = state
            scale = 1.0 if current <= 0.0 else min(1.0, reference / current)
        result.append(
            {
                symbol: 0.5 * weight * scale
                for symbol, weight in weights.items()
            }
        )
    return tuple(result)


def _dispersion_diagnostics(
    assets: dict[str, tuple],
    effective_weights: tuple[dict[str, float], ...],
) -> dict[str, Any]:
    scales = []
    current_values = []
    reference_values = []

    for index in range(min(len(effective_weights), RESEARCH_COUNT)):
        cs_weight = sum(effective_weights[index].values())
        scales.append(2.0 * cs_weight)
        state = _dispersion_state(assets, index)
        if state is not None:
            current_values.append(state[0])
            reference_values.append(state[1])

    return {
        "research_observations": len(scales),
        "median_cs_scale": statistics.median(scales),
        "minimum_cs_scale": min(scales),
        "mean_cs_scale": statistics.mean(scales),
        "fraction_reduced_below_full": (
            sum(value < 1.0 for value in scales) / len(scales)
        ),
        "dispersion_observations": len(current_values),
        "median_current_dispersion": (
            statistics.median(current_values) if current_values else None
        ),
        "median_reference_dispersion": (
            statistics.median(reference_values) if reference_values else None
        ),
    }


def _stats(rows: list[dict], start: int, end: int) -> dict:
    segment = rows[start:end]
    if not segment:
        return {
            "period_return": 0.0,
            "max_drawdown_percent": 0.0,
            "profit_factor": 0.0,
            "day_count": 0,
            "median_scale": 0.0,
            "minimum_scale": 0.0,
        }

    equity = peak = 1.0
    gross_profit = gross_loss = 0.0
    max_dd = 0.0
    scales = []

    for row in segment:
        value = row["net_return"]
        scales.append(row["scale"])
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_dd = max(
            max_dd,
            1.0 - equity / peak if equity > 0.0 else 1.0,
        )
        if value > 0.0:
            gross_profit += value
        elif value < 0.0:
            gross_loss -= value

    pf = (
        gross_profit / gross_loss
        if gross_loss > 0.0
        else ("inf" if gross_profit > 0.0 else 0.0)
    )
    ordered = sorted(scales)

    return {
        "period_return": equity - 1.0,
        "max_drawdown_percent": max_dd * 100.0,
        "profit_factor": pf,
        "day_count": len(segment),
        "median_scale": ordered[len(ordered) // 2],
        "minimum_scale": min(scales),
    }


def _rolling(rows: list[dict], research_end: int) -> list[dict]:
    width = research_end // 5
    output = []
    start = 0
    for index in range(5):
        end = research_end if index == 4 else start + width
        output.append({"window_index": index + 1, **_stats(rows, start, end)})
        start = end
    return output


def _summary(rows: list[dict], windows: list[dict]) -> dict:
    values = [row["net_return"] for row in rows]
    gross_profit = sum(value for value in values if value > 0.0)
    gross_loss = -sum(value for value in values if value < 0.0)
    equity = 1.0

    for value in values:
        equity *= 1.0 + value

    return {
        "window_count": len(windows),
        "profitable_windows": sum(
            item["period_return"] > 0.0 for item in windows
        ),
        "profitable_window_ratio": (
            sum(item["period_return"] > 0.0 for item in windows)
            / len(windows)
        ),
        "total_net_return": equity - 1.0,
        "overall_profit_factor": (
            gross_profit / gross_loss
            if gross_loss > 0.0
            else ("inf" if gross_profit > 0.0 else 0.0)
        ),
        "average_drawdown_percent": (
            sum(item["max_drawdown_percent"] for item in windows)
            / len(windows)
        ),
    }


def _simulate(
    rows: tuple[dict, ...],
    multiplier: float,
    use_budget: bool,
    total_return: bool,
) -> list[dict]:
    history: list[float] = []
    previous_scale = 1.0
    output = []
    cost_rate = (FEE_RATE + SLIPPAGE_RATE) * multiplier

    for row in rows:
        scale = 1.0
        realized_vol = None

        if use_budget and len(history) >= VOL_WINDOW:
            sample = history[-VOL_WINDOW:]
            mean = sum(sample) / len(sample)
            variance = sum((x - mean) ** 2 for x in sample) / len(sample)
            realized_vol = variance**0.5 * (252.0**0.5)
            if realized_vol > TARGET_VOL:
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


def _scenario(rows: tuple[dict, ...], multiplier: float) -> dict:
    out = {}

    for name, budget in (
        ("unscaled_baseline", False),
        ("vol_budget_10pct", True),
    ):
        price = _simulate(rows, multiplier, budget, False)
        total = _simulate(rows, multiplier, budget, True)
        rolling = _rolling(price, RESEARCH_COUNT)

        out[name] = {
            "price_only": {
                "research": _stats(price, 0, RESEARCH_COUNT),
                "holdout": _stats(price, RESEARCH_COUNT, len(price)),
                "rolling_windows": rolling,
                "rolling_summary": _summary(
                    price[:RESEARCH_COUNT],
                    rolling,
                ),
            },
            "total_return_sensitivity": {
                "research": _stats(total, 0, RESEARCH_COUNT),
                "holdout": _stats(total, RESEARCH_COUNT, len(total)),
            },
        }
        research = out[name]["price_only"]["research"]
        out[name]["price_only"]["oos_to_is_return_ratio"] = (
            out[name]["price_only"]["holdout"]["period_return"]
            / research["period_return"]
            if research["period_return"] > 0.0
            else 0.0
        )

    return out


def _gates(scenarios: dict) -> dict:
    return base._gates(scenarios, base.ResearchGateConfig())


def _compare(baseline: dict, candidate: dict) -> dict:
    b = baseline["base"]["vol_budget_10pct"]["price_only"]
    c = candidate["base"]["vol_budget_10pct"]["price_only"]
    br = b["rolling_summary"]
    cr = c["rolling_summary"]

    checks = {
        "research_drawdown_not_worse": (
            c["research"]["max_drawdown_percent"]
            <= b["research"]["max_drawdown_percent"]
        ),
        "rolling_profit_factor_not_worse": (
            _pf(cr["overall_profit_factor"])
            >= _pf(br["overall_profit_factor"])
        ),
        "rolling_average_drawdown_not_worse": (
            cr["average_drawdown_percent"]
            <= br["average_drawdown_percent"]
        ),
        "research_return_not_worse": (
            cr["total_net_return"] >= br["total_net_return"]
        ),
    }
    return {"checks": checks, "all_checks_passed": all(checks.values())}


def _holdout_confirm(baseline: dict, candidate: dict) -> dict:
    b = baseline["base"]["vol_budget_10pct"]["price_only"]["holdout"]
    c = candidate["base"]["vol_budget_10pct"]["price_only"]["holdout"]
    checks = {
        "holdout_return_not_worse": c["period_return"] >= b["period_return"],
        "holdout_drawdown_not_worse": (
            c["max_drawdown_percent"] <= b["max_drawdown_percent"]
        ),
        "holdout_profit_factor_not_worse": (
            _pf(c["profit_factor"]) >= _pf(b["profit_factor"])
        ),
    }
    return {"checks": checks, "all_checks_passed": all(checks.values())}


def run_validation(
    trend_data_dir: Path,
    trend_manifest_path: Path,
    cs_data_dir: Path,
    cs_manifest_path: Path,
    output_path: Path,
) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")

    trend_manifest = _manifest(trend_manifest_path, TREND_UNIVERSE)
    cs_manifest = _manifest(cs_manifest_path, CS_UNIVERSE)
    trend = _assets(trend_data_dir, trend_manifest)
    cs = _assets(cs_data_dir, cs_manifest)

    if set(trend).intersection(cs):
        raise ValueError("Trend- und CS-Universum sind nicht disjunkt.")

    trend_weights = base._build_weight_path(trend, TREND_STRATEGY)
    fixed_cs_weights = _cs_weights(cs)
    effective_cs_weights = _effective_cs_weights(cs, fixed_cs_weights)

    all_assets = {**trend, **cs}
    adjusted = {
        symbol: base._yahoo_adjclose(
            symbol,
            bars[0].timestamp,
            bars[-1].timestamp,
        )
        for symbol, bars in all_assets.items()
    }

    baseline_rows = base._align(
        trend,
        trend_weights,
        {symbol: adjusted[symbol] for symbol in trend},
        cs,
        fixed_cs_weights,
        {symbol: adjusted[symbol] for symbol in cs},
    )
    candidate_rows = base._align(
        trend,
        trend_weights,
        {symbol: adjusted[symbol] for symbol in trend},
        cs,
        effective_cs_weights,
        {symbol: adjusted[symbol] for symbol in cs},
    )

    if len(baseline_rows) != TARGET_COUNT - 2:
        raise ValueError(
            f"Baseline liefert {len(baseline_rows)} Returns statt {TARGET_COUNT - 2}."
        )
    if len(candidate_rows) != len(baseline_rows):
        raise ValueError("Baseline/Kandidat haben unterschiedliche Return-Längen.")

    baseline_scenarios = {
        name: _scenario(baseline_rows, multiplier)
        for name, multiplier in COST_SCENARIOS
    }
    candidate_scenarios = {
        name: _scenario(candidate_rows, multiplier)
        for name, multiplier in COST_SCENARIOS
    }

    report = {
        "schema_version": 1,
        "diagnostic_type": "cs_dispersion_budget_sixth_validation_2026_09_24",
        "status": "COMPLETED",
        "candidate_status": "RESEARCH_ONLY",
        "source": {
            "trend_universe": TREND_UNIVERSE,
            "trend_symbols": list(get_universe(TREND_UNIVERSE).symbols),
            "trend_manifest_fingerprint": trend_manifest["manifest_fingerprint"],
            "cs_universe": CS_UNIVERSE,
            "cs_symbols": list(get_universe(CS_UNIVERSE).symbols),
            "cs_manifest_fingerprint": cs_manifest["manifest_fingerprint"],
            "raw_candle_count_per_asset": TARGET_COUNT,
            "research_return_count": RESEARCH_COUNT,
            "holdout_return_count": HOLDOUT_COUNT,
            "portfolio_return_count": len(candidate_rows),
            "fully_symbol_disjoint_validation_set": True,
            "data_acquisition_new": True,
        },
        "methodology": {
            "baseline_architecture_fixed": True,
            "trend_strategy": TREND_STRATEGY,
            "cs_lookback_sessions": CS_LOOKBACK,
            "cs_skip_sessions": CS_SKIP,
            "cs_rebalance_sessions": CS_REBALANCE,
            "cs_top_n": CS_TOP_N,
            "dispersion_lookback_sessions": CS_DISPERSION_LOOKBACK,
            "dispersion_reference_window": DISPERSION_REFERENCE_WINDOW,
            "dispersion_reference": "median of prior 63 observed 21-session cross-sectional dispersions",
            "cs_weight_formula": (
                "0.5 * fixed_top2_weight * min(1, reference_dispersion / "
                "current_dispersion) when current_dispersion > 0"
            ),
            "cs_weight_cap_above_baseline": False,
            "lookahead_control": (
                "Dispersion at index i uses closes through index i only and "
                "modifies the following Open-to-Open period."
            ),
            "parameter_search": False,
            "threshold_search": False,
            "variant_search": False,
            "asset_selection": False,
            "holdout_used_for_selection": False,
            "gate_changes": False,
            "production_mutation": False,
            "orders_enabled": False,
        },
        "scope": {
            "new_data_downloads": True,
            "new_disjoint_validation_set": True,
            "research_holdout_split": "2798 / 700",
            "holdout_used_for_selection": False,
        },
        "dispersion_diagnostics": _dispersion_diagnostics(
            cs,
            effective_cs_weights,
        ),
        "baseline_scenarios": baseline_scenarios,
        "candidate_scenarios": candidate_scenarios,
        "research_hypothesis": _compare(
            baseline_scenarios,
            candidate_scenarios,
        ),
        "holdout_confirmation": _holdout_confirm(
            baseline_scenarios,
            candidate_scenarios,
        ),
        "baseline_gates": {
            name: _gates(baseline_scenarios)
            for name in ("base",)
        },
        "candidate_gates": {
            name: _gates(candidate_scenarios)
            for name in ("base",)
        },
        "governance": {
            "trial_id": "T-2026-09-24-010",
            "selection_family_id": "cs-dispersion-budget-2026-09-24",
            "single_preregistered_hypothesis": True,
            "pbo_ready": False,
            "dsr_ready": False,
            "statistical_selection_gate": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }

    report["research_hypothesis_status"] = (
        "PASS"
        if report["research_hypothesis"]["all_checks_passed"]
        else "FAIL"
    )
    report["holdout_confirmation_status"] = (
        "PASS"
        if report["holdout_confirmation"]["all_checks_passed"]
        else "FAIL"
    )
    report["research_validation_status"] = (
        "PASS"
        if (
            report["research_hypothesis_status"] == "PASS"
            and report["candidate_gates"]["base"]["all_relevant_checks_passed"]
            and report["holdout_confirmation_status"] == "PASS"
        )
        else "FAIL"
    )

    report = json.loads(
        json.dumps(report, ensure_ascii=False, allow_nan=False)
    )
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trend-data-dir", required=True)
    parser.add_argument("--trend-manifest", required=True)
    parser.add_argument("--cs-data-dir", required=True)
    parser.add_argument("--cs-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_validation(
        Path(args.trend_data_dir),
        Path(args.trend_manifest),
        Path(args.cs_data_dir),
        Path(args.cs_manifest),
        Path(args.output),
    )

    print("CS_DISPERSION_BUDGET_VALIDATION_STATUS:", report["status"])
    print("RESEARCH_HYPOTHESIS_STATUS:", report["research_hypothesis_status"])
    print("HOLDOUT_CONFIRMATION_STATUS:", report["holdout_confirmation_status"])
    print("RESEARCH_VALIDATION_STATUS:", report["research_validation_status"])
    print("REPORT_FINGERPRINT:", report["report_fingerprint"])
    print("DISPERSION_DIAGNOSTICS:", report["dispersion_diagnostics"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
