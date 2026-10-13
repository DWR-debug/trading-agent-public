from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

from automation import q220_single_feed_boundary_validation as probe
from automation import q220_primary_source_vintage_forensics as forensic

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "research/run_requests/q220_single_feed_boundary_validation.trigger"
SOURCE = ROOT / "research/fixtures/q220_historical_representation_pit_2026-10-12T071514Z.json"


def _feed_archive() -> bytes:
    accession = "0000064040-19-000059"
    filename = "spgi-20181231x10k.htm"
    primary = b"<!DOCTYPE html>\r\n<HTML><BODY>Mock original SEC source</BODY></HTML>\r\n"
    submission = (
        b"<SEC-HEADER>\n"
        + f"<ACCESSION-NUMBER>{accession}\n".encode()
        + b"<FILER>\n<COMPANY-DATA>\n<CIK>0000064040\n</COMPANY-DATA>\n</FILER>\n"
        + b"</SEC-HEADER>\n<TYPE>10-K\n<FILING-DATE>20190213\n"
        + b"<DOCUMENT>\n<TYPE>10-K\n<FILENAME>" + filename.encode()
        + b"\n<TEXT>\r\n" + primary + b"</TEXT>\n</DOCUMENT>\n"
    )
    archive_bytes = io.BytesIO()
    with tarfile.open(fileobj=archive_bytes, mode="w:gz") as archive:
        member = tarfile.TarInfo("./" + accession + ".nc")
        member.size = len(submission)
        archive.addfile(member, io.BytesIO(submission))
    return archive_bytes.getvalue()


def test_registered_single_feed_request_and_frozen_source_pins_validate():
    request = probe.read_request(REQUEST)
    receipt, row = probe.validate_source(SOURCE, request)
    assert request["TARGET_RECORD_KEY"] == "0000064040|0000064040-19-000059|10-K|2019-02-13"
    assert receipt["receipt_fingerprint"] == probe.FROZEN["SOURCE_RECEIPT_FINGERPRINT"]
    assert receipt["source_hash_failure_count"] == 55
    assert row["record_key"] == request["TARGET_RECORD_KEY"]


def test_single_feed_run_is_bounded_and_keeps_gate_closed(tmp_path):
    current = b"<html>mock current SEC primary</html>\r\n"
    feed = _feed_archive()
    calls = []

    def fetcher(url, max_bytes, budget):
        calls.append((url, max_bytes))
        body = feed if url.endswith("/20190213.nc.tar.gz") else current
        budget.add(len(body))
        return {
            "status": "FETCHED",
            "http_status": 200,
            "body": body,
            "response_bytes": len(body),
            "response_sha256": forensic.sha256(body),
            "content_length_header": str(len(body)),
            "last_modified": "Wed, 13 Feb 2019 11:02:53 GMT",
            "final_url": url,
            "requested_url": url,
        }

    output = tmp_path / "receipt.json"
    result = probe.run(REQUEST, SOURCE, output, fetcher=fetcher)
    persisted = json.loads(output.read_text(encoding="utf-8"))

    assert result["status"] == "SINGLE_FEED_BOUNDARY_COMPARISON_COMPLETE"
    assert persisted["receipt_fingerprint"] == result["receipt_fingerprint"]
    assert result["comparison"]["feed"]["identity_validated"] is True
    assert result["comparison"]["feed"]["comparison_complete"] is True
    assert result["comparison"]["feed"]["frozen_expected_sha256_match_count"] == 0
    assert result["source_download_bytes"] == len(current) + len(feed)
    assert result["source_download_bytes"] <= 950_000_000
    assert calls[0][1] == 15_000_000
    assert calls[1][1] == 900_000_000
    assert result["gate_positive"] is False
    assert result["scientific_evidence"] is False
    assert result["performance_authorization"] is False
    assert result["holdout_selection"] is False
    assert result["ranking"] is False
    assert result["tuning"] is False
    assert result["promotion"] is False
    assert result["live_execution"] is False


def test_changed_source_hash_pin_is_rejected_before_network(tmp_path):
    content = REQUEST.read_text(encoding="utf-8").replace(
        "EXPECTED_SHA256=27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83",
        "EXPECTED_SHA256=" + "a" * 64,
    )
    path = tmp_path / "request.trigger"
    path.write_text(content, encoding="utf-8")
    calls = []

    def forbidden_fetcher(*_args, **_kwargs):
        calls.append(True)
        raise AssertionError("network request must not be attempted after a pin mismatch")

    result = probe.run(path, SOURCE, tmp_path / "receipt.json", fetcher=forbidden_fetcher)
    assert result["status"] == "REQUEST_REJECTED"
    assert calls == []
    assert result["gate_positive"] is False
    assert result["live_execution"] is False
