from automation.q117_treasury_demand_population import validate

def test_q117_population_contract():
    rows=[
      {"auction_date":"2026-01-01","record_date":"2026-01-01","cusip":"A","security_type":"Note","security_term":"10-Year","bid_to_cover_ratio":"2.5"},
      {"auction_date":"2026-02-01","record_date":"2026-02-01","cusip":"B","security_type":"Note","security_term":"10-Year","bid_to_cover_ratio":"2.7"}]
    out=validate(rows)
    assert out["raw_events"]==2
    assert out["state_counts"]["IMPROVED"]==1
