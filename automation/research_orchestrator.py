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
from automation.one_command_research import run_universe


DEFAULT_UNIVERSE = "benchmark"


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
        preregistration = (
            Path("research/preregistrations")
            / "trial_039_network_momentum_2026_09_24.json"
        )
        payload = run_preflight(
            preregistration,
            output_root=root / "coverage_preflight",
        )
        snapshot = _state_snapshot(
            mode=mode,
            universe=universe,
            status=payload["status"],
            run_fingerprint=payload["coverage_fingerprint"],
        )
    elif mode == "research":
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
        raise ValueError("mode must be observe or research")

    path = root / universe / "orchestrator_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("observe", "preflight", "research"), required=True)
    parser.add_argument("--universe", default=DEFAULT_UNIVERSE)
    parser.add_argument("--output-root", default="research/runs")
    parser.add_argument("--total", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(**vars(args)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
