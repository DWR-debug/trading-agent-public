"""Avoid repeating a completed Q220 as-filed population receipt.

This is an operational resource gate only. It does not create scientific
evidence and never changes the frozen population/PIT contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from automation.q220_as_filed_xbrl_population_gate import (
    CONTRACT_PATH,
    ROOT,
    TARGET_ISSUERS,
    WINDOW_END,
    WINDOW_START,
)

RECEIPT_PATH = ROOT / "research/evidence/q220_as_filed_xbrl_population_latest.json"
GATE_PATH = ROOT / "automation/q220_as_filed_xbrl_population_gate.py"
EXPECTED_RECORD_COUNT = 55
POSITIVE_STATUS = "Q220_AS_FILED_XBRL_POPULATION_COMPLETED"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value.lower())
    )


def canonical_receipt_fingerprint(receipt: Mapping[str, Any]) -> str:
    payload = dict(receipt)
    payload.pop("receipt_fingerprint", None)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256_bytes(encoded)


def positive_receipt_is_current(
    receipt: Mapping[str, Any],
    *,
    gate_code_path: Path = GATE_PATH,
    contract_path: Path = CONTRACT_PATH,
) -> bool:
    """Return true only for a positive receipt matching current frozen code/contract."""
    try:
        expected_gate_sha = sha256_bytes(gate_code_path.read_bytes())
        expected_contract_sha = sha256_bytes(contract_path.read_bytes())
    except OSError:
        return False

    if (
        receipt.get("candidate_id") != "Q220"
        or receipt.get("mode") != "population"
        or receipt.get("status") != POSITIVE_STATUS
        or receipt.get("row_count") != EXPECTED_RECORD_COUNT
        or receipt.get("record_count") != EXPECTED_RECORD_COUNT
        or receipt.get("failure_count") != 0
        or receipt.get("gate_code_sha256") != expected_gate_sha
        or receipt.get("contract_sha256") != expected_contract_sha
        or receipt.get("fixed_universe") != dict(TARGET_ISSUERS)
        or receipt.get("window")
        != {"start": WINDOW_START.isoformat(), "end": WINDOW_END.isoformat()}
    ):
        return False

    digest = receipt.get("receipt_fingerprint")
    if not valid_sha256(digest) or digest != canonical_receipt_fingerprint(receipt):
        return False

    interpretation = receipt.get("interpretation")
    if not isinstance(interpretation, dict) or (
        interpretation.get("source_pit_structure_ready") is not True
        or interpretation.get("performance_evidence") is not False
        or interpretation.get("performance_authorized") is not False
        or interpretation.get("promotion_allowed") is not False
    ):
        return False

    safety = receipt.get("safety")
    return isinstance(safety, dict) and (
        safety.get("paper_only") is True
        and safety.get("live_trading_enabled") is False
        and safety.get("orders_enabled") is False
        and safety.get("automatic_promotion") is False
    )


def population_repair_decision(
    receipt_path: Path = RECEIPT_PATH,
    *,
    force_rebuild: bool = False,
) -> tuple[bool, str]:
    """Return (run_population, reason); unknown or stale receipt means rerun."""
    if force_rebuild:
        return True, "FORCE_REBUILD_REQUESTED"
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return True, "RECEIPT_MISSING_OR_UNREADABLE"
    if not isinstance(receipt, dict) or not positive_receipt_is_current(receipt):
        return True, "RECEIPT_MISSING_NEGATIVE_STALE_OR_INVALID"
    return False, "SKIP_CURRENT_POSITIVE_RECEIPT"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, default=RECEIPT_PATH)
    parser.add_argument("--force", default="false")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    force = str(args.force).strip().lower() in {"1", "true", "yes", "on"}
    receipt_path = args.receipt if args.receipt.is_absolute() else ROOT / args.receipt
    run_population, reason = population_repair_decision(
        receipt_path,
        force_rebuild=force,
    )
    output = (
        f"run_population={'true' if run_population else 'false'}\n"
        f"reason={reason}\n"
    )
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(output)
    print(json.dumps({
        "run_population": run_population,
        "reason": reason,
        "scientific_evidence": False,
        "performance_authorization": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
