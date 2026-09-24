"""Unified research orchestration entry point.

observe = current/updated market observation
research = existing gated research runner

No mode can place orders and no mode requires an agent API.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from automation.coverage_preflight import run_preflight
from automation.live_market_observer import observe_universe
from automation.network_momentum_lab import run_trial as run_t039_trial
from automation.coverage_candidate_discovery import run_discovery
from automation.adversarial_failure_diagnosis import write_report as write_failure_diagnosis
from automation.cross_trial_failure_diagnosis import write_report as write_cross_trial_diagnosis
from automation.one_command_research import run_universe


DEFAULT_UNIVERSE = "benchmark"

PREREGISTRATIONS = {
    "validation_2026_09_24_network_momentum_t039": (
        Path("research/preregistrations")
        / "trial_039_network_momentum_2026_09_24.json"
    ),
    "validation_2026_09_24_network_momentum_t040": (
        Path("research/preregistrations")
        / "trial_040_network_momentum_2026_09_24.json"
    ),
}

COVERAGE_PREREGISTRATIONS = {
    **PREREGISTRATIONS,
    "validation_2026_09_24_portfolio_risk_control_trend": (
        Path("research/preregistrations")
        / "trial_041_portfolio_risk_control_trend_2026_09_24.json"
    ),
    "validation_2026_09_24_portfolio_risk_control_cs": (
        Path("research/preregistrations")
        / "trial_041_portfolio_risk_control_cs_2026_09_24.json"
    ),
}


def _preregistration_for(universe: str) -> Path:
    try:
        return COVERAGE_PREREGISTRATIONS[universe]
    except KeyError as exc:
        raise ValueError(
            f"Keine Präregistrierung für {universe}."
        ) from exc


def _state_snapshot(
    *,
    mode: str,
    universe: str,
    status: str,
    observation_fingerprint: str | None = None,
    run_fingerprint: str | None = None,
) -> dict:
    return {
        "schema_version": "1.0",
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "universe": universe,
        "status": status,
        "observation_fingerprint": observation_fingerprint,
        "run_fingerprint": run_fingerprint,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
        "agent_usage": {
            "paid_api_budget_usd": 0.0,
            "auto_paid_api_calls": False,
            "free_credit_only": True,
        },
    }


def run(
    *,
    mode: str,
    universe: str = DEFAULT_UNIVERSE,
    output_root: str | Path = "research/runs",
    total: int | None = None,
    resume: bool = False,
) -> dict:
    root = Path(output_root)

    if mode == "observe":
        output = root / universe / "observations" / "latest.json"
        payload = observe_universe(
            universe,
            total=total,
            output=output,
        )
        snapshot = _state_snapshot(
            mode=mode,
            universe=universe,
            status=payload["status"],
            observation_fingerprint=payload["observation_fingerprint"],
        )
    elif mode == "preflight":
        preregistration = _preregistration_for(universe)
        payload = run_preflight(
            preregistration,
            output_root=root / "coverage_preflight",
        )
        snapshot = _state_snapshot(
            mode=mode,
            universe=payload["universe"],
            status=payload["status"],
            run_fingerprint=payload["coverage_fingerprint"],
        )
    elif mode == "discover_coverage":
        report = run_discovery(
            output=root / "coverage_discovery" / "t040_candidates.json",
        )
        snapshot = _state_snapshot(
            mode=mode,
            universe="T040-COVERAGE-CANDIDATE-POOL",
            status=(
                "CANDIDATES_AVAILABLE"
                if report["coverage_valid_candidates"]
                else "NO_COVERAGE_VALID_CANDIDATE"
            ),
            run_fingerprint=report["fingerprint"],
        )
    elif mode == "diagnose_failure":
        report = write_failure_diagnosis(
            output_path=(
                root
                / "diagnostics"
                / "t040_failure_diagnosis.json"
            ),
        )
        snapshot = _state_snapshot(
            mode=mode,
            universe="T040-FAILURE-DIAGNOSIS",
            status=report["status"],
            run_fingerprint=report["fingerprint"],
        )
    elif mode == "diagnose_history":
        report = write_cross_trial_diagnosis(
            output_path=(
                root
                / "diagnostics"
                / "cross_trial_failure_diagnosis.json"
            ),
        )
        snapshot = _state_snapshot(
            mode=mode,
            universe="CROSS-TRIAL-FAILURE-DIAGNOSIS",
            status=report["status"],
            run_fingerprint=report["fingerprint"],
        )
    elif mode == "research":
        if universe in PREREGISTRATIONS:
            preregistration = _preregistration_for(universe)
            coverage = run_preflight(
                preregistration,
                output_root=root / "coverage_preflight",
            )
            if coverage["status"] != "coverage_passed":
                snapshot = _state_snapshot(
                    mode=mode,
                    universe=universe,
                    status=coverage["status"],
                    run_fingerprint=coverage["coverage_fingerprint"],
                )
            else:
                coverage_path = Path(coverage["output"])
                if not coverage_path.is_absolute():
                    coverage_path = Path.cwd() / coverage_path
                output = (
                    root
                    / universe
                    / "formal"
                    / f"{universe.split('_')[-1]}.json"
                )
                report = run_t039_trial(
                    coverage_path,
                    output,
                    preregistration,
                )
                snapshot = _state_snapshot(
                    mode=mode,
                    universe=universe,
                    status=report["status"],
                    run_fingerprint=report["report_fingerprint"],
                )
        else:
            report = run_universe(
                universe,
                minimum_count=1000,
                target_count=total,
                resume=resume,
                run_root=root / universe,
            )
            snapshot = _state_snapshot(
                mode=mode,
                universe=universe,
                status=report.get("status", "UNKNOWN"),
                run_fingerprint=report.get("run_manifest", {}).get("run_fingerprint"),
            )
    else:
        raise ValueError("mode must be observe, preflight, discover_coverage, diagnose_failure, diagnose_history, or research")

    path = root / universe / "orchestrator_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("observe", "preflight", "discover_coverage", "diagnose_failure", "diagnose_history", "research"), required=True)
    parser.add_argument("--universe", default=DEFAULT_UNIVERSE)
    parser.add_argument("--output-root", default="research/runs")
    parser.add_argument("--total", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(**vars(args)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
