from automation.research_worker import build_output
from automation.research_workflow import result_fingerprint, verify_result_fingerprint


def test_legacy_worker_output_is_non_authoritative_and_fingerprinted():
    result = {
        "safety": {"paper_only": True, "live_trading_enabled": False},
        "protocol": {},
        "symbol": "TEST",
        "interval": "1h",
        "candle_count": 10,
        "research_candle_count": 9,
        "holdout_candle_count": 1,
        "data_start": "2026-01-01T00:00:00+00:00",
        "research_end": "2026-01-01T08:00:00+00:00",
        "holdout_start": "2026-01-01T09:00:00+00:00",
        "data_end": "2026-01-01T09:00:00+00:00",
        "dataset_fingerprint": "data",
        "research_dataset_fingerprint": "research",
        "holdout_dataset_fingerprint": "holdout",
        "baseline": {},
        "walk_forward": {},
        "rolling_walk_forward": {},
        "holdout": {"trade_count": 0},
        "optimization": [],
    }
    gates = {"status": "BLOCKED", "failed_gates": ["backtest"], "gate_count": 7}
    manifest = {
        "identity_version": 3,
        "code_version": "abc123",
        "datasets": [],
        "protocol": {},
        "parameter_space": {},
        "execution_config": {},
        "settings": {},
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False},
        "run_fingerprint": "run-abc",
    }

    output = build_output(result, gates, manifest)

    assert output["research_type"] == "legacy_local_diagnostic"
    assert output["authoritative"] is False
    assert output["result_fingerprint"] == result_fingerprint(output)
    verify_result_fingerprint(output)