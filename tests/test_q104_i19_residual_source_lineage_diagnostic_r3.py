from __future__ import annotations

import io
import zipfile

import pytest

from automation import q104_i19_residual_source_lineage_diagnostic_r3 as lineage


def test_parse_header_observation_uses_filer_scope_and_stops_before_document():
    body = (
        b"<SEC-HEADER>\n"
        b"<ACCESSION-NUMBER>0000950123-15-003104\n"
        b"<FILER>\n<COMPANY-DATA>\n<CIK>0000123456\n</COMPANY-DATA>\n</FILER>\n"
        b"</SEC-HEADER><TYPE>13F-HR\n"
        b"<FILING-DATE>20150313\n"
        b"<ACCEPTANCE-DATETIME>20150313170521\n"
        b"<DOCUMENT>\n<TYPE>EX-99.1\n<FILENAME>exhibit.txt\n"
    )

    observed = lineage.parse_header_observation(body, "raw_sgml_header")

    assert observed == {
        "source_type": "raw_sgml_header",
        "accession": "0000950123-15-003104",
        "filer_cik": "0000123456",
        "form": "13F-HR",
        "filing_date": "2015-03-13",
        "acceptance_datetime": "2015-03-13T17:05:21",
    }


def test_parse_index_header_fields_keeps_missing_identity_fields_missing():
    body = (
        b"ACCESSION NUMBER: 0001800724-20-000002\n"
        b"CENTRAL INDEX KEY: 0001800724\n"
        b"CONFORMED SUBMISSION TYPE: 13F-HR/A\n"
        b"FILED AS OF DATE: 20200814\n"
        b"<ACCEPTANCE-DATETIME>20200814172108\n"
        b"<DOCUMENT>\n<TYPE>EX-99.1\n"
    )

    observed = lineage.parse_header_observation(body, "index_headers")

    assert observed["accession"] == "0001800724-20-000002"
    assert observed["filer_cik"] == "0001800724"
    assert observed["form"] == "13F-HR/A"
    assert observed["filing_date"] == "2020-08-14"
    assert observed["acceptance_datetime"] == "2020-08-14T17:21:08"


def test_compare_to_archive_reports_disagreement_without_overriding_source_row():
    source_row = {
        "accession": "0000950123-15-003104",
        "filer_cik": "0000123456",
        "form": "13F-HR",
        "filing_date_iso": "2015-03-16",
    }
    observed = {
        "accession": "0000950123-15-003104",
        "filer_cik": "0000123456",
        "form": "13F-HR",
        "filing_date": "2015-03-13",
    }

    result = lineage.compare_observed_to_archive(source_row, observed)

    assert result == {
        "accession_matches": True,
        "filer_cik_matches": True,
        "form_matches": True,
        "filing_date_matches": False,
    }
    assert source_row["filing_date_iso"] == "2015-03-16"


def test_read_source_rows_extracts_only_pinned_accessions_and_normalizes_date():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "submission.tsv",
            "ACCESSION_NUMBER\tFILING_DATE\tCIK\tSUBMISSIONTYPE\tPERIODOFREPORT\n"
            "0000950123-15-003104\t13-MAR-2015\t123456\t13F-HR\t31-DEC-2014\n"
            "0000000000-15-999999\t14-MAR-2015\t999999\t13F-HR\t31-DEC-2014\n",
        )

    rows = lineage.read_source_rows(buffer.getvalue(), {"0000950123-15-003104"})

    assert list(rows) == ["0000950123-15-003104"]
    assert rows["0000950123-15-003104"] == {
        "accession": "0000950123-15-003104",
        "filer_cik": "0000123456",
        "form": "13F-HR",
        "filing_date_raw": "13-MAR-2015",
        "filing_date_iso": "2015-03-13",
        "period_of_report": "31-DEC-2014",
    }


def test_request_is_exact_and_live_execution_cannot_be_enabled(tmp_path):
    request = tmp_path / "request.trigger"
    pairs = dict(lineage.FROZEN_REQUEST_VALUES)
    pairs["REQUEST_SEQUENCE"] = "2026-10-12T13:18:00Z"
    request.write_text("".join(f"{k}={v}\n" for k, v in pairs.items()), encoding="utf-8")

    parsed = lineage.read_request(request)
    assert parsed["SOURCE_RUN_ID"] == "38168441086"
    assert parsed["SAMPLE_COUNT"] == "1"

    pairs["LIVE_EXECUTION"] = "true"
    request.write_text("".join(f"{k}={v}\n" for k, v in pairs.items()), encoding="utf-8")
    with pytest.raises(lineage.DiagnosticError, match="REQUEST_VALUE_MISMATCH:LIVE_EXECUTION"):
        lineage.read_request(request)


def test_download_fetches_repeated_short_reads_to_declared_length(monkeypatch):
    payload = b"exact SEC header bytes" * 13

    class Headers(dict):
        pass

    class Response:
        status = 200
        headers = Headers({"Content-Length": str(len(payload)), "Content-Type": "text/plain"})

        def __init__(self):
            self.offset = 0

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def geturl(self):
            return "https://www.sec.gov/test.hdr.sgml"

        def read(self, size):
            amount = min(size, 9, len(payload) - self.offset)
            result = payload[self.offset:self.offset + amount]
            self.offset += amount
            return result

    monkeypatch.setattr(
        lineage.urllib.request,
        "urlopen",
        lambda _request, timeout: Response(),
    )
    budget = lineage.DownloadBudget(10000)
    result = lineage.fetch_bounded(
        "https://www.sec.gov/test.hdr.sgml",
        budget,
        max_bytes=10000,
    )

    assert result["status"] == "FETCHED"
    assert result["response_bytes"] == len(payload)
    assert result["_body"] == payload
    assert result["response_sha256"] == lineage.sha256(payload)
    assert budget.used == len(payload)


def test_r3_freezes_only_the_remaining_2017q2_mismatch_and_never_expands_the_census():
    assert set(lineage.SOURCE_SHARDS) == {"2017-2018"}
    assert set(lineage.ARCHIVE_PINS) == {"2017q2_form13f.zip"}
    assert {x["accession"] for x in lineage.SAMPLES} == {"0001008929-17-000008"}
    assert lineage.ARCHIVE_PINS["2017q2_form13f.zip"]["sha256"] == "39298fa803677758b6d1854af89be0825c7a82baf596b872505066a267e60c5b"
    assert lineage.ARCHIVE_PINS["2017q2_form13f.zip"]["bytes"] == 43293228
    assert lineage.MAX_SOURCE_ARCHIVE_BYTES == 50_000_000
    assert lineage.MAX_TOTAL_DOWNLOAD_BYTES == 50_000_000
    assert lineage.FROZEN_REQUEST_VALUES["CENSUS_RESTART"] == "false"
    assert lineage.FROZEN_REQUEST_VALUES["REPAIR_RECEIPTS"] == "false"
    assert lineage.FROZEN_REQUEST_VALUES["FIELD_PRECEDENCE_APPLIED"] if "FIELD_PRECEDENCE_APPLIED" in lineage.FROZEN_REQUEST_VALUES else True
