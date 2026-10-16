from __future__ import annotations

import json
import shutil
import urllib.error
from pathlib import Path

from automation import q221_dod_097_wayback_replay_head_diagnostic_r6 as diag

ROOT = Path(__file__).resolve().parents[1]


def _minimal_repo(tmp_path):
    target = tmp_path / "repo"
    required = [diag.PREREG_PATH, diag.REQUEST_PATH, diag.MANIFEST_PATH, diag.R3_RECEIPT_PATH, diag.R5_RECEIPT_PATH]
    for rel in required:
        src = ROOT / rel
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    return target


def test_r6_preregistration_pins_r3_r5_and_manifest_offline():
    pins = diag.validate_inputs(ROOT)
    assert pins["manifest_blob_sha1"] == diag.MANIFEST_BLOB
    assert pins["r3_receipt_fingerprint"] == diag.R3_FP
    assert pins["r5_receipt_fingerprint"] == diag.R5_FP


def test_r6_marker_tampering_fails_closed(tmp_path):
    repo = _minimal_repo(tmp_path)
    marker = repo / diag.REQUEST_PATH
    marker.write_text(marker.read_text(encoding="utf-8").replace("HTTP_METHOD=HEAD", "HTTP_METHOD=GET"), encoding="utf-8")
    try:
        diag.validate_inputs(repo)
    except diag.DiagnosticError as exc:
        assert "MARKER_PIN_MISMATCH" in exc.status
    else:
        raise AssertionError("marker mutation must fail closed")


def test_head_metadata_capture_reads_no_body_and_records_only_allowlisted_headers(monkeypatch, tmp_path):
    seen = {}
    class Response:
        status = 200
        headers = {"Content-Length": "13697800", "Content-Type": "application/zip",
                   "Content-Encoding": "identity", "Transfer-Encoding": "chunked",
                   "Set-Cookie": "must-not-be-recorded"}
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, *args, **kwargs): raise AssertionError("R6 must never read the response body")
    class Opener:
        def open(self, request, timeout):
            seen["method"] = request.get_method()
            seen["url"] = request.full_url
            seen["timeout"] = timeout
            seen["accept_encoding"] = request.get_header("Accept-encoding")
            return Response()
    monkeypatch.setattr(diag.urllib.request, "build_opener", lambda *args: Opener())
    output = tmp_path / "receipt.json"
    receipt = diag.run_diagnostic(ROOT, output, fetcher=diag.head_only)
    assert receipt["status"] == "Q221_R6_HEAD_METADATA_CAPTURED"
    assert receipt["source_probe"]["request_count"] == 1
    assert receipt["source_probe"]["response_body_read_bytes"] == 0
    assert receipt["source_probe"]["archive_replay_get_request_count"] == 0
    assert receipt["http_metadata"]["headers"]["content-length"] == "13697800"
    assert "set-cookie" not in receipt["http_metadata"]["headers"]
    assert seen["method"] == "HEAD" and seen["url"] == diag.REPLAY_URL and seen["timeout"] == 60
    assert seen["accept_encoding"].lower() == "identity"
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["receipt_fingerprint"] == diag.canonical_fingerprint(written)


def test_head_redirect_is_not_followed_and_body_is_not_read(monkeypatch, tmp_path):
    class Opener:
        def open(self, request, timeout):
            raise urllib.error.HTTPError(diag.REPLAY_URL, 302, "Found",
                {"Location": "https://example.invalid/other.zip", "Content-Type": "text/plain"}, None)
    monkeypatch.setattr(diag.urllib.request, "build_opener", lambda *args: Opener())
    receipt = diag.run_diagnostic(ROOT, tmp_path / "redirect.json")
    assert receipt["status"] == "Q221_R6_HEAD_REDIRECT_BLOCKED"
    assert receipt["source_probe"]["request_count"] == 1
    assert receipt["source_probe"]["responses"][0]["http_status"] == 302
    assert receipt["source_probe"]["response_body_read_bytes"] == 0


def test_r6_source_contract_keeps_gates_closed_and_does_not_allow_get():
    marker = (ROOT / diag.REQUEST_PATH).read_text(encoding="utf-8")
    assert "HTTP_METHOD=HEAD" in marker
    assert "ARCHIVE_REPLAY_GET_ALLOWED=false" in marker
    assert "RESPONSE_BODY_BYTES_READ=0" in marker
    assert diag.EXPECTED_SAFETY["paper_only"] is True
    assert all(diag.EXPECTED_SAFETY[key] is False for key in (
        "scientific_evidence", "performance_authorization", "holdout_selection",
        "ranking", "tuning", "promotion", "live_execution",
        "archive_payload_download_allowed", "archive_schema_examined", "transaction_row_presence_examined",
    ))
