from datetime import datetime, timezone
from data.gdelt_events import GDELTEvent
from research.event_intelligence import aggregate_daily_events, conflict_flag, event_importance

def event(day, quad, goldstein, mentions):
    return GDELTEvent(day * 10 + quad, datetime(2026, 9, day, 12, tzinfo=timezone.utc), "190", "190", "19", quad, goldstein, mentions, 2, 2, -1.0, "USA", "RUS", "", "")

def test_daily_aggregation():
    features = aggregate_daily_events([event(1, 3, -3.0, 4), event(1, 4, -5.0, 9), event(2, 2, 2.0, 2)])
    assert len(features) == 2
    assert features[0].material_conflict_count == 1
    assert features[0].verbal_conflict_count == 1
    assert conflict_flag(features[0]) is True
    assert event_importance(event(1, 4, -5.0, 9)) > 0
