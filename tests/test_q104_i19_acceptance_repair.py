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
    _archive_accession_metadata,
    accession_hdr_sgml_url,
    is_repairable_failure,
    is_transient_failure,
    repair_shard_payload,
    resolve_accession_header,
)
from automation.q104_i19_13f_historical_identity_census_merge import canonical_fingerprint


ACCESSION = "0001045810-25-000001"
CIK = "0001045810"
FORM = "13F-HR"
FILING_DATE = "2025-01-15"
PERIOD = "31-DEC-2024"


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


def test_archive_metadata_does_not_confuse_accession_prefix_with_filer_cik():
    accession = "0000950123-13-005205"
    filer_cik = "0000728618"
    submission = (
        "ACCESSION_NUMBER\tFILING_DATE\tPERIODOFREPORT\tCIK\tSUBMISSIONTYPE\n"
        f"{accession}\t31-JUL-2013\t2013-06-30\t728618\t13F-HR\n"
    )
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("SUBMISSION.tsv", submission)
    archive_record = {
        "target_hits": {
            "SPGI": {
                "filing_dates": ["2013-07-31"],
                "periods": ["2013-06-30"],
            }
        }
    }

    metadata = _archive_accession_metadata(raw.getvalue(), {accession}, archive_record)

    assert metadata[accession] == {
        "filing_date": "2013-07-31",
        "period": "2013-06-30",
        "filer_cik": filer_cik,
        "submission_type": "13F-HR",
    }


def test_header_identity_still_rejects_cik_that_conflicts_with_archive_metadata():
    accession = "0000950123-13-005205"
    filer_cik = "0000728618"
    header = (
        "<SEC-HEADER>\n"
        f"ACCESSION NUMBER: {accession}\n"
        "CONFORMED SUBMISSION TYPE: 13F-HR\n"
        "FILED AS OF DATE: 20130731\n"
        "CENTRAL INDEX KEY: 0000950123\n"
        "<ACCEPTANCE-DATETIME>20130731170611\n"
        "</SEC-HEADER>"
    )
    meta = {
        "filer_cik": filer_cik,
        "filing_date": "2013-07-31",
        "period": "2013-06-30",
        "submission_type": "13F-HR",
    }

    record, error, attempts = resolve_accession_header(
        accession,
        meta,
        NoopLimiter(),
        urlopen=lambda *_args, **_kwargs: Response(header.encode()),
        sleep=lambda _: None,
    )

    assert record is None
    assert error == "HEADER_VALIDATION:FILER_CIK_MISMATCH"
    assert attempts == 1

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
        "header_source_type": "sec_index_headers",
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



def test_legacy_header_404_is_repairable_only_via_same_accession_sgml_fallback():
    assert is_repairable_failure("SEC_HEADER_HTTP_404")
    assert is_repairable_failure("MISSING_ACCEPTANCE_DATETIME")
    assert is_repairable_failure("HEADER_VALIDATION:MISSING_ACCEPTANCE_DATETIME")
    assert not is_repairable_failure("SEC_HEADER_FALLBACK_HTTP_404")
    assert not is_repairable_failure("HEADER_VALIDATION:FILER_CIK_MISMATCH")
    assert not is_repairable_failure("HEADER_VALIDATION:FILING_DATE_MISMATCH")


def test_header_resolver_falls_back_to_exact_accession_hdr_sgml_after_index_404():
    calls = []

    def opener(req, timeout):
        calls.append(req.full_url)
        if req.full_url.endswith("-index-headers.html"):
            raise urllib.error.HTTPError(req.full_url, 404, "not found", hdrs={}, fp=None)
        assert req.full_url == accession_hdr_sgml_url(CIK, ACCESSION)
        return Response(make_header())

    meta = {"filer_cik": CIK, "filing_date": FILING_DATE, "period": PERIOD, "submission_type": FORM}
    record, error, attempts = resolve_accession_header(
        ACCESSION, meta, NoopLimiter(), retries=3, urlopen=opener, sleep=lambda _: None
    )

    assert error is None
    assert attempts == 2
    assert calls == [
        census.accession_header_url(CIK, ACCESSION),
        accession_hdr_sgml_url(CIK, ACCESSION),
    ]
    assert record["header_source_type"] == "sec_hdr_sgml_fallback"
    assert record["source_url"] == accession_hdr_sgml_url(CIK, ACCESSION)
    assert record["acceptance_datetime"] == "2025-01-15T16:15:42"


def test_known_legacy_404_skips_the_missing_html_endpoint():
    calls = []

    def opener(req, timeout):
        calls.append(req.full_url)
        assert req.full_url == accession_hdr_sgml_url(CIK, ACCESSION)
        return Response(make_header())

    meta = {"filer_cik": CIK, "filing_date": FILING_DATE, "period": PERIOD, "submission_type": FORM}
    record, error, attempts = resolve_accession_header(
        ACCESSION, meta, NoopLimiter(), urlopen=opener, sleep=lambda _: None, prefer_sgml=True
    )

    assert error is None
    assert attempts == 1
    assert calls == [accession_hdr_sgml_url(CIK, ACCESSION)]
    assert record["header_source_type"] == "sec_hdr_sgml_fallback"


def test_targeted_repair_routes_frozen_header_404s_to_hdr_sgml(monkeypatch):
    from automation import q104_i19_acceptance_repair as repair

    blob = make_archive()
    receipt = make_shard_receipt(blob)
    receipt["acceptance_failures"][ACCESSION] = "SEC_HEADER_HTTP_404"
    receipt["archives"][0]["acceptance_failures"][ACCESSION] = "SEC_HEADER_HTTP_404"
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    calls = []

    def opener(req, timeout):
        calls.append(req.full_url)
        assert req.full_url == accession_hdr_sgml_url(CIK, ACCESSION)
        return Response(make_header())

    monkeypatch.setattr(repair.urllib.request, "urlopen", opener)
    fixed, entries = repair_shard_payload(
        receipt,
        rate_limiter=NoopLimiter(),
        archive_fetcher=lambda _url, _limiter: blob,
    )

    assert calls == [accession_hdr_sgml_url(CIK, ACCESSION)]
    assert entries[0]["status"] == "REPAIRED"
    assert fixed["acceptance_failures"] == {}
    assert fixed["archives"][0]["target_hits"]["SPGI"]["acceptance_complete"] is True


@pytest.mark.parametrize(
    "reason",
    [
        "<urlopen error [Errno 11001] getaddrinfo failed>",
        "<urlopen error [WinError 10065] Der Host war bei einem Socketvorgang nicht erreichbar>",
        "[WinError 10054] Eine vorhandene Verbindung wurde vom Remotehost geschlossen",
        "URLError:Temporary failure in name resolution",
        "SEC_HEADER_HTTP_503",
        "<urlopen error _ssl.c:1015: The handshake operation timed out>",
    ],
)
def test_localized_windows_and_dns_transport_errors_are_repairable(reason):
    assert is_transient_failure(reason)
    assert is_repairable_failure(reason)


@pytest.mark.parametrize(
    "reason",
    [
        "FILING_DATE_MISMATCH",
        "HEADER_VALIDATION:FILER_CIK_MISMATCH",
        "HEADER_VALIDATION:ACCESSION_MISMATCH",
        "SEC_HEADER_FALLBACK_HTTP_404",
    ],
)
def test_repair_keeps_identity_and_irrecoverable_header_errors_fail_closed(reason):
    assert not is_repairable_failure(reason)


def test_q104_targeted_repair_request_is_receipt_gated_and_paper_only():
    root = Path(__file__).resolve().parents[1]
    wrapper = (root / ".github/workflows/q104-i19-targeted-acceptance-repair-request.yml").read_text(encoding="utf-8")
    repair = (root / ".github/workflows/q104-i19-targeted-acceptance-repair.yml").read_text(encoding="utf-8")
    request = (root / "research/run_requests/q104_i19_targeted_acceptance_repair.trigger").read_text(encoding="utf-8")
    census = (root / ".github/workflows/q104-i19-13f-historical-identity-census.yml").read_text(encoding="utf-8")

    assert 'branches: [master]' in wrapper
    assert 'paths:' in wrapper
    assert '- "research/run_requests/q104_i19_targeted_acceptance_repair.trigger"' in wrapper
    assert r"^[A-Z0-9_]+=[A-Za-z0-9._,:-]*$" in wrapper
    assert "RUN_Q104_I19_TARGETED_REPAIR|REASON|SOURCE_RUN_ID|SHARD_RECOVERY_RUN_ID|RECOVERED_SHARDS" in wrapper
    wrapper_global_permissions = wrapper.split("permissions:", 1)[1].split("concurrency:", 1)[0]
    assert "actions: write" in wrapper_global_permissions
    repair_job = wrapper.split("  repair:", 1)[1].split("    uses: ./.github/workflows/q104-i19-targeted-acceptance-repair.yml", 1)[0]
    assert "actions: write" in repair_job
    repair_global_permissions = repair.split("permissions:", 1)[1].split("concurrency:", 1)[0]
    assert "actions: write" in repair_global_permissions
    relay = (root / ".github/workflows/research-completion-relay.yml").read_text(encoding="utf-8")
    assert "actions: write" in relay.split("permissions:", 1)[1].split("jobs:", 1)[0]

    assert 'SOURCE_RUN_ID=38168441086' in request
    assert 'SHARD_RECOVERY_RUN_ID=38168441086' in request
    assert 'CENSUS_RESTART=false' in request
    assert 'SOURCE_SNAPSHOT_REUSE=true' in request
    for flag in ("PERFORMANCE=false", "HOLDOUT_SELECTION=false", "RANKING=false", "TUNING=false", "PROMOTION=false", "LIVE_EXECUTION=false"):
        assert flag in request
    assert '.conclusion == "failure"' in wrapper
    assert 'key="${line%%=*}"' in wrapper
    assert 'grep -c "^${key}=" "$request" || true' in wrapper
    assert 'for shard in "${recovered[@]}";' in wrapper
    assert "Q104 I19 Historical 13F Identity Census" in wrapper
    assert "q104-i19-sec-source-snapshot-$source_run_id" in wrapper
    for shard in ("2013-2016", "2017-2018", "2019-2020", "2021-2022", "2023", "2024-2025-09"):
        assert f"q104-i19-census-$shard-$source_run_id" in wrapper
    assert "Q104_I19_REQUIRED_SHARD_RECEIPT_MISSING_OR_EXPIRED" in wrapper
    assert 'gh api "/repos/$GITHUB_REPOSITORY/actions/runs/$SOURCE_RUN_ID/artifacts?per_page=100"' in repair
    assert "q104-i19-census-$shard-$source_run_id" in repair
    assert 'gh run rerun "$GITHUB_RUN_ID"' not in census
