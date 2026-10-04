"""Universal early candidate-robustness gate.

This gate is intentionally pre-formal and non-performance. It tests whether a
candidate contract is structurally robust enough to enter any formal research
phase. It never ranks, tunes, selects, evaluates holdouts, authorizes
performance, promotes or executes live trading.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INVENTORIES = (
    "research/frontier/q104_candidate_wave_2026_10_01.json",
    "research/frontier/q109_candidate_wave_2026_10_01.json",
    "research/frontier/q123_candidate_wave_2026_10_02.json",
    "research/frontier/q126_q132_candidate_wave_2026_10_03.json",
    "research/frontier/q133_q145_candidate_wave_2026_10_03.json",
    "research/frontier/q146_q151_candidate_wave_2026_10_03.json",
    "research/frontier/q152_q165_candidate_wave_2026_10_03.json",
    "research/frontier/q166_q170_candidate_wave_2026_10_03.json",
    "research/frontier/q171_q178_candidate_wave_2026_10_03.json",
    "research/frontier/q179_q184_candidate_wave_2026_10_04.json",
    "research/frontier/q185_q186_candidate_wave_2026_10_04.json",
)

FORBIDDEN_KEYS = {
    "performance",
    "performance_rank",
    "candidate_rank",
    "holdout_return",
    "holdout_drawdown",
    "profit_factor",
    "drawdown",
    "pnl",
    "return",
    "returns",
    "winner",
    "selected",
    "promotion",
    "optimized_weights",
    "parameter_search",
    "threshold_search",
    "horizon_search",
    "asset_search",
    "variant_search",
    "holdout_selection",
    "candidate_selection",
    "family_ranking",
    "promotion_decision",
    "performance_authorization",
    "future_data",
    "amendment_rewrite",
}

REQUIRED_FIELDS = ("id", "name", "hypothesis", "construction", "sources", "next_gate")

ROBUSTNESS_DIMENSIONS = (
    "construction_invariance",
    "input_order_invariance",
    "future_data_invariance",
    "missingness_fail_closed",
    "revision_amendment_invariance",
    "identity_mapping_fail_closed",
    "parameter_threshold_horizon_lock",
    "source_reproducibility",
)

FORMAL_STATES = frozenset({
    "FORMAL",
    "PREREGISTERED",
    "COVERAGE_FORMAL",
    "PIT_FORMAL",
    "PERFORMANCE_FORMAL",
})


def canonical(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(payload: Any) -> str:
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


def _construction_has_deterministic_boundary(candidate: dict[str, Any]) -> bool:
    text = " ".join(
        str(candidate.get(key, "")).lower()
        for key in ("construction", "hypothesis", "next_gate")
    )
    markers = (
        "fixed",
        "frozen",
        "deterministic",
        "pit",
        "public availability",
        "acceptance timestamp",
        "publication",
    )
    return any(marker in text for marker in markers)


def validate_candidate(
    candidate: dict[str, Any],
    source_path: str,
    artifact_path: str = "ACTION_ARTIFACT_NOT_YET_WRITTEN",
) -> dict[str, Any]:
    violations: list[str] = []
    forbidden = sorted(FORBIDDEN_KEYS.intersection(candidate))
    if forbidden:
        violations.append("forbidden_fields:" + ",".join(forbidden))

    missing = [key for key in REQUIRED_FIELDS if candidate.get(key) in (None, "", [])]
    if missing:
        violations.append("missing_fields:" + ",".join(missing))

    sources = candidate.get("sources")
    valid_sources = (
        isinstance(sources, list)
        and bool(sources)
        and all(isinstance(x, str) and x.strip() for x in sources)
        and len(set(sources)) == len(sources)
    )
    if not valid_sources:
        violations.append("invalid_sources")

    next_gate = str(candidate.get("next_gate", "")).strip().lower()
    if not next_gate or next_gate in {"performance", "backtest", "select_best"}:
        violations.append("unsafe_next_gate")

    deterministic_boundary = _construction_has_deterministic_boundary(candidate)
    if not deterministic_boundary:
        violations.append("missing_deterministic_boundary_marker")

    normalized = dict(candidate)
    normalized["sources"] = sorted(set(str(x) for x in sources)) if valid_sources else sources
    base_fp = fingerprint(normalized)

    reordered = dict(candidate)
    if isinstance(candidate.get("sources"), list):
        reordered["sources"] = list(reversed(candidate["sources"]))
    reordered["sources"] = sorted(set(str(x) for x in reordered["sources"])) if valid_sources else reordered["sources"]
    input_order_invariance = base_fp == fingerprint(reordered)
    if not input_order_invariance:
        violations.append("source_order_invariance_failed")

    contaminated = dict(candidate)
    contaminated["holdout_return"] = 1.0
    future_data_rejected = bool(FORBIDDEN_KEYS.intersection(contaminated))
    if not future_data_rejected:
        violations.append("future_data_mutation_not_rejected")

    missingness_probe = dict(candidate)
    missingness_probe["sources"] = []
    missingness_rejected = (
        not isinstance(missingness_probe.get("sources"), list)
        or not missingness_probe["sources"]
        or len(set(missingness_probe["sources"])) != len(missingness_probe["sources"])
    )
    if not missingness_rejected:
        violations.append("missingness_fail_closed_failed")

    identity_probe = dict(candidate)
    identity_probe.pop("id", None)
    identity_rejected = any(
        identity_probe.get(key) in (None, "", [])
        for key in REQUIRED_FIELDS
    )
    if not identity_rejected:
        violations.append("identity_fail_closed_failed")

    lock_probe = dict(candidate)
    lock_probe.update({
        "parameter_search": True,
        "threshold_search": True,
        "horizon_search": True,
    })
    parameter_lock_rejected = bool(FORBIDDEN_KEYS.intersection(lock_probe))
    if not parameter_lock_rejected:
        violations.append("parameter_lock_mutation_not_rejected")

    revision_probe = dict(candidate)
    revision_probe["amendment_rewrite"] = True
    revision_rejected = bool(FORBIDDEN_KEYS.intersection(revision_probe))
    if not revision_rejected:
        violations.append("revision_mutation_not_rejected")

    governance = {
        "holdout_selection": False,
        "parameter_search": False,
        "asset_search": False,
        "threshold_search": False,
        "horizon_search": False,
        "variant_search": False,
        "family_ranking": False,
        "candidate_selection": False,
        "promotion_decision": False,
        "performance_authorization": False,
    }

    dimensions = {
        "construction_invariance": deterministic_boundary and canonical(candidate) == canonical(json.loads(canonical(candidate))),
        "input_order_invariance": input_order_invariance,
        "future_data_invariance": future_data_rejected,
        "missingness_fail_closed": missingness_rejected,
        "revision_amendment_invariance": revision_rejected,
        "identity_mapping_fail_closed": identity_rejected,
        "parameter_threshold_horizon_lock": parameter_lock_rejected,
        "source_reproducibility": valid_sources and bool(source_path),
    }
    if not all(dimensions.values()):
        violations.append("robustness_dimension_failed")

    return {
        "candidate_id": str(candidate.get("id", "")),
        "source_path": source_path,
        "artifact_path": artifact_path,
        "candidate_fingerprint": base_fp,
        "status": "PRE_FORMAL_ROBUSTNESS_COMPLETED" if not violations else "PRE_FORMAL_ROBUSTNESS_FAILED",
        "formalization_allowed": False,
        "research_only": True,
        "screen_is_descriptive_only": True,
        "no_post_hoc_tuning": True,
        "dimensions": dimensions,
        "synthetic_checks": {
            "future_data_mutation_rejected": future_data_rejected,
            "missingness_mutation_rejected": missingness_rejected,
            "identity_mutation_rejected": identity_rejected,
            "parameter_lock_mutation_rejected": parameter_lock_rejected,
            "revision_mutation_rejected": revision_rejected,
        },
        "governance": governance,
        "violations": violations,
        "scientific_evidence": False,
        "performance_authorization": False,
        "promotion": False,
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }

def compile_receipt(
    inventory_paths: list[Path],
    artifact_path: str = "ACTION_ARTIFACT_NOT_YET_WRITTEN",
    root: Path = ROOT,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    inventory_manifests: list[dict[str, Any]] = []
    seen: set[str] = set()

    for path in inventory_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("candidates"), list):
            raise ValueError(f"INVALID_INVENTORY:{path}")
        inventory_manifests.append({
            "path": str(path.resolve().relative_to(root.resolve())).replace("\\", "/"),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "candidate_count": len(payload["candidates"]),
        })
        for candidate in payload["candidates"]:
            if not isinstance(candidate, dict):
                raise ValueError(f"INVALID_CANDIDATE_OBJECT:{path}")
            candidate_id = str(candidate.get("id", ""))
            if candidate_id in seen:
                raise ValueError(f"DUPLICATE_CANDIDATE_ID:{candidate_id}")
            seen.add(candidate_id)
            candidates.append(
                validate_candidate(
                    candidate,
                    str(path.resolve().relative_to(root.resolve())).replace("\\", "/"),
                    artifact_path,
                )
            )

    candidates.sort(key=lambda item: item["candidate_id"])
    failed = [item for item in candidates if item["status"] != "PRE_FORMAL_ROBUSTNESS_COMPLETED"]
    receipt = {
        "schema_version": 1,
        "receipt_type": "universal_pre_formal_candidate_robustness",
        "status": "PRE_FORMAL_ROBUSTNESS_COMPLETED" if not failed else "PRE_FORMAL_ROBUSTNESS_FAILED",
        "effective_policy": "candidate robustness is mandatory before any formal phase",
        "inventory_manifests": sorted(inventory_manifests, key=lambda x: x["path"]),
        "candidate_count": len(candidates),
        "failed_candidate_count": len(failed),
        "candidates": candidates,
        "required_dimensions": list(ROBUSTNESS_DIMENSIONS),
        "formalization_allowed": False,
        "scientific_evidence": False,
        "performance_authorization": False,
        "promotion": False,
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    receipt["bundle_fingerprint"] = fingerprint(receipt)
    return receipt


def require_receipt_for_formal_phase(candidate_id: str, receipt: dict[str, Any]) -> None:
    if receipt.get("status") != "PRE_FORMAL_ROBUSTNESS_COMPLETED":
        raise RuntimeError(f"UNIVERSAL_CANDIDATE_ROBUSTNESS_GATE_FAIL:{candidate_id}:receipt_status")
    item = next((x for x in receipt.get("candidates", []) if x.get("candidate_id") == candidate_id), None)
    if not isinstance(item, dict):
        raise RuntimeError(f"UNIVERSAL_CANDIDATE_ROBUSTNESS_GATE_FAIL:{candidate_id}:missing_candidate")
    if item.get("status") != "PRE_FORMAL_ROBUSTNESS_COMPLETED":
        raise RuntimeError(f"UNIVERSAL_CANDIDATE_ROBUSTNESS_GATE_FAIL:{candidate_id}:candidate_failed")
    if item.get("formalization_allowed") is not False:
        raise RuntimeError(f"UNIVERSAL_CANDIDATE_ROBUSTNESS_GATE_FAIL:{candidate_id}:formalization_flag")
    if item.get("research_only") is not True or item.get("no_post_hoc_tuning") is not True:
        raise RuntimeError(f"UNIVERSAL_CANDIDATE_ROBUSTNESS_GATE_FAIL:{candidate_id}:governance_boundary")
    dimensions = set(item.get("dimensions", {}))
    missing = sorted(set(ROBUSTNESS_DIMENSIONS) - dimensions)
    if missing or not all(item["dimensions"].get(x) is True for x in ROBUSTNESS_DIMENSIONS):
        raise RuntimeError(f"UNIVERSAL_CANDIDATE_ROBUSTNESS_GATE_FAIL:{candidate_id}:dimensions")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--input", action="append", dest="inputs")
    args = parser.parse_args()
    raw_inputs = args.inputs or list(DEFAULT_INVENTORIES)
    paths = [(ROOT / item).resolve() for item in raw_inputs]
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"INVENTORY_NOT_FOUND:{path}")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    artifact_path = str(out.relative_to(ROOT)).replace("\\", "/") if out.is_relative_to(ROOT) else str(out)
    receipt = compile_receipt(paths, artifact_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "candidate_count": receipt["candidate_count"],
        "failed_candidate_count": receipt["failed_candidate_count"],
        "bundle_fingerprint": receipt["bundle_fingerprint"],
    }, sort_keys=True))
    return 0 if receipt["status"] == "PRE_FORMAL_ROBUSTNESS_COMPLETED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
