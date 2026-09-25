from automation.wide_search_round_002_volatility_regime import (
    MIN_EVENTS,
    RESEARCH_CANDLES,
    SHOCK_RATIO,
    SUPPORT_THRESHOLD,
    _classify,
    _classify_temporal_events,
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

def test_round_002_temporal_split_uses_calendar_midpoint_not_event_count():
    midpoint = RESEARCH_CANDLES // 2
    events = (
        [{"event_index": 10, "forward_to_baseline_ratio": 1.2}] * 55
        + [{"event_index": midpoint + 10, "forward_to_baseline_ratio": 0.9}] * 5
    )
    assert _classify_temporal_events(events) == "PRUNE_NO_RISK_REGIME_SUPPORT"

    events = (
        [{"event_index": 10, "forward_to_baseline_ratio": 1.2}] * 5
        + [{"event_index": midpoint + 10, "forward_to_baseline_ratio": 0.9}] * 55
    )
    assert _classify_temporal_events(events) == "PRUNE_NO_RISK_REGIME_SUPPORT"
