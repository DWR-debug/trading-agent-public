from datetime import date

import pytest

from research.turn_of_month_alpha import TurnOfMonthAlphaError, TurnOfMonthPolicy


def calendar():
    return (
        date(2025, 1, 29),
        date(2025, 1, 30),
        date(2025, 1, 31),
        date(2025, 2, 3),
        date(2025, 2, 4),
        date(2025, 2, 5),
        date(2025, 2, 6),
        date(2025, 2, 7),
        date(2025, 2, 28),
        date(2025, 3, 3),
        date(2025, 3, 4),
        date(2025, 3, 5),
    )


def test_policy_is_fixed_eight_asset_one_x_long():
    policy = TurnOfMonthPolicy()
    weights = policy.weights_for_day(date(2025, 2, 4), calendar())
    assert len(weights) == 8
    assert sum(weights.values()) == pytest.approx(1.0)


def test_four_day_turn_of_month_window():
    days = calendar()
    policy = TurnOfMonthPolicy()
    assert not policy.is_active(date(2025, 1, 29), days)
    assert policy.is_active(date(2025, 1, 31), days)
    assert policy.is_active(date(2025, 2, 3), days)
    assert policy.is_active(date(2025, 2, 4), days)
    assert policy.is_active(date(2025, 2, 5), days)
    assert not policy.is_active(date(2025, 2, 6), days)
    assert policy.is_active(date(2025, 2, 28), days)
    assert policy.is_active(date(2025, 3, 3), days)
    assert policy.is_active(date(2025, 3, 4), days)
    assert policy.is_active(date(2025, 3, 5), days)


def test_unknown_day_is_rejected():
    with pytest.raises(TurnOfMonthAlphaError):
        TurnOfMonthPolicy().is_active(date(2025, 1, 28), calendar())
