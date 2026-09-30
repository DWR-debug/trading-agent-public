"""Retrospective regime-conditioned negative-evidence atlas.

Consumes an immutable completed diagnostic artifact. No new market data,
backtest, optimization, candidate selection, holdout selection, gate change or
authorization is performed.

Purpose: identify regime intervals where multiple rejected signal families show
similar directional behavior, which can motivate a separate state/routing
research question without selecting a winning signal.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SOURCE = "research/evidence/q090_q089_failure_diagnosis_result.json"


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("INPUT_NOT_OBJECT")
    if data.get("status") != "COMPLETED_DIAGNOSTIC_ONLY":
        raise ValueError("SOURCE_NOT_DIAGNOSTIC_ONLY")
    if not data.get("reconstruction", {}).get("no_new_performance_trial"):
        raise ValueError("SOURCE_RECONSTRUCTION_INVALID")
    return data


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def analyze(source: dict[str, Any]) -> dict[str, Any]:
    arms = source.get("arms", {})
    if not isinstance(arms, dict) or not arms:
        raise ValueError("NO_ARMS")

    regime_rows: dict[str, list[dict[str, Any]]] = {}
    for arm, payload in arms.items():
        regimes = payload.get("regimes", {})
        if not isinstance(regimes, dict):
            continue
        for regime, stats in regimes.items():
            if not isinstance(stats, dict) or not stats.get("day_count"):
                continue
            regime_rows.setdefault(regime, []).append(
                {
                    "arm": arm,
                    "day_count": int(stats["day_count"]),
                    "compound_return": float(stats.get("compound_return", 0.0)),
                    "mean_daily_return": float(stats.get("mean_daily_return", 0.0)),
                    "negative_day_fraction": float(stats.get("negative_day_fraction", 0.0)),
                }
            )

    consensus = {}
    for regime, rows in sorted(regime_rows.items()):
        returns = [r["mean_daily_return"] for r in rows]
        positive = sum(x > 0 for x in returns)
        negative = sum(x < 0 for x in returns)
        neutral = len(returns) - positive - negative
        dominant_count = max(positive, negative, neutral)
        if dominant_count == positive and positive > 0:
            direction = "positive"
        elif dominant_count == negative and negative > 0:
            direction = "negative"
        else:
            direction = "mixed_or_flat"

        consensus[regime] = {
            "arm_count": len(rows),
            "positive_arm_count": positive,
            "negative_arm_count": negative,
            "neutral_arm_count": neutral,
            "dominant_share": dominant_count / len(rows) if rows else 0.0,
            "common_direction": direction,
            "mean_of_arm_mean_daily_returns": _mean(returns),
            "median_like_center": sorted(returns)[len(returns) // 2] if returns else 0.0,
            "arms": rows,
        }

    common_mode_candidates = [
        {
            "regime": regime,
            "common_direction": item["common_direction"],
            "dominant_share": item["dominant_share"],
            "arm_count": item["arm_count"],
            "interpretation": "possible common-state exposure; not evidence of a superior signal",
        }
        for regime, item in consensus.items()
        if item["arm_count"] >= 4 and item["dominant_share"] >= 0.8
    ]

    result = {
        "schema_version": "1.0",
        "diagnostic_id": "Q102-REGIME-NEGATIVE-EVIDENCE-2026-09-30",
        "status": "RETROSPECTIVE_REGIME_DIAGNOSTIC_ONLY",
        "source": {
            "path": SOURCE,
            "trial_id": source.get("trial_id"),
            "parent_trial_id": source.get("parent_trial_id"),
            "source_fingerprint": _fingerprint(source),
        },
        "method": {
            "description": "Reclassifies only already-recorded Q090 regime diagnostics into cross-arm directional consensus.",
            "new_market_data": False,
            "new_backtest": False,
            "new_performance_trial": False,
            "holdout_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "gate_change": False,
            "performance_authorization": False,
        },
        "regime_consensus": consensus,
        "possible_common_mode_states": common_mode_candidates,
        "research_questions": [
            {
                "id": "STATE-01",
                "question": "Can a frozen, lagged state topology identify common-mode loss regions before routing mechanisms?",
                "next_gate": "RCCSM synthetic state-routing integrity tests",
            },
            {
                "id": "STATE-02",
                "question": "Does mechanism disagreement contain transition-state information rather than simply noise?",
                "next_gate": "predeclared disagreement-state feasibility test",
            },
            {
                "id": "STATE-03",
                "question": "Can liquidity, volatility and trend state descriptors separate state-wide exposure from mechanism-specific decay?",
                "next_gate": "state-descriptor PIT and stability audit",
            },
        ],
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["analysis_fingerprint"] = _fingerprint(result)
    return result


def markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Q102 Regime Negative-Evidence Atlas",
        "",
        f"Status: {result['status']}",
        f"Fingerprint: {result['analysis_fingerprint']}",
        "",
        "This is retrospective diagnostic analysis only. It does not rank or select signals.",
        "",
        "## Possible common-mode states",
        "",
        "| Regime | Direction | Dominant share | Arms |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in result["possible_common_mode_states"]:
        lines.append(
            f"| {row['regime']} | {row['common_direction']} | "
            f"{row['dominant_share']:.2f} | {row['arm_count']} |"
        )
    lines.extend(["", "## Research questions", ""])
    for q in result["research_questions"]:
        lines.extend(
            [
                f"### {q['id']}",
                q["question"],
                f"Next gate: {q['next_gate']}",
                "",
            ]
        )
    lines.append(
        "Paper-Only: True; Live-Trading: False; Orders: False; Automatic-Promotion: False."
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=SOURCE)
    parser.add_argument("--output-dir", default="research/runs/q102_regime_negative_evidence")
    args = parser.parse_args()

    result = analyze(_load(Path(args.input)))
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "result.md").write_text(markdown(result), encoding="utf-8")
    print("Q102_STATUS:", result["status"])
    print("Q102_COMMON_MODE_STATES:", len(result["possible_common_mode_states"]))
    print("Q102_FINGERPRINT:", result["analysis_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
