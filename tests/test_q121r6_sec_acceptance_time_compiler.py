from __future__ import annotations

from datetime import time

from automation.q121r6_sec_acceptance_time_compiler import (
    DISSEMINATION_CUTOFF,
    R5_ROW_COUNT,
    R5_ROW_MULTICHET,
    STANDARD_CUTOFF,
    classify_acceptance,
    key_fingerprint,
)


def test_acceptance_boundaries_are_exact() -> None:
    before = classify_acceptance("2024-02-05", "2024-02-05 17:29:59")
    at_standard = classify_acceptance("2024-02-05", "2024-02-05 17:30:00")
    at_close = classify_acceptance("2024-02-05", "2024-02-05 22:00:00")
    after_close = classify_acceptance("2024-02-05", "2024-02-05 22:00:01")

    assert before["event_class"] == "STANDARD_DAY"
    assert at_standard["event_class"] == "LATE_DAY_SAME_DATE"
    assert at_close["event_class"] == "LATE_DAY_SAME_DATE"
    assert after_close["event_class"] == "OUT_OF_CONTRACT"


def test_filing_date_mismatch_is_fail_closed() -> None:
    result = classify_acceptance("2024-02-06", "2024-02-05 18:00:00")
    assert result["filing_date_matches_acceptance_date"] is False
    assert result["event_class"] == "OUT_OF_CONTRACT"


def test_timezone_is_explicit_and_cutoffs_are_fixed() -> None:
    result = classify_acceptance("2024-07-01", "2024-07-01 17:30:00")
    assert result["timezone"] == "America/New_York"
    assert result["event_class"] == "LATE_DAY_SAME_DATE"
    assert STANDARD_CUTOFF == time(17, 30)
    assert DISSEMINATION_CUTOFF == time(22, 0)


def test_r5_population_anchor_is_frozen() -> None:
    assert R5_ROW_COUNT == 61818
    assert len(R5_ROW_MULTICHET) == 64


def test_key_fingerprint_is_order_sensitive_for_partition_inputs() -> None:
    rows = [
        {"cik":"0000000001","form":"SC 13G","filed_date":"2024-02-05","accession_number":"0000000001-24-000001"},
        {"cik":"0000000002","form":"SC 13D","filed_date":"2024-02-06","accession_number":"0000000002-24-000002"},
    ]
    assert key_fingerprint(rows) != key_fingerprint(list(reversed(rows)))
