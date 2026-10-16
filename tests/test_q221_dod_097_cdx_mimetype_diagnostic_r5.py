from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from automation import q221_dod_097_wayback_cdx_mimetype_diagnostic_r5 as diag

ROOT = Path(__file__).resolve().parents[1]


def _cdx_body(mimetype="application/zip"):
    payload = [
        ["timestamp", "original", "mimetype", "statuscode", "digest", "length"],
        [diag.CAPTURE_TIMESTAMP, diag.ARCHIVE_URL, mimetype, "200", diag.CDX_SHA1_BASE32, str(diag.CDX_LENGTH)],
    ]
    return json.dumps(payload).encode("utf-8")


def _minimal_repo(tmp_path):
    target = tmp_path / "repo"
    required = [
        diag.PREREG_PATH,
        diag.REQUEST_PATH,
        diag.R3_PREREG_PATH,
        diag.R3_REQUEST_PATH,
        diag.MANIFEST_PATH,
    ]
    for relative in required:
        source = ROOT / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    return target


def test_r5_prereg_and_marker_validate_offline_and_keep_28_key_manifest():
    result = diag.validate_inputs(ROOT)
    assert result["manifest_blob_sha1"] == diag.MANIFEST_BLOB
    assert result["target_count"] == 28
    assert result["request"]["MAX_REQUESTS"] == "1"
    assert result["request"]["ARCHIVE_REPLAY_REQUESTS_ALLOWED"] == "false"
    assert result["request"]["PER_REQUEST_TIMEOUT_SECONDS"] == "60"


def test_r5_marker_tampering_fails_closed(tmp_path):
    repo = _minimal_repo(tmp_path)
    marker_path = repo / diag.REQUEST_PATH
    marker_path.write_text(
        marker_path.read_text(encoding="utf-8").replace(
            "PER_REQUEST_TIMEOUT_SECONDS=60", "PER_REQUEST_TIMEOUT_SECONDS=25"
        ),
        encoding="utf-8",
    )
    with pytest.raises(diag.DiagnosticError, match="marker differs from frozen request"):
        diag.validate_inputs(repo)


def test_r5_query_adds_only_mimetype_and_never_builds_archive_replay_url():
    url = diag.build_cdx_url()
    assert url.startswith("https://web.archive.org/cdx/search/cdx?")
    assert "mimetype" in url
    assert "statuscode%3A200" in url
    assert "original%3A.%2A097.%2AContracts.%2Azip" in url
    assert "from=2019" in url and "to=2026" in url and "limit=100" in url
    assert "q221_dod_097_wayback_archive_presence_latest" not in url
    assert "FY2025_097_Contracts_Full_20250106.zip" not in url


def test_r5_single_cdx_request_records_mimetype_and_does_not_fetch_archive(monkeypatch, tmp_path):
    captured = {}
    body = _cdx_body("application/zip")

    class FakeResponse:
        status = 200
        headers = {"Content-Type": "application/json", "Content-Length": str(len(body)), "Content-Encoding": "identity"}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            captured["read_limit"] = limit
            return body

    class FakeOpener:
        def open(self, request, timeout):
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            return FakeResponse()

    monkeypatch.setattr(diag.urllib.request, "build_opener", lambda *handlers: FakeOpener())
    output = tmp_path / "receipt.json"
    receipt = diag.run_diagnostic(ROOT, output_path=output)
    assert receipt["status"] == "Q221_DOD_097_CDX_MIMETYPE_DIAGNOSTIC_COMPLETE"
    assert receipt["cdx_inventory"]["target_capture"]["mimetype"] == "application/zip"
    assert receipt["source_probe"]["request_count"] == 1
    assert receipt["source_probe"]["archive_replay_request_count"] == 0
    assert receipt["source_probe"]["archive_payload_downloaded"] is False
    assert captured["timeout"] == 60
    assert captured["read_limit"] == diag.MAX_CDX_BYTES + 1
    assert captured["url"] == diag.build_cdx_url()
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["receipt_fingerprint"] == receipt["receipt_fingerprint"]
    assert receipt["safety"]["live_trading_enabled"] is False


def test_r5_revisit_mimetype_is_reported_as_metadata_not_row_evidence(monkeypatch, tmp_path):
    body = _cdx_body("warc/revisit")

    class FakeResponse:
        status = 200
        headers = {"Content-Type": "application/json"}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            return body

    class FakeOpener:
        def open(self, request, timeout):
            return FakeResponse()

    monkeypatch.setattr(diag.urllib.request, "build_opener", lambda *handlers: FakeOpener())
    receipt = diag.run_diagnostic(ROOT, output_path=tmp_path / "receipt.json")
    assert receipt["status"] == "Q221_DOD_097_CDX_MIMETYPE_DIAGNOSTIC_COMPLETE"
    assert receipt["cdx_inventory"]["mimetype_class"] == "warc_revisit"
    assert receipt["interpretation"]["transaction_row_presence_examined"] is False
    assert receipt["safety"]["scientific_evidence"] is False


def test_r5_response_cap_is_fail_closed_with_a_fingerprinted_receipt(monkeypatch, tmp_path):
    body = b"x" * (diag.MAX_CDX_BYTES + 1)

    class FakeResponse:
        status = 200
        headers = {"Content-Type": "application/json"}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            return body[:limit]

    class FakeOpener:
        def open(self, request, timeout):
            return FakeResponse()

    monkeypatch.setattr(diag.urllib.request, "build_opener", lambda *handlers: FakeOpener())
    output = tmp_path / "receipt.json"
    receipt = diag.run_diagnostic(ROOT, output_path=output)
    assert receipt["status"] == "Q221_DOD_097_CDX_DIAGNOSTIC_RESPONSE_CAP_EXCEEDED"
    assert receipt["source_probe"]["request_count"] == 1
    assert receipt["source_probe"]["response_bytes"] == diag.MAX_CDX_BYTES + 1
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["receipt_fingerprint"] == diag.fingerprint(written)


def test_r5_diagnostics_persist_error_receipt_on_transport_timeout(monkeypatch, tmp_path):
    def fail(url, state):
        state["request_count"] += 1
        state["transport_errors"].append("TimeoutError")
        raise diag.DiagnosticError("Q221_DOD_097_CDX_DIAGNOSTIC_TRANSPORT_ERROR", "TimeoutError")

    output = tmp_path / "receipt.json"
    receipt = diag.run_diagnostic(ROOT, output_path=output, fetcher=fail)
    assert receipt["status"] == "Q221_DOD_097_CDX_DIAGNOSTIC_TRANSPORT_ERROR"
    assert receipt["source_probe"]["request_count"] == 1
    assert receipt["safety"]["source_requests_made"] == 1
    assert receipt["receipt_fingerprint"] == diag.fingerprint(json.loads(output.read_text(encoding="utf-8")))


def test_r5_workflows_and_sync_keep_replay_and_scientific_gates_closed():
    wf = (ROOT / ".github/workflows/q221-dod-097-cdx-mimetype-diagnostic-r5.yml").read_text(encoding="utf-8")
    assert "research/run_requests/q221_dod_097_cdx_mimetype_diagnostic_r5.trigger" in wf
    assert "workflow_dispatch:" not in wf and "schedule:" not in wf
    assert "q221-dod-097-cdx-mimetype-diagnostic-r5.yml/runs" in wf
    assert "no archive replay" in wf.lower()
    assert "python -m automation.q221_dod_097_wayback_cdx_mimetype_diagnostic_r5" in wf
    assert (ROOT / "automation" / "q221_dod_097_wayback_cdx_mimetype_diagnostic_r5.py").is_file()
    assert "python -m automation.q221_dod_097_cdx_mimetype_diagnostic" not in wf
    sync = (ROOT / ".github/workflows/q221-dod-097-cdx-mimetype-diagnostic-r5-sync.yml").read_text(encoding="utf-8")
    assert "q221-dod-097-cdx-mimetype-diagnostic-r5.json" in sync
    assert "q221_dod_097_cdx_mimetype_diagnostic_r5_attempt_" in sync
    assert "github.event.workflow_run.head_branch == 'master'" in sync
    assert 'run_id = os.environ["SOURCE_RUN_ID"]' in sync
    assert 'attempt=evidence / f"q221_dod_097_cdx_mimetype_diagnostic_r5_attempt_{run_id}.json"' in sync
    assert 'attempt_file="research/evidence/q221_dod_097_cdx_mimetype_diagnostic_r5_attempt_${SOURCE_RUN_ID}.json"' in sync
    integrity = (ROOT / "automation/project_integrity_check.py").read_text(encoding="utf-8")
    assert '"q221-dod-097-cdx-mimetype-diagnostic-r5.yml"' in integrity
    assert '"q221-dod-097-cdx-mimetype-diagnostic-r5-sync.yml"' in integrity
