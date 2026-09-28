"""Performance-free RCCSM feasibility primitives.

The router is deliberately small: frozen mechanism/state registries, deterministic
admissibility rules, canonical provenance fingerprints, and fail-closed validation.
It never consumes returns, P&L, holdout labels, or optimizer output.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from typing import Any

STATUS_VALUES = ("ADMISSIBLE", "NEUTRAL", "INADMISSIBLE")

# Frozen synthetic feasibility registry. These thresholds are structural test
# fixtures only; they are not calibrated on market performance.
MECHANISM_RULES: dict[str, dict[str, Any]] = {
    "trend_efficiency": {
        "requirements": {"trend_coherence": {"min": 0.50}},
    },
    "cross_sectional_momentum": {
        "requirements": {
            "trend_coherence": {"min": 0.25},
            "breadth": {"min": 0.40},
        },
    },
    "reversal": {
        "requirements": {
            "dispersion": {"min": 0.50},
            "trend_coherence": {"max": 0.50},
        },
    },
    "event_timing": {
        "requirements": {"event_density": {"min": 0.25}},
    },
}

STATE_FIELDS = (
    "trend_coherence",
    "breadth",
    "dispersion",
    "event_density",
)


def _finite(value: Any, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def canonical_fingerprint(payload: Mapping[str, Any]) -> str:
    """Return a byte-stable SHA-256 fingerprint for JSON-compatible mappings."""
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def mechanism_registry() -> tuple[dict[str, Any], ...]:
    """Return a deterministic, read-only view of the frozen mechanism registry."""
    return tuple(
        {
            "mechanism_id": mechanism_id,
            "requirements": {
                field: dict(condition)
                for field, condition in spec["requirements"].items()
            },
        }
        for mechanism_id, spec in sorted(MECHANISM_RULES.items())
    )


def _validate_state(state: Mapping[str, Any]) -> dict[str, float]:
    if not isinstance(state, Mapping):
        raise TypeError("state must be a mapping")
    missing = [field for field in STATE_FIELDS if field not in state]
    extra = [field for field in state if field not in STATE_FIELDS]
    if missing:
        raise ValueError(f"state is missing required fields: {missing}")
    if extra:
        raise ValueError(f"state contains unexpected fields: {extra}")
    return {
        field: _finite(state[field], f"state[{field}]")
        for field in STATE_FIELDS
    }


def _requirement_matches(value: float, condition: Mapping[str, Any]) -> bool:
    minimum = condition.get("min")
    maximum = condition.get("max")
    if minimum is not None and value < _finite(minimum, "min"):
        return False
    if maximum is not None and value > _finite(maximum, "max"):
        return False
    return True


def route_mechanism(
    mechanism_id: str,
    state: Mapping[str, Any],
    *,
    state_id: str = "STATE-UNSPECIFIED",
) -> dict[str, Any]:
    """Route one frozen mechanism from one explicitly supplied state."""
    if mechanism_id not in MECHANISM_RULES:
        raise ValueError(f"unknown mechanism_id: {mechanism_id}")
    state_values = _validate_state(state)
    spec = MECHANISM_RULES[mechanism_id]
    matches = all(
        _requirement_matches(state_values[field], condition)
        for field, condition in spec["requirements"].items()
    )
    admissibility = "ADMISSIBLE" if matches else "INADMISSIBLE"
    payload = {
        "state_id": str(state_id),
        "mechanism_id": mechanism_id,
        "admissibility": admissibility,
        "state": state_values,
        "requirements": spec["requirements"],
    }
    payload["provenance_fingerprint"] = canonical_fingerprint(payload)
    return {
        "state_id": payload["state_id"],
        "mechanism_id": mechanism_id,
        "admissibility": admissibility,
        "provenance_fingerprint": payload["provenance_fingerprint"],
    }


def route_mesh(
    state_id: str,
    state: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    """Route the complete frozen mechanism registry in canonical order."""
    return tuple(
        route_mechanism(mechanism_id, state, state_id=state_id)
        for mechanism_id in sorted(MECHANISM_RULES)
    )


def feasibility_manifest() -> dict[str, Any]:
    """Return a deterministic manifest suitable for later evidence freezing."""
    manifest = {
        "component": "RCCSM-0",
        "performance_authorized": False,
        "uses_returns": False,
        "uses_holdout": False,
        "uses_optimizer": False,
        "state_fields": list(STATE_FIELDS),
        "mechanisms": mechanism_registry(),
    }
    manifest["fingerprint"] = canonical_fingerprint(manifest)
    return manifest
