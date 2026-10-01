import pytest

from automation.q118_candidate_composition import (
    CompositionIncompatible,
    synthetic_contract,
    validate_components,
)


def test_q118_synthetic_contract():
    assert all(synthetic_contract().values())


def _base():
    return {
        "component_id": "A",
        "family_id": "family_a",
        "decision_timestamp": "2026-10-01T15:00:00+00:00",
        "public_at": "2026-10-01T14:00:00+00:00",
        "eligible_session": "2026-10-02",
        "source_fingerprint": "src-a",
        "entity_fingerprint": "entity-1",
        "missingness": "PRESENT",
        "direction": "LONG",
        "component_version": "v1",
        "lineage_id": "lineage-a",
    }


def test_q118_future_public_event_fails_closed():
    row = _base()
    row["public_at"] = "2026-10-01T16:00:00+00:00"
    with pytest.raises(CompositionIncompatible, match="Q118_PIT_PUBLIC_AFTER_CUTOFF"):
        validate_components([row], decision_timestamp="2026-10-01T15:00:00+00:00")


def test_q118_forbidden_performance_field_fails_closed():
    row = _base()
    row["holdout_return"] = 1.0
    with pytest.raises(CompositionIncompatible, match="Q118_FORBIDDEN_PERFORMANCE_FIELD"):
        validate_components([row], decision_timestamp="2026-10-01T15:00:00+00:00")


def test_q118_duplicate_lineage_fails_closed():
    a = _base()
    b = dict(a)
    b["component_id"] = "B"
    b["family_id"] = "family_b"
    b["source_fingerprint"] = "src-b"
    with pytest.raises(CompositionIncompatible, match="Q118_DUPLICATE_INFORMATION_LINEAGE"):
        validate_components([a, b], decision_timestamp="2026-10-01T15:00:00+00:00")


def test_q118_entity_mismatch_fails_closed():
    a = _base()
    b = dict(a)
    b["component_id"] = "B"
    b["family_id"] = "family_b"
    b["source_fingerprint"] = "src-b"
    b["entity_fingerprint"] = "entity-2"
    b["lineage_id"] = "lineage-b"
    with pytest.raises(CompositionIncompatible, match="Q118_ENTITY_MISMATCH"):
        validate_components([a, b], decision_timestamp="2026-10-01T15:00:00+00:00")
