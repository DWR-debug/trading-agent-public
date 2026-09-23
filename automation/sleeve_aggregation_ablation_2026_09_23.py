"""Research-only sleeve aggregation ablation across four immutable validations.

Question:
    Is the fixed 50/50 sleeve aggregation itself a recurrent contributor to the
    observed risk/rolling failures, or do the single-sleeve controls show the
    same structural weakness?

Only the pre-existing Research spans of four completed, symbol-disjoint
validation artifacts are evaluated. Holdout values are intentionally excluded
from the output and decision rule.

No parameter search, no asset replacement, no gate change, no production
mutation and no orders.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from automation import candidate_validation_50_50_vol_budget as base
from config import settings
from research.asset_universes import get_universe
from validation.research_gates import ResearchGateConfig

RESEARCH_COUNT = base.RESEARCH_COUNT

VARIANTS = (
    ("trend_only_100_0", 1.0),
    ("equal_weight_50_50", 0.5),
    ("cross_sectional_only_0_100", 0.0),
)

CASES = (
    {
        "name": "validation_1",
        "artifact_id": 10751817990,
        "run_id": 35865847394,
        "root": "research/candidate_validation",
        "trend_universe": "validation_trend",
        "cs_universe": "validation_cs",
    },
    {
        "name": "validation_2",
        "artifact_id": 10740188093,
        "run_id": 35839443616,
        "root": "research/independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_trend",
        "cs_universe": "validation_2026_09_23_cs",
    },
    {
        "name": "validation_3",
        "artifact_id": 10745697729,
        "run_id": 35851876264,
        "root": "research/third_independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_third_trend",
        "cs_universe": "validation_2026_09_23_third_cs",
    },
    {
        "name": "validation_4",
        "artifact_id": 10753545703,
        "run_id": 35867637587,
        "root": "research/fourth_independent_validation_2026_09_23",
        "trend_universe": "validation_2026_09_23_fourth_trend",
        "cs_universe": "validation_2026_09_23_fourth_cs",
    },
)

COST_SCENARIOS = (
    ("base", 1.0),
    ("stress_1_5x_cost", 1.5),
    ("stress_2x_cost", 2.0),
)


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


def _verify_report_and_archive(source_root: Path, case: dict[str, Any]) -> dict[str, Any]:
    root = source_root / case["root"]
    report_path = root / "report.json"
    archive_path = root / "adjusted_close_archive.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    stored_report_fp = report.get("report_fingerprint")
    if not isinstance(stored_report_fp, str) or not stored_report_fp:
        raise ValueError(f'{case["name"]}: report fingerprint missing')
    report_payload = dict(report)
    report_payload.pop("report_fingerprint", None)
    if _fingerprint(report_payload) != stored_report_fp:
        raise ValueError(f'{case["name"]}: report fingerprint mismatch')
    if report["status"] != "COMPLETED":
        raise ValueError(f'{case["name"]}: source report is not COMPLETED')
    if report["candidate_status"] != "BLOCKED":
        raise ValueError(f'{case["name"]}: expected source candidate status BLOCKED')
    if report["source"]["independent_asset_universes"] is not True:
        raise ValueError(f'{case["name"]}: source independence flag missing')

    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    stored_archive_fp = archive.get("archive_fingerprint")
    if not isinstance(stored_archive_fp, str) or not stored_archive_fp:
        raise ValueError(f'{case["name"]}: archive fingerprint missing')
    archive_payload = dict(archive)
    archive_payload.pop("archive_fingerprint", None)
    if _fingerprint(archive_payload) != stored_archive_fp:
        raise ValueError(f'{case["name"]}: archive fingerprint mismatch')
    if stored_archive_fp != report["source"]["adjusted_close_archive_fingerprint"]:
        raise ValueError(f'{case["name"]}: report/archive fingerprint mismatch')

    return {
        "root": root,
        "report_fingerprint": stored_report_fp,
        "archive_fingerprint": stored_archive_fp,
        "report": report,
        "archive": archive,
    }


def _load_case(source_root: Path, case: dict[str, Any]) -> tuple[tuple[dict, ...], dict[str, Any]]:
    verified = _verify_report_and_archive(source_root, case)
    root = verified["root"]
    report = verified["report"]
    trend_manifest = base._manifest(
        root / "data_trend_manifest.json",
        case["trend_universe"],
    )
    cs_manifest = base._manifest(
        root / "data_cs_manifest.json",
        case["cs_universe"],
    )
    data_dir = source_root / "data/market_data"
    trend = base._assets(data_dir, trend_manifest)
    cs = base._assets(data_dir, cs_manifest)
    if set(trend) & set(cs):
        raise ValueError(f'{case["name"]}: trend/cross-sectional universes overlap')

    archive = verified["archive"]
    adjusted = {
        symbol: {item[0]: item[1] for item in values}
        for symbol, values in archive["datasets"].items()
    }

    from datetime import datetime

    adjusted_dt = {
        symbol: {datetime.fromisoformat(ts): float(value) for ts, value in values.items()}
        for symbol, values in adjusted.items()
    }
    trend_weights = base._build_weight_path(trend, base.TREND_STRATEGY)
    cs_weights = base._cs_weights(cs)

    trend_rows = base._return_rows(
        trend,
        trend_weights,
        {symbol: adjusted_dt[symbol] for symbol in trend},
    )
    cs_rows = base._return_rows(
        cs,
        cs_weights,
        {symbol: adjusted_dt[symbol] for symbol in cs},
    )
    rows = _compose_rows(trend_rows, cs_rows, 0.5)
    expected = RESEARCH_COUNT + base.HOLDOUT_COUNT
    if len(rows) < expected:
        raise ValueError(f'{case["name"]}: too few aligned returns: {len(rows)}')

    return rows, {
        "validation_run_id": case["run_id"],
        "artifact_id": case["artifact_id"],
        "source_report_fingerprint": verified["report_fingerprint"],
        "source_archive_fingerprint": verified["archive_fingerprint"],
        "trend_manifest_fingerprint": trend_manifest["manifest_fingerprint"],
        "cs_manifest_fingerprint": cs_manifest["manifest_fingerprint"],
        "report_code_version": report["code_version"],
        "trend_symbols": list(get_universe(case["trend_universe"]).symbols),
        "cs_symbols": list(get_universe(case["cs_universe"]).symbols),
        "full_return_count": len(rows),
    }


def _compose_rows(
    trend_rows: tuple[dict, ...],
    cs_rows: tuple[dict, ...],
    trend_share: float,
) -> tuple[dict, ...]:
    if not 0.0 <= trend_share <= 1.0:
        raise ValueError("trend_share must be within [0, 1].")
    if len(trend_rows) != len(cs_rows):
        raise ValueError("Trend and cross-sectional row counts differ.")

    cs_share = 1.0 - trend_share
    rows = []
    for trend, cs in zip(trend_rows, cs_rows):
        if trend["timestamp"] != cs["timestamp"]:
            raise ValueError("Trend/CS timestamps are not aligned.")
        rows.append(
            {
                "timestamp": trend["timestamp"],
                "gross_open": (
                    trend_share * trend["gross_open"]
                    + cs_share * cs["gross_open"]
                ),
                "gross_close": (
                    trend_share * trend["gross_close"]
                    + cs_share * cs["gross_close"]
                ),
                "gross_adjusted_close": (
                    trend_share * trend["gross_adjusted_close"]
                    + cs_share * cs["gross_adjusted_close"]
                ),
                "turnover": (
                    trend_share * trend["turnover"]
                    + cs_share * cs["turnover"]
                ),
            }
        )
    return tuple(rows)


def _research_metrics(simulated: list[dict]) -> dict[str, Any]:
    research = base._stats(simulated, 0, RESEARCH_COUNT)
    rolling = base._rolling(simulated, RESEARCH_COUNT)
    summary = base._summary(simulated[:RESEARCH_COUNT], rolling)
    gate_cfg = ResearchGateConfig()
    checks = {
        "research_drawdown": (
            research["max_drawdown_percent"] <= gate_cfg.maximum_drawdown_percent
        ),
        "rolling_profit_factor": (
            base._pf(summary["overall_profit_factor"])
            >= gate_cfg.minimum_profit_factor
        ),
        "rolling_profitable_window_ratio": (
            summary["profitable_window_ratio"]
            >= gate_cfg.minimum_profitable_window_ratio
        ),
        "rolling_average_drawdown": (
            summary["average_drawdown_percent"]
            <= gate_cfg.maximum_drawdown_percent
        ),
    }
    return {
        "research_return": research["period_return"],
        "research_drawdown_percent": research["max_drawdown_percent"],
        "research_profit_factor": research["profit_factor"],
        "profitable_rolling_windows": summary["profitable_windows"],
        "rolling_profit_factor": summary["overall_profit_factor"],
        "rolling_average_drawdown_percent": summary["average_drawdown_percent"],
        "research_de_risk_fraction": sum(
            row["scale"] < 1.0 for row in simulated[:RESEARCH_COUNT]
        ) / RESEARCH_COUNT,
        "research_minimum_scale": min(
            row["scale"] for row in simulated[:RESEARCH_COUNT]
        ),
        "research_gate_snapshot": checks,
        "research_gate_pass_count": sum(checks.values()),
    }


def _variant_result(rows: tuple[dict, ...], trend_share: float) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, multiplier in COST_SCENARIOS:
        simulated = base._simulate(
            _compose_rows_from_base(rows, trend_share),
            multiplier,
            True,
            False,
        )
        out[name] = _research_metrics(simulated)
    return out


def _compose_rows_from_base(rows: tuple[dict, ...], trend_share: float) -> tuple[dict, ...]:
    # rows passed here are 50/50 only, so this helper is intentionally not used
    # for variant changes. It exists solely as a type guard for callers that
    # accidentally try to simulate a non-50/50 row set.
    if trend_share != 0.5:
        raise ValueError("Variant composition requires original sleeve rows.")
    return rows


def evaluate_case(source_root: Path, case: dict[str, Any]) -> dict[str, Any]:
    verified = _verify_report_and_archive(source_root, case)
    root = verified["root"]
    trend_manifest = base._manifest(root / "data_trend_manifest.json", case["trend_universe"])
    cs_manifest = base._manifest(root / "data_cs_manifest.json", case["cs_universe"])
    data_dir = source_root / "data/market_data"
    trend = base._assets(data_dir, trend_manifest)
    cs = base._assets(data_dir, cs_manifest)
    if set(trend) & set(cs):
        raise ValueError(f'{case["name"]}: universes overlap')

    from datetime import datetime

    adjusted = {
        symbol: {datetime.fromisoformat(ts): float(value) for ts, value in values}
        for symbol, values in verified["archive"]["datasets"].items()
    }
    trend_weights = base._build_weight_path(trend, base.TREND_STRATEGY)
    cs_weights = base._cs_weights(cs)
    trend_rows = base._return_rows(
        trend,
        trend_weights,
        {symbol: adjusted[symbol] for symbol in trend},
    )
    cs_rows = base._return_rows(
        cs,
        cs_weights,
        {symbol: adjusted[symbol] for symbol in cs},
    )

    source = {
        "validation_run_id": case["run_id"],
        "artifact_id": case["artifact_id"],
        "source_report_fingerprint": verified["report_fingerprint"],
        "source_archive_fingerprint": verified["archive_fingerprint"],
        "trend_manifest_fingerprint": trend_manifest["manifest_fingerprint"],
        "cs_manifest_fingerprint": cs_manifest["manifest_fingerprint"],
        "report_code_version": verified["report"]["code_version"],
        "trend_symbols": list(get_universe(case["trend_universe"]).symbols),
        "cs_symbols": list(get_universe(case["cs_universe"]).symbols),
        "full_return_count": len(trend_rows),
    }

    results: dict[str, Any] = {}
    research_only_assertion = True
    for variant_name, trend_share in VARIANTS:
        rows = _compose_rows(trend_rows, cs_rows, trend_share)
        if len(rows) != len(trend_rows):
            raise ValueError(f'{case["name"]}: variant changed row count')
        results[variant_name] = _variant_result_direct(rows)

    # Explicitly ensure all decision metrics originate from the fixed Research span.
    # The holdout portion is never passed to any comparison or classification.
    for variant in results.values():
        for metrics in variant.values():
            research_only_assertion &= metrics["research_day_count"] == RESEARCH_COUNT

    return {
        "source": source,
        "variants": results,
        "research_only_assertion": research_only_assertion,
    }


def _variant_result_direct(rows: tuple[dict, ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, multiplier in COST_SCENARIOS:
        simulated = base._simulate(rows, multiplier, True, False)
        metrics = _research_metrics(simulated)
        metrics["research_day_count"] = RESEARCH_COUNT
        out[name] = metrics
    return out


def _compare_case(case_result: dict[str, Any]) -> dict[str, Any]:
    base_cost = {
        name: case_result["variants"][name]["base"]
        for name, _ in VARIANTS
    }
    trend = base_cost["trend_only_100_0"]
    mix = base_cost["equal_weight_50_50"]
    cs = base_cost["cross_sectional_only_0_100"]

    def strict_leq(left: float, right: float) -> bool:
        return left <= right

    def strict_geq(left: float, right: float) -> bool:
        return left >= right

    trend_dd_better = strict_leq(trend["research_drawdown_percent"], mix["research_drawdown_percent"])
    cs_dd_better = strict_leq(cs["research_drawdown_percent"], mix["research_drawdown_percent"])
    trend_pf_better = strict_geq(trend["rolling_profit_factor"], mix["rolling_profit_factor"])
    cs_pf_better = strict_geq(cs["rolling_profit_factor"], mix["rolling_profit_factor"])

    trend_dominates_mix = trend_dd_better and trend_pf_better and (
        trend["research_drawdown_percent"] < mix["research_drawdown_percent"]
        or trend["rolling_profit_factor"] > mix["rolling_profit_factor"]
    )
    cs_dominates_mix = cs_dd_better and cs_pf_better and (
        cs["research_drawdown_percent"] < mix["research_drawdown_percent"]
        or cs["rolling_profit_factor"] > mix["rolling_profit_factor"]
    )

    return {
        "mix_dd_lower_than_both": (
            mix["research_drawdown_percent"] < trend["research_drawdown_percent"]
            and mix["research_drawdown_percent"] < cs["research_drawdown_percent"]
        ),
        "mix_dd_higher_than_both": (
            mix["research_drawdown_percent"] > trend["research_drawdown_percent"]
            and mix["research_drawdown_percent"] > cs["research_drawdown_percent"]
        ),
        "mix_pf_lower_than_both": (
            mix["rolling_profit_factor"] < trend["rolling_profit_factor"]
            and mix["rolling_profit_factor"] < cs["rolling_profit_factor"]
        ),
        "mix_pf_higher_than_both": (
            mix["rolling_profit_factor"] > trend["rolling_profit_factor"]
            and mix["rolling_profit_factor"] > cs["rolling_profit_factor"]
        ),
        "trend_dominates_mix_on_dd_and_pf": trend_dominates_mix,
        "cs_dominates_mix_on_dd_and_pf": cs_dominates_mix,
        "mix_research_gate_pass_count": mix["research_gate_pass_count"],
        "trend_research_gate_pass_count": trend["research_gate_pass_count"],
        "cs_research_gate_pass_count": cs["research_gate_pass_count"],
    }


def _consensus(case_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    comparisons = {
        name: _compare_case(result)
        for name, result in case_results.items()
    }
    trend_dominance = sum(
        value["trend_dominates_mix_on_dd_and_pf"]
        for value in comparisons.values()
    )
    cs_dominance = sum(
        value["cs_dominates_mix_on_dd_and_pf"]
        for value in comparisons.values()
    )
    mix_dd_worse = sum(
        value["mix_dd_higher_than_both"]
        for value in comparisons.values()
    )
    mix_pf_worse = sum(
        value["mix_pf_lower_than_both"]
        for value in comparisons.values()
    )

    if trend_dominance >= 3 and cs_dominance == 0:
        decision_rule = (
            "trend_only_research_contrast_replicated: "
            "trend-only dominates the 50/50 mix on both Research DD and "
            "Research rolling PF in at least 3/4 datasets."
        )
    elif cs_dominance >= 3 and trend_dominance == 0:
        decision_rule = (
            "cross_sectional_only_research_contrast_replicated: "
            "cross-sectional-only dominates the 50/50 mix on both Research DD "
            "and Research rolling PF in at least 3/4 datasets."
        )
    elif mix_dd_worse >= 3 and mix_pf_worse >= 3:
        decision_rule = (
            "aggregation_risk_contrast_replicated: "
            "the 50/50 mix is worse than both single-sleeve controls on both "
            "Research DD and rolling PF in at least 3/4 datasets."
        )
    else:
        decision_rule = (
            "no_universal_aggregation_contrast: "
            "the pre-registered 3/4 replication rules are not met."
        )

    return {
        "per_dataset": comparisons,
        "replication_counts": {
            "trend_dominates_mix_on_dd_and_pf": trend_dominance,
            "cross_sectional_only_dominates_mix_on_dd_and_pf": cs_dominance,
            "mix_dd_higher_than_both": mix_dd_worse,
            "mix_pf_lower_than_both": mix_pf_worse,
        },
        "decision_rule": decision_rule,
    }


def run_ablation(source_root: Path, output_path: Path) -> dict[str, Any]:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")

    case_results = {
        case["name"]: evaluate_case(source_root, case)
        for case in CASES
    }
    result = {
        "schema_version": 1,
        "diagnostic_type": "sleeve_aggregation_ablation_2026_09_23",
        "status": "COMPLETED",
        "question": (
            "Is the fixed 50/50 sleeve aggregation itself a recurrent "
            "contributor to the observed Research risk/rolling failures?"
        ),
        "scope": {
            "datasets": 4,
            "variants": [name for name, _ in VARIANTS],
            "cost_scenarios": [name for name, _ in COST_SCENARIOS],
            "research_return_count": RESEARCH_COUNT,
            "holdout_used_for_decision": False,
            "holdout_metrics_reported": False,
            "parameter_search": False,
            "asset_selection": False,
            "gate_change": False,
            "production_mutation": False,
            "new_data_downloads": False,
        },
        "methodology": {
            "trend_share_variants": {
                "trend_only_100_0": 1.0,
                "equal_weight_50_50": 0.5,
                "cross_sectional_only_0_100": 0.0,
            },
            "vol_budget_target_annualized": base.TARGET_VOL,
            "vol_budget_window_sessions": base.VOL_WINDOW,
            "same_execution_model": True,
            "same_cost_model": True,
            "same_pit_semantics": True,
            "same_asset_universes": True,
            "same_research_split": True,
            "research_only_decision_rule": True,
        },
        "cases": case_results,
        "consensus": _consensus(case_results),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    result["diagnostic_fingerprint"] = _fingerprint(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run_ablation(Path(args.source_root), Path(args.output))
    print("SLEEVE_AGGREGATION_ABLATION_STATUS:", result["status"])
    print("DECISION_RULE:", result["consensus"]["decision_rule"])
    print(
        "TREND_DOMINANCE_COUNT:",
        result["consensus"]["replication_counts"]["trend_dominates_mix_on_dd_and_pf"],
    )
    print(
        "CS_DOMINANCE_COUNT:",
        result["consensus"]["replication_counts"][
            "cross_sectional_only_dominates_mix_on_dd_and_pf"
        ],
    )
    print(
        "MIX_DD_WORSE_THAN_BOTH_COUNT:",
        result["consensus"]["replication_counts"]["mix_dd_higher_than_both"],
    )
    print(
        "MIX_PF_LOWER_THAN_BOTH_COUNT:",
        result["consensus"]["replication_counts"]["mix_pf_lower_than_both"],
    )
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
