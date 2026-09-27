from datetime import date

from automation import q025_treasury_auction_date_pit_feasibility as q025


def test_date_lag_rule_is_strict():
    assert (date(2025, 8, 15) - date(2025, 8, 6)).days == 9
    assert q025.MIN_LAG_DAYS == 1


def test_fingerprint_is_deterministic():
    assert q025._fp({"x": 1}) == q025._fp({"x": 1})
    assert len(q025._fp({"x": 1})) == 64
