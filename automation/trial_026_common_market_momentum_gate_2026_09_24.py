"""Trial 026: common-market momentum gate on the fixed 50/50 candidate.

Research-only. One fixed intervention, no optimization or holdout selection.
The gate is computed from ACWI adjusted-close momentum known at the candidate
decision timestamp and is applied after the existing 63-session/10% risk budget.
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

TRIAL_ID = "T-2026-09-24-026"
UNIVERSE = "validation_2026_09_24_common_market_momentum_gate"
SIGNAL_PROXY = "ACWI"
TREND_SYMBOLS = ("VBR", "VSS", "VCIT", "BIL", "GSG", "VPL", "EWQ", "EWL")
CS_SYMBOLS = ("EWW", "EZU", "ILF", "SCHD", "USMV")
PORTFOLIO_SYMBOLS = TREND_SYMBOLS + CS_SYMBOLS
TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
HOLDOUT_COUNT = 700
MARKET_MOMENTUM_LOOKBACK = 252
TARGET_VOL = 0.10
VOL_WINDOW = 63
FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005
COST_SCENARIOS = (
    ("base", 1.0),
    ("stress_1_5x_cost", 1.5),
    ("stress_2x_cost", 2.0),
)


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _pf(value: float | str) -> float:
    return float("inf") if value == "inf" else float(value)


def _load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    universe = get_universe(UNIVERSE)
    expected = tuple(universe.symbols)
    actual = tuple(item["symbol"] for item in manifest.get("datasets", []))
    if manifest.get("universe") != UNIVERSE or actual != expected:
        raise ValueError("Manifest passt nicht zum Trial-026-Universum.")
    if manifest.get("target_count") != TARGET_COUNT or manifest.get("source") != "yahoo_chart":
        raise ValueError("Unerwartete Trial-026-Datenbasis.")
    safety = manifest.get("safety", {})
    if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False:
        raise RuntimeError("Paper-only-Sicherheitsvertrag im Manifest verletzt.")
    if safety.get("orders_enabled") is not False:
        raise RuntimeError("Orders müssen deaktiviert sein.")
    return manifest


def _load_assets(data_dir: Path, manifest: dict) -> dict[str, tuple]:
    assets: dict[str, tuple] = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        bars = load_bars(data_dir / symbol / "1d.csv", expected_count=int(item["candle_count"]))
        if len(bars) != TARGET_COUNT:
            raise ValueError(f"{symbol}: {len(bars)} statt {TARGET_COUNT} Candles.")
        if dataset_fingerprint(bars) != item["fingerprint"]:
            raise ValueError(f"{symbol}: Dataset-Fingerprint stimmt nicht.")
        assets[symbol] = bars
    expected = set(PORTFOLIO_SYMBOLS) | {SIGNAL_PROXY}
    if set(assets) != expected:
        raise ValueError("Portfolio- oder Signal-Symbole fehlen.")
    return assets


def _align_assets(assets: dict[str, tuple]) -> dict[str, tuple]:
    common = set.intersection(*[{bar.timestamp for bar in bars} for bars in assets.values()])
    if len(common) < TARGET_COUNT:
        raise ValueError(f"Zu wenig gemeinsame Candles: {len(common)}")
    selected = sorted(common)[-TARGET_COUNT:]
    return {
        symbol: tuple({bar.timestamp: bar for bar in bars}[ts] for ts in selected)
        for symbol, bars in assets.items()
    }


def _candidate_rows(assets: dict[str, tuple], adjusted: dict[str, dict]) -> tuple[dict, ...]:
    trend_assets = {symbol: assets[symbol] for symbol in TREND_SYMBOLS}
    cs_assets = {symbol: assets[symbol] for symbol in CS_SYMBOLS}
    trend_weights = _build_weight_path(trend_assets, "sma_50_200_inverse_vol")
    cs_weights = _cs_weights(cs_assets)

    trend_rows = _return_rows(
        trend_assets, trend_weights, {symbol: adjusted[symbol] for symbol in TREND_SYMBOLS}
    )
    cs_rows = _return_rows(
        cs_assets, cs_weights, {symbol: adjusted[symbol] for symbol in CS_SYMBOLS}
    )
    trend_by_ts = {row["timestamp"]: row for row in trend_rows}
    cs_by_ts = {row["timestamp"]: row for row in cs_rows}
    common = sorted(set(trend_by_ts) & set(cs_by_ts))
    if len(common) != RESEARCH_COUNT + HOLDOUT_COUNT:
        raise ValueError(f"Unerwartete Return-Anzahl: {len(common)}")
    return tuple(
        {
            "timestamp": ts,
            "gross_open": 0.5 * trend_by_ts[ts]["gross_open"] + 0.5 * cs_by_ts[ts]["gross_open"],
            "gross_close": 0.5 * trend_by_ts[ts]["gross_close"] + 0.5 * cs_by_ts[ts]["gross_close"],
            "gross_adjusted_close": (
                0.5 * trend_by_ts[ts]["gross_adjusted_close"]
                + 0.5 * cs_by_ts[ts]["gross_adjusted_close"]
            ),
            "turnover": 0.5 * trend_by_ts[ts]["turnover"] + 0.5 * cs_by_ts[ts]["turnover"],
        }
        for ts in common
    )


def _decision_timestamp_map(reference_bars: tuple) -> dict:
    return {
        reference_bars[index].timestamp: reference_bars[index - 2].timestamp
        for index in range(2, len(reference_bars))
    }


def _market_gate(market_bars: tuple, adjusted_close: dict, decision_timestamps: set) -> dict:
    by_time = {bar.timestamp: index for index, bar in enumerate(market_bars)}
    gate = {}
    for ts in decision_timestamps:
        index = by_time.get(ts)
        if index is None:
            raise ValueError(f"{SIGNAL_PROXY}: decision timestamp nicht gefunden.")
        if index < MARKET_MOMENTUM_LOOKBACK:
            gate[ts] = True
            continue
        current = adjusted_close.get(ts)
        anchor_ts = market_bars[index - MARKET_MOMENTUM_LOOKBACK].timestamp
        anchor = adjusted_close.get(anchor_ts)
        if current is None or anchor is None or anchor <= 0.0:
            raise ValueError(f"{SIGNAL_PROXY}: Market-Momentum-Daten fehlen.")
        gate[ts] = (current / anchor - 1.0) > 0.0
    return gate


def _simulate(rows: tuple[dict, ...], multiplier: float, market_gate_by_return_timestamp: dict | None = None) -> list[dict]:
    history: list[float] = []
    previous_exposure = 0.0
    cost_rate = (FEE_RATE + SLIPPAGE_RATE) * multiplier
    output = []

    for row in rows:
        realized_vol = None
        if len(history) >= VOL_WINDOW:
            sample = history[-VOL_WINDOW:]
            mean = sum(sample) / len(sample)
            variance = sum((value - mean) ** 2 for value in sample) / len(sample)
            realized_vol = math.sqrt(variance) * math.sqrt(252.0)

        risk_scale = 1.0
        if realized_vol is not None and realized_vol > TARGET_VOL:
            risk_scale = min(1.0, TARGET_VOL / realized_vol)

        gate_on = True if market_gate_by_return_timestamp is None else bool(
            market_gate_by_return_timestamp[row["timestamp"]]
        )
        exposure = risk_scale if gate_on else 0.0
        turnover = exposure * float(row["turnover"]) + abs(exposure - previous_exposure)
        gross = exposure * float(row["gross_open"])
        net = gross - cost_rate * turnover

        output.append(
            {
                "timestamp": row["timestamp"],
                "net_return": net,
                "gross_return": gross,
                "turnover": turnover,
                "scale": exposure,
                "risk_scale": risk_scale,
                "market_gate_on": gate_on,
                "realized_vol_estimate": realized_vol,
            }
        )
        previous_exposure = exposure
        history.append(float(row["gross_open"]) - cost_rate * float(row["turnover"]))

    return output


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


def _summarize(simulated: list[dict]) -> dict:
    research = _stats(simulated, 0, RESEARCH_COUNT)
    holdout = _stats(simulated, RESEARCH_COUNT, RESEARCH_COUNT + HOLDOUT_COUNT)
    rolling = _rolling_summary(simulated)
    return {
        "research": research,
        "holdout": holdout,
        "rolling_summary": rolling,
        "oos_to_is_return_ratio": (
            holdout["period_return"] / research["period_return"]
            if research["period_return"] > 0.0
            else 0.0
        ),
        "gate_on_rate_research": sum(int(row["market_gate_on"]) for row in simulated[:RESEARCH_COUNT]) / RESEARCH_COUNT,
        "gate_on_rate_holdout": sum(int(row["market_gate_on"]) for row in simulated[RESEARCH_COUNT:]) / HOLDOUT_COUNT,
    }


def _scenario(rows: tuple[dict, ...], multiplier: float, gate: dict) -> dict:
    return {
        "baseline": _summarize(_simulate(rows, multiplier)),
        "market_momentum_gate": _summarize(_simulate(rows, multiplier, gate)),
    }


def _checks(scenarios: dict, config: ResearchGateConfig) -> dict:
    base = scenarios["base"]["market_momentum_gate"]
    baseline = scenarios["base"]["baseline"]
    stress15 = scenarios["stress_1_5x_cost"]["market_momentum_gate"]
    stress2 = scenarios["stress_2x_cost"]["market_momentum_gate"]

    absolute = {
        "research_return_positive": base["research"]["period_return"] > 0.0,
        "research_drawdown": base["research"]["max_drawdown_percent"] <= config.maximum_drawdown_percent,
        "research_profit_factor": _pf(base["research"]["profit_factor"]) >= config.minimum_profit_factor,
        "rolling_profit_factor": _pf(base["rolling_summary"]["overall_profit_factor"]) >= config.minimum_profit_factor,
        "rolling_profitable_window_ratio": base["rolling_summary"]["profitable_window_ratio"] >= config.minimum_profitable_window_ratio,
        "rolling_average_drawdown": base["rolling_summary"]["average_drawdown_percent"] <= config.maximum_drawdown_percent,
        "oos_to_is_return_ratio": base["oos_to_is_return_ratio"] >= config.minimum_oos_to_is_return_ratio,
        "holdout_return_positive": base["holdout"]["period_return"] > 0.0,
        "holdout_profit_factor": _pf(base["holdout"]["profit_factor"]) >= config.minimum_profit_factor,
        "holdout_drawdown": base["holdout"]["max_drawdown_percent"] <= config.maximum_drawdown_percent,
        "stress_1_5x_nonnegative": stress15["holdout"]["period_return"] >= 0.0,
        "stress_2x_nonnegative": stress2["holdout"]["period_return"] >= 0.0,
    }
    non_worsening = {
        "research_drawdown_not_worse": base["research"]["max_drawdown_percent"] <= baseline["research"]["max_drawdown_percent"],
        "research_rolling_pf_not_worse": _pf(base["rolling_summary"]["overall_profit_factor"]) >= _pf(baseline["rolling_summary"]["overall_profit_factor"]),
        "holdout_return_not_worse": base["holdout"]["period_return"] >= baseline["holdout"]["period_return"],
        "holdout_drawdown_not_worse": base["holdout"]["max_drawdown_percent"] <= baseline["holdout"]["max_drawdown_percent"],
        "holdout_pf_not_worse": _pf(base["holdout"]["profit_factor"]) >= _pf(baseline["holdout"]["profit_factor"]),
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
    expected = set(PORTFOLIO_SYMBOLS) | {SIGNAL_PROXY}
    for universe in list_universes():
        if universe.name == UNIVERSE:
            continue
        if expected.intersection(universe.symbols):
            raise ValueError(f"Symbol-Overlap mit bestehendem Universum: {universe.name}")

    assets = _align_assets(_load_assets(data_dir, manifest))
    adjusted = {
        symbol: _yahoo_adjclose(symbol, bars[0].timestamp, bars[-1].timestamp)
        for symbol, bars in assets.items()
    }
    rows = _candidate_rows(assets, adjusted)

    reference = assets[SIGNAL_PROXY]
    decision_map = _decision_timestamp_map(reference)
    decision_timestamps = {decision_map[row["timestamp"]] for row in rows}
    gate_by_decision = _market_gate(reference, adjusted[SIGNAL_PROXY], decision_timestamps)
    gate_by_return = {
        row["timestamp"]: gate_by_decision[decision_map[row["timestamp"]]]
        for row in rows
    }

    scenarios = {
        name: _scenario(rows, multiplier, gate_by_return)
        for name, multiplier in COST_SCENARIOS
    }
    checks = _checks(scenarios, ResearchGateConfig())

    report = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "status": "COMPLETED",
        "research_only": True,
        "hypothesis": (
            "A fixed common-market 12-1 momentum state from ACWI, applied after "
            "the existing 10% volatility budget, improves risk and robustness "
            "without reducing holdout return versus the fixed 50/50 candidate."
        ),
        "source": {
            "universe": UNIVERSE,
            "portfolio_symbols": list(PORTFOLIO_SYMBOLS),
            "trend_symbols": list(TREND_SYMBOLS),
            "cross_sectional_symbols": list(CS_SYMBOLS),
            "signal_proxy": SIGNAL_PROXY,
            "target_candles": TARGET_COUNT,
            "common_returns": len(rows),
            "research_count": RESEARCH_COUNT,
            "holdout_count": HOLDOUT_COUNT,
            "fully_symbol_disjoint": True,
            "signal_is_external_to_traded_portfolio": True,
            "market_momentum_lookback_sessions": MARKET_MOMENTUM_LOOKBACK,
            "manifest_fingerprint": manifest["manifest_fingerprint"],
        },
        "methodology": {
            "baseline": "fixed 50/50 SMA-50/200 + 12-1 CS Top-2 candidate with 10% vol budget",
            "intervention": "ACWI prior 252-session adjusted-close return > 0 keeps exposure; <= 0 gates exposure to cash",
            "signal_information_cutoff": "candidate decision timestamp",
            "risk_budget_order": "existing 63-session/10% budget first, then common-market gate",
            "warmup_rule": "before 252 market observations exist, gate remains on because no state is computable",
            "gate_switches_are_costed": True,
            "costs": {"fee_rate": FEE_RATE, "slippage_rate": SLIPPAGE_RATE},
            "cost_scenarios": [name for name, _ in COST_SCENARIOS],
            "optimization_used": False,
            "selection_used": False,
            "holdout_used_for_selection": False,
            "parameter_search": False,
            "orders_enabled": False,
        },
        "scenarios": scenarios,
        "decision_contract": checks,
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False},
    }
    report["report_fingerprint"] = _fp(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run_validation(Path(args.data_dir), Path(args.manifest), Path(args.output))
    print("TRIAL_026_STATUS:", report["status"])
    print("TRIAL_026_CHECKS:", json.dumps(report["decision_contract"], sort_keys=True))
    print("TRIAL_026_REPORT_FINGERPRINT:", report["report_fingerprint"])


if __name__ == "__main__":
    main()
