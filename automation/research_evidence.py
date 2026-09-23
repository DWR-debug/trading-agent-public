"""Reproducible evidence-family aggregation for controlled Research runs.

This module only aggregates already generated, fingerprint-verified Research
reports. It does not alter Research-Gates and does not rank or select a
strategy.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from automation.research_workflow import verify_result_fingerprint


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def evidence_fingerprint(summary: dict[str, Any]) -> str:
    payload = dict(summary)
    payload.pop("evidence_fingerprint", None)
    return hashlib.sha256(
        _canonical_json(payload).encode("utf-8")
    ).hexdigest()


def _build_gate_summaries(
    verified_reports: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    overall: dict[str, dict[str, int | str]] = {}
    by_profile: dict[tuple[str, str], dict[str, int | str]] = {}

    for report_index, report in enumerate(verified_reports):
        for dataset_index, dataset in enumerate(report.get("datasets", [])):
            diagnostics = dataset.get("statistical_diagnostics", {})
            profile = diagnostics.get("multiple_testing", {}).get(
                "selection_profile"
            )
            if not isinstance(profile, str) or not profile:
                raise ValueError(
                    "Research-Report "
                    f"{report_index} Dataset {dataset_index} besitzt "
                    "kein gültiges Selection-Profil."
                )

            gates = dataset.get("research_gates", {}).get("gates", [])
            if not isinstance(gates, list) or not gates:
                raise ValueError(
                    "Research-Report "
                    f"{report_index} Dataset {dataset_index} besitzt "
                    "keine gültige Gate-Liste."
                )

            for gate in gates:
                if not isinstance(gate, dict):
                    raise ValueError(
                        "Research-Report "
                        f"{report_index} Dataset {dataset_index} enthält "
                        "ein ungültiges Gate-Objekt."
                    )
                name = gate.get("name")
                scope = gate.get("scope")
                passed = gate.get("passed")
                if not isinstance(name, str) or not name:
                    raise ValueError(
                        "Research-Report "
                        f"{report_index} Dataset {dataset_index} enthält "
                        "ein Gate ohne gültigen Namen."
                    )
                if not isinstance(scope, str) or not scope:
                    raise ValueError(
                        "Research-Report "
                        f"{report_index} Dataset {dataset_index} Gate "
                        f"{name!r} besitzt keinen gültigen Evidenz-Scope."
                    )
                if not isinstance(passed, bool):
                    raise ValueError(
                        "Research-Report "
                        f"{report_index} Dataset {dataset_index} Gate "
                        f"{name!r} besitzt keinen booleschen Status."
                    )

                bucket = overall.setdefault(
                    name,
                    {
                        "scope": scope,
                        "evaluation_count": 0,
                        "passed_count": 0,
                        "failed_count": 0,
                    },
                )
                if bucket["scope"] != scope:
                    raise ValueError(
                        "Research-Report "
                        f"{report_index} Dataset {dataset_index} verwendet "
                        f"für Gate {name!r} inkonsistente Evidenz-Scopes."
                    )
                bucket["evaluation_count"] += 1
                bucket["passed_count"] += int(passed)
                bucket["failed_count"] += int(not passed)

                profile_bucket = by_profile.setdefault(
                    (profile, name),
                    {
                        "scope": scope,
                        "evaluation_count": 0,
                        "passed_count": 0,
                        "failed_count": 0,
                    },
                )
                if profile_bucket["scope"] != scope:
                    raise ValueError(
                        "Research-Report "
                        f"{report_index} Dataset {dataset_index} verwendet "
                        f"für Gate {name!r} je Profil inkonsistente Evidenz-Scopes."
                    )
                profile_bucket["evaluation_count"] += 1
                profile_bucket["passed_count"] += int(passed)
                profile_bucket["failed_count"] += int(not passed)

    gate_summary = [
        {
            "gate": gate_name,
            **counts,
            "pass_rate": (
                counts["passed_count"] / counts["evaluation_count"]
                if counts["evaluation_count"]
                else 0.0
            ),
        }
        for gate_name, counts in sorted(overall.items())
    ]

    profile_gate_summary = [
        {
            "selection_profile": profile,
            "gate": gate_name,
            **counts,
            "pass_rate": (
                counts["passed_count"] / counts["evaluation_count"]
                if counts["evaluation_count"]
                else 0.0
            ),
        }
        for (profile, gate_name), counts in sorted(by_profile.items())
    ]

    return gate_summary, profile_gate_summary



def _failed_criteria(gate: dict[str, Any]) -> list[str]:
    """Return the concrete failed criteria exposed by a gate's details.

    The criteria are non-exclusive: one failed gate may contribute multiple
    diagnostic criteria. This function only interprets fields already emitted
    by the unchanged Research-Gates; it does not alter gate outcomes.
    """
    if gate.get("passed") is True:
        return []

    name = gate.get("name")
    details = gate.get("details", {})
    if not isinstance(details, dict):
        return ["unclassified_failure"]

    failed = []

    if name == "data_quality":
        if details.get("error"):
            failed.append("data_validation_error")
        candle_count = details.get("candle_count")
        minimum = details.get("minimum_candles")
        if (
            isinstance(candle_count, int)
            and isinstance(minimum, int)
            and candle_count < minimum
        ):
            failed.append("insufficient_candles")

    elif name == "backtest":
        if details.get("metrics_valid") is False:
            failed.append("invalid_metrics")
        trade_count = details.get("trade_count")
        minimum = details.get("minimum_trades")
        if (
            isinstance(trade_count, int)
            and isinstance(minimum, int)
            and trade_count < minimum
        ):
            failed.append("insufficient_trades")
        final_capital = details.get("final_capital_eur")
        if isinstance(final_capital, (int, float)) and final_capital <= 0.0:
            failed.append("non_positive_final_capital")
        drawdown = details.get("max_drawdown_percent")
        maximum = details.get("maximum_drawdown_percent")
        if (
            isinstance(drawdown, (int, float))
            and isinstance(maximum, (int, float))
            and drawdown > maximum
        ):
            failed.append("drawdown_exceeded")

    elif name == "walk_forward":
        if details.get("metrics_valid") is False:
            failed.append("invalid_metrics")
        trade_count = details.get("oos_trade_count")
        minimum = details.get("minimum_oos_trades")
        if (
            isinstance(trade_count, int)
            and isinstance(minimum, int)
            and trade_count < minimum
        ):
            failed.append("insufficient_oos_trades")
        profit = details.get("oos_net_profit_eur")
        if isinstance(profit, (int, float)) and profit <= 0.0:
            failed.append("non_positive_oos_profit")
        profit_factor = details.get("profit_factor")
        numeric_profit_factor = (
            float("inf") if profit_factor == "inf" else profit_factor
        )
        minimum_profit_factor = details.get("minimum_profit_factor")
        if (
            isinstance(numeric_profit_factor, (int, float))
            and isinstance(minimum_profit_factor, (int, float))
            and numeric_profit_factor < minimum_profit_factor
        ):
            failed.append("profit_factor_below_minimum")
        drawdown = details.get("oos_max_drawdown_percent")
        maximum = details.get("maximum_drawdown_percent")
        if (
            isinstance(drawdown, (int, float))
            and isinstance(maximum, (int, float))
            and drawdown > maximum
        ):
            failed.append("drawdown_exceeded")

    elif name == "rolling_walk_forward":
        window_count = details.get("window_count")
        if isinstance(window_count, int) and window_count <= 0:
            failed.append("no_windows")
        total_trades = details.get("total_trade_count")
        minimum_trades = details.get("minimum_total_trades")
        if (
            isinstance(total_trades, int)
            and isinstance(minimum_trades, int)
            and total_trades < minimum_trades
        ):
            failed.append("insufficient_total_trades")
        total_profit = details.get("total_net_profit_eur")
        if isinstance(total_profit, (int, float)) and total_profit <= 0.0:
            failed.append("non_positive_total_profit")
        profit_factor = details.get("overall_profit_factor")
        numeric_profit_factor = (
            float("inf") if profit_factor == "inf" else profit_factor
        )
        minimum_profit_factor = details.get("minimum_profit_factor")
        if (
            isinstance(numeric_profit_factor, (int, float))
            and isinstance(minimum_profit_factor, (int, float))
            and numeric_profit_factor < minimum_profit_factor
        ):
            failed.append("profit_factor_below_minimum")
        profitable_ratio = details.get("profitable_window_ratio")
        minimum_ratio = details.get("minimum_profitable_window_ratio")
        if (
            isinstance(profitable_ratio, (int, float))
            and isinstance(minimum_ratio, (int, float))
            and profitable_ratio < minimum_ratio
        ):
            failed.append("profitable_window_ratio_below_minimum")
        zero_trade_ratio = details.get("zero_trade_window_ratio")
        maximum_zero_trade_ratio = details.get(
            "maximum_zero_trade_window_ratio"
        )
        if (
            isinstance(zero_trade_ratio, (int, float))
            and isinstance(maximum_zero_trade_ratio, (int, float))
            and zero_trade_ratio > maximum_zero_trade_ratio
        ):
            failed.append("zero_trade_window_ratio_exceeded")
        average_drawdown = details.get("average_drawdown_percent")
        maximum_drawdown = details.get("maximum_drawdown_percent")
        if (
            isinstance(average_drawdown, (int, float))
            and isinstance(maximum_drawdown, (int, float))
            and average_drawdown > maximum_drawdown
        ):
            failed.append("average_drawdown_exceeded")

    elif name == "robustness":
        variant_count = details.get("variant_count")
        minimum_variants = details.get("minimum_variants")
        if (
            isinstance(variant_count, int)
            and isinstance(minimum_variants, int)
            and variant_count < minimum_variants
        ):
            failed.append("insufficient_variants")
        profitable_ratio = details.get("profitable_variant_ratio")
        minimum_ratio = details.get("minimum_profitable_variant_ratio")
        if (
            isinstance(profitable_ratio, (int, float))
            and isinstance(minimum_ratio, (int, float))
            and profitable_ratio < minimum_ratio
        ):
            failed.append("profitable_variant_ratio_below_minimum")
        stressed_profit = details.get("stressed_net_profit_eur")
        if (
            isinstance(stressed_profit, (int, float))
            and stressed_profit < 0.0
        ):
            failed.append("stressed_profit_negative")

    elif name == "overfit":
        train_return = details.get("train_return_percent")
        if isinstance(train_return, (int, float)) and train_return <= 0.0:
            failed.append("non_positive_train_return")
        ratio = details.get("oos_to_is_return_ratio")
        minimum_ratio = details.get("minimum_oos_to_is_return_ratio")
        if (
            isinstance(ratio, (int, float))
            and isinstance(minimum_ratio, (int, float))
            and ratio < minimum_ratio
        ):
            failed.append("oos_to_is_ratio_below_minimum")

    elif name == "holdout":
        trade_count = details.get("trade_count")
        minimum_trades = details.get("minimum_holdout_trades")
        if (
            isinstance(trade_count, int)
            and isinstance(minimum_trades, int)
            and trade_count < minimum_trades
        ):
            failed.append("insufficient_holdout_trades")
        profit = details.get("net_profit_eur")
        if isinstance(profit, (int, float)) and profit <= 0.0:
            failed.append("non_positive_holdout_profit")
        profit_factor = details.get("profit_factor")
        numeric_profit_factor = (
            float("inf") if profit_factor == "inf" else profit_factor
        )
        minimum_profit_factor = details.get("minimum_profit_factor")
        if (
            isinstance(numeric_profit_factor, (int, float))
            and isinstance(minimum_profit_factor, (int, float))
            and numeric_profit_factor < minimum_profit_factor
        ):
            failed.append("profit_factor_below_minimum")
        drawdown = details.get("max_drawdown_percent")
        maximum_drawdown = details.get("maximum_drawdown_percent")
        if (
            isinstance(drawdown, (int, float))
            and isinstance(maximum_drawdown, (int, float))
            and drawdown > maximum_drawdown
        ):
            failed.append("drawdown_exceeded")

    if not failed:
        failed.append("unclassified_failure")
    return failed


def _build_failure_diagnostics(
    verified_reports: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    overall: dict[str, dict[str, Any]] = {}
    by_profile: dict[tuple[str, str], dict[str, Any]] = {}

    for report in verified_reports:
        for dataset in report.get("datasets", []):
            diagnostics = dataset.get("statistical_diagnostics", {})
            profile = diagnostics.get("multiple_testing", {}).get(
                "selection_profile"
            )
            gates = dataset.get("research_gates", {}).get("gates", [])

            for gate in gates:
                name = gate["name"]
                scope = gate["scope"]

                bucket = overall.setdefault(
                    name,
                    {
                        "scope": scope,
                        "evaluation_count": 0,
                        "failure_count": 0,
                        "criteria_counts": {},
                    },
                )
                bucket["evaluation_count"] += 1

                profile_bucket = by_profile.setdefault(
                    (profile, name),
                    {
                        "scope": scope,
                        "evaluation_count": 0,
                        "failure_count": 0,
                        "criteria_counts": {},
                    },
                )
                profile_bucket["evaluation_count"] += 1

                if gate.get("passed") is True:
                    continue

                bucket["failure_count"] += 1
                for criterion in _failed_criteria(gate):
                    bucket["criteria_counts"][criterion] = (
                        bucket["criteria_counts"].get(criterion, 0) + 1
                    )

                profile_bucket["failure_count"] += 1
                for criterion in _failed_criteria(gate):
                    profile_bucket["criteria_counts"][criterion] = (
                        profile_bucket["criteria_counts"].get(criterion, 0) + 1
                    )

    def render(
        buckets: dict[Any, dict[str, Any]],
        *,
        profile_mode: bool,
    ) -> list[dict[str, Any]]:
        items = []
        for key, bucket in sorted(buckets.items()):
            if profile_mode:
                profile, gate_name = key
            else:
                gate_name = key

            criteria = [
                {
                    "criterion": criterion,
                    "count": count,
                    "failure_rate": (
                        count / bucket["evaluation_count"]
                        if bucket["evaluation_count"]
                        else 0.0
                    ),
                }
                for criterion, count in sorted(
                    bucket["criteria_counts"].items()
                )
            ]

            item = {
                "gate": gate_name,
                "scope": bucket["scope"],
                "evaluation_count": bucket["evaluation_count"],
                "failure_count": bucket["failure_count"],
                "criteria": criteria,
                "interpretation": (
                    "Kriterien sind nicht exklusiv: ein fehlgeschlagenes "
                    "Gate kann mehrere konkrete Ursachenbedingungen "
                    "erfüllen. Die failure_rate bezieht sich auf alle "
                    "Auswertungen dieses Gates. Die Diagnose beschreibt "
                    "nur vorhandene Gate-Details und ändert keine "
                    "Gate-Entscheidung."
                ),
            }
            if profile_mode:
                item["selection_profile"] = profile
            items.append(item)
        return items

    return (
        render(overall, profile_mode=False),
        render(by_profile, profile_mode=True),
    )



def _candidate_fingerprint(candidate: dict[str, Any]) -> str:
    return hashlib.sha256(
        _canonical_json(candidate).encode("utf-8")
    ).hexdigest()


def _build_candidate_diagnostics(
    verified_reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Expose already-computed candidate metrics without re-running Research."""
    diagnostics = []

    for report in verified_reports:
        for dataset in report.get("datasets", []):
            gates = {
                gate["name"]: gate
                for gate in dataset.get("research_gates", {}).get(
                    "gates", []
                )
            }
            walk_forward = dataset.get("walk_forward")
            rolling_section = dataset.get("rolling_walk_forward")
            holdout = dataset.get("holdout")
            if not isinstance(walk_forward, dict):
                continue
            if not isinstance(rolling_section, dict):
                continue
            if not isinstance(holdout, dict):
                continue
            selected_candidate = walk_forward.get("selected_candidate")
            if not isinstance(selected_candidate, dict):
                continue
            rolling = rolling_section.get("summary", {})
            rolling_windows = rolling_section.get("windows", [])
            if not isinstance(rolling, dict):
                continue
            if not isinstance(rolling_windows, list):
                continue
            robustness = gates.get("robustness", {}).get("details", {})
            overfit = gates.get("overfit", {}).get("details", {})
            if not isinstance(robustness, dict):
                robustness = {}
            if not isinstance(overfit, dict):
                overfit = {}

            diagnostics.append(
                {
                    "symbol": dataset.get("symbol"),
                    "interval": dataset.get("interval"),
                    "selection_profile": walk_forward.get(
                        "selection_profile"
                    ),
                    "candidate_fingerprint": _candidate_fingerprint(
                        selected_candidate
                    ),
                    "selected_candidate": selected_candidate,
                    "optimization_candidate_count": dataset.get(
                        "optimization_candidate_count"
                    ),
                    "optimization_reported_top_n": dataset.get(
                        "optimization_reported_top_n"
                    ),
                    "wfo_oos": {
                        "train_candles": walk_forward.get("train_candles"),
                        "test_candles": walk_forward.get("test_candles"),
                        "trade_count": walk_forward.get("test_trade_count"),
                        "net_profit_eur": walk_forward.get(
                            "test_net_profit_eur"
                        ),
                        "return_percent": walk_forward.get(
                            "test_return_percent"
                        ),
                        "profit_factor": walk_forward.get(
                            "test_profit_factor"
                        ),
                        "max_drawdown_percent": walk_forward.get(
                            "test_max_drawdown_percent"
                        ),
                    },
                    "rolling_wf": {
                        "window_count": rolling.get("window_count"),
                        "total_trade_count": rolling.get(
                            "total_trade_count"
                        ),
                        "total_net_profit_eur": rolling.get(
                            "total_net_profit_eur"
                        ),
                        "overall_profit_factor": rolling.get(
                            "overall_profit_factor"
                        ),
                        "profitable_window_ratio": rolling.get(
                            "profitable_window_ratio"
                        ),
                        "zero_trade_window_ratio": rolling.get(
                            "zero_trade_window_ratio"
                        ),
                        "average_drawdown_percent": rolling.get(
                            "average_drawdown_percent"
                        ),
                        "windows": [
                            {
                                "window_index": window.get("window_index"),
                                "selected_candidate_fingerprint": (
                                    _candidate_fingerprint(candidate)
                                    if isinstance(
                                        (candidate := window.get(
                                            "selected_candidate"
                                        )),
                                        dict,
                                    )
                                    else None
                                ),
                                "same_as_wfo_candidate": (
                                    candidate == selected_candidate
                                    if isinstance(candidate, dict)
                                    else None
                                ),
                                "test_net_profit_eur": window.get(
                                    "test_net_profit_eur"
                                ),
                                "test_return_percent": window.get(
                                    "test_return_percent"
                                ),
                                "test_profit_factor": window.get(
                                    "test_profit_factor"
                                ),
                                "test_max_drawdown_percent": window.get(
                                    "test_max_drawdown_percent"
                                ),
                                "test_trade_count": window.get(
                                    "test_trade_count"
                                ),
                            }
                            for window in rolling_windows
                        ],
                        "unique_candidate_count": len(
                            {
                                _canonical_json(
                                    window.get("selected_candidate")
                                )
                                for window in rolling_windows
                                if isinstance(
                                    window.get("selected_candidate"),
                                    dict,
                                )
                            }
                        ),
                    },
                    "robustness": {
                        "variant_count": robustness.get("variant_count"),
                        "profitable_variant_count": robustness.get(
                            "profitable_variant_count"
                        ),
                        "profitable_variant_ratio": robustness.get(
                            "profitable_variant_ratio"
                        ),
                        "stress_cost_multiplier": robustness.get(
                            "stress_cost_multiplier"
                        ),
                        "stressed_net_profit_eur": robustness.get(
                            "stressed_net_profit_eur"
                        ),
                    },
                    "overfit": {
                        "train_return_percent": overfit.get(
                            "train_return_percent"
                        ),
                        "oos_return_percent": overfit.get(
                            "oos_return_percent"
                        ),
                        "oos_to_is_return_ratio": overfit.get(
                            "oos_to_is_return_ratio"
                        ),
                    },
                    "holdout": {
                        "trade_count": holdout.get("trade_count"),
                        "net_profit_eur": holdout.get("net_profit_eur"),
                        "return_percent": holdout.get("return_percent"),
                        "profit_factor": holdout.get("profit_factor"),
                        "max_drawdown_percent": holdout.get(
                            "max_drawdown_percent"
                        ),
                        "permutation_positive_tail_probability": holdout.get(
                            "permutation_positive_tail_probability"
                        ),
                    },
                    "failed_gates": list(
                        dataset.get("research_gates", {}).get(
                            "failed_gates", []
                        )
                    ),
                    "failed_criteria": {
                        gate["name"]: _failed_criteria(gate)
                        for gate in dataset.get("research_gates", {}).get(
                            "gates", []
                        )
                        if not gate.get("passed", False)
                    },
                }
            )

    return diagnostics


def build_evidence_summary(reports: Iterable[dict[str, Any]]) -> dict[str, Any]:
    report_list = list(reports)
    if not report_list:
        raise ValueError("Mindestens ein Research-Report wird benötigt.")

    verified_reports = []
    run_fingerprints = []
    selection_profiles = []
    dataset_results = []

    for index, report in enumerate(report_list):
        if not isinstance(report, dict):
            raise ValueError(
                f"Research-Report {index} muss ein JSON-Objekt sein."
            )

        verify_result_fingerprint(report)

        manifest = report.get("run_manifest", {})
        run_fingerprint = manifest.get("run_fingerprint")
        if not isinstance(run_fingerprint, str) or not run_fingerprint:
            raise ValueError(
                f"Research-Report {index} besitzt keine gültige Run-Identität."
            )

        verified_reports.append(report)
        run_fingerprints.append(run_fingerprint)

        for dataset in report.get("datasets", []):
            diagnostics = dataset.get("statistical_diagnostics", {})
            multiple_testing = diagnostics.get("multiple_testing", {})
            selection_profile = multiple_testing.get("selection_profile")
            if isinstance(selection_profile, str):
                selection_profiles.append(selection_profile)

            dataset_results.append(
                {
                    "symbol": dataset.get("symbol"),
                    "interval": dataset.get("interval"),
                    "status": dataset.get("research_gates", {}).get("status"),
                    "passed": dataset.get("research_gates", {}).get("passed"),
                    "run_fingerprint": run_fingerprint,
                    "result_fingerprint": report.get("result_fingerprint"),
                    "failed_criteria": {
                        gate["name"]: _failed_criteria(gate)
                        for gate in dataset.get("research_gates", {}).get(
                            "gates", []
                        )
                        if not gate.get("passed", False)
                    },
                    "permutation_positive_tail_probability": (
                        diagnostics.get("permutation", {}).get(
                            "positive_tail_probability"
                        )
                    ),
                }
            )

    gate_summary, profile_gate_summary = _build_gate_summaries(
        verified_reports
    )
    failure_diagnostics, profile_failure_diagnostics = (
        _build_failure_diagnostics(verified_reports)
    )
    candidate_diagnostics = _build_candidate_diagnostics(verified_reports)

    statuses = [
        report.get("status")
        for report in verified_reports
    ]

    summary = {
        "report_count": len(verified_reports),
        "unique_run_count": len(set(run_fingerprints)),
        "run_fingerprints": sorted(set(run_fingerprints)),
        "selection_profiles": sorted(set(selection_profiles)),
        "dataset_result_count": len(dataset_results),
        "passed_dataset_count": sum(
            1
            for item in dataset_results
            if item["passed"] is True
        ),
        "blocked_dataset_count": sum(
            1
            for item in dataset_results
            if item["passed"] is False
        ),
        "report_statuses": statuses,
        "evidence_scope": (
            "multi_report"
            if len(verified_reports) > 1
            else "single_report"
        ),
        "gate_summary": gate_summary,
        "profile_gate_summary": profile_gate_summary,
        "failure_diagnostics": failure_diagnostics,
        "profile_failure_diagnostics": profile_failure_diagnostics,
        "candidate_diagnostics": candidate_diagnostics,
        "multiple_testing": {
            "unique_run_count": len(set(run_fingerprints)),
            "unique_selection_profile_count": len(set(selection_profiles)),
            "selection_profiles": sorted(set(selection_profiles)),
            "interpretation": (
                "Die Reports werden als gemeinsame explorative "
                "Evidenzfamilie dokumentiert. Die Aggregation führt "
                "keine nachträgliche Signifikanzkorrektur durch."
            ),
        },
        "permutation": {
            "diagnostic_values": [
                {
                    "symbol": item["symbol"],
                    "interval": item["interval"],
                    "run_fingerprint": item["run_fingerprint"],
                    "positive_tail_probability": item[
                        "permutation_positive_tail_probability"
                    ],
                }
                for item in dataset_results
            ],
            "interpretation": (
                "Permutationswerte werden einzeln und reproduzierbar "
                "aufbewahrt; sie werden nicht zu einer künstlichen "
                "Gesamt-Signifikanz kombiniert."
            ),
        },
        "datasets": dataset_results,
        "source_result_fingerprints": sorted(
            {
                report["result_fingerprint"]
                for report in verified_reports
            }
        ),
    }
    summary["evidence_fingerprint"] = evidence_fingerprint(summary)
    return summary


def write_evidence_summary(
    path,
    reports: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    summary = build_evidence_summary(reports)
    path = str(path)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            summary,
            handle,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
    return summary
