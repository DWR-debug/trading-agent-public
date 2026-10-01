"""Q118 structural validator for deterministic candidate composition.

This module is intentionally research-contract-only. It never evaluates returns,
selects candidates, consults holdout outcomes, tunes weights, or authorizes
performance/live execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_COMPONENT_KEYS = {
    "component_id",
    "lineage_id",
    "version",
    "preregistration_id",
    "decision_cutoff",
    "public_at",
    "eligible_session",
    "entity_ids",
    "signal_direction",
    "missingness_semantics",
    "source_fingerprint",
}

FORBIDDEN_COMPONENT_KEYS = {
    "research_return",
    "holdout_return",
    "future_return",
    "performance_return",
    "drawdown",
    "profit_factor",
    "pnl",
    "selected_by_performance",
    "selected_candidate",
    "performance_rank",
    "ranking",
    "optimized_weight",
    "fitted_weight",
    "holdout_used_for_selection",
}

SIGNAL_DIRECTIONS = {
    "LONG_POSITIVE",
    "LONG_NEGATIVE",
    "TWO_SIDED",
    "NEUTRAL",
}


def _parse_datetime(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("Q118_INVALID_DATETIME")
    raw = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        raise ValueError("Q118_DATETIME_MUST_BE_TIMEZONE_AWARE")
    return parsed.astimezone(timezone.utc)


def canonical_bundle_payload(manifest: dict[str, Any]) -> dict[str, Any]:
    components = manifest.get("components")
    if not isinstance(components, list) or not components:
        raise ValueError("Q118_COMPONENTS_REQUIRED")
    canonical_components = []
    for component in sorted(components, key=lambda x: x["component_id"]):
        canonical_components.append(
            {
                "component_id": component["component_id"],
                "lineage_id": component["lineage_id"],
                "version": component["version"],
                "preregistration_id": component["preregistration_id"],
                "decision_cutoff": _parse_datetime(component["decision_cutoff"]).isoformat(),
                "public_at": _parse_datetime(component["public_at"]).isoformat(),
                "eligible_session": component["eligible_session"],
                "entity_ids": sorted(component["entity_ids"]),
                "signal_direction": component["signal_direction"],
                "missingness_semantics": component["missingness_semantics"],
                "source_fingerprint": component["source_fingerprint"],
                "dependencies": sorted(component.get("dependencies", [])),
            }
        )
    return {
        "bundle_id": manifest.get("bundle_id"),
        "composition_form": manifest.get("composition_form"),
        "decision_cutoff": _parse_datetime(manifest["decision_cutoff"]).isoformat(),
        "eligible_session": manifest["eligible_session"],
        "entity_ids": sorted(manifest["entity_ids"]),
        "components": canonical_components,
        "require_independent_lineages": bool(manifest.get("require_independent_lineages", True)),
    }


def composition_fingerprint(manifest: dict[str, Any]) -> str:
    payload = canonical_bundle_payload(manifest)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_composition(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("performance_authorized") is True:
        raise ValueError("Q118_PERFORMANCE_AUTHORIZATION_FORBIDDEN")
    if manifest.get("holdout_selection_allowed") is True:
        raise ValueError("Q118_HOLDOUT_SELECTION_FORBIDDEN")
    if manifest.get("parameter_search_allowed") is True:
        raise ValueError("Q118_PARAMETER_SEARCH_FORBIDDEN")

    cutoff = _parse_datetime(manifest["decision_cutoff"])
    components = manifest.get("components")
    if not isinstance(components, list) or not components:
        raise ValueError("Q118_COMPONENTS_REQUIRED")

    bundle_entities = set(manifest.get("entity_ids", []))
    if not bundle_entities:
        raise ValueError("Q118_BUNDLE_ENTITIES_REQUIRED")

    component_ids = []
    lineage_ids = []
    eligible_sessions = set()
    public_times = []

    for component in components:
        missing = REQUIRED_COMPONENT_KEYS - component.keys()
        if missing:
            raise ValueError("Q118_COMPONENT_KEYS_MISSING:" + ",".join(sorted(missing)))
        forbidden = FORBIDDEN_COMPONENT_KEYS.intersection(component.keys())
        if forbidden:
            raise ValueError("Q118_FORBIDDEN_RESULT_FIELDS:" + ",".join(sorted(forbidden)))

        cid = component["component_id"]
        lineage = component["lineage_id"]
        if not isinstance(cid, str) or not cid:
            raise ValueError("Q118_INVALID_COMPONENT_ID")
        if not isinstance(lineage, str) or not lineage:
            raise ValueError("Q118_INVALID_LINEAGE_ID")
        if cid in component_ids:
            raise ValueError("Q118_DUPLICATE_COMPONENT_ID")
        component_ids.append(cid)
        lineage_ids.append(lineage)

        if component["signal_direction"] not in SIGNAL_DIRECTIONS:
            raise ValueError("Q118_INVALID_SIGNAL_DIRECTION")
        if not isinstance(component["missingness_semantics"], str) or not component["missingness_semantics"]:
            raise ValueError("Q118_INVALID_MISSINGNESS_SEMANTICS")
        if not isinstance(component["source_fingerprint"], str) or len(component["source_fingerprint"]) < 16:
            raise ValueError("Q118_INVALID_SOURCE_FINGERPRINT")

        public_at = _parse_datetime(component["public_at"])
        component_cutoff = _parse_datetime(component["decision_cutoff"])
        if public_at > component_cutoff:
            raise ValueError("Q118_COMPONENT_PUBLISHED_AFTER_OWN_CUTOFF")
        if public_at > cutoff:
            raise ValueError("Q118_FUTURE_INFORMATION_DETECTED")
        if component_cutoff != cutoff:
            raise ValueError("Q118_CUTOFF_MISMATCH")
        if component["eligible_session"] != manifest["eligible_session"]:
            raise ValueError("Q118_SESSION_MISMATCH")

        entities = set(component["entity_ids"])
        if entities != bundle_entities:
            raise ValueError("Q118_ENTITY_SET_MISMATCH")

        dependencies = component.get("dependencies", [])
        if not isinstance(dependencies, list):
            raise ValueError("Q118_INVALID_DEPENDENCIES")
        if manifest.get("bundle_id") in dependencies:
            raise ValueError("Q118_RECURSIVE_BUNDLE_DEPENDENCY")

        public_times.append(public_at)
        eligible_sessions.add(component["eligible_session"])

    if manifest.get("require_independent_lineages", True) and len(lineage_ids) != len(set(lineage_ids)):
        raise ValueError("Q118_DUPLICATE_LINEAGE_REQUIRES_EXPLICIT_DEDUPLICATION")

    if len(eligible_sessions) != 1:
        raise ValueError("Q118_MULTIPLE_SESSIONS")

    result = {
        "schema_version": "1.0",
        "status": "COMPOSITION_STRUCTURALLY_VALID",
        "bundle_id": manifest["bundle_id"],
        "composition_form": manifest["composition_form"],
        "component_count": len(components),
        "independent_lineage_count": len(set(lineage_ids)),
        "earliest_component_public_at": min(public_times).isoformat(),
        "latest_component_public_at": max(public_times).isoformat(),
        "decision_cutoff": cutoff.isoformat(),
        "eligible_session": manifest["eligible_session"],
        "entity_count": len(bundle_entities),
        "performance_evidence_consulted": False,
        "holdout_evidence_consulted": False,
        "result_fingerprint": composition_fingerprint(manifest),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = validate_composition(manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Q118_STATUS:", result["status"])
    print("Q118_FINGERPRINT:", result["result_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
