from datetime import date

from automation.q119_treasury_demand_shape import compile_states, synthetic_contract

def test_q119_synthetic_contract():
    assert all(synthetic_contract().values())

def test_q119_wrong_order_fails_closed():
    row = {"auction_date":"2026-01-01","record_date":"2026-01-01","cusip":"BAD","security_type":"Note","security_term":"10-Year","high_yield":"4.00","median_yield":"4.10","low_yield":"4.20"}
    try:
        compile_states([row])
    except ValueError as exc:
        assert str(exc) == "Q119_YIELD_ORDER_INVALID"
    else:
        raise AssertionError("invalid demand-curve ordering must fail closed")

def test_q119_pit_date_order_fails_closed():
    row = {"auction_date":"2026-02-01","record_date":"2026-01-31","cusip":"BAD","security_type":"Note","security_term":"10-Year","high_yield":"4.20","median_yield":"4.10","low_yield":"4.00"}
    try:
        compile_states([row])
    except ValueError as exc:
        assert str(exc) == "Q119_PIT_DATE_ORDER"
    else:
        raise AssertionError("record-date before auction-date must fail closed")

def test_q119_future_record_excluded_by_cutoff():
    rows = [{"auction_date":"2026-01-01","record_date":"2026-01-01","cusip":"A","security_type":"Note","security_term":"10-Year","high_yield":"4.20","median_yield":"4.10","low_yield":"4.00"},{"auction_date":"2026-03-01","record_date":"2026-03-01","cusip":"FUTURE","security_type":"Note","security_term":"10-Year","high_yield":"5.00","median_yield":"4.90","low_yield":"4.80"}]
    assert len(compile_states(rows, cutoff=date(2026, 1, 31))) == 1
    assert compile_states(rows, cutoff=date(2026, 1, 31)) == compile_states(rows, cutoff=date(2026, 1, 31))
