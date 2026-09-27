from pathlib import Path

def test_t051_is_performance_free_and_future_mutation_based():
    spec=Path("research/preregistrations/trial_051_fixed_core_strategy_pit_2026_09_27.json").read_text(encoding="utf-8")
    assert '"performance_evaluation": false' in spec
    assert '"holdout_evaluation": false' in spec
    assert '"performance_trial_authorized": false' in spec
    assert '"future_close_mutation": true' in spec

def test_t051_validator_uses_existing_fixed_signal_implementations():
    text=Path("automation/strategy_pit_preflight.py").read_text(encoding="utf-8")
    assert "from automation.candidate_validation_50_50_vol_budget import _cs_weights" in text
    assert "from automation.cross_asset_trend_replication import _sma_signal" in text
    assert "future" in text
    assert "PIT_PASSED" in text
