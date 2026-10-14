from __future__ import annotations

import re
import urllib.request
from pathlib import Path

import pytest

from automation import q220_complete_submission_representation_audit as audit


ROOT = Path(__file__).resolve().parents[1]


def synthetic_submission(sample: dict, body: bytes | None = None) -> bytes:
    if body is None:
        body = (
            b"<!doctype html><html><body>"
            + b"diagnostic-only filing bytes for "
            + sample["accession"].encode("ascii")
            + b"</body></html>\r\n"
        )
    accepted = re.sub(r"[^0-9]", "", sample["acceptance_datetime"]).encode("ascii")
    header = (
        b"<SEC-DOCUMENT>\n"
        b"<SEC-HEADER>\n"
        + b"<ACCESSION-NUMBER>" + sample["accession"].encode("ascii") + b"\n"
        + b"<TYPE>" + sample["form"].encode("ascii") + b"\n"
        + b"<FILING-DATE>" + sample["filed_date"].replace("-", "").encode("ascii") + b"\n"
        + b"<ACCEPTANCE-DATETIME>" + accepted + b"\n"
        + b"<FILER>\n<COMPANY-DATA>\n<CIK>" + sample["cik"].encode("ascii") + b"\n"
        + b"</COMPANY-DATA>\n</FILER>\n</SEC-HEADER>\n"
    )
    document = (
        b"<DOCUMENT>\n<TYPE>" + sample["form"].encode("ascii")
        + b"\n<SEQUENCE>1\n<FILENAME>" + sample["primary_filename"].encode("ascii")
        + b"\n<TEXT>\r\n" + body + b"</TEXT>\n</DOCUMENT>\n"
    )
    return header + document


def fake_fetcher_for_test(calls: list[str]):
    def fetcher(url: str, max_bytes: int, budget: audit.DownloadBudget) -> dict:
        sample = next((x for x in audit.SAMPLES if url.endswith(x["accession"] + ".txt")), None)
        assert sample is not None
        assert url == audit.complete_submission_url(sample)
        assert max_bytes == audit.MAX_COMPLETE_SUBMISSION_BYTES
        calls.append(url)
        body = synthetic_submission(
            sample,
            b"<!doctype html><html><body>Only the exact preregistered block is retained.</body></html>\r\n",
        )
        return {
            "requested_url": url,
            "final_url": url,
            "http_status": 200,
            "content_type": "text/plain",
            "content_encoding": "",
            "content_length_header": len(body),
            "last_modified": "Wed, 01 Jan 2020 00:00:00 GMT",
            "etag": None,
            "status": "FETCHED",
            "response_bytes": len(body),
            "response_sha256": audit.sha256(body),
            "error": None,
            "attempt_count": 1,
            "body": body,
        }
    return fetcher


def test_registered_preregistration_has_exact_sample_contract_and_closed_gates():
    prereg = audit.validate_preregistration(ROOT)
    assert prereg["bounds"]["sample_count"] == 3
    assert prereg["bounds"]["retry_count"] == 0
    assert prereg["bounds"]["persist_complete_submission_text"] is False
    assert [x["record_key"] for x in prereg["samples"]] == [x["record_key"] for x in audit.SAMPLES]
    assert prereg["gate_change_authorized"] is False
    assert prereg["gates"]["source_complete"] is False
    assert prereg["gates"]["historical_pit_positive"] is False
    assert prereg["safety"]["paper_only"] is True
    assert prereg["safety"]["live_trading_enabled"] is False
    assert prereg["safety"]["orders_enabled"] is False
    assert prereg["safety"]["automatic_promotion"] is False


def test_frozen_request_rejects_retry_or_changed_safety_boundary(tmp_path: Path):
    request_path = ROOT / audit.REQUEST_PATH
    original = request_path.read_text(encoding="utf-8")
    changed = tmp_path / "changed.trigger"
    changed.write_text(original.replace("RETRIES=0", "RETRIES=1"), encoding="utf-8")
    with pytest.raises(ValueError, match="REQUEST_FROZEN_VALUE_OR_KEYSET_MISMATCH"):
        audit.read_request(changed)
    changed.write_text(original.replace("LIVE_TRADING_ENABLED=false", "LIVE_TRADING_ENABLED=true"), encoding="utf-8")
    with pytest.raises(ValueError, match="REQUEST_FROZEN_VALUE_OR_KEYSET_MISMATCH"):
        audit.read_request(changed)


def test_primary_document_parser_preserves_all_bytes_after_literal_inner_text_closer():
    sample = audit.SAMPLES[0]
    raw_body = (
        b"<!doctype html><html><body>literal token </TEXT> is inside HTML; "
        b"all bytes after it must remain. </body></html>\r\n"
    )
    submission = synthetic_submission(sample, raw_body)
    info, document_block, extracted = audit.parse_primary_document_block(submission, sample["primary_filename"])
    assert extracted == b"\r\n" + raw_body
    assert info["raw_text_block_sha256"] == audit.sha256(extracted)
    assert info["raw_text_block_bytes"] == len(extracted)
    assert info["document_block_sha256"] == audit.sha256(document_block)
    assert info["text_closing_tag_count"] == 2
    assert info["body_hash_variants"]["drop_one_leading_linebreak"]["sha256"] == audit.sha256(raw_body)


def test_capture_uses_only_three_frozen_txt_routes_and_offline_replay_is_deterministic(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(audit, "validate_frozen_inputs", lambda root, forensics_artifact_dir: {"test_fixture": True})
    calls: list[str] = []
    capture_dir = tmp_path / "capture"
    result = audit.run_capture(
        ROOT,
        ROOT / audit.REQUEST_PATH,
        tmp_path / "pinned-forensics-artifact",
        capture_dir,
        fetcher=fake_fetcher_for_test(calls),
    )
    assert result["status"] == "Q220_COMPLETE_SUBMISSION_REPRESENTATION_DIAGNOSTIC_ONLY"
    assert len(calls) == 3
    assert all(url.endswith(".txt") for url in calls)
    assert all(".nc.tar.gz" not in url and not url.endswith(".htm") for url in calls)
    assert result["analysis_payload"]["interpretation"]["gate_positive"] is False
    assert result["analysis_payload"]["interpretation"]["frozen_hashes_changed"] is False
    assert result["analysis_payload"]["interpretation"]["source_vintage_proven"] is False
    assert not list(capture_dir.rglob("*.txt")), "complete submission response bodies must not be persisted"
    for sample in audit.SAMPLES:
        record = next(x for x in result["records"] if x["record_key"] == sample["record_key"])
        assert record["identity_validated"] is True
        assert record["primary_document_extracted"] is True
        assert (capture_dir / record["submission_header_artifact_path"]).is_file()
        assert (capture_dir / record["primary_document_block_artifact_path"]).is_file()

    verification = audit.verify_capture(
        capture_dir,
        tmp_path / "verify",
        result["analysis_fingerprint"],
        repo_root=ROOT,
        forensics_artifact_dir=tmp_path / "pinned-forensics-artifact",
    )
    assert verification["status"] == "Q220_COMPLETE_SUBMISSION_REPRESENTATION_REPRODUCED_OFFLINE"
    assert verification["verified_sample_count"] == 3
    assert verification["network_requests_made"] == 0
    assert verification["gate_positive"] is False
    assert verification["safety"]["paper_only"] is True


def test_offline_replay_fails_closed_if_any_retained_document_block_changes(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(audit, "validate_frozen_inputs", lambda root, forensics_artifact_dir: {"test_fixture": True})
    capture_dir = tmp_path / "capture"
    result = audit.run_capture(
        ROOT,
        ROOT / audit.REQUEST_PATH,
        tmp_path / "pinned-forensics-artifact",
        capture_dir,
        fetcher=fake_fetcher_for_test([]),
    )
    sample = audit.SAMPLES[0]
    record = next(x for x in result["records"] if x["record_key"] == sample["record_key"])
    block_path = capture_dir / record["primary_document_block_artifact_path"]
    block_path.write_bytes(block_path.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="CAPTURE_ARTIFACT_BYTE_OR_HASH_MISMATCH"):
        audit.verify_capture(
            capture_dir,
            tmp_path / "verify-tampered",
            result["analysis_fingerprint"],
            repo_root=ROOT,
            forensics_artifact_dir=tmp_path / "pinned-forensics-artifact",
        )


def test_http_redirects_are_not_followed():
    handler = audit.NoRedirectHandler()
    request = urllib.request.Request("https://www.sec.gov/frozen.txt")
    result = handler.redirect_request(
        request,
        object(),
        302,
        "Found",
        {},
        "https://www.sec.gov/alternate-route.txt",
    )
    assert result is None
