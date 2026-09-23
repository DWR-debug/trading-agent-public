"""Checkpointed orchestration for selection-profile research experiments.

Each profile executes the existing gated research pipeline against the same
prepared dataset. Every profile receives its own manifest, fingerprint,
checkpoint, report and gate results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation.one_command_research import run_universe
from automation.research_experiment_loop import _classify_result
from optimization.selection_profiles import (
    available_selection_profile_names,
    list_selection_profiles,
)


STATE_VERSION = 1


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _state_fingerprint(state: dict[str, Any]) -> str:
    payload = dict(state)
    payload.pop("state_fingerprint", None)
    payload.pop("updated_at", None)
    return _canonical_hash(payload)


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    payload.pop("state_fingerprint", None)
    payload["state_fingerprint"] = _state_fingerprint(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    os.replace(temp, path)


def _new_state(
    universe: str,
    profiles: tuple[str, ...],
    minimum_count: int,
) -> dict[str, Any]:
    identity = {
        "state_version": STATE_VERSION,
        "universe": universe,
        "profiles": list(profiles),
        "minimum_count": minimum_count,
    }
    return {
        **identity,
        "experiment_fingerprint": _canonical_hash(identity),
        "statistical_family": {
            "family_type": "selection_profile_comparison",
            "profile_count": len(profiles),
            "profiles": list(profiles),
            "shared_input_universe": universe,
            "shared_input_dataset": True,
            "multiple_selection_profiles": len(profiles) > 1,
            "interpretation": (
                "Mehrere Auswahlprofile durchsuchen dieselbe vorbereitete "
                "Datenbasis; die Ergebnisse sind daher als explorative "
                "Vergleichsfamilie zu betrachten."
            ),
        },
        "started_at": _timestamp(),
        "updated_at": _timestamp(),
        "status": "RUNNING",
        "current_index": 0,
        "completed": [],
        "results": [],
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }


def _load_or_create_state(
    path: Path,
    universe: str,
    profiles: tuple[str, ...],
    minimum_count: int,
    *,
    resume: bool,
) -> dict[str, Any]:
    if not resume or not path.exists():
        return _new_state(universe, profiles, minimum_count)

    state = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise ValueError("Experiment-State muss ein JSON-Objekt sein.")

    expected = _new_state(universe, profiles, minimum_count)
    for key in ("state_version", "universe", "profiles", "minimum_count"):
        if state.get(key) != expected[key]:
            raise RuntimeError(
                "Experiment-State passt nicht zur aktuellen "
                f"Konfiguration: {key}"
            )

    stored_state_fingerprint = state.get("state_fingerprint")
    if (
        not isinstance(stored_state_fingerprint, str)
        or stored_state_fingerprint != _state_fingerprint(state)
    ):
        raise RuntimeError(
            "Experiment-State besitzt keinen gültigen State-Fingerprint."
        )

    if state.get("experiment_fingerprint") != expected["experiment_fingerprint"]:
        raise RuntimeError(
            "Experiment-State besitzt keinen passenden Fingerprint."
        )

    safety = state.get("safety", {})
    if (
        safety.get("paper_only") is not True
        or safety.get("live_trading_enabled") is not False
        or safety.get("orders_enabled") is not False
    ):
        raise RuntimeError("Unsichere Selection-Experiment-Konfiguration.")

    return state


def _record(
    state: dict[str, Any],
    profile: str,
    classification: str,
    *,
    report: dict[str, Any] | None = None,
    run_manifest_path: str | None = None,
    error: str | None = None,
) -> None:
    state["results"] = [
        item for item in state["results"] if item["profile"] != profile
    ]

    state["results"].append(
        {
            "profile": profile,
            "classification": classification,
            "completed_at": _timestamp(),
            "report_status": (
                report.get("status") if report is not None else None
            ),
            "run_fingerprint": (
                report.get("run_manifest", {}).get("run_fingerprint")
                if report is not None
                else None
            ),
            "run_manifest": run_manifest_path,
            "report": report.get("_report_path") if report is not None else None,
            "failed_gates": (
                list(report.get("failed_gates", []))
                if report is not None
                else []
            ),
            "error": error,
        }
    )

    if classification in {"PASSED", "REJECT"}:
        if profile not in state["completed"]:
            state["completed"].append(profile)


def run_selection_profile_experiments(
    universe: str,
    *,
    profiles: tuple[str, ...] | None = None,
    minimum_count: int = 1000,
    target_count: int | None = None,
    root: str | Path | None = None,
    state_path: str | Path | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    selected_profiles = profiles or available_selection_profile_names()
    if not selected_profiles:
        raise ValueError("Mindestens ein Selection-Profil wird benötigt.")

    known = set(available_selection_profile_names())
    unknown = sorted(set(selected_profiles) - known)
    if unknown:
        raise ValueError(
            f"Unbekannte Selection-Profile: {', '.join(unknown)}"
        )

    if len(set(selected_profiles)) != len(selected_profiles):
        raise ValueError("Selection-Profile dürfen nicht doppelt angegeben werden.")

    if minimum_count < 500:
        raise ValueError("minimum_count muss mindestens 500 sein.")

    experiment_root = (
        Path(root)
        if root is not None
        else Path("research/runs") / universe / "selection_profiles"
    )
    state_file = (
        Path(state_path)
        if state_path is not None
        else experiment_root / "experiment_state.json"
    )

    state = _load_or_create_state(
        state_file,
        universe,
        selected_profiles,
        minimum_count,
        resume=resume,
    )
    state["status"] = "RUNNING"
    state["updated_at"] = _timestamp()
    _atomic_write(state_file, state)

    completed = set(state.get("completed", []))
    shared_data_manifest = None
    if state.get("results"):
        first_result = state["results"][0]
        run_manifest = first_result.get("run_manifest")
        if run_manifest:
            shared_data_manifest = (
                Path(run_manifest).parent / "data_manifest.json"
            )

    for index, profile in enumerate(selected_profiles):
        if profile in completed:
            state["current_index"] = index + 1
            continue

        profile_root = experiment_root / profile
        prepare_data = shared_data_manifest is None

        try:
            report = run_universe(
                universe,
                minimum_count=minimum_count,
                target_count=target_count,
                resume=True,
                selection_profile=profile,
                run_root=profile_root,
                prepare_data=prepare_data,
                prepared_data_manifest=shared_data_manifest,
            )
        except Exception as exc:
            _record(
                state,
                profile,
                "BLOCKED",
                error=f"{type(exc).__name__}: {exc}",
            )
            processed_report = None
        else:
            report_files = sorted(
                (profile_root / "reports").glob("analysis_*.json")
            )
            report["_report_path"] = (
                str(report_files[-1])
                if report_files
                else None
            )
            classification = _classify_result(report)
            _record(
                state,
                profile,
                classification,
                report=report,
                run_manifest_path=str(profile_root / "run_manifest.json"),
            )
            processed_report = report

        if prepare_data and processed_report is not None:
            shared_data_manifest = profile_root / "data_manifest.json"
        elif shared_data_manifest is None and prepare_data:
            candidate_manifest = profile_root / "data_manifest.json"
            if candidate_manifest.exists():
                shared_data_manifest = candidate_manifest

        completed = set(state.get("completed", []))
        state["current_index"] = index + 1
        state["updated_at"] = _timestamp()
        _atomic_write(state_file, state)

        if processed_report is None and prepare_data:
            break
        if processed_report is not None and state["results"][-1]["classification"] == "BLOCKED":
            break

    all_done = all(
        profile in set(state.get("completed", []))
        for profile in selected_profiles
    )
    state["status"] = "COMPLETED" if all_done else "PARTIAL"
    state["updated_at"] = _timestamp()
    _atomic_write(state_file, state)
    return state


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Vergleicht deterministische Research-Selection-Profile."
    )
    parser.add_argument("--universe", required=True)
    parser.add_argument("--minimum-count", type=int, default=1000)
    parser.add_argument("--target-count", type=int, default=None)
    parser.add_argument(
        "--profile",
        action="append",
        dest="profiles",
        choices=available_selection_profile_names(),
    )
    parser.add_argument(
        "--root",
        default=None,
    )
    parser.add_argument(
        "--state",
        default=None,
    )
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    profiles = (
        tuple(args.profiles)
        if args.profiles
        else available_selection_profile_names()
    )
    state = run_selection_profile_experiments(
        args.universe,
        profiles=profiles,
        minimum_count=args.minimum_count,
        target_count=args.target_count,
        root=args.root,
        state_path=args.state,
        resume=args.resume,
    )

    print(f"SELECTION_EXPERIMENT_STATUS: {state['status']}")
    print(f"SELECTION_EXPERIMENT_FINGERPRINT: {state['experiment_fingerprint']}")
    for item in state["results"]:
        print(
            f"{item['profile']}: {item['classification']} "
            f"| {item['run_fingerprint']}"
        )

    return 0 if state["status"] == "COMPLETED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
