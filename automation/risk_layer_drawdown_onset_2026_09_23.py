"""Research-only diagnosis of risk-layer timing at maximum drawdown onset.

The fixed 50/50 candidate and its 63-session / 10% volatility budget are kept
unchanged. For each of four immutable validation artifacts, only the Research
span is inspected.

Question:
    Was the risk layer already de-risked at, or immediately before, the onset
    of its own maximum Research drawdown, or does de-risking generally arrive
    only after the drawdown has begun?

No parameter search, no asset selection, no holdout decision, no production
mutation, and no orders.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from automation import candidate_validation_50_50_vol_budget as base
from config import settings

RESEARCH_COUNT = base.RESEARCH_COUNT

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


def _canon(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fp(value: object) -> str:
    return hashlib.sha256(_canon(value).encode()).hexdigest()


def _load_rows(source_root: Path, case: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    root = source_root / case["root"]
    report = json.loads((root / "report.json").read_text(encoding="utf-8"))
    stored_report_fp = report["report_fingerprint"]
    report_payload = dict(report)
    report_payload.pop("report_fingerprint", None)
    if _fp(report_payload) != stored_report_fp:
        raise ValueError(f'{case["name"]}: report fingerprint mismatch')
    if report["status"] != "COMPLETED":
        raise ValueError(f'{case["name"]}: report is not completed')
    if report["candidate_status"] != "BLOCKED":
        raise ValueError(f'{case["name"]}: source candidate must remain BLOCKED')

    archive = json.loads(
        (root / "adjusted_close_archive.json").read_text(encoding="utf-8")
    )
    stored_archive_fp = archive["archive_fingerprint"]
    archive_payload = dict(archive)
    archive_payload.pop("archive_fingerprint", None)
    if _fp(archive_payload) != stored_archive_fp:
        raise ValueError(f'{case["name"]}: archive fingerprint mismatch')
    if stored_archive_fp != report["source"]["adjusted_close_archive_fingerprint"]:
        raise ValueError(f'{case["name"]}: report/archive mismatch')

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
        raise ValueError(f'{case["name"]}: validation universes overlap')

    adjusted = {
        symbol: {
            datetime.fromisoformat(ts): float(value)
            for ts, value in values
        }
        for symbol, values in archive["datasets"].items()
    }

    trend_weights = base._build_weight_path(trend, base.TREND_STRATEGY)
    cs_weights = base._cs_weights(cs)
    rows = base._align(
        trend,
        trend_weights,
        {symbol: adjusted[symbol] for symbol in trend},
        cs,
        cs_weights,
        {symbol: adjusted[symbol] for symbol in cs},
    )
    if len(rows) != RESEARCH_COUNT + base.HOLDOUT_COUNT:
        raise ValueError(f'{case["name"]}: unexpected return count')
    return rows


def _max_drawdown_interval(
    simulated: list[dict[str, Any]],
) -> tuple[int, int, float]:
    research = simulated[:RESEARCH_COUNT]
    equity = peak_equity = 1.0
    peak_index = 0
    best = (0, 0, 0.0)
    for index, row in enumerate(research):
        equity *= 1.0 + row["net_return"]
        if equity > peak_equity:
            peak_equity = equity
            peak_index = index
        drawdown = 1.0 - equity / peak_equity
        if drawdown > best[2]:
            best = (peak_index, index, drawdown)
    return best


def _analyze_case(rows: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    simulated = base._simulate(rows, 1.0, True, False)
    peak_index, trough_index, max_dd = _max_drawdown_interval(simulated)
    episode_start = min(peak_index + 1, RESEARCH_COUNT - 1)
    episode = simulated[episode_start : trough_index + 1]

    activation_index = None
    for offset, row in enumerate(episode):
        if row["scale"] < 1.0:
            activation_index = episode_start + offset
            break

    pre_window_start = max(0, episode_start - 5)
    pre_window = simulated[pre_window_start:episode_start]
    first_two = episode[:2]

    worsening_days = []
    equity = 1.0
    previous_equity = 1.0
    for row in simulated[:RESEARCH_COUNT]:
        equity *= 1.0 + row["net_return"]
        worsening_days.append(equity < previous_equity)
        previous_equity = equity

    worsening_episode = [
        (row, worsening_days[index])
        for index, row in enumerate(
            simulated[episode_start : trough_index + 1],
            start=episode_start,
        )
    ]

    early_delivered = bool(first_two) and all(row["scale"] < 1.0 for row in first_two)
    onset_active = bool(episode) and episode[0]["scale"] < 1.0
    pre_peak_active = simulated[peak_index]["scale"] < 1.0

    return {
        "max_drawdown_percent": max_dd * 100.0,
        "peak_index": peak_index,
        "trough_index": trough_index,
        "episode_length_days": len(episode),
        "peak_timestamp": simulated[peak_index]["timestamp"].isoformat(),
        "trough_timestamp": simulated[trough_index]["timestamp"].isoformat(),
        "scale_at_peak": simulated[peak_index]["scale"],
        "scale_one_to_five_days_before_onset": [
            row["scale"] for row in pre_window
        ],
        "pre_onset_de_risk_fraction_5d": (
            sum(row["scale"] < 1.0 for row in pre_window) / len(pre_window)
            if pre_window
            else 0.0
        ),
        "scale_first_five_drawdown_days": [
            row["scale"] for row in episode[:5]
        ],
        "onset_day_de_risk": onset_active,
        "first_two_drawdown_days_both_de_risk": early_delivered,
        "activation_index": activation_index,
        "activation_lag_drawdown_days": (
            activation_index - episode_start
            if activation_index is not None
            else None
        ),
        "full_episode_de_risk_fraction": (
            sum(row["scale"] < 1.0 for row in episode) / len(episode)
            if episode
            else 0.0
        ),
        "worsening_episode_de_risk_fraction": (
            sum(row["scale"] < 1.0 for row, worsening in worsening_episode if worsening)
            / sum(1 for _, worsening in worsening_episode if worsening)
            if any(worsening for _, worsening in worsening_episode)
            else 0.0
        ),
        "minimum_episode_scale": (
            min(row["scale"] for row in episode) if episode else 1.0
        ),
    }


def _classify(cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    delayed = sum(
        case["activation_lag_drawdown_days"] is None
        or case["activation_lag_drawdown_days"] >= 2
        for case in cases.values()
    )
    proactive = sum(
        case["onset_day_de_risk"]
        for case in cases.values()
    )
    both_early = sum(
        case["first_two_drawdown_days_both_de_risk"]
        for case in cases.values()
    )

    if delayed >= 3:
        decision = (
            "replicated_delayed_risk_layer_onset: "
            "in at least 3/4 maximum-Research-drawdown episodes, the fixed "
            "risk layer is not de-risked until at least two drawdown days "
            "after episode onset, or never de-risks during the episode."
        )
    elif proactive >= 3:
        decision = (
            "replicated_proactive_risk_layer_onset: "
            "the fixed risk layer is already de-risked on the first day of "
            "the maximum-Research-drawdown episode in at least 3/4 datasets."
        )
    else:
        decision = (
            "mixed_risk_layer_onset: "
            "the pre-registered 3/4 timing-consensus rules are not met."
        )

    return {
        "replication_counts": {
            "delayed_or_never": delayed,
            "onset_day_already_de_risked": proactive,
            "first_two_days_both_de_risked": both_early,
        },
        "decision_rule": decision,
    }


def run_diagnosis(source_root: Path, output_path: Path) -> dict[str, Any]:
    if settings.PAPER_ONLY is not True or settings.LIVE_TRADING_ENABLED is not False:
        raise RuntimeError("Paper-only safety contract violated.")

    cases = {
        case["name"]: _analyze_case(_load_rows(source_root, case))
        for case in CASES
    }

    result = {
        "schema_version": 1,
        "diagnostic_type": "risk_layer_drawdown_onset_2026_09_23",
        "status": "COMPLETED",
        "question": (
            "Does the fixed 63-session/10% volatility risk layer de-risk "
            "before or at the onset of the portfolio's own maximum Research "
            "drawdown?"
        ),
        "scope": {
            "datasets": 4,
            "research_return_count": RESEARCH_COUNT,
            "holdout_used_for_decision": False,
            "holdout_metrics_reported": False,
            "new_data_downloads": False,
            "parameter_search": False,
            "selection": False,
            "gate_changes": False,
            "production_mutation": False,
        },
        "methodology": {
            "risk_layer_window_sessions": base.VOL_WINDOW,
            "risk_layer_target_annualized_volatility": base.TARGET_VOL,
            "candidate_architecture_fixed": True,
            "cost_multiplier": 1.0,
            "drawdown_definition": "maximum peak-to-trough drawdown inside the fixed Research span",
            "drawdown_episode_start": "first session after the local peak preceding the maximum trough",
            "delayed_definition": (
                "first risk-layer de-risking occurs >=2 drawdown days after "
                "episode onset, or no de-risking occurs during the episode"
            ),
            "proactive_definition": "risk-layer scale < 1.0 on the first drawdown-episode day",
            "timing_consensus_threshold": "3/4 independent datasets",
            "descriptive_not_causal": True,
        },
        "cases": cases,
        "consensus": _classify(cases),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    result["diagnostic_fingerprint"] = _fp(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    print("RISK_LAYER_DRAWDOWN_ONSET_STATUS:", result["status"])
    print("DECISION_RULE:", result["consensus"]["decision_rule"])
    print("REPLICATION_COUNTS:", result["consensus"]["replication_counts"])
    print("DIAGNOSTIC_FINGERPRINT:", result["diagnostic_fingerprint"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_diagnosis(Path(args.source_root), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
