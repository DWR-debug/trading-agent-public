"""Deterministic metadata graph for reusable Trading-Agent research knowledge.

The index connects candidate contracts to reusable source/clock/identity
components and explicit cross-candidate relations. It never reads market
outcomes and never ranks candidates or authorizes performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TRUE = {
    "performance",
    "performance_authorization",
    "holdout_selection",
    "ranking",
    "tuning",
    "promotion_authorization",
    "live_execution",
}


def load(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"missing input: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_json(obj: object) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def assert_safe(obj: dict) -> None:
    for key in FORBIDDEN_TRUE:
        if obj.get(key) is True:
            raise SystemExit(f"unsafe metadata flag: {key}=true")


def build_index(contract: dict, candidate_specs: dict, active_registry: dict | None = None) -> dict:
    assert contract.get("status") == "ACTIVE_METADATA_ONLY"
    assert_safe(contract)
    candidates = candidate_specs.get("candidates", [])
    ids = [str(c.get("id")) for c in candidates if c.get("id")]
    if len(ids) != len(set(ids)):
        raise SystemExit("candidate IDs must be unique")

    contract_ids = {
        x["candidate"] for x in contract.get("candidate_component_links", [])
    }
    missing = sorted(contract_ids - set(ids))
    # Shared infrastructure may include historical compiler candidates that
    # are no longer in the active spec file. They remain visible as graph nodes
    # but are marked unresolved rather than silently dropped.
    candidate_status = {
        cid: {
            "present_in_current_spec": cid in ids,
            "active_registry_present": None if active_registry is None else cid in {
                str(x.get("code")) for x in active_registry.get("active_design_families", [])
            },
        }
        for cid in sorted(contract_ids | set(ids))
    }

    components = contract.get("reusable_components", [])
    links = contract.get("candidate_component_links", [])
    relations = contract.get("candidate_relations", [])
    motifs = contract.get("discovery_motifs", [])

    by_component = {}
    for link in links:
        by_component.setdefault(link["component"], []).append(link["candidate"])
    by_component = {
        k: sorted(set(v)) for k, v in sorted(by_component.items())
    }

    reusable_for = []
    for component_id, candidate_ids in by_component.items():
        component = next((c for c in components if c.get("id") == component_id), {})
        reusable_for.append({
            "component": component_id,
            "status": component.get("status"),
            "candidate_count": len(candidate_ids),
            "candidates": candidate_ids,
            "routing_hint": (
                "compute/verify shared structural prerequisite once, then fan out "
                "candidate-specific downstream gates"
            ) if len(candidate_ids) > 1 else "candidate-specific gate only",
        })

    out = {
        "schema_version": 1,
        "record_type": "knowledge_relation_index",
        "status": "METADATA_ONLY_NO_SCIENTIFIC_EVIDENCE",
        "source_contract": "research/governance/knowledge_relation_graph_contract_2026_10_06.json",
        "candidate_count_in_spec": len(ids),
        "candidate_status": candidate_status,
        "unresolved_contract_candidates": missing,
        "reusable_components": components,
        "shared_component_groups": reusable_for,
        "candidate_relations": relations,
        "discovery_motifs": motifs,
        "orchestration": contract.get("orchestration_rules", {}),
        "safety": {
            "PAPER_ONLY": True,
            "LIVE_TRADING_ENABLED": False,
            "ORDERS_ENABLED": False,
            "AUTOMATIC_PROMOTION": False,
            "performance": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
    }
    out["content_fingerprint"] = sha256_json(out)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--contract",
        type=Path,
        default=ROOT / "research/governance/knowledge_relation_graph_contract_2026_10_06.json",
    )
    ap.add_argument(
        "--candidate-specs",
        type=Path,
        default=ROOT / "research/candidates/orthogonal_candidate_specs_2026-10-05.json",
    )
    ap.add_argument(
        "--active-registry",
        type=Path,
        default=ROOT / "research/governance/active_research_registry.json",
    )
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    result = build_index(
        load(args.contract),
        load(args.candidate_specs),
        load(args.active_registry) if args.active_registry.is_file() else None,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
