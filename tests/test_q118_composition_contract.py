from __future__ import annotations

from copy import deepcopy

import pytest

from automation.q118_composition_contract import (
    composition_fingerprint,
    validate_composition,
)


def _component(
    component_id: str,
    lineage_id: str,
    source_fingerprint: str,
    *,
    public_at: str = "2026-09-30T15:00:00+00:00",
):
    return {
        "component_id": component_id,
        "lineage_id": lineage_id,
        "version": "v1",
        "preregistration_id": f"PREREG-{component_id}",
        "decision_cutoff": "2026-09-30T16:00:00+00:00",
        "public_at": public_at,
        "eligible_session": "2026-09-30",
        "entity_ids": ["A", "B", "C"],
        "signal_direction": "LONG_POSITIVE",
        "missingness_semantics": "explicit_absence_is_neutral",
        "source_fingerprint": source_fingerprint,
        "dependencies": [],
    }


def _manifest():
    return {
        "bundle_id": "B1-SYNTHETIC-001",
        "composition_form": "C1",
        "decision_cutoff": "2026-09-30T16:00:00+00:00",
        "eligible_session": "2026-09-30",
        "entity_ids": ["A", "B", "C"],
        "require_independent_lineages": True,
        "performance_authorized": False,
        "holdout_selection_allowed": False,
        "parameter_search_allowed": False,
        "components": [
            _component("A", "L-A", "aaaaaaaaaaaaaaaa"),
            _component("B", "L-B", "bbbbbbbbbbbbbbbb"),
        ],
    }


def test_q118_valid_composition_is_deterministic():
    manifest = _manifest()
    result = validate_composition(manifest)
    assert result["status"] == "COMPOSITION_STRUCTURALLY_VALID"
    assert result["component_count"] == 2
    assert result["independent_lineage_count"] == 2
    assert result["performance_evidence_consulted"] is False
    assert result["holdout_evidence_consulted"] is False
    assert result["result_fingerprint"] == composition_fingerprint(manifest)


def test_q118_component_order_does_not_change_fingerprint():
    manifest = _manifest()
    reverse = deepcopy(manifest)
    reverse["components"] = list(reversed(reverse["components"]))
    assert composition_fingerprint(manifest) == composition_fingerprint(reverse)


def test_q118_component_published_after_own_cutoff_fails_closed():
    manifest = _manifest()
    manifest["components"][0]["public_at"] = "2026-09-30T16:01:00+00:00"
    with pytest.raises(
        ValueError, match="^Q118_COMPONENT_PUBLISHED_AFTER_OWN_CUTOFF$"
    ):
        validate_composition(manifest)


def test_q118_future_information_relative_to_bundle_cutoff_fails_closed():
    manifest = _manifest()
    manifest["components"][0]["decision_cutoff"] = "2026-10-01T16:00:00+00:00"
    manifest["components"][0]["public_at"] = "2026-09-30T16:01:00+00:00"
    with pytest.raises(ValueError, match="^Q118_FUTURE_INFORMATION_DETECTED$"):
        validate_composition(manifest)


def test_q118_entity_mismatch_fails_closed():
    manifest = _manifest()
    manifest["components"][1]["entity_ids"] = ["A", "B", "D"]
    with pytest.raises(ValueError, match="ENTITY_SET_MISMATCH"):
        validate_composition(manifest)


def test_q118_duplicate_lineage_fails_closed():
    manifest = _manifest()
    manifest["components"][1]["lineage_id"] = manifest["components"][0]["lineage_id"]
    with pytest.raises(ValueError, match="DUPLICATE_LINEAGE"):
        validate_composition(manifest)


def test_q118_result_fields_cannot_enter_component_contract():
    manifest = _manifest()
    manifest["components"][0]["future_return"] = 0.12
    with pytest.raises(ValueError, match="FORBIDDEN_RESULT_FIELDS"):
        validate_composition(manifest)


def test_q118_recursive_bundle_dependency_fails_closed():
    manifest = _manifest()
    manifest["components"][0]["dependencies"] = [manifest["bundle_id"]]
    with pytest.raises(ValueError, match="RECURSIVE_BUNDLE_DEPENDENCY"):
        validate_composition(manifest)
