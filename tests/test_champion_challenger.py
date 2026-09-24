import pytest

from research.champion_challenger import (
    ChampionChallengerError,
    ChampionChallengerComparison,
    compare_snapshots,
    comparison_to_dict,
    pearson_correlation,
)
from research.evidence_contract import EvidenceSnapshot, GateResult


def snapshot(trial_id: str, strategy_id: str, *, holdout_used: bool = False):
    return EvidenceSnapshot(
        trial_id=trial_id,
        strategy_id=strategy_id,
        status="VALIDATED_PASS",
        artifact_id=1,
        artifact_digest_sha256="a" * 64,
        report_fingerprint_sha256="b" * 64,
        manifest_fingerprint_sha256="c" * 64,
        code_commit_sha="d" * 40,
        research_count=100,
        holdout_count=20,
        holdout_used_for_selection=holdout_used,
        gates=(
            GateResult("drawdown", True),
            GateResult("profit_factor", False),
        ),
    )


def test_comparison_is_descriptive_only():
    result = compare_snapshots(
        snapshot("T1", "strategy-a"),
        snapshot("T2", "strategy-b"),
    )
    assert isinstance(result, ChampionChallengerComparison)
    assert result.automatic_selection is False
    assert result.promotion_decision == "NOT_IMPLEMENTED"
    assert result.holdout_selection_blocked is False
    assert result.safety_verified is True
    assert result.common_gate_deltas == (
        ("drawdown", True, True),
        ("profit_factor", False, False),
    )


def test_holdout_selection_is_explicitly_blocked():
    result = compare_snapshots(
        snapshot("T1", "strategy-a"),
        snapshot("T2", "strategy-b", holdout_used=True),
    )
    assert result.holdout_selection_blocked is True


def test_provenance_changes_are_reported():
    result = compare_snapshots(
        snapshot("T1", "strategy-a"),
        snapshot("T2", "strategy-b"),
    )
    assert "strategy_id" in result.provenance_changes
    assert "artifact_id" not in result.provenance_changes


def test_same_trial_is_rejected():
    with pytest.raises(ChampionChallengerError):
        compare_snapshots(
            snapshot("T1", "strategy-a"),
            snapshot("T1", "strategy-b"),
        )


def test_correlation_handles_constant_series():
    assert pearson_correlation((1, 1, 1), (1, 2, 3)) == 0.0


def test_serialization_contains_no_selection_verdict():
    data = comparison_to_dict(
        compare_snapshots(
            snapshot("T1", "strategy-a"),
            snapshot("T2", "strategy-b"),
        )
    )
    assert data["automatic_selection"] is False
    assert data["promotion_decision"] == "NOT_IMPLEMENTED"
    assert "winner" not in data
