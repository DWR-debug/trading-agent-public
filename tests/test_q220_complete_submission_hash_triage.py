from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from automation import q220_complete_submission_hash_triage as triage


ROOT = Path(__file__).resolve().parents[1]


class FakeHeaders(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class FakeResponse:
    status = 200

    def __init__(self, body: bytes, url: str, *, headers: dict[str, str] | None = None):
        self.body = body
        self.url = url
        self.headers = FakeHeaders(headers or {})

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self.url

    def read(self, size=-1):
        return self.body if size < 0 else self.body[:size]


def test_request_binds_exact_frozen_q220_receipt_and_three_samples():
    request, receipt = triage.validate_frozen_inputs(
        ROOT / "research/run_requests/q220_complete_submission_hash_triage.trigger",
        ROOT / triage.SOURCE_REQUEST_PATH,
        ROOT / triage.SOURCE_RECEIPT_PATH,
    )

    assert request["SAMPLE_COUNT"] == "3"
    assert request["SAMPLE_RECORD_KEYS"].split(";") == list(triage.SAMPLE_KEYS)
    assert receipt["receipt_fingerprint"] == triage.SOURCE_RECEIPT_FINGERPRINT
    assert receipt["source_hash_failure_count"] == 55
    assert receipt["gate_positive"] is False
    assert triage.MAX_TOTAL_DOWNLOAD_BYTES <= 150_000_000


def test_request_rejects_safety_changes_and_manifest_byte_changes(tmp_path):
    request = ROOT / "research/run_requests/q220_complete_submission_hash_triage.trigger"
    receipt = ROOT / triage.SOURCE_RECEIPT_PATH
    text = request.read_text(encoding="utf-8")
    unsafe = tmp_path / "unsafe.trigger"
    unsafe.write_text(text.replace("PERFORMANCE=false", "PERFORMANCE=true"), encoding="utf-8")
    with pytest.raises(ValueError, match="REQUEST_VALUE_MISMATCH:PERFORMANCE"):
        triage.validate_frozen_inputs(unsafe, ROOT / triage.SOURCE_REQUEST_PATH, receipt)

    mutated_receipt = tmp_path / "changed-receipt.json"
    mutated_receipt.write_bytes(receipt.read_bytes() + b" ")
    with pytest.raises(ValueError, match="SOURCE_RECEIPT_BLOB_MISMATCH"):
        triage.validate_frozen_inputs(request, ROOT / triage.SOURCE_REQUEST_PATH, mutated_receipt)


def test_complete_submission_url_uses_company_cik_and_accession_directory():
    assert triage.complete_submission_url("0001090012", "0001564590-19-003382") == (
        "https://www.sec.gov/Archives/edgar/data/1090012/"
        "000156459019003382/0001564590-19-003382.txt"
    )


def test_current_primary_url_rejects_path_components():
    with pytest.raises(ValueError, match="INVALID_PRIMARY_FILENAME"):
        triage.current_primary_url("0000064040", "0000064040-19-000059", "../other.txt")


def test_bounded_get_stops_before_downloading_declared_oversize(monkeypatch):
    url = "https://www.sec.gov/example.txt"
    body = b"x" * 100
    response = FakeResponse(body, url, headers={"Content-Length": "100", "Content-Type": "text/plain"})
    monkeypatch.setattr(triage.urllib.request, "urlopen", lambda *args, **kwargs: response)
    budget = triage.DownloadBudget(1000)

    observed = triage.bounded_get(url, 10, budget)

    assert observed["status"] == "SKIPPED_DECLARED_LENGTH_OVER_LIMIT"
    assert observed["response_bytes"] == 0
    assert budget.used == 0


def test_bounded_get_caps_actual_bytes_and_propagates_budget(tmp_path, monkeypatch):
    url = "https://www.sec.gov/example.txt"
    response = FakeResponse(b"x" * 100, url)
    monkeypatch.setattr(triage.urllib.request, "urlopen", lambda *args, **kwargs: response)
    budget = triage.DownloadBudget(1000)

    observed = triage.bounded_get(url, 10, budget)

    assert observed["status"] == "SKIPPED_ACTUAL_LENGTH_OVER_LIMIT"
    assert observed["response_bytes"] == 11
    assert budget.used == 11


def test_run_is_diagnostic_only_and_never_claims_vintage_or_pit(monkeypatch, tmp_path):
    def fake_bounded_get(url, max_bytes, budget):
        budget.wait()
        if url.endswith(".txt"):
            key = next(k for k in triage.SAMPLE_KEYS if k.split("|")[1] + ".txt" in url)
            cik, accession, form, filed_date = key.split("|")
            date_digits = filed_date.replace("-", "")
            filename = triage.SAMPLE_PRIMARY_NAMES[key]
            primary = b"<!DOCTYPE html><html><body>fixture body</body></html>"
            submission = (
                "<SEC-HEADER>\n"
                f"ACCESSION NUMBER: {accession}\n"
                f"CONFORMED SUBMISSION TYPE: {form}\n"
                f"FILED AS OF DATE: {date_digits}\n"
                f"CENTRAL INDEX KEY: {cik}\n"
                f"<ACCEPTANCE-DATETIME>{date_digits}161542\n"
                "</SEC-HEADER>\n"
            ).encode() + (
                b"<DOCUMENT>\n<TYPE>" + form.encode() + b"\n<SEQUENCE>1\n<FILENAME>"
                + filename.encode() + b"\n<TEXT>\n" + primary + b"\n</TEXT>\n</DOCUMENT>\n"
            )
            body = submission
            content_type = "text/plain"
        else:
            body = b"<!DOCTYPE html><html><body>fixture body</body></html>"
            content_type = "text/html"
        budget.add(len(body))
        return {
            "requested_url": url,
            "final_url": url,
            "http_status": 200,
            "content_type": content_type,
            "content_encoding": "",
            "content_length_header": len(body),
            "last_modified": "Wed, 13 Feb 2019 11:02:53 GMT",
            "etag": "",
            "status": "FETCHED",
            "body": body,
            "response_bytes": len(body),
            "response_sha256": hashlib.sha256(body).hexdigest(),
        }

    monkeypatch.setattr(triage, "bounded_get", fake_bounded_get)
    output = tmp_path / "receipt.json"
    result = triage.run(
        ROOT / "research/run_requests/q220_complete_submission_hash_triage.trigger",
        ROOT / triage.SOURCE_REQUEST_PATH,
        ROOT / triage.SOURCE_RECEIPT_PATH,
        output,
    )

    assert output.exists()
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["status"] == "COMPLETE_SUBMISSION_TRIAGE_COMPLETE"
    assert saved["sample_count"] == 3
    assert saved["completed_sample_count"] == 3
    assert saved["gate_positive"] is False
    assert saved["scientific_evidence"] is False
    assert saved["performance_authorization"] is False
    assert saved["original_source_vintage_proven"] is False
    assert saved["historical_first_public_observation_proven"] is False
    assert all(item["comparison_complete"] is True for item in saved["samples"])
    assert result["source_hash_failure_count"] == 55
