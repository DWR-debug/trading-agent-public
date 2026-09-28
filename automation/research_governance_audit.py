"""Fail-closed audit for active research provenance and trial identity.

Historical artifacts remain immutable. Active performance preregistrations opt
into governance contract v2, which requires an explicit identity chain:
trial -> prerequisites -> receipts -> fingerprints -> authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}
PERFORMANCE_STATUS = "PREREGISTERED_PERFORMANCE"
REQUIRED_DATA_KEYS = (
    "coverage_trial_id",
    "coverage_result_fingerprint",
    "snapshot_fingerprint",
    "pit_trial_id",
    "pit_result_fingerprint",
    "input_bundle_trial_id",
    "input_bundle_fingerprint",
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _trial_suffix(trial_id: str) -> str:
    match = re.fullmatch(r"T-[0-9]{4}-[0-9]{2}-[0-9]{2}-(.+)", trial_id or "")
    if not match:
        raise ValueError(f"invalid trial_id format: {trial_id!r}")
    return re.sub(r"[^A-Z0-9]", "", match.group(1).upper())


def _trial_family_code(trial_id: str) -> str:
    match = re.fullmatch(r"T-[0-9]{4}-[0-9]{2}-[0-9]{2}-([^-]+)(?:-.+)?", trial_id or "")
    if not match:
        raise ValueError(f"invalid trial_id family format: {trial_id!r}")
    return re.sub(r"[^A-Z0-9]", "", match.group(1).upper())


def _path_trial_suffix(path: Path) -> str | None:
    match = re.search(r"(?:^|/)q([0-9]{3}(?:r[0-9]+)?)_", path.as_posix(), re.IGNORECASE)
    if not match:
        return None
    return re.sub(r"[^A-Z0-9]", "", match.group(1).upper())


def _fingerprint_path(data: dict, key: str) -> str:
    value = data
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ValueError(f"missing fingerprint key {key!r}")
        value = value[part]
    if not isinstance(value, str) or not value:
        raise ValueError(f"fingerprint value at {key!r} must be non-empty")
    return value


def _assert_safety(data: dict, location: str, errors: list[str]) -> None:
    if data.get("safety") != SAFETY:
        errors.append(f"{location}: safety contract mismatch")


def _audit_performance_prereg(root: Path, path: Path, data: dict, errors: list[str]) -> None:
    location = path.relative_to(root).as_posix()
    trial_id = data.get("trial_id")
    if not isinstance(trial_id, str) or not trial_id:
        errors.append(f"{location}: missing top-level trial_id")
        return

    if data.get("governance_contract_version") != 2:
        errors.append(f"{location}: governance_contract_version must be 2")

    expected_suffix = _path_trial_suffix(path)
    actual_suffix = _trial_family_code(trial_id)
    if expected_suffix is not None and expected_suffix != actual_suffix:
        errors.append(
            f"{location}: filename trial code {expected_suffix} != trial_id code {actual_suffix}"
        )

    identity = data.get("identity_contract")
    if not isinstance(identity, dict):
        errors.append(f"{location}: missing identity_contract")
        identity = {}
    if identity.get("trial_id") != trial_id:
        errors.append(f"{location}: identity_contract.trial_id mismatch")
    if identity.get("expected_trial_code") != actual_suffix:
        errors.append(f"{location}: identity_contract.expected_trial_code mismatch")

    mode = identity.get("mode")
    reused = identity.get("reused_source_trials", [])
    if not isinstance(reused, list) or any(not isinstance(x, str) for x in reused):
        errors.append(f"{location}: reused_source_trials must be a list of strings")
        reused = []
    reused_set = set(reused)
    if mode not in {"fresh_trial", "immutable_reuse"}:
        errors.append(f"{location}: identity_contract.mode invalid: {mode!r}")

    data_contract = data.get("data_contract")
    if not isinstance(data_contract, dict):
        errors.append(f"{location}: missing data_contract")
        return

    for key in REQUIRED_DATA_KEYS:
        if key not in data_contract:
            errors.append(f"{location}: missing data_contract.{key}")

    ref_ids = []
    for key in ("coverage_trial_id", "pit_trial_id", "input_bundle_trial_id"):
        value = data_contract.get(key)
        if isinstance(value, str):
            ref_ids.append(value)
    trial_family = _trial_family_code(trial_id)
    foreign = {
        ref for ref in ref_ids
        if _trial_family_code(ref) != trial_family
    }
    if mode == "fresh_trial" and foreign:
        errors.append(f"{location}: fresh trial references foreign prerequisite ids: {sorted(foreign)}")
    if mode == "immutable_reuse" and not foreign <= reused_set:
        errors.append(
            f"{location}: foreign prerequisites not declared in reused_source_trials: "
            f"{sorted(foreign - reused_set)}"
        )
    if mode == "immutable_reuse" and not isinstance(data.get("prior_trial_id"), str):
        errors.append(f"{location}: immutable_reuse requires prior_trial_id")

    _assert_safety(data, location, errors)

    receipts = identity.get("required_receipts")
    if not isinstance(receipts, list) or not receipts:
        errors.append(f"{location}: required_receipts must be non-empty")
        return

    seen_roles: set[str] = set()
    for receipt in receipts:
        if not isinstance(receipt, dict):
            errors.append(f"{location}: receipt entry must be an object")
            continue
        role = receipt.get("role")
        receipt_path = receipt.get("path")
        receipt_trial = receipt.get("trial_id")
        fingerprint_key = receipt.get("fingerprint_key")
        expected_key = receipt.get("expected_data_contract_key")
        if not all(isinstance(x, str) and x for x in (role, receipt_path, receipt_trial, fingerprint_key, expected_key)):
            errors.append(f"{location}: malformed receipt entry")
            continue
        if role in seen_roles:
            errors.append(f"{location}: duplicate receipt role {role}")
        seen_roles.add(role)

        target = root / receipt_path
        if not target.is_file():
            errors.append(f"{location}: required receipt missing: {receipt_path}")
            continue
        try:
            target_data = _load(target)
        except Exception as exc:
            errors.append(f"{location}: cannot parse {receipt_path}: {exc}")
            continue
        if not isinstance(target_data, dict):
            errors.append(f"{location}: receipt {receipt_path} is not an object")
            continue
        if target_data.get("trial_id") != receipt_trial:
            errors.append(
                f"{location}: receipt {receipt_path} trial_id mismatch: "
                f"{target_data.get('trial_id')!r} != {receipt_trial!r}"
            )
        try:
            actual_fp = _fingerprint_path(target_data, fingerprint_key)
        except ValueError as exc:
            errors.append(f"{location}: {receipt_path}: {exc}")
            continue
        if actual_fp != data_contract.get(expected_key):
            errors.append(f"{location}: fingerprint mismatch in {receipt_path}")


def _load_retired_authorizations(root: Path, errors: list[str]) -> set[str]:
    register_path = root / "research" / "governance" / "retired_authorizations.json"
    if not register_path.is_file():
        return set()
    try:
        register = _load(register_path)
    except Exception as exc:
        errors.append(f"{register_path.relative_to(root)}: cannot parse retired authorization register: {exc}")
        return set()
    retired: set[str] = set()
    entries = register.get("entries", []) if isinstance(register, dict) else []
    if not isinstance(entries, list):
        errors.append(f"{register_path.relative_to(root)}: entries must be a list")
        return set()
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append(f"{register_path.relative_to(root)}: entry must be an object")
            continue
        path = entry.get("path")
        trial_id = entry.get("trial_id")
        status = entry.get("status")
        if not all(isinstance(x, str) and x for x in (path, trial_id, status)):
            errors.append(f"{register_path.relative_to(root)}: malformed retired authorization entry")
            continue
        if status != "RETIRED_HISTORICAL_AUTHORIZATION":
            errors.append(f"{register_path.relative_to(root)}: invalid retired authorization status")
            continue
        target = root / path
        if not target.is_file():
            errors.append(f"{register_path.relative_to(root)}: registered retired authorization missing: {path}")
            continue
        try:
            data = _load(target)
        except Exception as exc:
            errors.append(f"{register_path.relative_to(root)}: cannot parse {path}: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{register_path.relative_to(root)}: authorization is not an object: {path}")
            continue
        observed_trial = data.get("trial_id")
        if observed_trial is not None and observed_trial != trial_id:
            errors.append(f"{register_path.relative_to(root)}: trial_id mismatch for {path}")
            continue
        retired.add(path)
    return retired


def _audit_authorizations(root: Path, errors: list[str], active_by_trial: dict[str, dict]) -> None:
    auth_root = root / "research" / "authorizations"
    retired_paths = _load_retired_authorizations(root, errors)
    if not auth_root.exists():
        return
    for path in sorted(auth_root.glob("*.json")):
        try:
            data = _load(path)
        except Exception as exc:
            errors.append(f"{path.relative_to(root)}: cannot parse authorization: {exc}")
            continue
        if not isinstance(data, dict) or data.get("authorized") is not True or data.get("performance_execution_authorized") is not True:
            continue

        location = path.relative_to(root).as_posix()
        if location in retired_paths:
            continue
        trial_id = data.get("trial_id")
        active = active_by_trial.get(trial_id) if isinstance(trial_id, str) else None
        if active is None:
            errors.append(f"{location}: authorized performance trial is not in active research registry")
            continue
        if active.get("performance_authorization_allowed") is not True:
            errors.append(f"{location}: active registry does not permit performance authorization")
        if data.get("authorization_contract_version") != 2:
            errors.append(f"{location}: authorized execution requires authorization_contract_version=2")
        if not isinstance(data.get("trial_id"), str) or not data.get("trial_id"):
            errors.append(f"{location}: authorized execution requires top-level trial_id")
        if data.get("one_shot") is not True:
            errors.append(f"{location}: authorized execution requires one_shot=true")

        prereg_path = data.get("preregistration_path")
        if not isinstance(prereg_path, str) or not prereg_path:
            errors.append(f"{location}: missing preregistration_path")
            continue
        prereg_file = root / prereg_path
        if not prereg_file.is_file():
            errors.append(f"{location}: referenced preregistration missing: {prereg_path}")
            continue
        prereg = _load(prereg_file)
        if not isinstance(prereg, dict) or prereg.get("trial_id") != data.get("trial_id"):
            errors.append(f"{location}: trial_id does not match referenced preregistration")
        elif prereg.get("governance_contract_version") != 2:
            errors.append(f"{location}: referenced preregistration is not governance v2")

        expected_fp = data.get("preregistration_fingerprint")
        if expected_fp:
            actual_fp = hashlib.sha256(
                json.dumps(prereg, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
            ).hexdigest()
            if actual_fp != expected_fp:
                errors.append(f"{location}: preregistration fingerprint mismatch")


def audit(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    registry_path = root / "research" / "governance" / "active_research_registry.json"
    if not registry_path.is_file():
        return {
            "schema_version": 1,
            "governance_contract_version": 2,
            "status": "BLOCKED",
            "active_performance_preregistrations": [],
            "error_count": 1,
            "errors": ["missing active_research_registry.json"],
            "safety": SAFETY,
        }

    registry = _load(registry_path)
    policy = registry.get("policy", {}) if isinstance(registry, dict) else {}
    if policy.get("only_listed_performance_trials_may_be_authorized") is not True:
        errors.append("active research registry policy is invalid")

    active_by_trial: dict[str, dict] = {}
    for entry in registry.get("active_trials", []) if isinstance(registry, dict) else []:
        if not isinstance(entry, dict):
            errors.append("active research registry entry must be an object")
            continue
        trial_id = entry.get("trial_id")
        if isinstance(trial_id, str) and trial_id:
            if trial_id in active_by_trial:
                errors.append(f"duplicate active registry trial_id {trial_id}")
            active_by_trial[trial_id] = entry

    active: list[tuple[Path, dict]] = []
    for trial_id, entry in active_by_trial.items():
        if entry.get("class") not in {"performance_correction", "fresh_validation"}:
            continue
        prereg_path = entry.get("preregistration_path")
        if not prereg_path:
            if entry.get("state") == "PLANNED":
                continue
            errors.append(f"active registry performance entry {trial_id} missing preregistration_path")
            continue
        path = root / prereg_path
        if not path.is_file():
            errors.append(f"active registry performance preregistration missing: {prereg_path}")
            continue
        try:
            data = _load(path)
        except Exception as exc:
            errors.append(f"{path.relative_to(root)}: cannot parse JSON: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{path.relative_to(root)}: preregistration is not an object")
            continue
        active.append((path, data))

    seen: dict[str, Path] = {}
    for path, data in active:
        trial_id = data.get("trial_id")
        if isinstance(trial_id, str):
            if trial_id in seen:
                errors.append(f"duplicate active prereg trial_id {trial_id}: {seen[trial_id]} and {path}")
            seen[trial_id] = path
        _audit_performance_prereg(root, path, data, errors)

    _audit_authorizations(root, errors, active_by_trial)
    return {
        "schema_version": 1,
        "governance_contract_version": 2,
        "status": "PASS" if not errors else "BLOCKED",
        "active_performance_preregistrations": [p.relative_to(root).as_posix() for p, _ in active],
        "active_registry_trial_ids": sorted(active_by_trial),
        "error_count": len(errors),
        "errors": errors,
        "safety": SAFETY,
    }
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = audit(args.repo_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
