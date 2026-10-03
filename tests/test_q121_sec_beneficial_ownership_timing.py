from datetime import datetime, date, timezone
from automation.q121_sec_beneficial_ownership_timing import classify_event, compile_events


def row(acc="A1", acc_dt="2024-06-03T16:00:00Z", filing_date="2024-06-03"):
    return {
        "form":"SC 13G",
        "acceptanceDateTime":acc_dt,
        "filingDate":filing_date,
        "accessionNumber":acc,
    }


def test_boundary_classification():
    assert classify_event(row(acc_dt="2024-06-03T21:29:59Z"))["state"] == "STANDARD_DAY"
    assert classify_event(row(acc_dt="2024-06-03T21:30:00Z"))["state"] == "LATE_DAY_SAME_DATE"
    assert classify_event(row(acc_dt="2024-06-03T23:00:00Z"))["state"] == "LATE_DAY_SAME_DATE"


def test_acceptance_date_is_pit_clock_and_filing_date_difference_is_observable():
    out = classify_event(row(acc_dt="2024-06-03T20:00:00Z", filing_date="2024-06-04"))
    assert out["acceptance_date_et"] == "2024-06-03"
    assert out["filing_date"] == "2024-06-04"
    assert out["filing_date_alignment"] == "FILING_DATE_DIFFERS_FROM_ACCEPTANCE_DATE"
    assert out["state"] == "STANDARD_DAY"


def test_future_rows_do_not_change_prior_output():
    base=compile_events([row(acc="A1", acc_dt="2024-06-03T16:00:00Z")], date(2024,6,10))
    future=row(acc="FUT", acc_dt="2025-12-01T18:00:00Z", filing_date="2025-12-01")
    future_out=compile_events([row(acc="A1", acc_dt="2024-06-03T16:00:00Z"), future], date(2024,6,10))
    assert base == future_out


def test_input_order_invariance():
    rows=[row(acc="A1",acc_dt="2024-06-03T16:00:00Z"),row(acc="A2",acc_dt="2024-06-04T18:00:00Z",filing_date="2024-06-04")]
    a=compile_events(rows,date(2024,6,10))
    b=compile_events(list(reversed(rows)),date(2024,6,10))
    assert a == b


def test_amendment_accessions_are_retained():
    rows=[row(acc="A1"),row(acc="A1-AM",acc_dt="2024-06-03T18:00:00Z")]
    out=compile_events(rows,date(2024,6,10))
    assert out["event_count"] == 2
