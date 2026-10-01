"""Q118 deterministic candidate-composition compatibility compiler.

Structural/design validation only. The compiler accepts only already-frozen
component contracts and produces a deterministic bundle manifest. It never
reads performance, holdout, PnL or outcome fields and never ranks components.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

FORBIDDEN_FIELDS = {
    "return", "returns", "pnl", "profit_factor", "drawdown", "holdout",
    "research_return", "holdout_return", "stress_return", "performance",
    "performance_rank", "candidate_rank",
}
ALLOWED_MISSINGNESS = {"PRESENT", "MISSING", "NOT_APPLICABLE"}
ALLOWED_DIRECTIONS = {"LONG", "SHORT", "NEUTRAL", "UNSPECIFIED"}


class CompositionIncompatible(ValueError):
    pass


def _canonical(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(payload: Any) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _parse_ts(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise CompositionIncompatible(f"Q118_INVALID_{field.upper()}")
    try:
        out = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CompositionIncompatible(f"Q118_INVALID_{field.upper()}") from exc
    if out.tzinfo is None:
        raise CompositionIncompatible(f"Q118_TIMEZONE_REQUIRED_{field.upper()}")
    return out


def validate_components(components: list[dict[str, Any]], *, decision_timestamp: str, bundle_id: str = "Q118-SYNTHETIC") -> dict[str, Any]:
    cutoff = _parse_ts(decision_timestamp, "decision_timestamp")
    if not isinstance(components, list) or not components:
        raise CompositionIncompatible("Q118_NO_COMPONENTS")

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_lineages: set[str] = set()

    for raw in components:
        if not isinstance(raw, dict):
            raise CompositionIncompatible("Q118_COMPONENT_NOT_OBJECT")
        forbidden = sorted(FORBIDDEN_FIELDS.intersection(raw))
        if forbidden:
            raise CompositionIncompatible("Q118_FORBIDDEN_PERFORMANCE_FIELD:" + ",".join(forbidden))

        required = (
            "component_id", "family_id", "decision_timestamp", "eligible_session",
            "source_fingerprint", "entity_fingerprint", "missingness",
            "direction", "component_version",
        )
        missing = [name for name in required if raw.get(name) in (None, "")]
        if missing:
            raise CompositionIncompatible("Q118_MISSING_COMPONENT_FIELDS:" + ",".join(missing))

        cid = str(raw["component_id"])
        family = str(raw["family_id"])
        if cid in seen_ids:
            raise CompositionIncompatible("Q118_DUPLICATE_COMPONENT_ID")
        seen_ids.add(cid)

        if str(raw["missingness"]) not in ALLOWED_MISSINGNESS:
            raise CompositionIncompatible("Q118_INVALID_MISSINGNESS")
        if str(raw["direction"]) not in ALLOWED_DIRECTIONS:
            raise CompositionIncompatible("Q118_INVALID_DIRECTION")

        ts = _parse_ts(str(raw["decision_timestamp"]), "component_decision_timestamp")
        if ts > cutoff:
            raise CompositionIncompatible("Q118_COMPONENT_AFTER_DECISION_CUTOFF")
        public_at = raw.get("public_at") or raw["decision_timestamp"]
        public_dt = _parse_ts(str(public_at), "public_at")
        if public_dt > cutoff:
            raise CompositionIncompatible("Q118_PIT_PUBLIC_AFTER_CUTOFF")

        lineage = str(raw.get("lineage_id", family))
        if lineage in seen_lineages:
            raise CompositionIncompatible("Q118_DUPLICATE_INFORMATION_LINEAGE")
        seen_lineages.add(lineage)

        dependency = raw.get("depends_on")
        if dependency is not None:
            if isinstance(dependency, str):
                deps = [dependency]
            elif isinstance(dependency, list) and all(isinstance(x, str) for x in dependency):
                deps = dependency
            else:
                raise CompositionIncompatible("Q118_INVALID_DEPENDENCY_METADATA")
            if any(x == bundle_id or x.startswith("composition:") for x in deps):
                raise CompositionIncompatible("Q118_RECURSIVE_COMPOSITION_DEPENDENCY")

        normalized.append({
            "component_id": cid,
            "family_id": family,
            "decision_timestamp": ts.isoformat(),
            "public_at": public_dt.isoformat(),
            "eligible_session": str(raw["eligible_session"]),
            "source_fingerprint": str(raw["source_fingerprint"]),
            "entity_fingerprint": str(raw["entity_fingerprint"]),
            "missingness": str(raw["missingness"]),
            "direction": str(raw["direction"]),
            "component_version": str(raw["component_version"]),
            "lineage_id": lineage,
        })

    sessions = {x["eligible_session"] for x in normalized}
    entities = {x["entity_fingerprint"] for x in normalized}
    if len(sessions) != 1:
        raise CompositionIncompatible("Q118_SESSION_MISMATCH")
    if len(entities) != 1:
        raise CompositionIncompatible("Q118_ENTITY_MISMATCH")

    normalized.sort(key=lambda x: x["component_id"])
    component_fingerprints = [fingerprint(x) for x in normalized]
    manifest = {
        "schema_version": 1,
        "bundle_id": bundle_id,
        "decision_timestamp": cutoff.isoformat(),
        "eligible_session": normalized[0]["eligible_session"],
        "component_count": len(normalized),
        "components": normalized,
        "component_fingerprints": component_fingerprints,
        "composition_mode": "STRUCTURAL_ONLY",
        "pit_alignment": True,
        "entity_alignment": True,
        "session_alignment": True,
        "family_lineage_unique": True,
        "missingness_deterministic": True,
        "direction_semantics_frozen": True,
        "recursive_leakage_checked": True,
        "performance_fields_consulted": False,
        "holdout_used": False,
        "performance_authorized": False,
    }
    manifest["bundle_fingerprint"] = fingerprint(manifest)
    return manifest


def synthetic_contract() -> dict[str, bool]:
    base = {
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
    other = dict(base)
    other.update({"component_id": "B", "family_id": "family_b", "source_fingerprint": "src-b", "lineage_id": "lineage-b"})
    manifest = validate_components([other, base], decision_timestamp="2026-10-01T15:00:00+00:00")
    return {
        "deterministic_sort": manifest["components"][0]["component_id"] == "A",
        "pit_alignment": manifest["pit_alignment"],
        "lineage_unique": manifest["family_lineage_unique"],
        "fingerprint_present": len(manifest["bundle_fingerprint"]) == 64,
        "performance_quarantine": manifest["performance_fields_consulted"] is False,
    }
