from datetime import date
from pathlib import Path

from automation import q026_h2_treasury_auction_date_shift_performance as q026


def test_q026_universe_is_fixed():
    assert q026.UNIVERSE == "validation_2026_09_27_treasury_auction_date_shift_h2"
    assert len(q026.SYMBOLS) == 12
    assert len(set(q026.SYMBOLS)) == 12


def test_q026_mapping_uses_auction_date_not_record_date():
    rows = [{
        "record_date": "2025-08-15",
        "security_type": "Note",
        "security_term": "10-Year",
        "auction_date": "2025-08-06",
        "cusip": "91282CNT4",
        "bid_to_cover_ratio": "2.35",
    }]
    events, _, _ = q026._signal_events(rows, [
        date(2025, 8, 5),
        date(2025, 8, 7),
        date(2025, 8, 8),
    ])
    assert events[0]["next_eligible_common_trading_date"] == "2025-08-07"


def test_q026_authorization_is_fail_closed():
    path = Path(
        "research/authorizations/"
        "q026_h2_treasury_auction_date_shift_performance_2026_09_27.json"
    )
    text = path.read_text(encoding="utf-8")
    assert '"performance_execution_authorized": false' in text
    assert '"execution_scope": "DESIGN_ONLY"' in text
