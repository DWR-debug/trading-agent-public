"""Q104 I19/I20 XBRL concept-freeze audit.

This gate never chooses a concept. It verifies that the research design has
already frozen the exact XBRL fact/concept identifiers needed for reproducible
PIT construction. Missing specificity is a design blocker, not a performance
failure.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "research/preregistrations/q104_orthogonal_candidate_wave_2026_10_01.json"
INVENTORY = ROOT / "research/frontier/q104_candidate_wave_2026_10_01.json"

TARGETS = {"Q104:I19": ("accrual",), "Q104:I20": ("fundamental",)}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def exact_identifiers(text: str) -> list[str]:
    tokens = []
    for token in text.replace("`", " ").replace(",", " ").split():
        clean = token.strip("()[]{};:")
        if clean and any(ch.isupper() for ch in clean) and any(ch.islower() for ch in clean):
            if "http" not in clean.lower() and 3 <= len(clean) <= 80:
                tokens.append(clean)
    return sorted(set(tokens))


def audit() -> dict:
    prereg = load(PREREG)
    inventory = load(INVENTORY)
    by_id = {c["id"]: c for c in inventory.get("candidates", []) if isinstance(c, dict)}
    findings = []
    prereg_text = json.dumps(prereg, ensure_ascii=False, sort_keys=True)
    prereg_identifiers = exact_identifiers(prereg_text)
    for candidate_id, keywords in TARGETS.items():
        candidate = by_id.get(candidate_id, {})
        construction = str(candidate.get("construction", ""))
        pit = " ".join(str(x) for x in candidate.get("pit_requirements", []))
        identifiers = exact_identifiers(f"{construction} {pit}")
        related = [x for x in identifiers + prereg_identifiers if any(k in x.lower() for k in keywords)]
        findings.append({
            "candidate_id": candidate_id,
            "exact_identifier_candidates_seen": sorted(set(related)),
            "concept_frozen": bool(related),
            "status": "READY_FOR_CONCEPT_SPECIFIC_PIT_GATE" if related else "DESIGN_BLOCKED_CONCEPT_NOT_FROZEN",
        })
    blocked = [x for x in findings if not x["concept_frozen"]]
    return {
        "schema_version": 1,
        "task_id": "Q-2026-10-02-104-XBRL-CONCEPT-FREEZE-AUDIT",
        "status": "CONCEPT_FREEZE_AUDIT_COMPLETED",
        "findings": findings,
        "blocked_candidates": [x["candidate_id"] for x in blocked],
        "scientific_boundary": {
            "concept_selection": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "holdout_selection": False,
            "performance": False,
            "promotion": False,
            "live_execution": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research/runs/q104_xbrl_concept_freeze_audit/result.json"))
    args = parser.parse_args()
    result = audit()
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Q104_XBRL_CONCEPT_AUDIT_STATUS=" + result["status"])
    print("Q104_BLOCKED=" + ",".join(result["blocked_candidates"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
