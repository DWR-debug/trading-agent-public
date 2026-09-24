"""Governed champion/challenger evidence accounting.

This module compares already validated EvidenceSnapshot objects without ranking,
selecting, or promoting a strategy.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean
from typing import Sequence

from research.evidence_contract import EvidenceContractError, EvidenceSnapshot

class ChampionChallengerError(ValueError):
    """Raised for malformed champion/challenger accounting inputs."""

@dataclass(frozen=True)
class ChampionChallengerComparison:
    champion_trial_id: str
    challenger_trial_id: str
    champion_status: str
    challenger_status: str
    common_gate_deltas: tuple[tuple[str, bool, bool], ...]
    provenance_changes: tuple[str, ...]
    holdout_selection_blocked: bool
    safety_verified: bool
    automatic_selection: bool = False
    promotion_decision: str = "NOT_IMPLEMENTED"

    def __post_init__(self) -> None:
        if not self.champion_trial_id.strip() or not self.challenger_trial_id.strip():
            raise ChampionChallengerError("Champion and challenger trial IDs are required.")
        if self.champion_trial_id == self.challenger_trial_id:
            raise ChampionChallengerError("Champion and challenger must be distinct trials.")
        if self.automatic_selection:
            raise ChampionChallengerError("Automatic strategy selection is prohibited.")
        if self.promotion_decision != "NOT_IMPLEMENTED":
            raise ChampionChallengerError("Promotion decisions are outside this accounting layer.")

def pearson_correlation(a: Sequence[float], b: Sequence[float]) -> float:
    """Return a descriptive Pearson correlation; never used for selection."""
    if len(a) != len(b) or len(a) < 2:
        raise ChampionChallengerError("Correlation needs equal series of length >= 2.")
    try:
        values_a = tuple(float(value) for value in a)
        values_b = tuple(float(value) for value in b)
    except (TypeError, ValueError) as exc:
        raise ChampionChallengerError("Correlation inputs must be numeric.") from exc
    if any(not math.isfinite(value) for value in values_a + values_b):
        raise ChampionChallengerError("Correlation inputs must be finite.")
    mean_a, mean_b = mean(values_a), mean(values_b)
    centered_a = tuple(value - mean_a for value in values_a)
    centered_b = tuple(value - mean_b for value in values_b)
    variance_a = sum(value * value for value in centered_a)
    variance_b = sum(value * value for value in centered_b)
    if variance_a == 0.0 or variance_b == 0.0:
        return 0.0
    covariance = sum(a_value * b_value for a_value, b_value in zip(centered_a, centered_b))
    return covariance / math.sqrt(variance_a * variance_b)

def compare_snapshots(champion: EvidenceSnapshot, challenger: EvidenceSnapshot) -> ChampionChallengerComparison:
    """Create a neutral accounting record from two evidence snapshots."""
    if not isinstance(champion, EvidenceSnapshot) or not isinstance(challenger, EvidenceSnapshot):
        raise EvidenceContractError("Both inputs must be EvidenceSnapshot instances.")
    if champion.trial_id == challenger.trial_id:
        raise ChampionChallengerError("Champion and challenger must be distinct trials.")
    safety_verified = all(
        snapshot.paper_only is True
        and snapshot.live_trading_enabled is False
        and snapshot.orders_enabled is False
        for snapshot in (champion, challenger)
    )
    champion_gates = {gate.name: gate.passed for gate in champion.gates}
    challenger_gates = {gate.name: gate.passed for gate in challenger.gates}
    common_gate_deltas = tuple(
        (name, champion_gates[name], challenger_gates[name])
        for name in sorted(set(champion_gates) & set(challenger_gates))
    )
    provenance_changes = tuple(
        field
        for field in (
            "strategy_id", "artifact_id", "artifact_digest_sha256",
            "report_fingerprint_sha256", "manifest_fingerprint_sha256",
            "code_commit_sha", "research_count", "holdout_count",
            "holdout_used_for_selection",
        )
        if getattr(champion, field) != getattr(challenger, field)
    )
    return ChampionChallengerComparison(
        champion_trial_id=champion.trial_id,
        challenger_trial_id=challenger.trial_id,
        champion_status=champion.status,
        challenger_status=challenger.status,
        common_gate_deltas=common_gate_deltas,
        provenance_changes=provenance_changes,
        holdout_selection_blocked=(
            champion.holdout_used_for_selection or challenger.holdout_used_for_selection
        ),
        safety_verified=safety_verified,
    )

def comparison_to_dict(comparison: ChampionChallengerComparison) -> dict[str, object]:
    """Serialize accounting evidence without introducing a selection verdict."""
    return {
        "champion_trial_id": comparison.champion_trial_id,
        "challenger_trial_id": comparison.challenger_trial_id,
        "champion_status": comparison.champion_status,
        "challenger_status": comparison.challenger_status,
        "common_gate_deltas": [
            {
                "gate": name,
                "champion_passed": champion_passed,
                "challenger_passed": challenger_passed,
            }
            for name, champion_passed, challenger_passed in comparison.common_gate_deltas
        ],
        "provenance_changes": list(comparison.provenance_changes),
        "holdout_selection_blocked": comparison.holdout_selection_blocked,
        "safety_verified": comparison.safety_verified,
        "automatic_selection": comparison.automatic_selection,
        "promotion_decision": comparison.promotion_decision,
    }