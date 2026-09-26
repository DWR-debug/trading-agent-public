from automation.q022_h1_directional_inversion_performance import _positions


def test_q022_h1_inverts_only_nonzero_source_direction() -> None:
    events = [
        {"signal": 1, "next_eligible_common_trading_date": "2025-01-02"},
        {"signal": -1, "next_eligible_common_trading_date": "2025-01-03"},
        {"signal": 0, "next_eligible_common_trading_date": "2025-01-04"},
        {"signal": None, "next_eligible_common_trading_date": "2025-01-05"},
    ]
    assert _positions(events) == {
        __import__("datetime").date(2025, 1, 2): -1,
        __import__("datetime").date(2025, 1, 3): 1,
    }


def test_q022_h1_overlapping_events_aggregate_before_inversion() -> None:
    events = [
        {"signal": 1, "next_eligible_common_trading_date": "2025-01-02"},
        {"signal": 1, "next_eligible_common_trading_date": "2025-01-02"},
        {"signal": -1, "next_eligible_common_trading_date": "2025-01-03"},
    ]
    assert _positions(events) == {
        __import__("datetime").date(2025, 1, 2): -1,
        __import__("datetime").date(2025, 1, 3): 1,
    }
