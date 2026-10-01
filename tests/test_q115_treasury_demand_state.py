from automation.q115_treasury_demand_state import compile_states, synthetic_contract

def test_q115_synthetic_contract():
    assert all(synthetic_contract().values())

def test_q115_wrong_tenor_fails():
    rows=[{"auction_date":"2026-01-01","record_date":"2026-01-01","cusip":"A","security_type":"Bond","security_term":"10-Year","bid_to_cover_ratio":"2.5"}]
    try:
        compile_states(rows)
    except ValueError as exc:
        assert str(exc) == "Q115_UNEXPECTED_SECURITY"
    else:
        raise AssertionError("wrong tenor/type must fail")
