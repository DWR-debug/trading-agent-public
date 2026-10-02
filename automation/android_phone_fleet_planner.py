"""Fail-closed Android phone fleet runner discovery."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

SLOTS = {
    "01": "samsung-phone-01",
    "02": "samsung-phone-02",
    "03": "samsung-phone-03",
}
RUNTIME_STATUS_DIR = Path("ops/android_phone_runtime_status")
ACCEPTED_STATUS = "ANDROID_PHONE_UTILITY_ACCEPTED"


def load_registry(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        str(d["runner_label"])
        for d in payload.get("devices", [])
        if d.get("enabled") and d.get("runner_label")
    }


def discover_online_labels(repository: str) -> tuple[set[str], str]:
    try:
        raw = subprocess.check_output(
            ["gh", "api", f"/repos/{repository}/actions/runners?per_page=100"],
            text=True,
            stderr=subprocess.PIPE,
        )
        payload: dict[str, Any] = json.loads(raw)
    except (subprocess.CalledProcessError, OSError, json.JSONDecodeError):
        return set(), "RUNNER_DISCOVERY_UNAVAILABLE"

    labels = set()
    for runner in payload.get("runners", []):
        if runner.get("status") != "online":
            continue
        for label in runner.get("labels", []):
            if isinstance(label, dict) and label.get("name"):
                labels.add(str(label["name"]))
    return labels, "RUNNER_DISCOVERY_OK"


def load_acceptance_status(registry_path: Path, slot: str) -> tuple[str, str]:
    root = registry_path.resolve().parents[1]
    resource_id = f"SAMSUNG-PHONE-{slot}"
    path = root / RUNTIME_STATUS_DIR / f"{resource_id}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "NOT_ACCEPTED", "NO_RUNTIME_RECEIPT"
    status = str(payload.get("status", "NOT_ACCEPTED"))
    if status == ACCEPTED_STATUS and payload.get("eligible") is True:
        return "ACCEPTED", "ACCEPTED_RECEIPT"
    return "NOT_ACCEPTED", status or "NOT_ACCEPTED"


def build_plan(registry_path: Path, repository: str) -> dict[str, Any]:
    configured = load_registry(registry_path)
    online, status = discover_online_labels(repository)
    modes: dict[str, str] = {}
    receipt_states: dict[str, str] = {}
    for key, label in SLOTS.items():
        accepted_state, receipt_state = load_acceptance_status(registry_path, key)
        receipt_states[key] = receipt_state
        if status != "RUNNER_DISCOVERY_OK" or label not in configured or label not in online:
            modes[key] = "none"
        elif accepted_state == "ACCEPTED":
            modes[key] = "utility"
        else:
            modes[key] = "acceptance"
    routable = {key: mode != "none" for key, mode in modes.items()}
    return {
        "schema_version": 1,
        "status": status,
        "repository": repository,
        "configured_labels": sorted(configured),
        "online_labels": sorted(online),
        "routable_slots": routable,
        "slot_modes": modes,
        "receipt_states": receipt_states,
        "routing_policy": "online + exact label + accepted receipt => utility; otherwise acceptance; never scientific evidence",
        "fail_closed": status != "RUNNER_DISCOVERY_OK",
        "scientific_evidence": False,
        "performance_authorization": False,
        "candidate_selection": False,
        "candidate_ranking": False,
        "promotion": False,
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--github-output", required=True)
    args = parser.parse_args()

    plan = build_plan(
        Path(args.registry),
        os.environ["GITHUB_REPOSITORY"],
    )
    output = Path(args.output_json)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with Path(args.github_output).open("a", encoding="utf-8") as handle:
        for key, value in plan["routable_slots"].items():
            handle.write(f"phone_{key}={str(value).lower()}\n")
            handle.write(f"phone_{key}_mode={plan['slot_modes'][key]}\n")
        handle.write(f"discovery_status={plan['status']}\n")
    print(json.dumps(plan, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
