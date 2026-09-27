from datetime import date
from automation.q022_h2_treasury_release_timing_performance import _positions, _signal_events

def test_h2_r1_maps_after_auction_date_not_record_date():
    rows=[
      {"record_date":"2021-01-08","auction_date":"2021-01-07","security_type":"Note","security_term":"10-Year","cusip":"X1","bid_to_cover_ratio":"2.10"},
      {"record_date":"2021-01-19","auction_date":"2021-01-14","security_type":"Note","security_term":"10-Year","cusip":"X2","bid_to_cover_ratio":"2.20"},
    ]
    dates=[date(2021,1,7),date(2021,1,8),date(2021,1,11),date(2021,1,14),date(2021,1,15),date(2021,1,19),date(2021,1,20)]
    events,_=_signal_events(rows,dates)
    assert events[0]["next_eligible_common_trading_date"]=="2021-01-08"
    assert events[1]["next_eligible_common_trading_date"]=="2021-01-15"
    positions=_positions(events)
    assert date(2021,1,8) not in positions
    assert positions[date(2021,1,15)]==1
    assert date(2021,1,20) not in positions
