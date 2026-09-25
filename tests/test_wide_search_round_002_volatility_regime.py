from automation.wide_search_round_002_volatility_regime import (
    MIN_EVENTS,
    SHOCK_RATIO,
    SUPPORT_THRESHOLD,
    _classify,
)


def test_round_002_rule_is_fixed_ex_ante():
    assert SHOCK_RATIO == 1.5
    assert SUPPORT_THRESHOLD == 1.10
    assert MIN_EVENTS == 50


def test_round_002_support_requires_both_research_halves():
    assert _classify([1.2] * 30 + [1.2] * 30) == "DISCOVERY_SUPPORT_RISK_REGIME"
    assert _classify([1.2] * 30 + [0.9] * 30) == "PRUNE_NO_RISK_REGIME_SUPPORT"


def test_round_002_prunes_low_event_count():
    assert _classify([1.2] * 49) == "PRUNE_TOO_FEW_EVENTS"
