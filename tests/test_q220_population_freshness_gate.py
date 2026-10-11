from __future__ import annotations

import hashlib
import json
from pathlib import Path

from automation.q220_as_filed_xbrl_population_gate import (
    CONTRACT_PATH,
    ROOT,
    TARGET_ISSUERS,
    WINDOW_END,
    WINDOW_START,
)
from automation.q220_population_freshness_gate import (
    GATE_PATH,
    POSITIVE_STATUS,
    canonical_receipt_fingerprint,
    population_repair_decision,
    positive_receipt_is_current,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_positive_receipt() -> dict:
    receipt = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-06-Q220-AS-FILED-XBRL-POPULATION",
        "candidate_id": "Q220",
        "mode": "population",
        "status": POSITIVE_STATUS,
        "row_count": 55,
        "record_count": 55,
        "failure_count": 0,
        "gate_code_sha256": sha256(GATE_PATH),
        "contract_sha256": sha256(CONTRACT_PATH),
        "fixed_universe": dict(TARGET_ISSUERS),
        "window": {"start": WINDOW_START.isoformat(), "end": WINDOW_END.isoformat()},
        "interpretation": {
            "source_pit_structure_ready": True,
            "performance_evidence": False,
            "performance_authorized": False,
            "promotion_allowed": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    receipt["receipt_fingerprint"] = canonical_receipt_fingerprint(receipt)
    return receipt


def test_current_positive_q220_population_receipt_skips_expensive_rebuild(tmp_path):
    receipt = current_positive_receipt()

    assert positive_receipt_is_current(receipt)
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")

    assert population_repair_decision(path) == (False, "SKIP_CURRENT_POSITIVE_RECEIPT")


def test_q220_population_rebuilds_when_receipt_is_missing_or_unreadable(tmp_path):
    missing = tmp_path / "missing.json"
    assert population_repair_decision(missing) == (True, "RECEIPT_MISSING_OR_UNREADABLE")

    malformed = tmp_path / "malformed.json"
    malformed.write_text("{not-json", encoding="utf-8")
    assert population_repair_decision(malformed) == (True, "RECEIPT_MISSING_OR_UNREADABLE")


def test_q220_population_rebuilds_on_stale_code_or_contract_hash(tmp_path):
    receipt = current_positive_receipt()
    receipt["gate_code_sha256"] = "0" * 64
    receipt["receipt_fingerprint"] = canonical_receipt_fingerprint(receipt)
    path = tmp_path / "stale-code.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")

    assert not positive_receipt_is_current(receipt)
    assert population_repair_decision(path) == (
        True,
        "RECEIPT_MISSING_NEGATIVE_STALE_OR_INVALID",
    )

    receipt = current_positive_receipt()
    receipt["contract_sha256"] = "f" * 64
    receipt["receipt_fingerprint"] = canonical_receipt_fingerprint(receipt)
    path.write_text(json.dumps(receipt), encoding="utf-8")
    assert not positive_receipt_is_current(receipt)
    assert population_repair_decision(path) == (
        True,
        "RECEIPT_MISSING_NEGATIVE_STALE_OR_INVALID",
    )


def test_q220_population_rebuilds_if_receipt_content_was_mutated():
    receipt = current_positive_receipt()
    receipt["record_count"] = 54

    assert not positive_receipt_is_current(receipt)


def test_q220_population_rebuilds_for_negative_receipt_and_never_lifts_safety():
    receipt = current_positive_receipt()
    receipt["status"] = "Q220_AS_FILED_XBRL_POPULATION_BLOCKED"
    receipt["receipt_fingerprint"] = canonical_receipt_fingerprint(receipt)
    assert not positive_receipt_is_current(receipt)

    receipt = current_positive_receipt()
    receipt["safety"]["live_trading_enabled"] = True
    receipt["receipt_fingerprint"] = canonical_receipt_fingerprint(receipt)
    assert not positive_receipt_is_current(receipt)


def test_explicit_force_rebuild_overrides_a_current_positive_receipt(tmp_path):
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(current_positive_receipt()), encoding="utf-8")

    assert population_repair_decision(path, force_rebuild=True) == (
        True,
        "FORCE_REBUILD_REQUESTED",
    )


def test_q220_workflow_freshness_guard_preserves_route_probe_and_explicit_repair():
    workflow = (
        ROOT / ".github/workflows/q220-as-filed-xbrl-population.yml"
    ).read_text(encoding="utf-8")

    assert "force_rebuild:" in workflow
    assert "automation/q220_population_freshness_gate.py" in workflow
    assert "tests/test_q220_population_freshness_gate.py" in workflow
    assert "needs: [receipt_gate]" in workflow
    assert "needs.receipt_gate.outputs.run_population == 'true'" in workflow
    assert "Run bounded raw-archive route probe" in workflow
    assert "Run full bounded historical population" in workflow
    assert "cancel-in-progress: true" in workflow
