"""Deterministic new-candidate intake and non-authorizing capacity disposition.

New hypotheses are validated using the existing robustness/compiler gate, checked
against known project inventories, and surfaced to the dashboard. This module
never widens the fixed active focus and never dispatches work.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from automation.candidate_robustness_gate import DEFAULT_INVENTORIES
from automation.research_hypothesis_compiler import _validate_candidate, fingerprint

ROOT = Path(__file__).resolve().parents[1]
QUEUE_RELATIVE_PATH = "research/candidates/candidate_intake_queue.json"
PROJECT_INVENTORY = "research/candidates/orthogonal_candidate_specs_2026-10-05.json"
ACTIVE_REGISTRY = "research/governance/active_research_registry.json"
STATIC_PROJECT_IDS = {"Q104:I19", "Q218", "Q219", "Q220", "Q221"}
REQUIRED_DISCOVERY_LISTS = ("cheap_falsifiers", "gates")


def _canonical_id(value: Any) -> str:
    return "".join(ch for ch in str(value or "").lower() if ch.isalnum())


def identifier_aliases(value: Any) -> set[str]:
    """Normalize Q123 / 123 and the legacy Q104:I19 identifier without fuzzy matching."""
    normalized = _canonical_id(value)
    if not normalized:
        return set()
    aliases = {normalized}
    if normalized.startswith("q"):
        aliases.add(normalized[1:])
    if normalized.isdigit():
        aliases.add("q" + normalized)
    if normalized == "q104i19":
        aliases.add("104")
    return aliases


def _manifest(root: Path, relative_path: str) -> dict[str, str] | None:
    path = root / relative_path
    if not path.is_file():
        return None
    return {"path": relative_path, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def known_project_ids(root: Path = ROOT) -> tuple[set[str], list[dict[str, str]]]:
    """Read IDs only from declared candidate registries/inventories, never outcomes."""
    ids = set(STATIC_PROJECT_IDS)
    paths = [PROJECT_INVENTORY, ACTIVE_REGISTRY, *DEFAULT_INVENTORIES]
    manifests: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    for relative in paths:
        if relative in seen_paths:
            continue
        seen_paths.add(relative)
        path = root / relative
        if not path.is_file():
            continue
        manifest = _manifest(root, relative)
        if manifest:
            manifests.append(manifest)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            # Do not claim a candidate is novel just because a known inventory
            # is malformed; the source fingerprint remains available for audit.
            continue
        if relative == ACTIVE_REGISTRY and isinstance(payload, dict):
            for section in ("active_design_families", "active_trials"):
                rows = payload.get(section, [])
                if not isinstance(rows, list):
                    continue
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    if row.get("code"):
                        ids.add(str(row["code"]))
                    nested = row.get("candidate_contracts", {})
                    if isinstance(nested, dict):
                        ids.update(str(code) for code in nested)
        if isinstance(payload, dict) and isinstance(payload.get("candidates"), list):
            for row in payload["candidates"]:
                if isinstance(row, dict) and row.get("id"):
                    ids.add(str(row["id"]))
    return ids, sorted(manifests, key=lambda x: x["path"])


def _valid_text_list(candidate: dict[str, Any], field: str) -> bool:
    value = candidate.get(field)
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def _candidate_row(
    raw: Any,
    index: int,
    duplicate_aliases: set[str],
    known_aliases: set[str],
    queue_relative_path: str,
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {
            "queue_position": index,
            "candidate_id": f"ROW-{index}",
            "candidate_name": "Invalid candidate record",
            "status": "BLOCKED_INVALID_RECORD",
            "disposition": "BLOCKED",
            "reason": "Candidate entry must be a JSON object.",
            "dispatchable": False,
            "capacity_assignment": None,
        }

    candidate_id = str(raw.get("id") or "").strip()
    aliases = identifier_aliases(candidate_id)
    base = {
        "queue_position": index,
        "candidate_id": candidate_id or f"ROW-{index}",
        "candidate_name": str(raw.get("name") or "(name missing)"),
        "next_gate": str(raw.get("next_gate") or ""),
        "cheap_falsifiers": raw.get("cheap_falsifiers", []) if isinstance(raw.get("cheap_falsifiers", []), list) else [],
        "gates": raw.get("gates", []) if isinstance(raw.get("gates", []), list) else [],
        "dispatchable": False,
        "capacity_assignment": None,
    }
    if aliases & duplicate_aliases:
        return {
            **base,
            "status": "BLOCKED_DUPLICATE_QUEUE_ID",
            "disposition": "BLOCKED",
            "reason": "Mehrere Queue-Einträge verwenden dieselbe normalisierte Kandidaten-ID.",
        }
    if aliases & known_aliases:
        return {
            **base,
            "status": "BLOCKED_ID_ALREADY_IN_PROJECT",
            "disposition": "BLOCKED",
            "reason": "Die Kandidaten-ID existiert bereits in einem Projektinventar, der aktiven Registry oder dem gesperrten Fokus.",
        }
    missing_lists = [field for field in REQUIRED_DISCOVERY_LISTS if not _valid_text_list(raw, field)]
    if missing_lists:
        return {
            **base,
            "status": "BLOCKED_MISSING_FALSIFIERS_OR_GATES",
            "disposition": "BLOCKED",
            "reason": "Nicht-leere Textlisten erforderlich: " + ", ".join(missing_lists),
        }
    try:
        compiled = _validate_candidate(raw, f"{queue_relative_path}[{index}]")
    except (ValueError, TypeError, KeyError) as exc:
        return {
            **base,
            "status": "BLOCKED_ROBUSTNESS_OR_SCHEMA",
            "disposition": "BLOCKED",
            "reason": str(exc),
        }

    # Fingerprint the entire submitted contract (including falsifiers and gates),
    # not only the subset emitted by the shared hypothesis compiler.
    contract_fingerprint = fingerprint({"submitted_contract": raw, "compiled_contract": compiled})
    return {
        **base,
        "candidate_fingerprint": contract_fingerprint,
        "status": "VALIDATED_QUARANTINED_WAITING_FOR_FOCUS_RELEASE",
        "disposition": "QUARANTINED_NOT_DISPATCHABLE",
        "reason": "Schema und früher Robustheitsvertrag bestanden. Vor einer Kapazitätszuteilung ist eine explizite Fokusentscheidung erforderlich.",
        "suggested_lane": "FRONTIER DISCOVERY AFTER EXPLICIT ADMISSION",
        "performance_authorized": False,
        "promotion_allowed": False,
        "live_execution_allowed": False,
    }


def build_plan_from_payload(
    payload: Any,
    *,
    known_ids: set[str] | None = None,
    active_focus: list[str] | tuple[str, ...] = ("Q104:I19", "Q220", "Q221"),
    queue_fingerprint: str = "",
    queue_relative_path: str = QUEUE_RELATIVE_PATH,
    registry_manifests: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    valid_payload = (
        isinstance(payload, dict)
        and payload.get("schema_version") == 1
        and isinstance(payload.get("candidates"), list)
    )
    queue_error = None if valid_payload else "Queue must contain schema_version=1 and a candidates array."
    if not valid_payload:
        raw_candidates = []
        queue_status = "QUEUE_INVALID"
        payload_for_fingerprint = {"schema_version": None, "candidates": []}
    else:
        raw_candidates = payload["candidates"]
        payload_for_fingerprint = payload
        queue_status = "EMPTY_QUEUE" if not raw_candidates else "ASSESSMENT_COMPLETED"

    alias_counts: dict[str, int] = {}
    for raw in raw_candidates:
        candidate_id = raw.get("id") if isinstance(raw, dict) else None
        for alias in identifier_aliases(candidate_id):
            alias_counts[alias] = alias_counts.get(alias, 0) + 1
    duplicate_aliases = {alias for alias, count in alias_counts.items() if count > 1}

    project_ids = set(known_ids or set()) | set(active_focus) | STATIC_PROJECT_IDS
    known_aliases: set[str] = set()
    for candidate_id in project_ids:
        known_aliases.update(identifier_aliases(candidate_id))

    rows = [
        _candidate_row(raw, index, duplicate_aliases, known_aliases, queue_relative_path)
        for index, raw in enumerate(raw_candidates, start=1)
    ]
    validated = sum(row["status"] == "VALIDATED_QUARANTINED_WAITING_FOR_FOCUS_RELEASE" for row in rows)
    blocked = len(rows) - validated
    result = {
        "schema_version": 1,
        "record_type": "candidate_intake_capacity_disposition",
        "status": queue_status,
        "queue_path": queue_relative_path,
        "queue_fingerprint": queue_fingerprint or fingerprint(payload_for_fingerprint),
        "registry_manifests": sorted(registry_manifests or [], key=lambda x: x.get("path", "")),
        "active_focus_lock": list(active_focus),
        "policy": {
            "order": "FIFO in queue-file order; no outcome-based ranking",
            "new_candidates_auto_dispatch": False,
            "active_focus_auto_widening": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "parameter_search": False,
            "promotion": False,
            "live_execution": False,
            "padding_or_duplicate_compute": False,
        },
        "summary": {
            "total_candidates": len(rows),
            "validated_quarantined": validated,
            "blocked": blocked,
            "dispatchable_now": 0,
            "capacity_consumed": 0,
        },
        "queue_error": queue_error,
        "candidates": rows,
        "scientific_authority": False,
        "PAPER_ONLY": True,
        "LIVE_TRADING_ENABLED": False,
        "ORDERS_ENABLED": False,
        "AUTOMATIC_PROMOTION": False,
    }
    result["plan_fingerprint"] = fingerprint(result)
    return result


def build_candidate_intake_plan(
    root: Path = ROOT,
    active_focus: list[str] | tuple[str, ...] = ("Q104:I19", "Q220", "Q221"),
    queue_relative_path: str = QUEUE_RELATIVE_PATH,
) -> dict[str, Any]:
    path = root / queue_relative_path
    try:
        raw_bytes = path.read_bytes()
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        plan = build_plan_from_payload(
            {},
            active_focus=active_focus,
            queue_relative_path=queue_relative_path,
        )
        plan["status"] = "QUEUE_INVALID"
        plan["queue_error"] = f"Queue cannot be read: {type(exc).__name__}: {exc}"
        plan.pop("plan_fingerprint", None)
        plan["plan_fingerprint"] = fingerprint(plan)
        return plan

    known_ids, manifests = known_project_ids(root)
    return build_plan_from_payload(
        payload,
        known_ids=known_ids,
        active_focus=active_focus,
        queue_fingerprint=hashlib.sha256(raw_bytes).hexdigest(),
        queue_relative_path=queue_relative_path,
        registry_manifests=manifests,
    )
