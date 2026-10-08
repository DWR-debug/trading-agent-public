"""Fail-closed authorization gate for the exact Q218 independent replication trial."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUTH_PATH = ROOT / "research/authorizations/q218_independent_replication_2026_10_08.json"
CONTRACT_PATH = ROOT / "research/governance/q218_independent_replication_contract_2026_10_08.json"
SOURCE_TRIAL_ID = "T-2026-10-08-Q218-PERFORMANCE-01"
REPLICATION_TRIAL_ID = "T-2026-10-08-Q218-REPLICATION-01"
EXPECTED_SAFETY = {
    "paper_only": True,
    "live_trading_enabled": False,
    "orders_enabled": False,
    "automatic_promotion": False,
}
NO_SEARCH_FLAGS = (
    "selection_used",
    "holdout_selection_used",
    "parameter_search",
    "threshold_search",
    "horizon_search",
    "asset_search",
    "variant_search",
    "family_ranking",
    "promotion_decision",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_authorization(
    authorization_path: Path = AUTH_PATH,
    contract_path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    if not authorization_path.is_file():
        raise RuntimeError(
            "Q218 independent-replication performance authorization is missing; "
            "preparation may be recorded, but performance execution is blocked."
        )
    auth = json.loads(authorization_path.read_text(encoding="utf-8"))
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    expected = {
        "record_type": "q218_independent_replication_performance_authorization",
        "candidate_id": "Q218",
        "source_trial_id": SOURCE_TRIAL_ID,
        "replication_trial_id": REPLICATION_TRIAL_ID,
        "trial_id": REPLICATION_TRIAL_ID,
        "status": "AUTHORIZED",
        "authorized": True,
        "performance_execution_authorized": True,
        "one_shot": True,
    }
    for key, value in expected.items():
        if auth.get(key) != value:
            raise RuntimeError(f"Q218 replication authorization mismatch: {key}")

    if contract.get("replication_trial_id") != REPLICATION_TRIAL_ID:
        raise RuntimeError("Q218 frozen replication contract trial mismatch")
    expected_contract_sha = sha256_file(contract_path)
    if auth.get("replication_contract_sha256") != expected_contract_sha:
        raise RuntimeError("Q218 replication authorization contract fingerprint mismatch")

    basis = auth.get("authorization_basis", {})
    if basis.get("requested_by_user") is not True:
        raise RuntimeError("Q218 replication authorization lacks explicit user authorization")
    ci_run = basis.get("master_exact_ci_run_id")
    if not isinstance(ci_run, int) or ci_run <= 0:
        raise RuntimeError("Q218 replication authorization lacks exact Master CI receipt")

    try:
        authorized_at = datetime.fromisoformat(
            str(auth.get("authorized_at_utc", "")).replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise RuntimeError("Q218 replication authorization timestamp invalid") from exc
    if authorized_at.tzinfo is None:
        raise RuntimeError("Q218 replication authorization timestamp must be timezone-aware")

    if any(auth.get(key) is not False for key in NO_SEARCH_FLAGS):
        raise RuntimeError("Q218 replication authorization opens a prohibited search/selection path")
    if auth.get("safety") != EXPECTED_SAFETY:
        raise RuntimeError("Q218 replication authorization safety boundary mismatch")

    return auth


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization", type=Path, default=AUTH_PATH)
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    args = parser.parse_args()
    auth = validate_authorization(args.authorization, args.contract)
    print(json.dumps({
        "status": "Q218_REPLICATION_PERFORMANCE_AUTHORIZED",
        "trial_id": auth["trial_id"],
        "authorization_id": auth["authorization_id"],
        "one_shot": True,
        "performance_execution_authorized": True,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
