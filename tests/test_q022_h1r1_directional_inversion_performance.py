import json
from pathlib import Path

from automation.q022_h1r1_directional_inversion_performance import TRIAL_ID, SYMBOLS
from config import settings

ROOT = Path(__file__).resolve().parents[1]


def test_t047r1_preregistration_and_authorization_are_exactly_bound() -> None:
    prereg = json.loads(
        (ROOT / "research" / "preregistrations" / "q022_h1r1_directional_inversion_performance_2026_09_26.json").read_text()
    )
    auth = json.loads(
        (ROOT / "research" / "authorizations" / "q022_h1r1_directional_inversion_performance_2026_09_26.json").read_text()
    )
    assert TRIAL_ID == "T-2026-09-26-047R1-PERFORMANCE"
    assert tuple(SYMBOLS) == tuple(prereg["symbols"])
    assert prereg["trial_id"] == TRIAL_ID
    assert prereg["data_contract"]["requested_raw_candles_per_symbol"] == 4000
    assert prereg["data_contract"]["target_common_calendar"] == 3500
    assert prereg["authorization"]["performance_trial_authorized"] is False
    assert auth["authorized"] is True
    assert auth["performance_execution_authorized"] is True
    assert auth["execution_scope"] == "PERFORMANCE"
    assert auth["coverage_workflow_run_id"] == 36262630438
    assert auth["coverage_artifact_id"] == 10912259838
    assert auth["snapshot_fingerprint"] == "1e158aa8807ee48a08686191cf23abff258f8313b8df67c78bb0aeefbb09b315"
    assert auth["source_contract_fingerprint"] == "13072dbed7d60684f4a4fb8a3de69555cae83c66f3cfdfb603b9ed2a4b1c225b"
    assert auth["signal_events_fingerprint"] == "8af45e4eb7267266da10eb28cf5287eea1ff3572f38736382f1b004abf86c208"
    assert settings.PAPER_ONLY is True
    assert settings.LIVE_TRADING_ENABLED is False
    assert settings.ORDERS_ENABLED is False
