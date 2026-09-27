
from automation.q041_alpha_multiarm_performance import _a1_signal, _pf, _summary, SYMBOLS


def test_a1_consensus_is_fixed():
    closes = [100.0 + i for i in range(400)]
    assert _a1_signal(closes, 300) == 1
    assert _a1_signal(closes, 100) == 0


def test_summary_has_fixed_research_holdout_split():
    values = [0.001] * 3498
    summary = _summary(values)
    assert summary["research"]["day_count"] == 2798
    assert summary["holdout"]["day_count"] == 700
    assert summary["holdout"]["period_return"] > 0


def test_symbol_universe_is_exact_and_fixed():
    assert SYMBOLS == ("IVE", "IWL", "DLN", "DHS", "DON", "DES", "USRT", "ITB")


def test_profit_factor_parser():
    assert _pf("inf") == float("inf")
    assert _pf(1.25) == 1.25
