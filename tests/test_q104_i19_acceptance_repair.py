from __future__ import annotations

import hashlib
import io
import json
import urllib.error
import zipfile
from pathlib import Path

import pytest

from automation import q104_i19_13f_historical_identity_census as census
from automation.q104_i19_acceptance_repair import (
    is_transient_failure,
    repair_shard_payload,
    resolve_accession_header,
)
from automation.q104_i19_13f_historical_identity_census_merge import canonical_fingerprint


ACCESSION = "0001045810-25-000001"
CIK = "0001045810"
FORM = "13F-HR"
FILING_DATE = "2025-01-15"
PERIOD = "2024-12-31"


class NoopLimiter:
    def __init__(self):
        self.calls = 0

    def wait(self):
        self.calls += 1


class Response:
    status = 200
    headers = {}

    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


def make_archive():
    submission = (
        "ACCESSION_NUMBER\tFILING_DATE\tPERIODOFREPORT\tCIK\tSUBMISSIONTYPE\n"
        f"{ACCESSION}\t15-JAN-2025\t31-DEC-2024\t{CIK}\t{FORM}\n"
    )
    infotable = (
        "ACCESSION_NUMBER\tNAMEOFISSUER\tTITLEOFCLASS\tCUSIP\n"
        f"{ACCESSION}\tIssuer A\tCommon Stock\t78409V104\n"
    )
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("SUBMISSION.tsv", submission)
        zf.writestr("INFOTABLE.tsv", infotable)
    return raw.getvalue()


def make_header():
    return (
        "<SEC-HEADER>\n"
        f"ACCESSION NUMBER: {ACCESSION}\n"
        f"CONFORMED SUBMISSION TYPE: {FORM}\n"
        "FILED AS OF DATE: 20250115\n"
        f"CENTRAL INDEX KEY: {CIK}\n"
        "<ACCEPTANCE-DATETIME>20250115161542\n"
        "</SEC-HEADER>"
    ).encode()


def make_shard_receipt(blob: bytes):
    meta = {
        "url": "https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2025q1_form13f.zip",
        "label": "synthetic source archive fixture",
        "period_start": "2025-01-01",
    }
    scanned = census.scan_archive(blob, meta, {"SPGI": {"78409V104"}})
    scanned.pop("target_accession_meta", None)
    for hit in scanned["target_hits"].values():
        hit["acceptance_records"] = {}
        hit["acceptance_complete"] = False
    scanned["acceptance_failures"] = {ACCESSION: "SEC_HEADER_HTTP_503"}
    scanned["acceptance_record_count"] = 0
    scanned["target_unique_accession_count"] = 1

    receipt = {
        "schema_version": "1.0",
        "task_id": "Q-TEST-I19",
        "candidate_id": "Q104:I19",
        "status": "13F_HISTORICAL_CUSIP_IDENTITY_CENSUS_SOURCE_ONLY",
        "generated_at_utc": "2025-10-01T00:00:00+00:00",
        "official_source": census.PAGE,
        "source_page_sha256": "a" * 64,
        "data_boundary": {
            "start_inclusive": "2013-07-01",
            "end_exclusive": "2025-10-01",
            "filing_cutoff": "2025-09-24",
        },
        "shard": "2024-2025-09",
        "shard_boundary": {"start_inclusive": "2024-01-01", "end_exclusive": "2025-10-01"},
        "discovered_archive_count_total": 1,
        "selected_archive_count": 1,
        "frozen_cusips": {"SPGI": ["78409V104"]},
        "archives": [scanned],
        "coverage_summary": {"SPGI": {"archives_with_match": 1, "archives_without_match": 0}},
        "identity_conflicts": [],
        "acceptance_failures": {ACCESSION: "SEC_HEADER_HTTP_503"},
        "acceptance_time_join": {
            "records_checked": 0,
            "target_unique_accessions": 1,
            "failures": 1,
            "complete": False,
            "timezone_inference": False,
        },
        "archive_completeness_for_shard": True,
        "synthetic": {"hash": True, "matched": True, "future_excluded": True, "no_identity_conflict": True},
        "scientific_boundary": {
            "performance_authorized": False,
            "holdout_selection_allowed": False,
            "ranking_allowed": False,
            "parameter_search_allowed": False,
            "threshold_search_allowed": False,
            "horizon_search_allowed": False,
            "promotion_allowed": False,
            "live_execution_allowed": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "next_gate": "historical security-identity closure",
    }
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    return receipt


def fake_record(meta):
    body = make_header()
    return {
        "accession": ACCESSION,
        "filer_cik": CIK,
        "filing_date": FILING_DATE,
        "period": PERIOD,
        "submission_type": FORM,
        "acceptance_datetime": "2025-01-15T16:15:42",
        "acceptance_timezone": "America/New_York",
        "acceptance_clock_basis": "SEC_EDGAR_SGML_ACCEPTANCE_DATETIME",
        "source_url": census.accession_header_url(CIK, ACCESSION),
        "header_sha256": hashlib.sha256(body).hexdigest(),
        "header_bytes": len(body),
    }


def test_retry_classifier_retries_only_transient_errors():
    assert is_transient_failure("SEC_HEADER_HTTP_503")
    assert is_transient_failure("TimeoutError: timed out")
    assert is_transient_failure("URLError: connection reset")
    assert not is_transient_failure("ACCESSION_MISMATCH")
    assert not is_transient_failure("HEADER_VALIDATION:MISSING_ACCEPTANCE_DATETIME")


def test_header_fetch_uses_bounded_retries_and_exact_header_identity():
    calls = []
    def opener(req, timeout):
        calls.append(req.full_url)
        if len(calls) < 3:
            raise urllib.error.HTTPError(req.full_url, 503, "temporary", hdrs={"Retry-After": "0"}, fp=None)
        return Response(make_header())

    meta = {"filer_cik": CIK, "filing_date": FILING_DATE, "period": PERIOD, "submission_type": FORM}
    record, error, attempts = resolve_accession_header(
        ACCESSION, meta, NoopLimiter(), retries=3, urlopen=opener, sleep=lambda _: None
    )
    assert error is None
    assert attempts == 3
    assert len(calls) == 3
    assert set(calls) == {census.accession_header_url(CIK, ACCESSION)}
    assert record["acceptance_datetime"] == "2025-01-15T16:15:42"
    assert len(record["header_sha256"]) == 64


def test_repair_only_retries_failed_accession_and_seals_new_shard_receipt():
    blob = make_archive()
    receipt = make_shard_receipt(blob)
    asked = []

    def fetcher(url, limiter):
        asked.append(url)
        return blob

    def resolver(accession, meta, limiter):
        assert accession == ACCESSION
        assert meta == {
            "filing_date": FILING_DATE,
            "period": PERIOD,
            "filer_cik": CIK,
            "submission_type": FORM,
        }
        return fake_record(meta), None, 2

    fixed, entries = repair_shard_payload(
        receipt, rate_limiter=NoopLimiter(), archive_fetcher=fetcher, header_resolver=resolver
    )
    assert asked == [receipt["archives"][0]["archive"]["url"]]
    assert [x["accession"] for x in entries] == [ACCESSION]
    assert entries[0]["status"] == "REPAIRED"
    assert fixed["acceptance_failures"] == {}
    assert fixed["acceptance_time_join"] == {
        "records_checked": 1,
        "target_unique_accessions": 1,
        "failures": 0,
        "complete": True,
        "timezone_inference": False,
    }
    hit = fixed["archives"][0]["target_hits"]["SPGI"]
    assert hit["acceptance_complete"] is True
    assert hit["acceptance_records"][ACCESSION]["acceptance_datetime"] == "2025-01-15T16:15:42"
    assert fixed["receipt_fingerprint"] == canonical_fingerprint(fixed)


def test_repair_fails_closed_if_archive_hash_changes():
    receipt = make_shard_receipt(make_archive())
    with pytest.raises(ValueError, match="ARCHIVE_HASH_MISMATCH"):
        repair_shard_payload(
            receipt,
            rate_limiter=NoopLimiter(),
            archive_fetcher=lambda _url, _limiter: b"different archive",
            header_resolver=lambda *_args: pytest.fail("header must not be requested after archive mismatch"),
        )


def test_repair_fails_closed_if_top_level_failure_set_differs_from_archive_failures():
    receipt = make_shard_receipt(make_archive())
    receipt["acceptance_failures"] = {}
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    with pytest.raises(ValueError, match="TOP_LEVEL_FAILURE_SET_MISMATCH"):
        repair_shard_payload(receipt, rate_limiter=NoopLimiter())


def test_repair_does_not_retry_identity_mismatch():
    receipt = make_shard_receipt(make_archive())
    receipt["acceptance_failures"][ACCESSION] = "ACCESSION_MISMATCH"
    receipt["archives"][0]["acceptance_failures"][ACCESSION] = "ACCESSION_MISMATCH"
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    fixed, entries = repair_shard_payload(
        receipt,
        rate_limiter=NoopLimiter(),
        archive_fetcher=lambda *_args: pytest.fail("non-transient errors must not re-download archive"),
        header_resolver=lambda *_args: pytest.fail("identity errors must not be retried"),
    )
    assert entries[0]["status"] == "NOT_RETRIED_NONTRANSIENT"
    assert fixed["acceptance_time_join"]["complete"] is False
