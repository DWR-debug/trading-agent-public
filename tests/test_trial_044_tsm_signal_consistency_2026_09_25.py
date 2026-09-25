
from automation.trial_044_tsm_signal_consistency_2026_09_25 import (
    TSM_LOOKBACKS, _gates, _tsm_long_flat_signal
)
from validation.research_gates import ResearchGateConfig


def test_tsm_warmup_is_flat():
    closes = [100.0] * max(TSM_LOOKBACKS)
    assert _tsm_long_flat_signal(closes, len(closes) - 1) == 0


def test_tsm_unanimous_positive_is_long():
    n = max(TSM_LOOKBACKS) + 1
    closes = [100.0] * n
    for lb in TSM_LOOKBACKS:
        closes[n - 1 - lb] = 90.0
    closes[-1] = 110.0
    assert _tsm_long_flat_signal(closes, n - 1) == 1


def test_tsm_disagreement_is_flat():
    n = max(TSM_LOOKBACKS) + 1
    closes = [100.0] * n
    closes[n - 1 - TSM_LOOKBACKS[0]] = 90.0
    closes[n - 1 - TSM_LOOKBACKS[1]] = 90.0
    closes[n - 1 - TSM_LOOKBACKS[2]] = 110.0
    assert _tsm_long_flat_signal(closes, n - 1) == 0


def _mode(r=.2, dd=5.0, pf=1.2, rpf=1.2, ratio=.6, rdd=5.0, oos=.5, h=.1, hdd=5.0, hpf=1.2):
    return {
        "research": {"period_return": r, "max_drawdown_percent": dd, "profit_factor": pf},
        "rolling_summary": {
            "overall_profit_factor": rpf,
            "profitable_window_ratio": ratio,
            "average_drawdown_percent": rdd,
        },
        "oos_to_is_return_ratio": oos,
        "holdout": {"period_return": h, "max_drawdown_percent": hdd, "profit_factor": hpf},
    }


def _scenario():
    m = _mode()
    wrapped = {"price_only": m, "total_return_sensitivity": m}
    return {
        "base": {"fixed_candidate": wrapped, "tsm_ensemble_candidate": wrapped},
        "stress_1_5x_cost": {"fixed_candidate": wrapped, "tsm_ensemble_candidate": wrapped},
        "stress_2x_cost": {"fixed_candidate": wrapped, "tsm_ensemble_candidate": wrapped},
    }


def test_gate_contract_passes_for_equal_strong_candidate():
    r = _gates(_scenario(), ResearchGateConfig())
    assert r["all_absolute_passed"]
    assert r["all_non_worsening_passed"]
    assert r["all_checks_passed"]


def test_gate_contract_blocks_deterioration_vs_fixed():
    s = _scenario()
    s["base"]["tsm_ensemble_candidate"] = {
        "price_only": _mode(r=.1),
        "total_return_sensitivity": _mode(r=.1),
    }
    r = _gates(s, ResearchGateConfig())
    assert not r["non_worsening_vs_fixed_candidate"]["research_return_not_below_fixed"]
    assert not r["all_checks_passed"]


def test_tsm_lookback_definition_is_fixed():
    assert TSM_LOOKBACKS == (63, 126, 252)
