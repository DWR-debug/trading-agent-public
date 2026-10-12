from __future__ import annotations

import io
import urllib.error

from automation import q104_i19_13f_historical_identity_census as census
from automation.q104_i19_acceptance_repair import (
    accession_hdr_sgml_url,
    resolve_accession_header,
)

ACCESSION = "0001045810-25-000001"
CIK = "0001045810"
FORM = "13F-HR"
FILING_DATE = "2025-01-15"


class NoopLimiter:
    def wait(self):
        pass


class Response:
    status = 200
    headers = {}

    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size: int = -1):
        return self.body if size < 0 else self.body[:size]


def sgml_header(accession: str = ACCESSION) -> bytes:
    return (
        "<SEC-HEADER>\n"
        f"<ACCESSION-NUMBER>{accession}\n"
        f"<CONFORMED-SUBMISSION-TYPE>{FORM}\n"
        f"<FILED-AS-OF-DATE>20250115\n"
        f"<CENTRAL-INDEX-KEY>{CIK}\n"
        "<ACCEPTANCE-DATETIME>20250115161542\n"
        "</SEC-HEADER>\n"
    ).encode("ascii")


def meta():
    return {
        "filer_cik": CIK,
        "filing_date": FILING_DATE,
        "period": "31-DEC-2024",
        "submission_type": FORM,
    }


def test_raw_sgml_fallback_parses_tagged_identity_after_html_route_404():
    calls = []

    def opener(request, timeout):
        calls.append(request.full_url)
        if request.full_url == census.accession_header_url(CIK, ACCESSION):
            raise urllib.error.HTTPError(
                request.full_url, 404, "missing legacy HTML route", {}, io.BytesIO(b"")
            )
        assert request.full_url == accession_hdr_sgml_url(CIK, ACCESSION)
        return Response(sgml_header())

    record, error, attempts = resolve_accession_header(
        ACCESSION,
        meta(),
        NoopLimiter(),
        urlopen=opener,
        sleep=lambda _: None,
    )

    assert error is None
    assert record is not None
    assert record["acceptance_datetime"] == "2025-01-15T16:15:42"
    assert record["header_source_type"] == "sec_hdr_sgml_fallback"
    assert record["source_url"] == accession_hdr_sgml_url(CIK, ACCESSION)
    assert attempts == 2
    assert calls == [
        census.accession_header_url(CIK, ACCESSION),
        accession_hdr_sgml_url(CIK, ACCESSION),
    ]


def test_raw_sgml_fallback_keeps_accession_mismatch_fail_closed():
    def opener(request, timeout):
        if request.full_url == census.accession_header_url(CIK, ACCESSION):
            raise urllib.error.HTTPError(
                request.full_url, 404, "missing legacy HTML route", {}, io.BytesIO(b"")
            )
        return Response(sgml_header("0001045810-25-000099"))

    record, error, attempts = resolve_accession_header(
        ACCESSION,
        meta(),
        NoopLimiter(),
        urlopen=opener,
        sleep=lambda _: None,
    )

    assert record is None
    assert error == "HEADER_VALIDATION:ACCESSION_MISMATCH"
    assert attempts == 2
