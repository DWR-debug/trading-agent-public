from datetime import date, datetime, timezone

from automation.trial_017_political_event_intelligence import (
    _event_forward_returns,
    run_trial,
)
from data.gdelt_events import GDELTEvent


def event(day, quad=4):
    return GDELTEvent(
        day,
        datetime(2025, 1, day, 12, tzinfo=timezone.utc),
        "190",
        "190",
        "19",
        quad,
        -3.0,
        5,
        2,
        3,
        -1.0,
        "USA",
        "RUS",
        "",
        "",
    )


def test_weekend_event_maps_to_next_market_day_without_same_day():
    closes = {
        date(2025, 1, 3): 100.0,
        date(2025, 1, 6): 104.0,
        date(2025, 1, 7): 105.0,
        date(2025, 1, 8): 106.0,
        date(2025, 1, 9): 107.0,
        date(2025, 1, 10): 108.0,
    }
    one, five = _event_forward_returns(closes, date(2025, 1, 4))
    assert abs(one - 0.04) < 1e-12
    assert abs(five - 0.08) < 1e-12


def test_market_day_event_excludes_same_day_return():
    closes = {
        date(2025, 1, 2): 100.0,
        date(2025, 1, 3): 101.0,
        date(2025, 1, 6): 103.0,
        date(2025, 1, 7): 104.0,
        date(2025, 1, 8): 105.0,
        date(2025, 1, 9): 106.0,
    }
    one, five = _event_forward_returns(closes, date(2025, 1, 3))
    assert abs(one - (103.0 / 101.0 - 1.0)) < 1e-12
    assert five is None


def test_trial_uses_international_event_filter_and_remains_paper_only(tmp_path):
    def events(day):
        return [event(day.day)] if day.day == 2 else []

    def market(symbol, start, end):
        return {
            date(2025, 1, 2): 100.0,
            date(2025, 1, 3): 102.0,
            date(2025, 1, 6): 104.0,
            date(2025, 1, 7): 105.0,
            date(2025, 1, 8): 106.0,
            date(2025, 1, 9): 107.0,
            date(2025, 1, 10): 108.0,
        }

    report = run_trial(
        date(2025, 1, 1),
        date(2025, 1, 7),
        event_loader=events,
        market_loader=market,
        assets=("SPY",),
        output_path=tmp_path / "report.json",
    )
    row = next(row for row in report["observations"] if row["event_day"] == "2025-01-02")
    assert abs(row["market"]["SPY"]["next_market_day_return"] - 0.02) < 1e-12
    assert report["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
    }
