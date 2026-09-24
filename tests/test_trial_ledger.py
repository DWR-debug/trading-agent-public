import pytest

from research.trial_ledger import (
    TrialLedgerError,
    compute_pbo_from_cscv,
    statistical_readiness,
    validate_ledger,
    validate_trial,
)


def _trial(**overrides):
    record = {
        "trial_id": "T-001",
        "recorded_at": "2026-09-24T10:00:00+02:00",
        "status": "archived_diagnostic",
        "research_family": "signal_diagnostics",
        "hypothesis": {"text": "diagnostic only"},
        "data_scope": {
            "research_count": 2798,
            "holdout_count": 700,
            "holdout_used_for_selection": False,
            "artifact_ids": [10751817990],
        },
        "search_scope": {
            "raw_trial_count": None,
            "independent_trial_count": None,
            "parameter_search": False,
            "threshold_search": False,
            "variant_search": False,
        },
        "selection": {
            "selected": False,
            "selection_method": "none",
            "selection_family_id": "diagnostic/signal",
            "selection_metric": None,
        },
        "statistical_evidence": {
            "psr_probability": None,
            "dsr_probability": None,
            "pbo_probability": None,
            "trial_sharpes": None,
            "independent_trial_count": None,
            "ready": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }
    record.update(overrides)
    return record


def test_trial_contract_accepts_missing_statistical_inputs_explicitly():
    validate_trial(_trial())


def test_trial_contract_rejects_selection_without_family():
    record = _trial()
    del record["selection"]["selection_family_id"]
    with pytest.raises(TrialLedgerError):
        validate_trial(record)


def test_ledger_rejects_duplicate_trial_ids():
    a = _trial()
    b = _trial()
    b["trial_id"] = "T-002"
    ledger = {"schema_version": 1, "trials": [a, b]}
    validate_ledger(ledger)
    b["trial_id"] = "T-001"
    with pytest.raises(TrialLedgerError):
        validate_ledger({"schema_version": 1, "trials": [a, b]})


def test_pbo_identifies_repeated_is_winner_oos_bottom_half():
    splits = [
        {"is_sharpes": [2.0, 1.0, 0.5], "oos_sharpes": [-1.0, 0.2, 0.4]},
        {"is_sharpes": [1.5, 1.0, 0.5], "oos_sharpes": [-0.4, 0.3, 0.5]},
        {"is_sharpes": [1.1, 0.9, 0.2], "oos_sharpes": [-0.2, 0.1, 0.3]},
    ]
    result = compute_pbo_from_cscv(splits)
    assert result.split_count == 3
    assert result.probability == 1.0
    assert result.overfit_count == 3
    assert result.logit_median < 0.0


def test_pbo_identifies_repeated_is_winner_oos_top_half():
    splits = [
        {"is_sharpes": [2.0, 1.0, 0.5], "oos_sharpes": [0.5, 0.2, -0.1]},
        {"is_sharpes": [1.5, 1.0, 0.5], "oos_sharpes": [0.4, 0.3, -0.2]},
        {"is_sharpes": [1.1, 0.9, 0.2], "oos_sharpes": [0.3, 0.1, -0.2]},
    ]
    result = compute_pbo_from_cscv(splits)
    assert result.probability == 0.0
    assert result.overfit_count == 0
    assert result.logit_median > 0.0


def test_readiness_is_false_without_explicit_trial_family():
    assert statistical_readiness(
        trial_sharpes=None,
        independent_trial_count=None,
        pbo_probability=None,
    )["ready"] is False


def test_readiness_is_true_when_dsr_inputs_exist():
    assert statistical_readiness(
        trial_sharpes=[0.1, 0.2, 0.3],
        independent_trial_count=3,
        pbo_probability=None,
    )["ready"] is True
