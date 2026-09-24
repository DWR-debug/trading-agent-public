"""Post-hoc exploratory diagnosis of pre-event CS reversal precursors.

The analysis uses the same four immutable validation artifacts already established.
It asks which information available at the start of a return interval differs
between eventual CS winner-reversal and non-reversal periods.

No classifier, threshold optimization, asset selection, strategy mutation,
gate change, or production decision is performed.
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

TARGET_COUNT = 3500
RESEARCH_COUNT = 2798
CS_LOOKBACK = 252
CS_SKIP = 21
CS_REBALANCE = 21
CS_TOP_N = 2
PRE_EVENT_LOOKBACK = 21

CASES = (
    ("validation_1", 10751817990, "validation_trend", "validation_cs", "candidate_validation"),
    ("validation_2", 10740188093, "validation_2026_09_23_trend", "validation_2026_09_23_cs", "independent_validation_2026_09_23"),
    ("validation_3", 10745697729, "validation_2026_09_23_third_trend", "validation_2026_09_23_third_cs", "third_independent_validation_2026_09_23"),
    ("validation_4", 10753545703, "validation_2026_09_23_fourth_trend", "validation_2026_09_23_fourth_cs", "fourth_independent_validation_2026_09_23"),
)


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _manifest(path: Path, universe_name: str) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    universe = get_universe(universe_name)
    symbols = tuple(item["symbol"] for item in data.get("datasets", []))
    if data.get("universe") != universe_name or symbols != universe.symbols:
        raise ValueError(f"Manifest mismatch: {universe_name}")
    if data.get("target_count") != TARGET_COUNT or data.get("source") != "yahoo_chart":
        raise ValueError(f"Unexpected manifest contract: {universe_name}")
    safety = data.get("safety", {})
    if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False:
        raise RuntimeError("Manifest safety contract violated.")
    return data


def _load_assets(root: Path, manifest: dict) -> dict[str, tuple]:
    out = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        bars = base.load_bars(
            root / "data" / "market_data" / symbol / "1d.csv",
            expected_count=int(item["candle_count"]),
        )
        if len(bars) != TARGET_COUNT or dataset_fingerprint(bars) != item["fingerprint"]:
            raise ValueError(f"{symbol}: immutable dataset fingerprint mismatch")
        out[symbol] = bars

    common = set.intersection(*[{bar.timestamp for bar in bars} for bars in out.values()])
    if len(common) != TARGET_COUNT:
        raise ValueError(f"Expected {TARGET_COUNT} common candles, got {len(common)}")
    ordered = sorted(common)
    return {
        symbol: tuple({bar.timestamp: bar for bar in bars}[ts] for ts in ordered)
        for symbol, bars in out.items()
    }


def _selected_symbols(weights: dict[str, float]) -> tuple[str, ...]:
    return tuple(symbol for symbol, weight in weights.items() if weight > 0.0)


def _open_return_lookback(bars: tuple, current_open_index: int, sessions: int) -> float:
    return bars[current_open_index].open / bars[current_open_index - sessions].open - 1.0


def _feature_row(cs: dict[str, tuple], weights: tuple[dict[str, float], ...], i: int) -> dict[str, Any] | None:
    selected = _selected_symbols(weights[i])
    if len(selected) != CS_TOP_N or i < PRE_EVENT_LOOKBACK:
        return None

    current_open_index = i + 1
    if current_open_index < PRE_EVENT_LOOKBACK:
        return None

    relative = {}
    for symbol, bars in cs.items():
        relative[symbol] = _open_return_lookback(
            bars,
            current_open_index,
            PRE_EVENT_LOOKBACK,
        )

    selected_relative = statistics.mean(relative[symbol] for symbol in selected)
    nonselected_relative = statistics.mean(
        relative[symbol] for symbol in cs if symbol not in selected
    )
    dispersion = statistics.pstdev(relative.values())

    signal_anchor = i - CS_SKIP
    signal_origin = signal_anchor - CS_LOOKBACK
    if signal_origin < 0:
        return None

    signal_scores = {
        symbol: cs[symbol][signal_anchor].close / cs[symbol][signal_origin].close - 1.0
        for symbol in cs
    }
    selected_score = statistics.mean(signal_scores[symbol] for symbol in selected)
    nonselected_score = statistics.mean(
        signal_scores[symbol] for symbol in cs if symbol not in selected
    )

    return {
        "index": i,
        "timestamp": cs[next(iter(cs))][i + 1].timestamp.isoformat(),
        "reversal": None,
        "selected_21d_return": selected_relative,
        "nonselected_21d_return": nonselected_relative,
        "selected_minus_nonselected_21d_return": selected_relative - nonselected_relative,
        "cross_sectional_21d_dispersion": dispersion,
        "selected_signal_score": selected_score,
        "nonselected_signal_score": nonselected_score,
        "signal_score_gap": selected_score - nonselected_score,
        "selected_21d_return_negative": selected_relative < 0.0,
        "cross_sectional_return_min": min(relative.values()),
        "cross_sectional_return_max": max(relative.values()),
        "days_since_rebalance": i % CS_REBALANCE,
    }


def _case_analysis(cs: dict[str, tuple]) -> dict[str, Any]:
    cs_weights = base._cs_weights(cs)
    observations = []

    for i in range(RESEARCH_COUNT):
        spread = (
            sum(
                weights * (cs[symbol][i + 2].open / cs[symbol][i + 1].open - 1.0)
                for symbol, weights in cs_weights[i].items()
            )
            if _selected_symbols(cs_weights[i])
            else None
        )
        selected = _selected_symbols(cs_weights[i])
        if len(selected) != CS_TOP_N or i < PRE_EVENT_LOOKBACK:
            continue

        values = {
            symbol: cs[symbol][i + 2].open / cs[symbol][i + 1].open - 1.0
            for symbol in cs
        }
        winner_spread = (
            statistics.mean(values[symbol] for symbol in selected)
            - statistics.mean(values[symbol] for symbol in cs if symbol not in selected)
        )
        row = _feature_row(cs, cs_weights, i)
        if row is None:
            continue
        row["reversal"] = winner_spread < 0.0
        observations.append(row)

    def summarize(state: bool) -> dict[str, Any]:
        rows = [row for row in observations if row["reversal"] is state]
        if not rows:
            raise ValueError("No observations for state.")

        def mean(key: str) -> float:
            return statistics.mean(row[key] for row in rows)

        def median(key: str) -> float:
            return statistics.median(row[key] for row in rows)

        return {
            "observations": len(rows),
            "mean_selected_21d_return": mean("selected_21d_return"),
            "median_selected_21d_return": median("selected_21d_return"),
            "mean_relative_21d_return": mean("selected_minus_nonselected_21d_return"),
            "median_relative_21d_return": median("selected_minus_nonselected_21d_return"),
            "negative_selected_21d_return_rate": statistics.mean(
                row["selected_21d_return_negative"] for row in rows
            ),
            "mean_cross_sectional_21d_dispersion": mean("cross_sectional_21d_dispersion"),
            "median_cross_sectional_21d_dispersion": median("cross_sectional_21d_dispersion"),
            "mean_signal_score_gap": mean("signal_score_gap"),
            "median_signal_score_gap": median("signal_score_gap"),
            "mean_days_since_rebalance": mean("days_since_rebalance"),
        }

    reversal = summarize(True)
    non = summarize(False)

    phase = {
        phase: {
            "reversal_observations": 0,
            "total_observations": 0,
        }
        for phase in range(CS_REBALANCE)
    }
    for row in observations:
        slot = phase[int(row["days_since_rebalance"])]
        slot["total_observations"] += 1
        slot["reversal_observations"] += int(row["reversal"])

    return {
        "reversal": reversal,
        "non_reversal": non,
        "feature_differences_reversal_minus_non_reversal": {
            "selected_21d_return": (
                reversal["mean_selected_21d_return"]
                - non["mean_selected_21d_return"]
            ),
            "relative_21d_return": (
                reversal["mean_relative_21d_return"]
                - non["mean_relative_21d_return"]
            ),
            "cross_sectional_21d_dispersion": (
                reversal["mean_cross_sectional_21d_dispersion"]
                - non["mean_cross_sectional_21d_dispersion"]
            ),
            "signal_score_gap": (
                reversal["mean_signal_score_gap"]
                - non["mean_signal_score_gap"]
            ),
        },
        "phase_counts": phase,
    }


def analyze(source_root: Path) -> dict[str, Any]:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")

    cases = {}
    for name, artifact_id, trend_name, cs_name, report_root in CASES:
        # Trend data are not needed for this precursor analysis; the trend
        # manifest is still checked to preserve the exact validation universe.
        case_root = source_root / "sources" / name
        trend_manifest = _manifest(case_root / "research" / report_root / "data_trend_manifest.json", trend_name)
        cs_manifest = _manifest(case_root / "research" / report_root / "data_cs_manifest.json", cs_name)
        _load_assets(case_root, trend_manifest)
        cs = _load_assets(case_root, cs_manifest)
        cases[name] = {
            "source": {"artifact_id": artifact_id, "trend_universe": trend_name, "cs_universe": cs_name},
            "analysis": _case_analysis(cs),
        }

    result = {
        "schema_version": 1,
        "diagnostic_type": "exploratory_cs_reversal_precursors_2026_09_24",
        "status": "COMPLETED",
        "question": (
            "Welche Informationen, die am Beginn des Reversal-Return-Intervalls "
            "bereits bekannt sind, unterscheiden spätere CS-Winner-Reversals "
            "von Nicht-Reversal-Perioden?"
        ),
        "scope": {
            "datasets": 4,
            "research_return_count_per_dataset": RESEARCH_COUNT,
            "holdout_used_for_decision": False,
            "holdout_metrics_reported": False,
            "new_data_downloads": False,
            "parameter_search": False,
            "threshold_search": False,
            "asset_selection": False,
            "strategy_mutation": False,
            "gate_changes": False,
            "production_mutation": False,
            "exploratory_post_hoc": True,
        },
        "methodology": {
            "candidate_architecture_fixed": True,
            "cs_lookback_sessions": CS_LOOKBACK,
            "cs_skip_sessions": CS_SKIP,
            "cs_rebalance_sessions": CS_REBALANCE,
            "cs_top_n": CS_TOP_N,
            "pre_event_features": [
                "selected_vs_nonselected_21d_open_return",
                "cross_sectional_21d_open_return_dispersion",
                "fixed_252d_21d_skip_signal_score_gap",
                "days_since_rebalance",
            ],
            "feature_availability": (
                "Only information available at the start of the current "
                "open-to-open interval is used for precursor features."
            ),
            "descriptive_only": True,
            "not_confirmatory": True,
            "no_new_hypothesis_gate": True,
        },
        "cases": cases,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    result = json.loads(json.dumps(result, ensure_ascii=False, allow_nan=False))
    result["diagnostic_fingerprint"] = _fp(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = analyze(Path(args.source_root))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print("EXPLORATORY_PRECURSOR_STATUS:", result["status"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    for name, case in result["cases"].items():
        print(name, case["analysis"]["feature_differences_reversal_minus_non_reversal"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
