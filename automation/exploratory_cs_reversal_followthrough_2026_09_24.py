"""Post-hoc exploratory diagnosis of the immediate CS reversal follow-through.

This analysis uses the four immutable validation artifacts already established.
It is explicitly exploratory and is not a confirmatory test, gate, or strategy
change. It asks whether the next actual CS holding period remains positive
after a CS winner reversal and compares that response with non-reversal days.

No parameter search, threshold search, selection, or production mutation.
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

RESEARCH_COUNT = 2798
TARGET_COUNT = 3500
CS_LOOKBACK = 252
CS_SKIP = 21
CS_REBALANCE = 21
CS_TOP_N = 2

CASES = (
    ("validation_1", 10751817990, "validation_trend", "validation_cs"),
    ("validation_2", 10740188093, "validation_2026_09_23_trend", "validation_2026_09_23_cs"),
    ("validation_3", 10745697729, "validation_2026_09_23_third_trend", "validation_2026_09_23_third_cs"),
    ("validation_4", 10753545703, "validation_2026_09_23_fourth_trend", "validation_2026_09_23_fourth_cs"),
)


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _manifest(path: Path, universe_name: str) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    universe = get_universe(universe_name)
    symbols = tuple(item["symbol"] for item in data.get("datasets", []))
    if data.get("universe") != universe_name:
        raise ValueError(f"Manifest universe mismatch: {universe_name}")
    if symbols != universe.symbols or data.get("target_count") != TARGET_COUNT:
        raise ValueError(f"Manifest does not match fixed universe: {universe_name}")
    if data.get("source") != "yahoo_chart":
        raise ValueError(f"Unexpected manifest source: {universe_name}")
    safety = data.get("safety", {})
    if safety.get("paper_only") is not True or safety.get("live_trading_enabled") is not False:
        raise RuntimeError("Manifest safety contract violated.")
    return data


def _load_assets(root: Path, manifest: dict) -> dict[str, tuple]:
    out: dict[str, tuple] = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        bars = base.load_bars(
            root / "data" / "market_data" / symbol / "1d.csv",
            expected_count=int(item["candle_count"]),
        )
        if len(bars) != TARGET_COUNT or dataset_fingerprint(bars) != item["fingerprint"]:
            raise ValueError(f"{symbol}: immutable dataset fingerprint mismatch")
        out[symbol] = bars

    common = set.intersection(
        *[{bar.timestamp for bar in bars} for bars in out.values()]
    )
    if len(common) != TARGET_COUNT:
        raise ValueError(f"Expected {TARGET_COUNT} common candles, got {len(common)}")
    ordered = sorted(common)
    return {
        symbol: tuple({bar.timestamp: bar for bar in bars}[ts] for ts in ordered)
        for symbol, bars in out.items()
    }


def _cs_spread(
    cs: dict[str, tuple],
    weights: tuple[dict[str, float], ...],
    i: int,
) -> float | None:
    selected = tuple(symbol for symbol, weight in weights[i].items() if weight > 0.0)
    if len(selected) != CS_TOP_N:
        return None
    values = {
        symbol: cs[symbol][i + 2].open / cs[symbol][i + 1].open - 1.0
        for symbol in cs
    }
    winner = statistics.mean(values[symbol] for symbol in selected)
    nonwinner = statistics.mean(
        values[symbol] for symbol in cs if symbol not in selected
    )
    return winner - nonwinner


def _cs_sleeve_return(
    cs: dict[str, tuple],
    weights: tuple[dict[str, float], ...],
    i: int,
) -> float:
    return sum(
        weight
        * (cs[symbol][i + 2].open / cs[symbol][i + 1].open - 1.0)
        for symbol, weight in weights[i].items()
    )


def _trend_return(
    trend: dict[str, tuple],
    weights: tuple[dict[str, float], ...],
    i: int,
) -> float:
    return sum(
        weight
        * (trend[symbol][i + 2].open / trend[symbol][i + 1].open - 1.0)
        for symbol, weight in weights[i].items()
    )


def _case_analysis(trend: dict[str, tuple], cs: dict[str, tuple]) -> dict[str, Any]:
    trend_weights = base._build_weight_path(trend, base.TREND_STRATEGY)
    cs_weights = base._cs_weights(cs)

    reversal_flags = [
        (_cs_spread(cs, cs_weights, i) is not None)
        and (_cs_spread(cs, cs_weights, i) < 0.0)
        for i in range(RESEARCH_COUNT)
    ]

    observations = []
    for i in range(RESEARCH_COUNT - 1):
        if _cs_spread(cs, cs_weights, i) is None:
            continue

        next_cs = _cs_sleeve_return(cs, cs_weights, i + 1)
        next_trend = _trend_return(trend, trend_weights, i + 1)
        observations.append(
            {
                "reversal": bool(reversal_flags[i]),
                "next_cs_return": next_cs,
                "next_trend_return": next_trend,
                "next_portfolio_gross_open_return": 0.5 * next_cs + 0.5 * next_trend,
                "next_selected_winner_spread": _cs_spread(cs, cs_weights, i + 1),
            }
        )

    def summary(state: bool) -> dict[str, Any]:
        rows = [row for row in observations if row["reversal"] is state]
        if not rows:
            raise ValueError("State has no observations.")
        return {
            "observations": len(rows),
            "mean_next_cs_return": statistics.mean(
                row["next_cs_return"] for row in rows
            ),
            "median_next_cs_return": statistics.median(
                row["next_cs_return"] for row in rows
            ),
            "positive_next_cs_return_rate": sum(
                row["next_cs_return"] > 0.0 for row in rows
            ) / len(rows),
            "mean_next_selected_winner_spread": statistics.mean(
                row["next_selected_winner_spread"]
                for row in rows
                if row["next_selected_winner_spread"] is not None
            ),
            "positive_next_selected_winner_spread_rate": sum(
                row["next_selected_winner_spread"] > 0.0
                for row in rows
                if row["next_selected_winner_spread"] is not None
            ) / sum(
                row["next_selected_winner_spread"] is not None for row in rows
            ),
            "mean_next_portfolio_gross_open_return": statistics.mean(
                row["next_portfolio_gross_open_return"] for row in rows
            ),
            "positive_next_portfolio_gross_open_rate": sum(
                row["next_portfolio_gross_open_return"] > 0.0 for row in rows
            ) / len(rows),
        }

    reversal = summary(True)
    non_reversal = summary(False)
    reversal_rows = [row for row in observations if row["reversal"]]
    flip_rate = sum(
        row["next_selected_winner_spread"] > 0.0
        for row in reversal_rows
        if row["next_selected_winner_spread"] is not None
    ) / sum(
        row["next_selected_winner_spread"] is not None
        for row in reversal_rows
    )

    return {
        "reversal": reversal,
        "non_reversal": non_reversal,
        "reversal_followed_by_positive_next_spread_rate": flip_rate,
        "next_cs_return_difference_reversal_minus_non_reversal": (
            reversal["mean_next_cs_return"]
            - non_reversal["mean_next_cs_return"]
        ),
        "next_portfolio_return_difference_reversal_minus_non_reversal": (
            reversal["mean_next_portfolio_gross_open_return"]
            - non_reversal["mean_next_portfolio_gross_open_return"]
        ),
    }


def analyze(source_root: Path) -> dict[str, Any]:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")

    cases: dict[str, Any] = {}
    for name, artifact_id, trend_name, cs_name in CASES:
        trend_manifest = _manifest(
            source_root / "sources" / name / "research" / (
                "candidate_validation" if name == "validation_1"
                else (
                    "independent_validation_2026_09_23"
                    if name == "validation_2"
                    else (
                        "third_independent_validation_2026_09_23"
                        if name == "validation_3"
                        else "fourth_independent_validation_2026_09_23"
                    )
                )
            ) / "data_trend_manifest.json",
            trend_name,
        )
        cs_manifest = _manifest(
            source_root / "sources" / name / "research" / (
                "candidate_validation" if name == "validation_1"
                else (
                    "independent_validation_2026_09_23"
                    if name == "validation_2"
                    else (
                        "third_independent_validation_2026_09_23"
                        if name == "validation_3"
                        else "fourth_independent_validation_2026_09_23"
                    )
                )
            ) / "data_cs_manifest.json",
            cs_name,
        )
        case_root = source_root / "sources" / name
        trend = _load_assets(case_root, trend_manifest)
        cs = _load_assets(case_root, cs_manifest)
        if set(trend).intersection(cs):
            raise ValueError(f"{name}: trend/CS universes overlap")
        cases[name] = {
            "source": {"artifact_id": artifact_id, "trend_universe": trend_name, "cs_universe": cs_name},
            "analysis": _case_analysis(trend, cs),
        }

    result = {
        "schema_version": 1,
        "diagnostic_type": "exploratory_cs_reversal_followthrough_2026_09_24",
        "status": "COMPLETED",
        "question": (
            "Bleibt die tatsächliche nächste CS-Halteperiode nach einem "
            "vollständig beobachteten Winner-Reversal positiv, und unterscheidet "
            "sich diese Folgebewegung von Nicht-Reversal-Tagen?"
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
            "current_reversal_state": "fixed top-2 winner minus nonwinner open-to-open spread < 0",
            "followthrough_definition": (
                "next-period actual CS sleeve return under the already-fixed "
                "21-session rebalance signal, plus next-period selected-winner spread"
            ),
            "full_portfolio_reference": "0.5 * next CS sleeve gross open return + 0.5 * next trend sleeve gross open return",
            "descriptive_only": True,
            "not_confirmatory": True,
            "no_new_hypothesis_gate": True,
        },
        "cases": cases,
        "replication_summary": {
            "direction": (
                "positive_next_cs_return"
                if sum(
                    case["analysis"]["reversal"]["mean_next_cs_return"] > 0.0
                    for case in cases.values()
                ) >= 3
                else "not_replicated"
            ),
            "validations_with_positive_mean_next_cs_return_after_reversal": sum(
                case["analysis"]["reversal"]["mean_next_cs_return"] > 0.0
                for case in cases.values()
            ),
            "validations_with_positive_next_cs_return_rate_above_0_5": sum(
                case["analysis"]["reversal"]["positive_next_cs_return_rate"] > 0.5
                for case in cases.values()
            ),
        },
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
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print("EXPLORATORY_FOLLOWTHROUGH_STATUS:", result["status"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    print("REPLICATION_SUMMARY:", result["replication_summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
