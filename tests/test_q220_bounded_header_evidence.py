from __future__ import annotations

from pathlib import Path

import pytest

from automation import q220_bounded_header_evidence as evidence


def test_request_is_exact_and_paper_only(tmp_path):
    values = dict(evidence.FROZEN_REQUEST_VALUES)
    values["REQUEST_SEQUENCE"] = "2026-10-12T13:40:00Z"
    path = tmp_path / "request.trigger"
    path.write_text("".join(f"{key}={value}\n" for key, value in values.items()), encoding="utf-8")

    parsed = evidence.read_request(path)
    assert parsed["SOURCE_RUN_ID"] == "38254139755"
    assert parsed["SAMPLE_COUNT"] == "3"
    assert parsed["NO_FEED_DOWNLOADS"] == "true"
    assert parsed["NO_PRIMARY_DOCUMENT_DOWNLOADS"] == "true"

    values["LIVE_EXECUTION"] = "true"
    path.write_text("".join(f"{key}={value}\n" for key, value in values.items()), encoding="utf-8")
    with pytest.raises(evidence.HeaderEvidenceError, match="REQUEST_VALUE_MISMATCH:LIVE_EXECUTION"):
        evidence.read_request(path)


def test_header_parser_captures_edgar_identity_and_acceptance_time():
    body = (
        b"<SEC-HEADER>\n"
        b"<ACCEPTANCE-DATETIME>20190213110253\n"
        b"<ACCESSION-NUMBER>0000064040-19-000059\n"
        b"<TYPE>10-K\n"
        b"<FILING-DATE>20190213\n"
        b"<FILER>\n<COMPANY-DATA>\n<CIK>0000064040\n</COMPANY-DATA>\n</FILER>\n"
        b"</SEC-HEADER>\n"
        b"<DOCUMENT>\n<TYPE>EX-99.1\n<ACCEPTANCE-DATETIME>20990101000000\n"
    )
    parsed = evidence.parse_header_observation(body, "raw_sgml_header")
    assert parsed == {
        "source_type": "raw_sgml_header",
        "accession": "0000064040-19-000059",
        "filer_cik": "0000064040",
        "form": "10-K",
        "filing_date": "2019-02-13",
        "acceptance_datetime": "2019-02-13T11:02:53",
        "filing_date_change": None,
    }


def test_header_parser_observes_filing_date_change_without_rewriting_filing_date():
    body = (
        b"<SEC-HEADER>\n"
        b"ACCESSION NUMBER: 0001090012-19-003382\n"
        b"CONFORMED SUBMISSION TYPE: 10-K\n"
        b"FILED AS OF DATE: 20190220\n"
        b"DATE AS OF CHANGE: 20190221\n"
        b"CENTRAL INDEX KEY: 0001090012\n"
        b"<ACCEPTANCE-DATETIME>20190220172300\n"
        b"</SEC-HEADER>"
    )
    parsed = evidence.parse_header_observation(body, "complete_submission_header_prefix")
    assert parsed["filing_date"] == "2019-02-20"
    assert parsed["filing_date_change"] == "2019-02-21"
    assert parsed["acceptance_datetime"] == "2019-02-20T17:23:00"


def test_fetch_header_consumes_repeated_short_reads(monkeypatch):
    payload = (
        b"<SEC-HEADER>\n<ACCEPTANCE-DATETIME>20190213110253\n"
        b"ACCESSION NUMBER: 0000064040-19-000059\n"
        b"CONFORMED SUBMISSION TYPE: 10-K\nFILED AS OF DATE: 20190213\n"
        b"CENTRAL INDEX KEY: 0000064040\n</SEC-HEADER>\n"
    )

    class Response:
        status = 200
        headers = {"Content-Length": str(len(payload)), "Content-Type": "text/plain"}

        def __init__(self):
            self.offset = 0

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def geturl(self):
            return "https://www.sec.gov/test.txt"

        def read(self, size):
            amount = min(size, 11, len(payload) - self.offset)
            chunk = payload[self.offset:self.offset + amount]
            self.offset += amount
            return chunk

    monkeypatch.setattr(evidence.urllib.request, "urlopen", lambda _request, timeout: Response())
    budget = evidence.DownloadBudget(100_000)
    result = evidence.fetch_header("https://www.sec.gov/test.txt", budget, max_bytes=10_000)

    assert result["status"] == "FETCHED"
    assert result["response_bytes"] == len(payload)
    assert result["_body"] == payload
    assert result["response_sha256"] == evidence.sha256(payload)
    assert budget.used == len(payload)


def test_fetch_header_stops_at_header_marker_and_retains_no_document_body(monkeypatch):
    header = b"<SEC-HEADER>\n<ACCEPTANCE-DATETIME>20190213110253\n</SEC-HEADER>"
    payload = header + b"<DOCUMENT>\n" + (b"x" * 500_000)

    class Response:
        status = 200
        headers = {"Content-Length": str(len(payload)), "Content-Type": "text/plain"}

        def __init__(self):
            self.offset = 0

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def geturl(self):
            return "https://www.sec.gov/test.txt"

        def read(self, size):
            amount = min(size, len(payload) - self.offset)
            chunk = payload[self.offset:self.offset + amount]
            self.offset += amount
            return chunk

    monkeypatch.setattr(evidence.urllib.request, "urlopen", lambda _request, timeout: Response())
    budget = evidence.DownloadBudget(100_000)
    result = evidence.fetch_header(
        "https://www.sec.gov/test.txt",
        budget,
        max_bytes=10_000,
        prefix_marker=b"</SEC-HEADER>",
    )

    assert result["status"] == "FETCHED_PREFIX"
    assert result["prefix_marker_found"] is True
    assert result["_body"] == header
    assert result["response_bytes"] == len(header)
    assert budget.used == len(header)


def test_load_frozen_run_receipt_rejects_any_unpinned_payload(tmp_path):
    path = tmp_path / "receipt.json"
    path.write_text('{"status":"FORENSIC_COMPARISON_INCOMPLETE"}\n', encoding="utf-8")
    with pytest.raises(evidence.HeaderEvidenceError, match="SOURCE_RECEIPT_BLOB_MISMATCH"):
        evidence.load_frozen_run_receipt(path)
