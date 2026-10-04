from __future__ import annotations

from datetime import time

from automation.q121r6_sec_acceptance_time_compiler import (
    DISSEMINATION_CUTOFF,
    R5_ROW_COUNT,
    R5_ROW_MULTICHET,
    STANDARD_CUTOFF,
    classify_acceptance,
    key_fingerprint,
    r5_population_fingerprint,
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


def test_r6_reuses_exact_r5_multiset_fingerprint_definition() -> None:
    rows = [
        {"cik":"0000000001","form":"SC 13G","filed_date":"2024-02-05","accession_number":"0000000001-24-000001","filename":"edgar/data/1/000000000124000001/a.txt"},
        {"cik":"0000000002","form":"SC 13D","filed_date":"2024-02-06","accession_number":"0000000002-24-000002","filename":"edgar/data/2/000000000224000002/b.txt"},
    ]
    first = r5_population_fingerprint(rows)
    second = r5_population_fingerprint(list(reversed(rows)))
    assert first == second


def test_q121r6_workflow_uses_fleet_rate_budget() -> None:
    from pathlib import Path

    workflow = (
        Path(__file__).parents[1]
        / ".github"
        / "workflows"
        / "q121r6-sec-acceptance-time-compilation.yml"
    ).read_text(encoding="utf-8")
    assert "max-parallel: 2" in workflow
    assert "shard_index: [0,1,2,3]" in workflow
    assert "--shard-count 4" in workflow
    assert "--request-gap-seconds 0.25" in workflow


def test_q121r6_aggregate_uses_same_shard_count() -> None:
    from automation.q121r6_sec_acceptance_time_aggregate import SHARD_COUNT

    assert SHARD_COUNT == 4


def test_r6_uses_canonical_r3_accession_parser():
    from automation import q121r3_sec_form_index_reverse_issuer as r3
    from automation import q121r6_sec_acceptance_time_compiler as r6
    filename = "edgar/data/1/000000000124000001/a.txt"
    assert r3.accession_from_filename(filename) == "0000000001-24-000001"
    source = __import__("pathlib").Path(r6.__file__).read_text(encoding="utf-8")
    assert "r3.accession_from_filename(filename)" in source


def test_q121r6_archive_url_uses_subject_cik_from_form_index_path():
    from automation.q121r6_sec_acceptance_time_compiler import archive_header_url
    filename = "edgar/data/1007587/000110465924093411/0001104659-24-093411-index.htm"
    assert archive_header_url(filename) == (
        "https://www.sec.gov/Archives/edgar/data/1007587/000110465924093411/"
        "0001104659-24-093411-index-headers.html"
    )

def test_q121r6_problem_404_filename_preserves_subject_cik_root():
    from automation.q121r6_sec_acceptance_time_compiler import archive_header_url
    filename = "edgar/data/1007587/000110465924093411/0001104659-24-093411-index.htm"
    url = archive_header_url(filename)
    assert "/data/1007587/000110465924093411/" in url
    assert "/data/1104659/000110465924093411/" not in url


def test_q121r6_subject_and_filer_cik_are_distinct():
    source = __import__("pathlib").Path(
        __import__("automation.q121r6_sec_acceptance_time_compiler", fromlist=["__name__"]).__file__
    ).read_text(encoding="utf-8")
    assert "INDEX_SUBJECT_CIK_MISMATCH" in source
    assert "filer_cik = accession_dashed.split" in source


def test_q121r6_404_failure_payload_includes_source_url():
    from pathlib import Path
    source = Path(__import__("automation.q121r6_sec_acceptance_time_compiler", fromlist=["__name__"]).__file__).read_text(encoding="utf-8")
    assert '"source_url": archive_header_url(row["filename"])' in source
    assert "Q121R6_DEBUG_404" in source

