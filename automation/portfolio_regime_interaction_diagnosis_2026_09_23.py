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


def _load_and_verify_report(root: Path, report_path: str) -> dict:
    report = _load_json(root / report_path)
    stored = report.pop("report_fingerprint")
    if _fingerprint(report) != stored:
        raise ValueError(f"Report-Fingerprint ungültig: {report_path}")
    report["report_fingerprint"] = stored
    return report


def _load_and_verify_diagnosis(
    root: Path,
    diagnosis_path: str,
    expected_report_fingerprint: str,
) -> dict:
    diagnosis = _load_json(root / diagnosis_path)
    stored = diagnosis.pop("diagnostic_fingerprint")
    if _fingerprint(diagnosis) != stored:
        raise ValueError(f"Diagnose-Fingerprint ungültig: {diagnosis_path}")
    if diagnosis["input"]["source_report_fingerprint"] != expected_report_fingerprint:
        raise ValueError("Diagnose verweist auf den falschen Source-Report.")
    diagnosis["diagnostic_fingerprint"] = stored
    return diagnosis


def _base_snapshot(report: dict) -> dict:
    base = report["scenarios"]["base"]["vol_budget_10pct"]["price_only"]
    return {
        "candidate_status": report["candidate_status"],
        "research": base["research"],
        "holdout": base["holdout"],
        "rolling": base["rolling_summary"],
        "oos_to_is_return_ratio": base["oos_to_is_return_ratio"],
        "failed_gate_checks": sorted(
            name for name, passed in report["gate_contract"]["checks"].items()
            if passed is False
        ),
    }


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
                "max_drawdown_interval": (
                    diagnosis["failure_signature"]["max_drawdown_interval"]
                    if window["window_index"]
                    == next(
                        item["window_index"]
                        for item in diagnosis["windows"]
                        if item["portfolio"]["max_drawdown_percent"]
                        == max(
                            w["portfolio"]["max_drawdown_percent"]
                            for w in diagnosis["windows"]
                        )
                    )
                    else None
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
            "mean_median_scale": mean(
                row["median_scale"] for row in rows
            ),
            "mean_minimum_scale": mean(
                row["minimum_scale"] for row in rows
            ),
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
    report: dict,
    diagnosis: dict,
    label: str,
) -> dict:
    report_snapshot = _base_snapshot(report)
    if report_snapshot["candidate_status"] != "BLOCKED":
        raise ValueError(f"{label}: Kandidat ist nicht BLOCKED.")

    shared_safety = {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
    }
    if diagnosis["safety"] != shared_safety:
        raise ValueError(f"{label}: Safety-Vertrag verletzt.")

    window_data = _window_interaction_snapshot(diagnosis)["windows"]
    max_dd = max(
        window_data,
        key=lambda row: row["portfolio_max_drawdown_percent"],
    )

    return {
        "label": label,
        "report_fingerprint": report["report_fingerprint"],
        "diagnostic_fingerprint": diagnosis["diagnostic_fingerprint"],
        "candidate_status": report["candidate_status"],
        "failed_gate_checks": report_snapshot["failed_gate_checks"],
        "overall": {
            "research_period_return": report_snapshot["research"]["period_return"],
            "research_drawdown_percent": report_snapshot["research"]["max_drawdown_percent"],
            "research_profit_factor": report_snapshot["research"]["profit_factor"],
            "holdout_period_return": report_snapshot["holdout"]["period_return"],
            "holdout_drawdown_percent": report_snapshot["holdout"]["max_drawdown_percent"],
            "holdout_profit_factor": report_snapshot["holdout"]["profit_factor"],
            "rolling_profit_factor": report_snapshot["rolling"]["overall_profit_factor"],
            "rolling_average_drawdown_percent": report_snapshot["rolling"]["average_drawdown_percent"],
            "rolling_profitable_windows": report_snapshot["rolling"]["profitable_windows"],
            "rolling_window_count": report_snapshot["rolling"]["window_count"],
        },
        "window_analysis": {
            "rows": window_data,
            "conditional_means": _conditional_means(window_data),
            "worst_window_by_max_drawdown": max_dd,
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
    second_report = _load_and_verify_report(
        second_root,
        "research/independent_validation_2026_09_23/report.json",
    )
    third_report = _load_and_verify_report(
        third_root,
        "research/third_independent_validation_2026_09_23/report.json",
    )

    second_diag = _load_and_verify_diagnosis(
        second_root,
        "failure_diagnosis_2026_09_23.json",
        second_report["report_fingerprint"],
    )
    third_diag = _load_and_verify_diagnosis(
        third_root,
        "third_validation_failure_diagnosis_2026_09_23.json",
        third_report["report_fingerprint"],
    )

    second = _dataset_analysis(
        second_report,
        second_diag,
        "second_validation",
    )
    third = _dataset_analysis(
        third_report,
        third_diag,
        "third_validation",
    )

    second_failed = set(second["failed_gate_checks"])
    third_failed = set(third["failed_gate_checks"])
    if second_failed & third_failed != EXPECTED_SHARED_FAILURES:
        raise ValueError(
            "Gemeinsamer Failure-Fingerprint entspricht nicht dem archivierten Consensus."
        )

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
        "negative_portfolio_window_count": len(second_negative)
        + len(third_negative),
        "both_sleeves_negative_window_count": sum(
            row["both_sleeves_negative"]
            for row in all_windows
        ),
        "cross_sectional_drawdown_larger_window_count": sum(
            row["cross_sectional_drawdown_larger"]
            for row in all_windows
        ),
        "mean_sleeve_return_correlation": mean(
            row["sleeve_return_correlation"] for row in all_windows
        ),
        "mean_median_scale": mean(
            row["median_scale"] for row in all_windows
        ),
    }

    result = {
        "schema_version": 1,
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
                "Im dritten Satz liegt das einzige negative Portfolio-Fenster "
                "gleichzeitig mit negativen Trend- und Cross-Sectional-Sleeves vor; "
                "im zweiten Satz sind negative Portfolio-Fenster überwiegend mit "
                "negativer Cross-Sectional-Sleeve verbunden. Das Muster ist damit "
                "nicht auf eine einzelne Sleeve als universelle Ursache reduzierbar."
            ),
            "vol_budget_finding": (
                "Die Volatilitätssteuerung senkt die Exposition messbar, aber die "
                "window-level Failure-Muster bleiben auch bei niedrigerem Median-Scale "
                "bestehen. Der Control weist damit auf ein tieferes Interaktions-/Regime-"
                "Problem hin, ohne Kausalität zu behaupten."
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
