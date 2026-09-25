from datetime import date, datetime, timezone

from config import settings
from data.gdelt_events import GDELTEvent
from automation.information_alpha_discovery import (
    FIXED_FEATURES,
    _daily_event_features,
    _window_features,
    run_discovery,
)


def event(
    day: int,
    *,
    goldstein: float,
    mentions: int,
    sources: int = 2,
    articles: int = 3,
    left: str = "USA",
    right: str = "RUS",
) -> GDELTEvent:
    return GDELTEvent(
        event_id=day,
        date_added=datetime(2026, 8, day, 12, tzinfo=timezone.utc),
        event_code="190",
        event_base_code="190",
        event_root_code="19",
        quad_class=4,
        goldstein_scale=goldstein,
        num_mentions=mentions,
        num_sources=sources,
        num_articles=articles,
        avg_tone=-1.0,
        actor1_country_code=left,
        actor2_country_code=right,
        actor_geo_country_code="",
        source_url="",
    )


def test_q011_event_features_use_fixed_high_confidence_international_filter():
    daily = _daily_event_features(
        [
            event(1, goldstein=-4.0, mentions=9),
            event(1, goldstein=2.0, mentions=4, articles=2),
            event(1, goldstein=-3.0, mentions=5, left="USA", right="USA"),
        ]
    )
    assert set(daily) == {date(2026, 8, 1)}
    assert daily[date(2026, 8, 1)]["event_count"] == 1
    assert daily[date(2026, 8, 1)]["source_breadth"] == 2.0
    assert daily[date(2026, 8, 1)]["article_count"] == 3.0
    assert daily[date(2026, 8, 1)]["negative_goldstein"] == 4.0


def test_q011_window_contract_excludes_boundary_days():
    daily = {
        date(2026, 8, 1): {feature: 1.0 for feature in FIXED_FEATURES},
        date(2026, 8, 2): {feature: 2.0 for feature in FIXED_FEATURES},
        date(2026, 8, 3): {feature: 3.0 for feature in FIXED_FEATURES},
    }
    values = _window_features(daily, date(2026, 8, 1), date(2026, 8, 3))
    assert values["event_count"] == 2.0
    assert values["attention_score"] == 2.0
    assert values["mean_tone"] == 2.0


def test_q011_discovery_is_holdout_free_and_paper_only(tmp_path):
    assets = ("AAA",)
    prices = {
        "AAA": {
            date(2026, 8, 24): 100.0,
            date(2026, 8, 25): 101.0,
            date(2026, 8, 26): 102.0,
            date(2026, 8, 27): 101.0,
            date(2026, 8, 28): 103.0,
            date(2026, 8, 31): 104.0,
            date(2026, 9, 1): 105.0,
            date(2026, 9, 2): 106.0,
            date(2026, 9, 3): 105.0,
            date(2026, 9, 4): 107.0,
            date(2026, 9, 7): 108.0,
            date(2026, 9, 8): 109.0,
        }
    }

    def market_loader(symbol, start, end):
        return prices[symbol]

    def event_loader(day):
        if day == date(2026, 8, 26):
            return [event(26, goldstein=-4.0, mentions=9)]
        return []

    report = run_discovery(
        date(2026, 8, 24),
        date(2026, 9, 8),
        event_loader=event_loader,
        market_loader=market_loader,
        assets=assets,
        output_path=tmp_path / "q011.json",
    )
    assert report["status"] == "DISCOVERY_ONLY"
    assert report["holdout_used"] is False
    assert report["selection_used"] is False
    assert report["parameter_search_used"] is False
    assert report["paper_only"] is True
    assert report["live_trading_enabled"] is False
    assert report["orders_enabled"] is False
    assert len(report["observations"]) == 11
    assert report["observations"][1]["event_window_start_exclusive"] == "2026-08-25"
    assert report["observations"][1]["event_window_end_exclusive"] == "2026-08-26"
    assert settings.PAPER_ONLY is True
    assert settings.LIVE_TRADING_ENABLED is False
