from __future__ import annotations

import hashlib
import json
from pathlib import Path

from automation import q077r1_performance as runner
from automation import q077r1_reconcile as reconcile

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "research" / "preregistrations" / "q077r1_performance_2026_09_30.json"


def test_q077r1_runner_identity_and_frozen_scope() -> None:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    assert prereg["trial_id"] == "T-2026-09-30-077R1-PERFORMANCE"
    assert prereg["status"] == "PREREGISTERED_PERFORMANCE"
    assert runner.TRIAL_ID == prereg["trial_id"]
    assert runner.Q077R1_SYMBOLS == tuple(prereg["symbols"])
    assert runner.N == prereg["target_common_candles"] == 3500
    assert runner.RESEARCH == 2798
    assert runner.HOLDOUT == 700
    assert prereg["governance"]["performance_trial_authorized"] is False
    assert all(
        value is False
        for key, value in prereg["governance"].items()
        if key != "performance_trial_authorized"
    )
    assert prereg["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }


def test_q077r1_source_contract_matches_runtime_code() -> None:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    paths = {
        "performance_runner_sha256": ROOT / "automation" / "q077r1_performance.py",
        "alpha_mechanism_sha256": ROOT / "automation" / "q067_alpha_mechanisms.py",
        "cost_contract_sha256": ROOT / "execution" / "cost_contract.py",
        "settings_sha256": ROOT / "config" / "settings.py",
        "input_freeze_sha256": ROOT / "automation" / "q077r1_input_freeze.py",
    }
    for key, path in paths.items():
        assert prereg["source_contract"][key]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == prereg["source_contract"][key]


def test_q077r1_reconciliation_identity_is_dedicated() -> None:
    assert reconcile.TRIAL_ID == "T-2026-09-30-077R1-PERFORMANCE"
    assert reconcile.RESULT_PATH == "research/evidence/q077r1_performance_result.json"
    assert reconcile.AUTH_PATH == "research/authorizations/q077r1_performance_2026_09_30.json"
    assert reconcile.PREREG_PATH == "research/preregistrations/q077r1_performance_2026_09_30.json"


def test_q077r1_runner_contains_no_inherited_q079_identifiers() -> None:
    source = (ROOT / "automation" / "q077r1_performance.py").read_text(encoding="utf-8")
    assert "Q079" not in source
    assert "q079" not in source
    assert "T-2026-09-28-079" not in source
