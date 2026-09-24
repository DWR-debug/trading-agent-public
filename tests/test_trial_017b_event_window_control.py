from datetime import date, datetime, timezone

from automation.trial_017b_event_window_control import _event_window_feature, run_trial
from data.gdelt_events import GDELTEvent
from research.event_intelligence import aggregate_daily_events


def event(day, quad=4, articles=3):
    return GDELTEvent(day, datetime(2025, 1, day, 12, tzinfo=timezone.utc), "190", "190", "19", quad, -3.0, 5, 2, articles, -1.0, "USA", "RUS", "", "")


def test_weekend_events_bundle_into_one_target_window():
    features = {f.event_date: f for f in aggregate_daily_events([event(3), event(4), event(5)], international_only=True, high_confidence_only=True)}
    result = _event_window_feature(features, date(2025, 1, 2), date(2025, 1, 6))
    assert result["high_confidence_international_count"] == 3
    assert result["international_conflict_flag"] is True


def test_empty_window_is_zero_signal():
    result = _event_window_feature({}, date(2025, 1, 2), date(2025, 1, 6))
    assert result["high_confidence_international_count"] == 0
    assert result["international_conflict_flag"] is False


def test_target_market_day_is_unique_and_uses_previous_close(tmp_path):
    def events(day):
        return [event(day.day)] if day.day in {4, 5} else []
    def market(symbol, start, end):
        return {
            date(2025, 1, 3): 100.0, date(2025, 1, 6): 102.0,
            date(2025, 1, 7): 104.0, date(2025, 1, 8): 105.0,
            date(2025, 1, 9): 106.0, date(2025, 1, 10): 107.0,
        }
    report = run_trial(date(2025, 1, 1), date(2025, 1, 8), event_loader=events, market_loader=market, assets=("SPY",), output_path=tmp_path / "report.json")
    targets = [row["target_market_day"] for row in report["observations"]]
    assert len(targets) == len(set(targets))
    monday = next(row for row in report["observations"] if row["target_market_day"] == "2025-01-06")
    assert monday["has_qualifying_event"] is True
    assert abs(monday["market"]["SPY"]["next_market_day_return"] - 0.02) < 1e-12