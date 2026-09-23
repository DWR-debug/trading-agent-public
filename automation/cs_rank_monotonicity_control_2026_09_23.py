"""Rank-bucket and monotonicity diagnostic for the fixed CS mechanism.

Diagnostic-only. The fixed 12-1 ranking is unchanged. At each research
rebalance, every asset rank is followed for the next 21 sessions. No rank is
selected or optimized; all five ranks are reported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from statistics import mean, median


LOOKBACK = 252
SKIP = 21
REBALANCE = 21
RANKS = (1, 2, 3, 4, 5)


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _period_return(values: list[float]) -> float:
    equity = 1.0
    for value in values:
        equity *= 1.0 + value
    return equity - 1.0


def _pearson(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return 0.0
    left_mean = mean(left)
    right_mean = mean(right)
    left_var = sum((value - left_mean) ** 2 for value in left)
    right_var = sum((value - right_mean) ** 2 for value in right)
    if left_var == 0.0 or right_var == 0.0:
        return 0.0
    covariance = sum(
        (a - left_mean) * (b - right_mean)
        for a, b in zip(left, right)
    )
    return covariance / (left_var * right_var) ** 0.5


def _csv_rows(path: Path) -> list[dict]:
    import csv

    rows = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "timestamp": datetime.fromisoformat(
                        row["timestamp"].replace("Z", "+00:00")
                    ),
                    "open": float(row["open"]),
                    "close": float(row["close"]),
                }
            )
    return rows


def _load_aligned_assets(
    root: Path,
    manifest: dict,
) -> tuple[dict[str, list[dict]], list[datetime]]:
    data_root = root / "data/market_data"
    symbols = [item["symbol"] for item in manifest.get("datasets", [])]
    if len(symbols) != 5:
        raise ValueError(f"Erwartet 5 CS-Assets, erhalten: {symbols}")

    raw = {}
    for item in manifest["datasets"]:
        symbol = item["symbol"]
        rows = _csv_rows(data_root / symbol / "1d.csv")
        expected = int(item["candle_count"])
        if len(rows) != expected:
            raise ValueError(
                f"{symbol}: Manifest {expected} Candles, Datei {len(rows)}."
            )
        raw[symbol] = rows

    common = sorted(
        set.intersection(
            *[
                set(row["timestamp"] for row in rows)
                for rows in raw.values()
            ]
        )
    )
    if len(common) < LOOKBACK + SKIP + REBALANCE + 5:
        raise ValueError("Zu wenig gemeinsam ausgerichtete Candles.")

    aligned = {
        symbol: [
            next(
                row
                for row in raw[symbol]
                if row["timestamp"] == timestamp
            )
            for timestamp in common
        ]
        for symbol in symbols
    }
    return aligned, common


def _validate_report(report: dict) -> None:
    stored = report.get("report_fingerprint")
    if not stored:
        raise ValueError("report_fingerprint fehlt.")
    body = dict(report)
    body.pop("report_fingerprint")
    if _fingerprint(body) != stored:
        raise ValueError("Report-Fingerprint ungültig.")
    if report.get("status") != "COMPLETED":
        raise ValueError("Report nicht abgeschlossen.")

    methodology = report.get("methodology", {})
    primary_rule = str(methodology.get("primary_rule", "")).lower()
    architecture = str(methodology.get("architecture", "")).lower()
    if (
        "12-1 cross-sectional momentum, top-2 long-only" not in primary_rule
        and "12-1 cs momentum top-2 long-only" not in architecture
    ):
        raise ValueError("Feste 12-1-CS-Top-2-Architektur nicht verifiziert.")

    checks = {
        "formation_window_sessions": LOOKBACK,
        "skip_sessions": SKIP,
        "rebalance_sessions": REBALANCE,
    }
    for key, expected in checks.items():
        if key in methodology and int(methodology[key]) != expected:
            raise ValueError(f"{key} stimmt nicht mit {expected} überein.")

    if methodology.get("selection_profile_used") is not False:
        raise ValueError("Selection-profile Guard verletzt.")

    safety = report.get("safety", {})
    expected_safety = {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
    }
    if safety != expected_safety:
        raise ValueError("Paper-only Sicherheitsvertrag verletzt.")


def _research_count(report: dict, label: str) -> int:
    if label == "first_validation":
        return int(
            report["strategies"]["cs_momentum_252_long_only_top2"]["base"][
                "research"
            ]["day_count"]
        )
    return int(
        report["scenarios"]["base"]["vol_budget_10pct"]["price_only"][
            "research"
        ]["day_count"]
    )


def _analyse(
    assets: dict[str, list[dict]],
    timestamps: list[datetime],
    research_count: int,
) -> dict:
    symbols = tuple(assets)
    rank_forward_returns: dict[int, list[float]] = {
        rank: [] for rank in RANKS
    }
    rank_forward_positive_ratio: dict[int, list[bool]] = {
        rank: [] for rank in RANKS
    }
    rebalance_rows = []

    for index in range(research_count):
        if index < LOOKBACK + SKIP:
            continue
        if index % REBALANCE != 0:
            continue
        if index + REBALANCE > research_count:
            continue

        anchor = index - SKIP
        origin = anchor - LOOKBACK
        formation_scores = {
            symbol: (
                assets[symbol][anchor]["close"]
                / assets[symbol][origin]["close"]
                - 1.0
            )
            for symbol in symbols
        }
        ranking = sorted(
            symbols,
            key=lambda symbol: (-formation_scores[symbol], symbol),
        )

        forward_by_rank = {}
        for position, symbol in enumerate(ranking, start=1):
            path = []
            for future_index in range(index, index + REBALANCE):
                path.append(
                    assets[symbol][future_index + 2]["open"]
                    / assets[symbol][future_index + 1]["open"]
                    - 1.0
                )
            value = _period_return(path)
            forward_by_rank[position] = value
            rank_forward_returns[position].append(value)
            rank_forward_positive_ratio[position].append(value > 0.0)

        adjacent_good = sum(
            forward_by_rank[left] >= forward_by_rank[left + 1]
            for left in (1, 2, 3, 4)
        )
        full_monotone = adjacent_good == 4

        rebalance_rows.append(
            {
                "index": index,
                "timestamp": timestamps[index + 2].isoformat(),
                "formation_scores_by_rank": [
                    formation_scores[symbol] for symbol in ranking
                ],
                "forward_returns_by_rank": [
                    forward_by_rank[rank] for rank in RANKS
                ],
                "adjacent_non_increasing_pairs": adjacent_good,
                "full_non_increasing_rank_path": full_monotone,
            }
        )

    summary = {}
    pooled_rank_positions = []
    pooled_forward_returns = []

    for rank in RANKS:
        values = rank_forward_returns[rank]
        summary[str(rank)] = {
            "rank": rank,
            "formation_count": len(values),
            "mean_forward_return": mean(values) if values else 0.0,
            "median_forward_return": median(values) if values else 0.0,
            "positive_forward_ratio": (
                sum(rank_forward_positive_ratio[rank]) / len(values)
                if values
                else 0.0
            ),
        }
        pooled_rank_positions.extend([rank] * len(values))
        pooled_forward_returns.extend(values)

    adjacent_pair_mean = {}
    for left in (1, 2, 3, 4):
        right = left + 1
        values_left = rank_forward_returns[left]
        values_right = rank_forward_returns[right]
        pair = [
            a - b for a, b in zip(values_left, values_right)
        ]
        adjacent_pair_mean[f"{left}_minus_{right}"] = {
            "mean_difference": mean(pair) if pair else 0.0,
            "positive_difference_ratio": (
                sum(value > 0.0 for value in pair) / len(pair)
                if pair
                else 0.0
            ),
        }

    expected_monotone = len(rebalance_rows)
    full_monotone_count = sum(
        row["full_non_increasing_rank_path"]
        for row in rebalance_rows
    )
    adjacent_pair_total = expected_monotone * 4
    adjacent_pair_good = sum(
        row["adjacent_non_increasing_pairs"]
        for row in rebalance_rows
    )

    return {
        "research_return_count": research_count,
        "formation_count": expected_monotone,
        "rank_summary": summary,
        "adjacent_pair_summary": adjacent_pair_mean,
        "pooled_rank_position_vs_forward_return_correlation": _pearson(
            pooled_rank_positions,
            pooled_forward_returns,
        ),
        "full_rank_path_monotone_ratio": (
            full_monotone_count / expected_monotone
            if expected_monotone
            else 0.0
        ),
        "adjacent_non_increasing_ratio": (
            adjacent_pair_good / adjacent_pair_total
            if adjacent_pair_total
            else 0.0
        ),
        "rank_path_samples": rebalance_rows,
    }


def _discover(root: Path) -> tuple[dict, dict, str]:
    first = (
        root / "research/cs_momentum_replication/report.json",
        root / "research/cs_momentum_replication/manifest.json",
        "first_validation",
    )
    second = (
        root / "research/independent_validation_2026_09_23/report.json",
        root / "research/independent_validation_2026_09_23/data_cs_manifest.json",
        "second_validation",
    )
    for report_path, manifest_path, label in (first, second):
        if report_path.is_file() and manifest_path.is_file():
            return (
                json.loads(report_path.read_text(encoding="utf-8")),
                json.loads(manifest_path.read_text(encoding="utf-8")),
                label,
            )
    raise FileNotFoundError("CS-Artifact nicht erkannt.")


def run_control(
    first_root: Path,
    second_root: Path,
    output_path: Path,
) -> dict:
    first_report, first_manifest, first_label = _discover(first_root)
    second_report, second_manifest, second_label = _discover(second_root)
    if first_label != "first_validation":
        raise ValueError("Erstes Artifact ist nicht die erste Validation.")
    if second_label != "second_validation":
        raise ValueError("Zweites Artifact ist nicht die zweite Validation.")

    _validate_report(first_report)
    _validate_report(second_report)

    first_assets, first_timestamps = _load_aligned_assets(
        first_root,
        first_manifest,
    )
    second_assets, second_timestamps = _load_aligned_assets(
        second_root,
        second_manifest,
    )

    first = _analyse(
        first_assets,
        first_timestamps,
        _research_count(first_report, first_label),
    )
    second = _analyse(
        second_assets,
        second_timestamps,
        _research_count(second_report, second_label),
    )

    result = {
        "schema_version": 1,
        "diagnostic_type": "cs_rank_monotonicity_control_2026_09_23",
        "status": "COMPLETED",
        "fixed_rule": {
            "formation": "12-1 momentum",
            "formation_window_sessions": LOOKBACK,
            "skip_sessions": SKIP,
            "rebalance_sessions": REBALANCE,
            "reported_ranks": list(RANKS),
        },
        "datasets": {
            "first_validation": {
                "report_fingerprint": first_report["report_fingerprint"],
                "manifest_fingerprint": first_manifest["manifest_fingerprint"],
                "symbols": [
                    item["symbol"] for item in first_manifest["datasets"]
                ],
                **first,
            },
            "second_validation": {
                "report_fingerprint": second_report["report_fingerprint"],
                "manifest_fingerprint": second_manifest["manifest_fingerprint"],
                "symbols": [
                    item["symbol"] for item in second_manifest["datasets"]
                ],
                **second,
            },
        },
        "interpretation_constraints": [
            "diagnostic only",
            "all five ranks reported; no rank selected",
            "no parameter optimization",
            "no asset replacement",
            "no signal change",
            "no sleeve-weight change",
            "no gate change",
            "holdout returns not consumed",
            "no production change",
        ],
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    result["rank_control_fingerprint"] = _fingerprint(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--first-root", required=True)
    parser.add_argument("--second-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run_control(
        Path(args.first_root),
        Path(args.second_root),
        Path(args.output),
    )

    print("CS_RANK_MONOTONICITY_STATUS:", result["status"])
    for label in ("first_validation", "second_validation"):
        print(label)
        print(
            "pooled_corr=",
            result["datasets"][label][
                "pooled_rank_position_vs_forward_return_correlation"
            ],
            "full_monotone_ratio=",
            result["datasets"][label]["full_rank_path_monotone_ratio"],
            "adjacent_ratio=",
            result["datasets"][label]["adjacent_non_increasing_ratio"],
        )
        for rank, row in result["datasets"][label]["rank_summary"].items():
            print(
                "rank=",
                rank,
                "mean_forward=",
                row["mean_forward_return"],
                "positive_ratio=",
                row["positive_forward_ratio"],
            )
    print("RANK_CONTROL_FINGERPRINT:", result["rank_control_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
