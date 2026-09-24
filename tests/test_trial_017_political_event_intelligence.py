from datetime import date, datetime, timezone
from automation.trial_017_political_event_intelligence import run_trial
from data.gdelt_events import GDELTEvent

def event(day, quad):
    return GDELTEvent(day, datetime(2025, 1, day, 12, tzinfo=timezone.utc), "190", "190", "19", quad, -3.0, 5, 2, 2, -1.0, "USA", "RUS", "", "")

def test_next_market_day_is_used_and_output_is_paper_only(tmp_path):
    def events(day):
        return [event(day.day, 4)] if day.day == 2 else []
    def market(symbol, start, end):
        return {date(2025, 1, 2): 100.0, date(2025, 1, 3): 102.0, date(2025, 1, 6): 104.0, date(2025, 1, 7): 103.0}
    report = run_trial(date(2025, 1, 1), date(2025, 1, 7), event_loader=events, market_loader=market, assets=("SPY",), output_path=tmp_path / "report.json")
    row = next(row for row in report["observations"] if row["event_day"] == "2025-01-02")
    assert abs(row["market"]["SPY"]["next_day_return"] - 0.02) < 1e-12
    assert report["safety"] == {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False}
