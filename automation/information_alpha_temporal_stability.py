"""Q012: descriptive temporal-stability diagnosis for Q011 information features."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

from config import settings
from automation.information_alpha_discovery import (
    DEFAULT_ASSETS,
    FIXED_FEATURES,
    _pearson,
    _spearman,
    run_discovery,
)

DEFAULT_START = date(2026, 3, 29)
DEFAULT_END = date(2026, 9, 24)


def _sign(value: float | None) -> int | None:
    if value is None:
        return None
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _half_relationships(
    observations: list[dict],
    assets: tuple[str, ...],
    half_name: str,
) -> dict[str, dict[str, dict[str, float | int | None]]]:
    relationships: dict[str, dict[str, dict[str, float | int | None]]] = {}
    for symbol in assets:
        relationships[symbol] = {}
        for feature in FIXED_FEATURES:
            next_pairs = [
                (
                    row["features"][feature],
                    row["market"][symbol]["next_market_day_return"],
                )
                for row in observations
                if symbol in row["market"]
                and row["market"][symbol]["next_market_day_return"] is not None
            ]
            five_pairs = [
                (
                    row["features"][feature],
                    row["market"][symbol]["five_market_day_forward_return"],
                )
                for row in observations
                if symbol in row["market"]
                and row["market"][symbol]["five_market_day_forward_return"] is not None
            ]
            next_x = [pair[0] for pair in next_pairs]
            next_y = [pair[1] for pair in next_pairs]
            five_x = [pair[0] for pair in five_pairs]
            five_y = [pair[1] for pair in five_pairs]
            relationships[symbol][feature] = {
                "half": half_name,
                "sample_next_day": len(next_y),
                "pearson_next_day": _pearson(next_x, next_y),
                "spearman_next_day": _spearman(next_x, next_y),
                "sample_five_day": len(five_y),
                "pearson_five_day": _pearson(five_x, five_y),
                "spearman_five_day": _spearman(five_x, five_y),
            }
    return relationships


def run_stability_diagnostic(
    start: date = DEFAULT_START,
    end: date = DEFAULT_END,
    *,
    output_dir: str | Path = "research/runs/information_alpha_stability/q012",
) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")
    if end <= start:
        raise ValueError("end must be after start.")

    output_dir = Path(output_dir)
    base = run_discovery(
        start,
        end,
        assets=DEFAULT_ASSETS,
        output_path=output_dir / "base_discovery.json",
    )
    observations = base["observations"]
    if len(observations) < 20:
        raise ValueError(
            f"Q012 requires at least 20 common observations; found {len(observations)}."
        )

    split = len(observations) // 2
    first = observations[:split]
    second = observations[split:]
    first_relationships = _half_relationships(first, DEFAULT_ASSETS, "first_half")
    second_relationships = _half_relationships(second, DEFAULT_ASSETS, "second_half")

    stability: dict[str, dict[str, dict[str, object]]] = {}
    for symbol in DEFAULT_ASSETS:
        stability[symbol] = {}
        for feature in FIXED_FEATURES:
            one_a = first_relationships[symbol][feature]["pearson_next_day"]
            one_b = second_relationships[symbol][feature]["pearson_next_day"]
            five_a = first_relationships[symbol][feature]["pearson_five_day"]
            five_b = second_relationships[symbol][feature]["pearson_five_day"]
            stability[symbol][feature] = {
                "next_day_sign_consistent": (
                    _sign(one_a) is not None
                    and _sign(one_b) is not None
                    and _sign(one_a) == _sign(one_b)
                ),
                "next_day_first_pearson": one_a,
                "next_day_second_pearson": one_b,
                "next_day_abs_change": (
                    abs(one_b - one_a)
                    if one_a is not None and one_b is not None
                    else None
                ),
                "five_day_sign_consistent": (
                    _sign(five_a) is not None
                    and _sign(five_b) is not None
                    and _sign(five_a) == _sign(five_b)
                ),
                "five_day_first_pearson": five_a,
                "five_day_second_pearson": five_b,
                "five_day_abs_change": (
                    abs(five_b - five_a)
                    if five_a is not None and five_b is not None
                    else None
                ),
            }

    next_day_consistent = sum(
        int(stability[symbol][feature]["next_day_sign_consistent"])
        for symbol in DEFAULT_ASSETS
        for feature in FIXED_FEATURES
    )
    five_day_consistent = sum(
        int(stability[symbol][feature]["five_day_sign_consistent"])
        for symbol in DEFAULT_ASSETS
        for feature in FIXED_FEATURES
    )

    result = {
        "schema_version": "1.0",
        "task_id": "Q-012-INFORMATION-ALPHA-TEMPORAL-STABILITY-DIAGNOSTIC",
        "status": "STABILITY_DIAGNOSTIC_ONLY",
        "research_only": True,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "assets": list(DEFAULT_ASSETS),
        "fixed_features": list(FIXED_FEATURES),
        "source_task": "Q-011-ORTHOGONAL-INFORMATION-ALPHA-DISCOVERY",
        "point_in_time_contract": base["point_in_time_contract"],
        "observations": {
            "total": len(observations),
            "first_half": len(first),
            "second_half": len(second),
        },
        "event_presence": {
            "total_event_windows": sum(
                int(row["has_information_event"]) for row in observations
            ),
            "first_half_event_windows": sum(
                int(row["has_information_event"]) for row in first
            ),
            "second_half_event_windows": sum(
                int(row["has_information_event"]) for row in second
            ),
        },
        "first_half_relationships": first_relationships,
        "second_half_relationships": second_relationships,
        "temporal_stability": stability,
        "fixed_panel_sign_consistency": {
            "next_day": {
                "consistent_pairs": next_day_consistent,
                "total_pairs": len(DEFAULT_ASSETS) * len(FIXED_FEATURES),
                "ratio": next_day_consistent
                / (len(DEFAULT_ASSETS) * len(FIXED_FEATURES)),
            },
            "five_day": {
                "consistent_pairs": five_day_consistent,
                "total_pairs": len(DEFAULT_ASSETS) * len(FIXED_FEATURES),
                "ratio": five_day_consistent
                / (len(DEFAULT_ASSETS) * len(FIXED_FEATURES)),
            },
        },
        "selection_used": False,
        "holdout_used": False,
        "parameter_search_used": False,
        "feature_selection_used": False,
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    canonical = json.dumps(
        result, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    result["fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "q012_stability.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=DEFAULT_START.isoformat())
    parser.add_argument("--end", default=DEFAULT_END.isoformat())
    args = parser.parse_args()
    report = run_stability_diagnostic(
        date.fromisoformat(args.start),
        date.fromisoformat(args.end),
    )
    print("Q012_STATUS:", report["status"])
    print("Q012_FINGERPRINT:", report["fingerprint"])
    print("Q012_OBSERVATIONS:", report["observations"]["total"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
