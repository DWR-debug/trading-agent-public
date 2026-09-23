"""Stateful autonomous research orchestration.

The loop schedules existing gated research runs; it does not execute orders,
enable live trading, or write research results back into the source branch.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation.one_command_research import run_universe
from research.asset_universes import list_universes


STATE_VERSION = 1


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _state_fingerprint(state: dict[str, Any]) -> str:
    payload = dict(state)
    payload.pop("state_fingerprint", None)
    payload.pop("updated_at", None)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint_value(state: dict[str, Any]) -> str:
    import hashlib

    return hashlib.sha256(
        _state_fingerprint(state).encode("utf-8")
    ).hexdigest()


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    payload.pop("state_fingerprint", None)
    payload["state_fingerprint"] = _fingerprint_value(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    os.replace(temp, path)


def default_universes() -> tuple[str, ...]:
    return tuple(item.name for item in list_universes())


def _new_state(universes: tuple[str, ...], minimum_count: int) -> dict[str, Any]:
    return {
        "state_version": STATE_VERSION,
        "started_at": _timestamp(),
        "updated_at": _timestamp(),
        "status": "RUNNING",
        "universes": list(universes),
        "minimum_count": minimum_count,
        "current_index": 0,
        "completed": [],
        "results": [],
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }


def _load_state(
    path: Path,
    universes: tuple[str, ...],
    minimum_count: int,
    *,
    resume: bool,
) -> dict[str, Any]:
    if not resume or not path.exists():
        return _new_state(universes, minimum_count)

    state = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise ValueError("Research-Loop-State muss ein JSON-Objekt sein.")

    stored_fingerprint = state.get("state_fingerprint")
    if not isinstance(stored_fingerprint, str) or stored_fingerprint != _fingerprint_value(state):
        raise RuntimeError(
            "Research-Loop-State besitzt keinen gültigen Fingerprint."
        )

    if state.get("state_version") != STATE_VERSION:
        raise RuntimeError("Unbekannte Research-Loop-State-Version.")

    if tuple(state.get("universes", ())) != universes:
        raise RuntimeError(
            "Research-Loop-State passt nicht zum aktuellen Universum."
        )

    if state.get("minimum_count") != minimum_count:
        raise RuntimeError(
            "Research-Loop-State passt nicht zum aktuellen minimum_count."
        )

    safety = state.get("safety", {})
    if (
        safety.get("paper_only") is not True
        or safety.get("live_trading_enabled") is not False
        or safety.get("orders_enabled") is not False
    ):
        raise RuntimeError("Unsichere Research-Loop-State-Konfiguration.")

    return state


def _classify_result(report: dict[str, Any]) -> str:
    if report.get("status") == "PASSED":
        return "PASSED"

    failed = set(report.get("failed_gates", []))
    if any("data_quality" in item for item in failed):
        return "BLOCKED"

    if failed:
        return "REJECT"

    return "BLOCKED"


def _record_result(
    state: dict[str, Any],
    universe: str,
    classification: str,
    *,
    report: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    state["results"] = [
        item
        for item in state["results"]
        if item["universe"] != universe
    ]
    state["results"].append(
        {
            "universe": universe,
            "classification": classification,
            "completed_at": _timestamp(),
            "failed_gates": (
                report.get("failed_gates", [])
                if report is not None
                else []
            ),
            "report_status": (
                report.get("status")
                if report is not None
                else None
            ),
            "run_fingerprint": (
                report.get("run_manifest", {}).get("run_fingerprint")
                if report is not None
                else None
            ),
            "error": error,
        }
    )
    if classification in {"PASSED", "REJECT"} and universe not in state["completed"]:
        state["completed"].append(universe)


def run_loop(
    *,
    universes: tuple[str, ...] | None = None,
    minimum_count: int = 1000,
    max_universes: int | None = None,
    state_path: str | Path = "research/autonomous/loop_state.json",
    resume: bool = False,
) -> dict[str, Any]:
    selected = universes or default_universes()
    if not selected:
        raise ValueError("Mindestens ein Research-Universum wird benötigt.")
    if minimum_count < 500:
        raise ValueError("minimum_count muss mindestens 500 sein.")
    if max_universes is not None and max_universes < 1:
        raise ValueError("max_universes muss mindestens 1 sein.")

    path = Path(state_path)
    state = _load_state(
        path,
        selected,
        minimum_count,
        resume=resume,
    )

    state["status"] = "RUNNING"
    state["updated_at"] = _timestamp()
    _atomic_write(path, state)

    completed = set(state.get("completed", []))
    processed = 0
    # Always scan from the beginning on resume. Terminal results are skipped
    # via `completed`; BLOCKED results are retried instead of becoming a
    # permanent PARTIAL state after a transient data/runtime failure.
    for index in range(0, len(selected)):
        universe = selected[index]

        if universe in completed:
            state["current_index"] = index + 1
            continue

        if max_universes is not None and processed >= max_universes:
            break

        state["current_index"] = index
        state["updated_at"] = _timestamp()
        _atomic_write(path, state)

        try:
            report = run_universe(
                universe,
                minimum_count=minimum_count,
                resume=True,
            )
        except Exception as exc:
            _record_result(
                state,
                universe,
                "BLOCKED",
                error=f"{type(exc).__name__}: {exc}",
            )
        else:
            _record_result(
                state,
                universe,
                _classify_result(report),
                report=report,
            )

        processed += 1
        state["current_index"] = index + 1
        state["updated_at"] = _timestamp()
        _atomic_write(path, state)

    all_done = all(
        universe in set(state.get("completed", []))
        for universe in selected
    )
    state["status"] = "COMPLETED" if all_done else "PARTIAL"
    state["updated_at"] = _timestamp()
    _atomic_write(path, state)

    return state


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Autonomer, checkpointbasierter Research-Experiment-Loop."
    )
    parser.add_argument("--universe", action="append", dest="universes")
    parser.add_argument("--minimum-count", type=int, default=1000)
    parser.add_argument("--max-universes", type=int, default=None)
    parser.add_argument(
        "--state",
        default="research/autonomous/loop_state.json",
    )
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    universes = (
        tuple(args.universes)
        if args.universes
        else default_universes()
    )
    state = run_loop(
        universes=universes,
        minimum_count=args.minimum_count,
        max_universes=args.max_universes,
        state_path=args.state,
        resume=args.resume,
    )

    print(f"RESEARCH_LOOP_STATUS: {state['status']}")
    print(f"RESEARCH_LOOP_STATE: {args.state}")
    for item in state["results"]:
        print(
            f"{item['universe']}: {item['classification']}"
        )

    return 0 if state["status"] in {"COMPLETED", "PARTIAL"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
