from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

import pytest

from automation import q220_primary_source_vintage_forensics as forensic


ROOT = Path(__file__).resolve().parents[1]


def make_pds_control_block(
    accession: str,
    form: str,
    receipt_date: str,
    acceptance_date: str,
    acceptance_time: str,
) -> bytes:
    """Build a spec-shaped PDS control block for deterministic parser tests."""
    block = (
        accession.encode("ascii").ljust(20, b" ")
        + form.encode("ascii").ljust(10, b" ")
        + b"EXAMPLE COMPANY".ljust(60, b" ")
        + b"".ljust(60, b" ")
        + receipt_date.encode("ascii")
        + acceptance_date.encode("ascii")
        + acceptance_time.encode("ascii")
        + b"000000"
        + b"      "
        + b"4"
        + b"1"
        + b"1"
        + b"    "
        + b" " * 65
    )
    assert len(block) == 256
    return block + b"<SUBMISSION>\\n"


def test_frozen_q220_request_matches_exact_current_blocked_receipt():
    request, receipt = forensic.validate_frozen_source(
        ROOT / "research/run_requests/q220_primary_source_vintage_forensics.trigger",
        ROOT / forensic.SOURCE_RECEIPT_PATH,
    )
    assert request["SAMPLE_COUNT"] == "3"
    assert receipt["receipt_fingerprint"] == forensic.SOURCE_RECEIPT_FINGERPRINT
    assert receipt["source_hash_failure_count"] == 55
    assert receipt["gate_positive"] is False
    assert request["SAMPLE_RECORD_KEYS"].split(";") == list(forensic.SAMPLE_KEYS)



def test_parse_pds_control_block_reads_fixed_width_acceptance_clock():
    accession = "0000064040-25-000052"
    payload = make_pds_control_block(
        accession, "10-K", "20250211", "20250211", "170704"
    )
    parsed = forensic.parse_pds_control_block(payload)

    assert parsed["status"] == "PDS_CONTROL_BLOCK_VALID"
    assert parsed["control_block_bytes"] == 256
    assert parsed["accession"] == accession
    assert parsed["submission_type"] == "10-K"
    assert parsed["receipt_date"] == "20250211"
    assert parsed["acceptance_date"] == "20250211"
    assert parsed["acceptance_time"] == "170704"
    assert parsed["acceptance_datetime"] == "20250211170704"
    assert parsed["acceptance_datetime_iso"] == "2025-02-11T17:07:04"
    assert parsed["submission_marker_matches"] is True


def test_parse_pds_control_block_fails_closed_on_invalid_clock_and_accession():
    bad_clock = make_pds_control_block(
        "0000064040-25-000052", "10-K", "20250211", "20250230", "256199"
    )
    parsed_clock = forensic.parse_pds_control_block(bad_clock)
    assert parsed_clock["status"] == "PDS_CONTROL_BLOCK_INVALID"
    assert parsed_clock["error"] == "PDS_CONTROL_BLOCK_DATE_TIME_OUT_OF_RANGE"

    bad_accession = b"not-an-accession".ljust(20, b" ") + bad_clock[20:]
    parsed_accession = forensic.parse_pds_control_block(bad_accession)
    assert parsed_accession["status"] == "PDS_CONTROL_BLOCK_INVALID"
    assert parsed_accession["error"] == "PDS_CONTROL_BLOCK_ACCESSION_INVALID"

def test_frozen_q220_request_rejects_changed_request_and_source_pins(tmp_path):
    request_path = ROOT / "research/run_requests/q220_primary_source_vintage_forensics.trigger"
    receipt_path = ROOT / forensic.SOURCE_RECEIPT_PATH
    original = request_path.read_text(encoding="utf-8")
    changed_request = tmp_path / request_path.name
    changed_request.write_text(original.replace("PERFORMANCE=false", "PERFORMANCE=true"), encoding="utf-8")
    with pytest.raises(ValueError, match="REQUEST_VALUE_MISMATCH:PERFORMANCE"):
        forensic.validate_frozen_source(changed_request, receipt_path)

    changed_request.write_text(original.replace(forensic.SOURCE_RECEIPT_FINGERPRINT, "0" * 64), encoding="utf-8")
    with pytest.raises(ValueError, match="REQUEST_VALUE_MISMATCH:SOURCE_RECEIPT_FINGERPRINT"):
        forensic.validate_frozen_source(changed_request, receipt_path)


def test_extract_primary_document_preserves_bytes_and_reports_edge_variants():
    filename = "sample-10k.htm"
    body = b"<!DOCTYPE html>\r\n<HTML><BODY>Original filing</BODY></HTML>\r\n"
    submission = (
        b"<SEC-HEADER>\nACCESSION NUMBER: 0000064040-19-000059\n</SEC-HEADER>\n"
        b"<DOCUMENT>\n<TYPE>10-K\n<SEQUENCE>1\n<FILENAME>" + filename.encode()
        + b"\n<TEXT>\r\n" + body + b"</TEXT>\n</DOCUMENT>\n"
    )
    parsed = forensic.extract_primary_document(submission, filename)
    assert parsed["found"] is True
    assert parsed["filename"] == filename
    variants = parsed["body_hash_variants"]
    assert variants["raw_text_block"]["sha256"] == forensic.sha256(b"\r\n" + body)
    assert variants["drop_one_leading_linebreak"]["sha256"] == forensic.sha256(body)
    assert variants["drop_outer_linebreaks"]["sha256"] == forensic.sha256(body.strip(b"\r\n"))


def test_parse_submission_header_requires_exact_accession_form_date_and_cik_fields():
    header = (
        b"<SEC-HEADER>\n"
        b"ACCESSION NUMBER: 0001564590-19-003382\n"
        b"CONFORMED SUBMISSION TYPE: 10-K\n"
        b"FILED AS OF DATE: 20190220\n"
        b"CENTRAL INDEX KEY: 0001090012\n"
        b"<ACCEPTANCE-DATETIME>20190220172300\n"
        b"</SEC-HEADER>"
    )
    parsed = forensic.parse_submission_header(header)
    assert parsed["accession"] == "0001564590-19-003382"
    assert parsed["filer_cik"] == "0001090012"
    assert parsed["form"] == "10-K"
    assert parsed["filed_date_iso"] == "2019-02-20"
    assert parsed["acceptance_datetime_iso"] == "2019-02-20T17:23:00"



def test_parse_submission_header_accepts_raw_sec_sgml_and_scopes_cik_to_filer():
    header = (
        b"<SEC-HEADER>\n"
        b"<ACCEPTANCE-DATETIME>20190213110253\n"
        b"<ACCESSION-NUMBER>0000064040-19-000059\n"
        b"<TYPE>10-K\n"
        b"<FILING-DATE>20190213\n"
        b"<FILER>\n"
        b"<COMPANY-DATA>\n"
        b"<CIK>0000064040\n"
        b"</COMPANY-DATA>\n"
        b"</FILER>\n"
        b"<ISSUER>\n"
        b"<COMPANY-DATA>\n"
        b"<CIK>0009999999\n"
        b"</COMPANY-DATA>\n"
        b"</ISSUER>\n"
        b"</SEC-HEADER>\n"
        b"<DOCUMENT>\n<TYPE>EX-99.1\n"
    )
    parsed = forensic.parse_submission_header(header)

    assert parsed["header_format"] == "sec_sgml_tags"
    assert parsed["accession"] == "0000064040-19-000059"
    assert parsed["filer_cik"] == "0000064040"
    assert parsed["form"] == "10-K"
    assert parsed["filed_date_iso"] == "2019-02-13"
    assert parsed["acceptance_datetime_iso"] == "2019-02-13T11:02:53"


def test_parse_submission_header_never_reads_document_type_as_header_form():
    body = (
        b"<SEC-HEADER>\n"
        b"<ACCESSION-NUMBER>0000064040-19-000059\n"
        b"<FILING-DATE>20190213\n"
        b"</SEC-HEADER>\n"
        b"<DOCUMENT>\n"
        b"<TYPE>10-K\n"
        b"</DOCUMENT>\n"
    )
    parsed = forensic.parse_submission_header(body)

    assert parsed["form"] is None
    assert parsed["header_format"] == "sec_sgml_tags"


def test_daily_feed_url_uses_official_year_quarter_directory():
    assert forensic.daily_feed_url("2019-02-13") == (
        "https://www.sec.gov/Archives/edgar/Feed/2019/QTR1/20190213.nc.tar.gz"
    )
    assert forensic.daily_feed_url("2019-02-20") == (
        "https://www.sec.gov/Archives/edgar/Feed/2019/QTR1/20190220.nc.tar.gz"
    )
    assert forensic.daily_feed_url("2025-02-11") == (
        "https://www.sec.gov/Archives/edgar/Feed/2025/QTR1/20250211.nc.tar.gz"
    )
    assert forensic.daily_feed_url("2019-10-01") == (
        "https://www.sec.gov/Archives/edgar/Feed/2019/QTR4/20191001.nc.tar.gz"
    )


def test_scan_daily_feed_finds_exact_original_and_records_correction_names():
    accession = "0000064040-19-000059"
    filename = "spgi-20181231x10k.htm"
    primary = b"<!DOCTYPE html><HTML><BODY>Original body</BODY></HTML>"
    submission = (
        b"<SEC-HEADER>\n"
        + f"ACCESSION NUMBER: {accession}\n".encode()
        + b"CONFORMED SUBMISSION TYPE: 10-K\n"
        + b"FILED AS OF DATE: 20190213\n"
        + b"CENTRAL INDEX KEY: 0000064040\n"
        + b"<ACCEPTANCE-DATETIME>20190213110253\n"
        + b"</SEC-HEADER>\n"
        + b"<DOCUMENT>\n<TYPE>10-K\n<SEQUENCE>1\n<FILENAME>"
        + filename.encode()
        + b"\n<TEXT>\n"
        + primary
        + b"\n</TEXT>\n</DOCUMENT>\n"
    )
    submission = make_pds_control_block(
        accession, "10-K", "20190213", "20190213", "110253"
    ) + submission
    archive_bytes = io.BytesIO()
    with tarfile.open(fileobj=archive_bytes, mode="w:gz") as archive:
        original = tarfile.TarInfo(accession + ".nc")
        original.size = len(submission)
        archive.addfile(original, io.BytesIO(submission))
        correction_payload = b"correction record; never applied by this probe"
        correction = tarfile.TarInfo(accession + ".corr01")
        correction.size = len(correction_payload)
        archive.addfile(correction, io.BytesIO(correction_payload))

    scan = forensic.scan_daily_feed(
        archive_bytes.getvalue(),
        accession,
        filename,
        max_scan_bytes=1_000_000,
        max_member_bytes=100_000,
    )
    assert scan["scan_complete"] is True
    assert scan["original_member_name"] == accession + ".nc"
    assert scan["correction_members"] == [{"name": accession + ".corr01", "declared_bytes": len(correction_payload)}]
    assert scan["submission_header"]["accession"] == accession
    assert scan["pds_control_block"]["status"] == "PDS_CONTROL_BLOCK_VALID"
    assert scan["submission_header"]["acceptance_datetime"] == "20190213110253"
    assert scan["submission_header"]["acceptance_datetime_source"] == "sgml_header_and_pds_control_block"
    assert scan["submission_header"]["sgml_acceptance_datetime_comparison"] == "MATCH"
    assert scan["primary"]["found"] is True
    assert scan["primary"]["body_hash_variants"]["raw_text_block"]["sha256"] == forensic.sha256(b"\n" + primary + b"\n")


def test_scan_daily_feed_does_not_confuse_pds_dissem_name_with_internal_nc_member():
    accession = "0000064040-19-000059"
    archive_bytes = io.BytesIO()
    payload = b"PDS outer-layer name only; not a Feed .nc submission"
    with tarfile.open(fileobj=archive_bytes, mode="w:gz") as archive:
        pds_member = tarfile.TarInfo(accession + ".dissem")
        pds_member.size = len(payload)
        archive.addfile(pds_member, io.BytesIO(payload))

    scan = forensic.scan_daily_feed(
        archive_bytes.getvalue(),
        accession,
        "spgi-20181231x10k.htm",
        max_scan_bytes=1_000_000,
        max_member_bytes=100_000,
    )

    assert scan["scan_complete"] is True
    assert scan["original_member_name"] is None
    assert scan["primary"] is None
    assert scan["scan_error"] == "ORIGINAL_SUBMISSION_MEMBER_NOT_FOUND_IN_FILING_DAY_FEED"



def test_scan_daily_feed_separates_submission_wrapper_cap_from_primary_document_cap():
    accession = "0000064040-25-000052"
    filename = "spgi-20241231.htm"
    primary = b"<html>small primary</html>"
    exhibit = b"EXHIBIT-" + (b"x" * 2048)
    submission = (
        b"<SEC-HEADER>\n"
        + f"ACCESSION NUMBER: {accession}\n".encode()
        + b"CONFORMED SUBMISSION TYPE: 10-K\n"
        + b"FILED AS OF DATE: 20250211\n"
        + b"CENTRAL INDEX KEY: 0000064040\n"
        + b"</SEC-HEADER>\n"
        + b"<DOCUMENT>\n<TYPE>10-K\n<FILENAME>" + filename.encode()
        + b"\n<TEXT>\n" + primary + b"\n</TEXT>\n</DOCUMENT>\n"
        + b"<DOCUMENT>\n<TYPE>EX-99.1\n<FILENAME>exhibit.txt\n<TEXT>\n"
        + exhibit + b"\n</TEXT>\n</DOCUMENT>\n"
    )
    submission = make_pds_control_block(
        accession, "10-K", "20250211", "20250211", "170704"
    ) + submission
    assert len(submission) > 100
    archive_bytes = io.BytesIO()
    with tarfile.open(fileobj=archive_bytes, mode="w:gz") as archive:
        member = tarfile.TarInfo(accession + ".nc")
        member.size = len(submission)
        archive.addfile(member, io.BytesIO(submission))

    scan = forensic.scan_daily_feed(
        archive_bytes.getvalue(),
        accession,
        filename,
        max_scan_bytes=10_000,
        max_member_bytes=100,
        max_submission_bytes=10_000,
    )

    assert scan["scan_complete"] is True
    assert scan["original_member_declared_bytes"] == len(submission)
    assert scan["original_member_bytes"] == len(submission)
    assert scan["original_submission_member_limit_bytes"] == 10_000
    assert scan["primary_document_limit_bytes"] == 100
    assert scan["primary"]["found"] is True
    assert scan["primary"]["raw_text_block_bytes"] <= 100
    assert scan["submission_header"]["acceptance_datetime"] == "20250211170704"
    assert scan["submission_header"]["acceptance_datetime_source"] == "pds_control_block"
    assert scan["submission_header"]["sgml_acceptance_datetime_comparison"] == "NOT_PRESENT_CONTROL_BLOCK_USED"


def test_scan_daily_feed_records_size_when_submission_wrapper_exceeds_its_own_cap():
    accession = "0000064040-25-000052"
    payload = b"wrapper" * 100
    archive_bytes = io.BytesIO()
    with tarfile.open(fileobj=archive_bytes, mode="w:gz") as archive:
        member = tarfile.TarInfo(accession + ".nc")
        member.size = len(payload)
        archive.addfile(member, io.BytesIO(payload))

    scan = forensic.scan_daily_feed(
        archive_bytes.getvalue(),
        accession,
        "spgi-20241231.htm",
        max_scan_bytes=10_000,
        max_member_bytes=100,
        max_submission_bytes=500,
    )

    assert scan["scan_complete"] is False
    assert scan["original_member_name"] == accession + ".nc"
    assert scan["original_member_declared_bytes"] == len(payload)
    assert scan["original_submission_member_limit_bytes"] == 500
    assert scan["scan_error"] == "ORIGINAL_SUBMISSION_MEMBER_OVER_LIMIT"
    assert scan["primary"] is None


def test_extract_primary_document_fails_closed_when_primary_exceeds_its_own_cap():
    filename = "primary.htm"
    body = b"x" * 40
    submission = (
        b"<DOCUMENT>\n<TYPE>10-K\n<FILENAME>" + filename.encode()
        + b"\n<TEXT>\n" + body + b"\n</TEXT>\n</DOCUMENT>\n"
    )
    parsed = forensic.extract_primary_document(
        submission,
        filename,
        max_primary_bytes=10,
    )
    assert parsed["found"] is False
    assert parsed["error"] == "PRIMARY_DOCUMENT_OVER_LIMIT"
    assert parsed["primary_document_bytes"] > parsed["primary_document_limit_bytes"]

def test_original_feed_hash_comparison_never_changes_scientific_gate():
    expected = "a" * 64
    assert forensic.compare_hash_origin(expected, "b" * 64, {"raw": {"sha256": expected}}) == (
        "FROZEN_HASH_MATCHES_ORIGINAL_FEED_BODY_CURRENT_ARCHIVE_DIFFERS"
    )
    assert forensic.compare_hash_origin(expected, expected, {"raw": {"sha256": expected}}) == (
        "FROZEN_HASH_MATCHES_ORIGINAL_FEED_BODY"
    )
    assert forensic.compare_hash_origin(expected, "b" * 64, {"raw": {"sha256": "c" * 64}}) == (
        "FROZEN_HASH_MATCHES_NEITHER_OBSERVED_BODY"
    )
    assert forensic.SOURCE_RECEIPT_FINGERPRINT == "c7fc53c9ef2daaef9caee29c0ba1084602c0bf4b24c6d2a13cb812b7b592c075"
    assert forensic.EXPECTED_SOURCE_HASH_FAILURE_COUNT == 55


def test_bounded_get_rejects_truncated_body_when_content_length_is_known(monkeypatch):
    class Response:
        status = 200
        headers = {
            "Content-Type": "application/gzip",
            "Content-Length": "100",
        }

        def __init__(self):
            self.calls = 0

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def geturl(self):
            return "https://www.sec.gov/truncated.nc.tar.gz"

        def read(self, _size):
            self.calls += 1
            return b"x" * 50 if self.calls == 1 else b""

    monkeypatch.setattr(
        forensic.urllib.request,
        "urlopen",
        lambda _request, timeout: Response(),
    )
    budget = forensic.DownloadBudget(1000)
    result = forensic._bounded_get(
        "https://www.sec.gov/truncated.nc.tar.gz",
        max_bytes=200,
        budget=budget,
    )

    assert result["http_status"] == 200
    assert result["content_length_header"] == 100
    assert result["status"] == "INCOMPLETE_CONTENT_LENGTH"
    assert result["response_bytes"] == 50
    assert result["error"] == "CONTENT_LENGTH_MISMATCH:declared=100:received=50"
    assert result["body"] == b""
    assert budget.used == 50


def test_bounded_get_completes_a_response_from_repeated_short_reads(monkeypatch):
    payload = b"SEC Feed compressed data" * 8

    class Response:
        status = 200
        headers = {
            "Content-Type": "application/gzip",
            "Content-Length": str(len(payload)),
        }

        def __init__(self):
            self.offset = 0

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def geturl(self):
            return "https://www.sec.gov/chunked.nc.tar.gz"

        def read(self, size):
            amount = min(size, 25, len(payload) - self.offset)
            chunk = payload[self.offset:self.offset + amount]
            self.offset += amount
            return chunk

    monkeypatch.setattr(
        forensic.urllib.request,
        "urlopen",
        lambda _request, timeout: Response(),
    )
    budget = forensic.DownloadBudget(1000)
    result = forensic._bounded_get(
        "https://www.sec.gov/chunked.nc.tar.gz",
        max_bytes=1000,
        budget=budget,
    )

    assert result["status"] == "FETCHED"
    assert result["response_bytes"] == len(payload)
    assert result["body"] == payload
    assert result["response_sha256"] == forensic.sha256(payload)
    assert budget.used == len(payload)


def test_parse_submission_header_reads_type_tag_without_line_start_anchor():
    body = (
        b"<SEC-HEADER>\n"
        b"<ACCESSION-NUMBER>0000064040-25-000052\n"
        b"<FILER>\n<COMPANY-DATA>\n<CIK>0000064040\n</COMPANY-DATA>\n</FILER>\n"
        b"</SEC-HEADER><TYPE>10-K\n"
        b"<FILING-DATE>20250211\n"
        b"<ACCEPTANCE-DATETIME>20250211170704\n"
        b"<DOCUMENT>\n<TYPE>EX-99.1\n"
    )
    parsed = forensic.parse_submission_header(body)
    assert parsed["form"] == "10-K"
    assert parsed["filer_cik"] == "0000064040"
    assert parsed["filed_date_iso"] == "2025-02-11"
    assert parsed["acceptance_datetime_iso"] == "2025-02-11T17:07:04"


def test_parse_submission_header_reads_metadata_outside_sec_header_but_before_document():
    body = (
        b"<SEC-HEADER>\n"
        b"<ACCESSION-NUMBER>0000064040-25-000052\n"
        b"<FILER>\n<COMPANY-DATA>\n<CIK>0000064040\n</COMPANY-DATA>\n</FILER>\n"
        b"</SEC-HEADER>\n"
        b"<TYPE>10-K\n"
        b"<FILING-DATE>20250211\n"
        b"<ACCEPTANCE-DATETIME>20250211170704\n"
        b"<DOCUMENT>\n<TYPE>EX-99.1\n"
    )
    parsed = forensic.parse_submission_header(body)

    assert parsed["accession"] == "0000064040-25-000052"
    assert parsed["filer_cik"] == "0000064040"
    assert parsed["form"] == "10-K"
    assert parsed["filed_date_iso"] == "2025-02-11"
    assert parsed["acceptance_datetime"] == "20250211170704"
    assert parsed["acceptance_datetime_iso"] == "2025-02-11T17:07:04"
