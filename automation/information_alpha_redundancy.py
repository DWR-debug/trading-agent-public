"""Q013: descriptive GDELT mechanism/redundancy diagnostic."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

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

MECHANISM_GROUPS = {
    "intensity_breadth": (
        "event_count",
        "attention_score",
        "source_breadth",
        "article_count",
    ),
    "severity": ("negative_goldstein",),
    "tone": ("mean_tone",),
}


def _pairs(observations, symbol, feature, horizon_key):
    pairs = [
        (row["features"][feature], row["market"][symbol][horizon_key])
        for row in observations
        if symbol in row["market"]
        and row["market"][symbol][horizon_key] is not None
    ]
    return [x for x, _ in pairs], [y for _, y in pairs]


def _feature_matrix(observations, features):
    matrix = {}
    for left in features:
        matrix[left] = {}
        for right in features:
            x = [row["features"][left] for row in observations]
            y = [row["features"][right] for row in observations]
            matrix[left][right] = _spearman(x, y)
    return matrix


def _return_associations(observations, assets):
    out = {}
    for symbol in assets:
        out[symbol] = {}
        for feature in FIXED_FEATURES:
            nx, ny = _pairs(observations, symbol, feature, "next_market_day_return")
            fx, fy = _pairs(observations, symbol, feature, "five_market_day_forward_return")
            out[symbol][feature] = {
                "sample_next_day": len(ny),
                "pearson_next_day": _pearson(nx, ny),
                "spearman_next_day": _spearman(nx, ny),
                "sample_five_day": len(fy),
                "pearson_five_day": _pearson(fx, fy),
                "spearman_five_day": _spearman(fx, fy),
            }
    return out


def _group_summary(feature_matrix):
    summary = {}
    for name, features in MECHANISM_GROUPS.items():
        values = []
        for index, left in enumerate(features):
            for right in features[index + 1:]:
                value = feature_matrix[left][right]
                if value is not None:
                    values.append(abs(value))
        summary[name] = {
            "features": list(features),
            "pairwise_mean_abs_spearman": sum(values) / len(values) if values else None,
            "pair_count": len(values),
        }
    return summary


def run_redundancy_diagnostic(
    start: date = DEFAULT_START,
    end: date = DEFAULT_END,
    *,
    output_dir: str | Path = "research/runs/information_alpha_redundancy/q013",
) -> dict:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")
    if end <= start:
        raise ValueError("end must be after start.")

    root = Path(output_dir)
    base = run_discovery(
        start,
        end,
        assets=DEFAULT_ASSETS,
        output_path=root / "base_discovery.json",
    )
    observations = base["observations"]
    event_observations = [row for row in observations if row["has_information_event"]]
    if len(observations) < 20:
        raise ValueError(f"Q013 requires at least 20 common observations; found {len(observations)}.")
    if len(event_observations) < 20:
        raise ValueError(f"Q013 requires at least 20 event-window observations; found {len(event_observations)}.")

    all_matrix = _feature_matrix(observations, FIXED_FEATURES)
    event_matrix = _feature_matrix(event_observations, FIXED_FEATURES)

    result = {
        "schema_version": "1.0",
        "task_id": "Q-013-INFORMATION-ALPHA-MECHANISM-REDUNDANCY-DIAGNOSTIC",
        "status": "MECHANISM_REDUNDANCY_DIAGNOSTIC_ONLY",
        "research_only": True,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "assets": list(DEFAULT_ASSETS),
        "fixed_features": list(FIXED_FEATURES),
        "mechanism_groups": {name: list(features) for name, features in MECHANISM_GROUPS.items()},
        "source_task": "Q-012-INFORMATION-ALPHA-TEMPORAL-STABILITY-DIAGNOSTIC",
        "point_in_time_contract": base["point_in_time_contract"],
        "observations": {
            "total": len(observations),
            "event_windows": len(event_observations),
            "no_event_windows": len(observations) - len(event_observations),
        },
        "data_quality": base["data_quality"],
        "feature_redundancy": {
            "all_common_observations_spearman": all_matrix,
            "event_only_spearman": event_matrix,
            "group_summary_all": _group_summary(all_matrix),
            "group_summary_event_only": _group_summary(event_matrix),
        },
        "return_associations": {
            "all_common_observations": _return_associations(observations, DEFAULT_ASSETS),
            "event_only": _return_associations(event_observations, DEFAULT_ASSETS),
        },
        "selection_used": False,
        "holdout_used": False,
        "parameter_search_used": False,
        "feature_selection_used": False,
        "asset_selection_used": False,
        "performance_trial_authorized": False,
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    result["fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    root.mkdir(parents=True, exist_ok=True)
    (root / "q013_redundancy.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=DEFAULT_START.isoformat())
    parser.add_argument("--end", default=DEFAULT_END.isoformat())
    args = parser.parse_args()
    report = run_redundancy_diagnostic(date.fromisoformat(args.start), date.fromisoformat(args.end))
    print("Q013_STATUS:", report["status"])
    print("Q013_FINGERPRINT:", report["fingerprint"])
    print("Q013_EVENT_WINDOWS:", report["observations"]["event_windows"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
