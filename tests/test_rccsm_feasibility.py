from __future__ import annotations

import math

import pytest

from automation.rccsm_feasibility import (
    STATUS_VALUES,
    canonical_fingerprint,
    feasibility_manifest,
    mechanism_registry,
    route_mesh,
    route_mechanism,
)


STATE = {
    "trend_coherence": 0.80,
    "breadth": 0.70,
    "dispersion": 0.30,
    "event_density": 0.10,
}


def test_registry_is_frozen_and_deterministic() -> None:
    assert [item["mechanism_id"] for item in mechanism_registry()] == [
        "cross_sectional_momentum",
        "event_timing",
        "reversal",
        "trend_efficiency",
    ]
    assert mechanism_registry() == mechanism_registry()


def test_router_emits_only_structural_fields() -> None:
    result = route_mechanism("trend_efficiency", STATE, state_id="S1")
    assert set(result) == {
        "state_id",
        "mechanism_id",
        "admissibility",
        "provenance_fingerprint",
    }
    assert result["admissibility"] in STATUS_VALUES
    assert result["admissibility"] == "ADMISSIBLE"
    assert len(result["provenance_fingerprint"]) == 64


def test_mesh_is_canonical_and_fail_closed() -> None:
    result = route_mesh("S1", STATE)
    assert tuple(item["mechanism_id"] for item in result) == (
        "cross_sectional_momentum",
        "event_timing",
        "reversal",
        "trend_efficiency",
    )
    assert all(item["admissibility"] in STATUS_VALUES for item in result)
    with pytest.raises(ValueError):
        route_mesh("S1", {**STATE, "breadth": float("nan")})


def test_future_or_holdout_fields_are_rejected() -> None:
    leaked = {
        **STATE,
        "future_return": 9999.0,
        "future_label": -9999.0,
        "holdout_result": 123.0,
    }
    with pytest.raises(ValueError):
        route_mesh("S1", leaked)


def test_required_state_fields_are_fail_closed() -> None:
    incomplete = dict(STATE)
    del incomplete["dispersion"]
    with pytest.raises(ValueError):
        route_mesh("S1", incomplete)


def test_unknown_mechanism_is_rejected() -> None:
    with pytest.raises(ValueError):
        route_mechanism("unknown", STATE)


def test_fingerprint_is_byte_stable() -> None:
    payload = {"b": 2, "a": 1}
    assert canonical_fingerprint(payload) == canonical_fingerprint({"a": 1, "b": 2})


def test_manifest_is_explicitly_non_performance_authorizing() -> None:
    manifest = feasibility_manifest()
    assert manifest["component"] == "RCCSM-0"
    assert manifest["performance_authorized"] is False
    assert manifest["uses_returns"] is False
    assert manifest["uses_holdout"] is False
    assert manifest["uses_optimizer"] is False
    assert all(math.isfinite(float(value)) for value in (0.8, 0.7, 0.3, 0.1))
    assert len(manifest["fingerprint"]) == 64
