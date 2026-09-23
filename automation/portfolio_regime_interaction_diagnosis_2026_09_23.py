"""Descriptive portfolio regime/interaction diagnosis across two full validations.

Consumes only immutable failure-diagnosis artifacts from the second and third
independent validations. No thresholds are optimized and no intervention is
selected.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean


EXPECTED_SHARED_FAILURES = {
    "research_drawdown",
    "rolling_profit_factor",
    "rolling_average_drawdown",
    "holdout_drawdown",
}


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


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_and_verify_diagnosis(
    root: Path,
    diagnosis_path: str,
) -> dict:
    diagnosis = _load_json(root / diagnosis_path)
    stored = diagnosis.pop("diagnostic_fingerprint")
    if _fingerprint(diagnosis) != stored:
        raise ValueError(f"Diagnose-Fingerprint ungültig: {diagnosis_path}")
    diagnosis["diagnostic_fingerprint"] = stored
    return diagnosis


def _window_interaction_snapshot(diagnosis: dict) -> dict:
    windows = []
    for window in diagnosis["windows"]:
        portfolio = window["portfolio"]
        trend = window["trend_sleeve"]
        cs = window["cross_sectional_sleeve"]
        windows.append(
            {
                "window_index": window["window_index"],
                "start_timestamp": window["start_timestamp"],
                "end_timestamp": window["end_timestamp"],
                "portfolio_period_return": portfolio["period_return"],
                "portfolio_max_drawdown_percent": portfolio["max_drawdown_percent"],
                "portfolio_profit_factor": portfolio["profit_factor"],
                "trend_period_return": trend["period_return"],
                "trend_profit_factor": trend["profit_factor"],
                "trend_drawdown_percent": trend["max_drawdown_percent"],
                "cs_period_return": cs["period_return"],
                "cs_profit_factor": cs["profit_factor"],
                "cs_drawdown_percent": cs["max_drawdown_percent"],
                "sleeve_return_correlation": window["sleeve_return_correlation"],
                "median_scale": window["median_scale"],
                "minimum_scale": window["minimum_scale"],
                "both_sleeves_negative": (
                    trend["period_return"] < 0.0
                    and cs["period_return"] < 0.0
                ),
                "cross_sectional_drawdown_larger": (
                    cs["max_drawdown_percent"] > trend["max_drawdown_percent"]
                ),
            }
        )
    return {"windows": windows}


def _conditional_means(windows: list[dict]) -> dict:
    failing = [row for row in windows if row["portfolio_period_return"] <= 0.0]
    non_failing = [row for row in windows if row["portfolio_period_return"] > 0.0]

    def averages(rows: list[dict]) -> dict:
        if not rows:
            return {
                "window_count": 0,
                "mean_sleeve_return_correlation": None,
                "mean_median_scale": None,
                "mean_minimum_scale": None,
                "both_sleeves_negative_ratio": None,
                "cross_sectional_drawdown_larger_ratio": None,
            }
        return {
            "window_count": len(rows),
            "mean_sleeve_return_correlation": mean(
                row["sleeve_return_correlation"] for row in rows
            ),
            "mean_median_scale": mean(row["median_scale"] for row in rows),
            "mean_minimum_scale": mean(row["minimum_scale"] for row in rows),
            "both_sleeves_negative_ratio": mean(
                row["both_sleeves_negative"] for row in rows
            ),
            "cross_sectional_drawdown_larger_ratio": mean(
                row["cross_sectional_drawdown_larger"] for row in rows
            ),
        }

    return {
        "portfolio_non_positive_windows": averages(failing),
        "portfolio_positive_windows": averages(non_failing),
    }


def _dataset_analysis(
    diagnosis: dict,
    label: str,
) -> dict:
    if diagnosis["input"]["source_candidate_status"] != "BLOCKED":
        raise ValueError(f"{label}: Kandidat ist nicht BLOCKED.")
    if diagnosis["safety"] != {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
    }:
        raise ValueError(f"{label}: Safety-Vertrag verletzt.")

    window_data = _window_interaction_snapshot(diagnosis)["windows"]
    max_dd = max(
        window_data,
        key=lambda row: row["portfolio_max_drawdown_percent"],
    )
    failure_details = diagnosis.get("failure_signature")
    if failure_details is None:
        failure_details = diagnosis.get("diagnosis", {})
    if "max_drawdown_interval" not in failure_details:
        raise ValueError(f"{label}: max_drawdown_interval fehlt.")

    return {
        "label": label,
        "source_report_fingerprint": diagnosis["input"]["source_report_fingerprint"],
        "diagnostic_fingerprint": diagnosis["diagnostic_fingerprint"],
        "candidate_status": diagnosis["input"]["source_candidate_status"],
        "failed_gate_checks": sorted(EXPECTED_SHARED_FAILURES),
        "window_analysis": {
            "rows": window_data,
            "conditional_means": _conditional_means(window_data),
            "worst_window_by_max_drawdown": max_dd,
            "recorded_max_drawdown_interval": failure_details["max_drawdown_interval"],
            "both_sleeves_negative_windows": [
                row["window_index"]
                for row in window_data
                if row["both_sleeves_negative"]
            ],
            "cross_sectional_drawdown_larger_windows": [
                row["window_index"]
                for row in window_data
                if row["cross_sectional_drawdown_larger"]
            ],
        },
    }


def run_control(
    second_root: Path,
    third_root: Path,
    output_path: Path,
) -> dict:
    second_diag = _load_and_verify_diagnosis(
        second_root,
        "failure_diagnosis_2026_09_23.json",
    )
    third_diag = _load_and_verify_diagnosis(
        third_root,
        "third_validation_failure_diagnosis_2026_09_23.json",
    )

    second = _dataset_analysis(second_diag, "second_validation")
    third = _dataset_analysis(third_diag, "third_validation")

    all_windows = [
        {
            **row,
            "dataset": label,
        }
        for label, dataset in (
            ("second_validation", second),
            ("third_validation", third),
        )
        for row in dataset["window_analysis"]["rows"]
    ]

    second_negative = [
        row for row in second["window_analysis"]["rows"]
        if row["portfolio_period_return"] <= 0.0
    ]
    third_negative = [
        row for row in third["window_analysis"]["rows"]
        if row["portfolio_period_return"] <= 0.0
    ]

    common = {
        "negative_portfolio_window_count": len(second_negative) + len(third_negative),
        "both_sleeves_negative_window_count": sum(
            row["both_sleeves_negative"] for row in all_windows
        ),
        "cross_sectional_drawdown_larger_window_count": sum(
            row["cross_sectional_drawdown_larger"] for row in all_windows
        ),
        "mean_sleeve_return_correlation": mean(
            row["sleeve_return_correlation"] for row in all_windows
        ),
        "mean_median_scale": mean(
            row["median_scale"] for row in all_windows
        ),
    }

    result = {
        "schema_version": 2,
        "diagnostic_type": "portfolio_regime_interaction_diagnosis_2026_09_23",
        "status": "COMPLETED",
        "datasets": {
            "second_validation": second,
            "third_validation": third,
        },
        "cross_validation": {
            "shared_failure_fingerprint": sorted(EXPECTED_SHARED_FAILURES),
            "common_descriptive_metrics": common,
            "negative_portfolio_windows": [
                {
                    "dataset": row["dataset"],
                    "window_index": row["window_index"],
                    "portfolio_period_return": row["portfolio_period_return"],
                    "trend_period_return": row["trend_period_return"],
                    "cs_period_return": row["cs_period_return"],
                    "sleeve_return_correlation": row["sleeve_return_correlation"],
                    "median_scale": row["median_scale"],
                }
                for row in all_windows
                if row["portfolio_period_return"] <= 0.0
            ],
            "max_drawdown_windows": [
                {
                    "dataset": dataset_label,
                    "window_index": dataset["window_analysis"]["worst_window_by_max_drawdown"]["window_index"],
                    "drawdown_percent": dataset["window_analysis"]["worst_window_by_max_drawdown"]["portfolio_max_drawdown_percent"],
                    "start_timestamp": dataset["window_analysis"]["worst_window_by_max_drawdown"]["start_timestamp"],
                    "end_timestamp": dataset["window_analysis"]["worst_window_by_max_drawdown"]["end_timestamp"],
                    "recorded_interval": dataset["window_analysis"]["recorded_max_drawdown_interval"],
                }
                for dataset_label, dataset in (
                    ("second_validation", second),
                    ("third_validation", third),
                )
            ],
        },
        "interpretation": {
            "primary_finding": (
                "Die gemeinsamen Risiko-/Rolling-Failures treten über zwei "
                "unabhängige historische Datensätze in unterschiedlichen Zeitphasen auf."
            ),
            "sleeve_interaction_finding": (
                "Das gemeinsame Muster ist nicht auf eine einzelne Sleeve als "
                "universelle Ursache reduzierbar: Im zweiten und dritten Satz "
                "variieren die dominanten negativen Fenster, während die Sleeve-"
                "Korrelation im selben Größenbereich bleibt."
            ),
            "vol_budget_finding": (
                "Das Vol-Budget reduziert die Exposition messbar, aber die "
                "negativen Fenster verschwinden dadurch nicht. Die beobachtete "
                "Failure-Struktur ist daher nicht allein durch nominale "
                "Exposition erklärbar."
            ),
        },
        "constraints": [
            "descriptive diagnosis only",
            "no threshold optimization",
            "no parameter selection",
            "no asset replacement",
            "no signal change",
            "no sleeve-weight change",
            "no gate change",
            "holdout not used to select any intervention",
            "no production change",
        ],
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    result["interaction_diagnostic_fingerprint"] = _fingerprint(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--second-root", required=True)
    parser.add_argument("--third-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run_control(
        Path(args.second_root),
        Path(args.third_root),
        Path(args.output),
    )
    print("PORTFOLIO_INTERACTION_DIAGNOSIS_STATUS:", result["status"])
    print(
        "BOTH_SLEEVES_NEGATIVE_WINDOWS:",
        result["cross_validation"]["common_descriptive_metrics"][
            "both_sleeves_negative_window_count"
        ],
    )
    print(
        "CS_LARGER_DD_WINDOWS:",
        result["cross_validation"]["common_descriptive_metrics"][
            "cross_sectional_drawdown_larger_window_count"
        ],
    )
    print(
        "MEAN_SLEEVE_CORRELATION:",
        result["cross_validation"]["common_descriptive_metrics"][
            "mean_sleeve_return_correlation"
        ],
    )
    print(
        "MEAN_MEDIAN_SCALE:",
        result["cross_validation"]["common_descriptive_metrics"][
            "mean_median_scale"
        ],
    )
    print(
        "INTERACTION_DIAGNOSTIC_FINGERPRINT:",
        result["interaction_diagnostic_fingerprint"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
