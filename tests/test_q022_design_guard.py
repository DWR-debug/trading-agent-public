from copy import deepcopy
import json

from automation.q022_design_guard import (
    Q022DesignGuardError,
    design_fingerprint,
    validate_q022_design,
)

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    payload = json.loads((ROOT / "research/preregistrations/q022_treasury_failure_followup_design_2026_09_26.json").read_text(encoding="utf-8"))
    queue = json.loads((ROOT / "research/research_queue.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "research/evidence/trial_ledger.json").read_text(encoding="utf-8"))
    return payload, queue, ledger


def test_q022_design_guard_passes_current_contract():
    payload, queue, ledger = _load()
    fingerprint = validate_q022_design(payload, queue, ledger)
    assert len(fingerprint) == 64
    assert fingerprint == design_fingerprint(payload)


def test_q022_guard_rejects_ranked_design():
    payload, queue, ledger = _load()
    mutated = deepcopy(payload)
    mutated["ranked"] = True
    try:
        validate_q022_design(mutated, queue, ledger)
    except Q022DesignGuardError as exc:
        assert "unranked" in str(exc)
    else:
        raise AssertionError("ranked Q022 design was accepted")
