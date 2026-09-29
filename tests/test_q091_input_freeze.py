import json
from pathlib import Path

from automation.q091_input_freeze import INPUT_ID, TARGET


def test_q091_input_bundle_contract_constants():
    assert INPUT_ID == "T-2026-09-29-091-INPUT-FREEZE"
    assert TARGET == 3500


def test_q091_persisted_input_receipt_is_non_performance_when_present():
    path = Path("research/evidence/q091_input_freeze_result.json")
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["trial_id"] == INPUT_ID
    assert data["status"] == "INPUT_BUNDLE_FROZEN"
    assert data["performance_evaluation"] is False
    assert data["selection_used"] is False
