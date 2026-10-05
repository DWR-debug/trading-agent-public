"""Deterministic research-hypothesis intake compiler.

The compiler converts literature-driven candidate inventories into validated,
quarantined research objects. It is deliberately non-authoritative: it cannot
rank, select, tune, evaluate performance, use holdout outcomes, or authorize
promotion. It is suitable for feeding AI-generated or human-generated ideas
into the deterministic research gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from automation.candidate_robustness_gate import validate_candidate as validate_early_robustness

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_KEYS = {
    "performance", "performance_rank", "candidate_rank", "holdout_return",
    "holdout_drawdown", "profit_factor", "drawdown", "pnl", "return",
    "returns", "winner", "selected", "promotion", "optimized_weights",
}
REQUIRED = ("id", "name", "hypothesis", "construction", "sources", "next_gate")


def canonical(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(payload: Any) -> str:
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


def _validate_candidate(candidate: dict[str, Any], source_path: str) -> dict[str, Any]:
    forbidden = sorted(FORBIDDEN_KEYS.intersection(candidate))
    if forbidden:
        raise ValueError(f"DISCOVERY_FORBIDDEN_FIELDS:{source_path}:{candidate.get('id','?')}:{','.join(forbidden)}")
    missing = [key for key in REQUIRED if candidate.get(key) in (None, "", [])]
    if missing:
        raise ValueError(f"DISCOVERY_MISSING_FIELDS:{source_path}:{candidate.get('id','?')}:{','.join(missing)}")
    if not isinstance(candidate["sources"], list) or not candidate["sources"] or not all(isinstance(x, str) and x.strip() for x in candidate["sources"]):
        raise ValueError(f"DISCOVERY_INVALID_SOURCES:{source_path}:{candidate['id']}")
    next_gate = str(candidate["next_gate"]).strip()
    if not next_gate or next_gate.lower() in {"performance", "backtest", "select_best"}:
        raise ValueError(f"DISCOVERY_UNSAFE_NEXT_GATE:{source_path}:{candidate['id']}")
    early = validate_early_robustness(candidate, source_path)
    if early["status"] != "PRE_FORMAL_ROBUSTNESS_COMPLETED":
        raise ValueError(
            f"DISCOVERY_CANDIDATE_ROBUSTNESS_GATE_FAIL:{source_path}:{candidate['id']}:"
            + ";".join(early["violations"])
        )
    return {
        "id": str(candidate["id"]),
        "name": str(candidate["name"]),
        "hypothesis": str(candidate["hypothesis"]),
        "construction": str(candidate["construction"]),
        "sources": sorted(set(candidate["sources"])),
        "next_gate": next_gate,
        "status": "QUARANTINED_HYPOTHESIS_ONLY",
        "performance_authorized": False,
        "holdout_used": False,
        "family_selected": False,
        "parameter_search_allowed": False,
        "asset_search_allowed": False,
        "threshold_search_allowed": False,
        "horizon_search_allowed": False,
        "promotion_allowed": False,
        "candidate_robustness_gate": {
            "status": early["status"],
            "candidate_fingerprint": early["candidate_fingerprint"],
            "dimensions": early["dimensions"],
            "formalization_allowed": False,
            "receipt_required_before_any_formal_phase": True,
        },
    }


def compile_inventories(paths: list[Path]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    input_manifests: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("candidates"), list):
            raise ValueError(f"DISCOVERY_INVALID_INVENTORY:{path}")
        input_manifests.append({
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "candidate_count": len(payload["candidates"]),
            "inventory_status": payload.get("status"),
        })
        for raw in payload["candidates"]:
            compiled = _validate_candidate(raw, str(path))
            if compiled["id"] in seen_ids:
                raise ValueError(f"DISCOVERY_DUPLICATE_CANDIDATE_ID:{compiled['id']}")
            seen_ids.add(compiled["id"])
            compiled["candidate_fingerprint"] = fingerprint(compiled)
            candidates.append(compiled)

    candidates.sort(key=lambda item: item["id"])
    result = {
        "schema_version": 1,
        "compiler": "research_hypothesis_compiler",
        "status": "HYPOTHESIS_QUARANTINE_COMPILED",
        "input_manifests": sorted(input_manifests, key=lambda item: item["path"]),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "scientific_boundary": {
            "source_claims_are_not_project_evidence": True,
            "performance": False,
            "holdout": False,
            "ranking": False,
            "selection": False,
            "parameter_search": False,
            "asset_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "promotion": False,
            "live_execution": False,
        },
    }
    result["bundle_fingerprint"] = fingerprint(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research/runs/self_hosted/research_discovery/hypothesis_quarantine.json"))
    parser.add_argument(
        "--input",
        action="append",
        dest="inputs",
        default=[
            "research/frontier/q104_candidate_wave_2026_10_01.json",
            "research/frontier/q109_candidate_wave_2026_10_01.json",
            "research/frontier/q123_candidate_wave_2026_10_02.json",
            "research/frontier/q126_q132_candidate_wave_2026_10_03.json",
            "research/frontier/q197_q198_candidate_wave_2026_10_04.json",
            "research/frontier/q199_q201_candidate_wave_2026_10_04.json",
            "research/frontier/q205_nlrb_robustness_inventory_2026_10_05.json",
    "research/frontier/q214_disclosure_risk_state_2026_10_05.json",
        ],
    )
    args = parser.parse_args()
    paths = [ROOT / item for item in args.inputs]
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"DISCOVERY_INPUT_NOT_FOUND:{path}")
    result = compile_inventories(paths)
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    from automation.candidate_robustness_gate import compile_receipt
    robustness_receipt = compile_receipt(paths, str((out.parent / "pre_formal_candidate_robustness.json").relative_to(ROOT)))
    robustness_path = out.parent / "pre_formal_candidate_robustness.json"
    robustness_path.write_text(
        json.dumps(robustness_receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if robustness_receipt["status"] != "PRE_FORMAL_ROBUSTNESS_COMPLETED":
        raise RuntimeError("DISCOVERY_CANDIDATE_ROBUSTNESS_GATE_FAIL")
    print("PRE_FORMAL_ROBUSTNESS_STATUS=" + robustness_receipt["status"])
    print("PRE_FORMAL_ROBUSTNESS_FINGERPRINT=" + robustness_receipt["bundle_fingerprint"])
    print("DISCOVERY_STATUS=" + result["status"])
    print("DISCOVERY_CANDIDATES=" + str(result["candidate_count"]))
    print("DISCOVERY_FINGERPRINT=" + result["bundle_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
