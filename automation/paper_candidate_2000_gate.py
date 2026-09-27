"""Fail-closed eligibility gate for formal EUR 2000 paper experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from automation.paper_30_day_experiment import (
    Paper30DayExperimentError,
    load_evidence,
    load_return_stream,
)
from research.evidence_contract import evaluate_evidence

REQUIRED_CAPITAL_EUR = 2000.0


class Paper2000GateError(ValueError):
    """Raised when a formal EUR 2000 candidate contract is violated."""


def _resolve_repository_file(
    value: Any,
    *,
    name: str,
    repository_root: Path,
    allowed_directory: Path | None = None,
) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise Paper2000GateError(f"{name} must be a repository-relative path.")

    relative_path = Path(value)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise Paper2000GateError(f"{name} must be a repository-relative path.")

    try:
        resolved = (repository_root / relative_path).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise Paper2000GateError(f"{name} cannot be resolved inside the repository.") from exc

    try:
        resolved.relative_to(repository_root)
    except ValueError as exc:
        raise Paper2000GateError(f"{name} resolves outside the repository.") from exc

    if allowed_directory is not None:
        try:
            resolved.relative_to(allowed_directory)
        except ValueError as exc:
            raise Paper2000GateError(
                f"{name} must be inside {allowed_directory.relative_to(repository_root)}."
            ) from exc

    if not resolved.is_file():
        raise Paper2000GateError(f"{name} is not a file: {value}")
    return resolved


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Paper2000GateError(f"Manifest must be a JSON object: {path}")
    return payload


def validate_manifest(manifest_path: str | Path) -> dict[str, Any]:
    repository_root = Path.cwd().resolve()
    candidate_directory = (repository_root / "research/paper_candidates_2000").resolve()
    path = _resolve_repository_file(
        str(manifest_path),
        name="Candidate manifest",
        repository_root=repository_root,
        allowed_directory=candidate_directory,
    )
    manifest = _load_json(path)

    if manifest.get("schema_version") != 1:
        raise Paper2000GateError("Unsupported paper-2000 manifest schema.")
    if manifest.get("frozen") is not True:
        raise Paper2000GateError("Candidate manifest must be frozen=True.")

    candidate_id = manifest.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise Paper2000GateError("candidate_id is required.")

    try:
        initial_capital = float(manifest.get("initial_capital_eur", 0.0))
    except (TypeError, ValueError) as exc:
        raise Paper2000GateError("Formal candidate paper run requires exactly EUR 2000.") from exc
    if initial_capital != REQUIRED_CAPITAL_EUR:
        raise Paper2000GateError("Formal candidate paper run requires exactly EUR 2000.")
    if manifest.get("auto_select") is not False:
        raise Paper2000GateError("Candidate paper run must not auto-select candidates.")
    if manifest.get("comparison_mode") is not False:
        raise Paper2000GateError("Candidate paper run must not compare candidates.")
    if manifest.get("orders_enabled") is not False:
        raise Paper2000GateError("orders_enabled must remain False.")

    evidence_path = _resolve_repository_file(
        manifest.get("evidence_path"),
        name="Evidence path",
        repository_root=repository_root,
    )
    returns_path = _resolve_repository_file(
        manifest.get("returns_path"),
        name="Return-stream path",
        repository_root=repository_root,
    )

    try:
        evidence = load_evidence(evidence_path)
    except Paper30DayExperimentError as exc:
        raise Paper2000GateError(f"Evidence violates the project contract: {exc}") from exc

    if evidence.holdout_used_for_selection is not False:
        raise Paper2000GateError("Holdout must not be used for candidate selection.")
    if (
        evidence.paper_only is not True
        or evidence.live_trading_enabled is not False
        or evidence.orders_enabled is not False
    ):
        raise Paper2000GateError("Evidence violates the paper-only safety contract.")

    decision = evaluate_evidence(evidence)
    if not decision.eligible:
        raise Paper2000GateError(
            "Candidate is not Evidence-eligible: "
            f"{decision.reason}; failed_gates={list(decision.failed_gates)}"
        )

    strategy_id, _, _ = load_return_stream(returns_path)
    if strategy_id != evidence.strategy_id:
        raise Paper2000GateError(
            "Return-stream strategy_id does not match evidence strategy_id."
        )

    return {
        "candidate_id": candidate_id,
        "strategy_id": evidence.strategy_id,
        "trial_id": evidence.trial_id,
        "evidence_status": evidence.status,
        "initial_capital_eur": REQUIRED_CAPITAL_EUR,
        "capital_semantics": "hypothetical_reference_only",
        "holdout_used_for_selection": evidence.holdout_used_for_selection,
        "paper_only": evidence.paper_only,
        "live_trading_enabled": evidence.live_trading_enabled,
        "orders_enabled": evidence.orders_enabled,
        "auto_select": False,
        "comparison_mode": False,
        "eligible": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    print(json.dumps(validate_manifest(args.manifest), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
