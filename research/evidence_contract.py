"""Fail-closed evidence contract for research promotion decisions.

This module does not select strategies and does not execute orders. It binds
research provenance, safety, holdout handling and predefined gate results into
one explicit decision object. Missing or inconsistent evidence can only lead
to BLOCKED / NOT_ELIGIBLE.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Mapping

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")
STATUS_VALUES = ("VALIDATED_PASS", "VALIDATED_FAIL", "BLOCKED")

class EvidenceContractError(ValueError):
    """Raised when a research evidence contract is malformed."""

@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    observed: float | None = None
    threshold: float | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise EvidenceContractError("Gate name must not be empty.")
        for label, value in (("observed", self.observed), ("threshold", self.threshold)):
            if value is not None and not math.isfinite(float(value)):
                raise EvidenceContractError(f"{label} must be finite when present.")

@dataclass(frozen=True)
class EvidenceSnapshot:
    trial_id: str
    strategy_id: str
    status: str
    artifact_id: int
    artifact_digest_sha256: str
    report_fingerprint_sha256: str
    manifest_fingerprint_sha256: str
    code_commit_sha: str
    research_count: int
    holdout_count: int
    holdout_used_for_selection: bool
    gates: tuple[GateResult, ...]
    paper_only: bool = True
    live_trading_enabled: bool = False
    orders_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.trial_id.strip() or not self.strategy_id.strip():
            raise EvidenceContractError("trial_id and strategy_id are required.")
        if self.status not in STATUS_VALUES:
            raise EvidenceContractError(f"Unknown evidence status: {self.status}.")
        if int(self.artifact_id) < 1:
            raise EvidenceContractError("artifact_id must be >= 1.")
        for label, value in (
            ("artifact_digest_sha256", self.artifact_digest_sha256),
            ("report_fingerprint_sha256", self.report_fingerprint_sha256),
            ("manifest_fingerprint_sha256", self.manifest_fingerprint_sha256),
        ):
            if not SHA256_RE.fullmatch(value):
                raise EvidenceContractError(f"{label} must be a 64-character SHA-256 hex digest.")
        if not GIT_SHA_RE.fullmatch(self.code_commit_sha):
            raise EvidenceContractError("code_commit_sha must be a valid git SHA.")
        if int(self.research_count) < 1 or int(self.holdout_count) < 1:
            raise EvidenceContractError("research_count and holdout_count must be >= 1.")
        if not isinstance(self.holdout_used_for_selection, bool):
            raise EvidenceContractError("holdout_used_for_selection must be bool.")
        if not self.gates:
            raise EvidenceContractError("Evidence snapshots require at least one named gate.")
        if (self.paper_only, self.live_trading_enabled, self.orders_enabled) != (True, False, False):
            raise EvidenceContractError("Safety contract requires paper-only and disabled orders.")

@dataclass(frozen=True)
class EvidenceDecision:
    eligible: bool
    status: str
    reason: str
    failed_gates: tuple[str, ...]

def evaluate_evidence(snapshot: EvidenceSnapshot) -> EvidenceDecision:
    """Evaluate promotion eligibility without changing any project gate."""
    failed = tuple(gate.name for gate in snapshot.gates if not gate.passed)
    if snapshot.holdout_used_for_selection:
        return EvidenceDecision(False, "BLOCKED", "HOLDOUT_USED_FOR_SELECTION", failed)
    if not snapshot.gates:
        return EvidenceDecision(False, "BLOCKED", "NO_EVIDENCE_GATES", ())
    if snapshot.status != "VALIDATED_PASS":
        return EvidenceDecision(False, snapshot.status, "TRIAL_NOT_VALIDATED_PASS", failed)
    if failed:
        return EvidenceDecision(False, "VALIDATED_FAIL", "PREDEFINED_GATE_FAILURE", failed)
    return EvidenceDecision(True, "VALIDATED_PASS", "ALL_DECLARED_GATES_PASSED", ())

def compare_evidence_versions(previous: EvidenceSnapshot | None, current: EvidenceSnapshot) -> tuple[str, ...]:
    """Return provenance changes; missing previous evidence is explicit."""
    if previous is None:
        return ("NO_PREVIOUS_EVIDENCE",)
    changes: list[str] = []
    for field in (
        "strategy_id", "artifact_id", "artifact_digest_sha256",
        "report_fingerprint_sha256", "manifest_fingerprint_sha256",
        "code_commit_sha", "research_count", "holdout_count",
        "holdout_used_for_selection",
    ):
        if getattr(previous, field) != getattr(current, field):
            changes.append(field)
    return tuple(changes)

def merge_gate_results(gates: Mapping[str, bool]) -> tuple[GateResult, ...]:
    """Create deterministically ordered gate results from named booleans."""
    if not gates:
        raise EvidenceContractError("At least one named gate is required.")
    return tuple(GateResult(name=name, passed=bool(passed)) for name, passed in sorted(gates.items()))
