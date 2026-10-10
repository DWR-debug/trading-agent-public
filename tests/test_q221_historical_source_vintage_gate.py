import json
from pathlib import Path

from automation import q221_historical_source_vintage_gate as gate


MARKER_TEXT = (
    "Frequency of Updates to Prime Award Data for Contracts within five days. "
    "Contract award or modification. Three business days to FPDS. "
    "Made available to USAspending.gov on the following morning. "
    "Automatically published to the website the day after that. "
    "DOD and USACE data are delayed 90 days. FAR contract award within 30 days."
)


def test_q221_historical_vintage_gate_reconstructs_bounded_archived_policy_without_claiming_event_pit(tmp_path, monkeypatch):
    cdx_rows = [["timestamp", "original", "mimetype", "statuscode", "digest", "length"]]
    stamps = ["20241229000000", "20250629000000", "20251229000000", "20260629000000", "20261001000000"]
    for i, stamp in enumerate(stamps):
        cdx_rows.append([stamp, gate.ORIGINAL_URL, "application/pdf", "200", f"DIGEST{i}", "128000"])
    cdx_body = json.dumps(cdx_rows).encode("utf-8")

    def fake_fetch(url: str, limit: int):
        if url.startswith(gate.CDX_ENDPOINT):
            return 200, "application/json", cdx_body
        if "/web/" in url and "id_/" in url:
            return 200, "application/pdf", b"fake-pdf-" + url.encode("utf-8")
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(gate, "fetch", fake_fetch)
    monkeypatch.setattr(gate, "extract_pdf_text", lambda _body: MARKER_TEXT)
    path = tmp_path / "q221-vintage.json"
    result = gate.run(path)

    assert result["status"] == "Q221_HISTORICAL_POLICY_VINTAGES_RECONSTRUCTED"
    assert result["all_target_windows_covered"] is True
    assert result["policy_markers_consistent_across_vintages"] is True
    assert result["historical_policy_vintages_reconstructed"] is True
    assert result["historical_applicability_proven"] is False
    assert result["award_level_public_boundary_proven"] is False
    assert result["transaction_semantics_frozen"] is False
    assert result["recipient_to_issuer_mapping_frozen"] is False
    assert result["performance_authorization"] is False
    assert result["live_execution"] is False
    assert len(result["capture_rows"]) == len(gate.TARGETS)
    assert path.is_file()
    assert len(result["receipt_fingerprint"]) == 64


def test_q221_historical_vintage_gate_fails_closed_when_a_target_window_is_missing(tmp_path, monkeypatch):
    cdx_rows = [["timestamp", "original", "mimetype", "statuscode", "digest", "length"]]
    cdx_rows += [
        ["20250629000000", gate.ORIGINAL_URL, "application/pdf", "200", "DIGESTA", "100"],
        ["20261001000000", gate.ORIGINAL_URL, "application/pdf", "200", "DIGESTB", "100"],
    ]
    cdx_body = json.dumps(cdx_rows).encode("utf-8")

    def fake_fetch(url: str, limit: int):
        if url.startswith(gate.CDX_ENDPOINT):
            return 200, "application/json", cdx_body
        return 200, "application/pdf", b"fake-pdf"

    monkeypatch.setattr(gate, "fetch", fake_fetch)
    monkeypatch.setattr(gate, "extract_pdf_text", lambda _body: MARKER_TEXT)
    result = gate.run(tmp_path / "blocked.json")

    assert result["status"] == "Q221_HISTORICAL_POLICY_VINTAGE_COVERAGE_INCOMPLETE_OR_SEMANTICS_DRIFT"
    assert result["historical_policy_vintages_reconstructed"] is False
    assert result["performance_authorization"] is False
    assert result["live_execution"] is False


def test_q221_cdx_parser_ignores_malformed_rows():
    rows = [
        ["timestamp", "original", "mimetype", "statuscode", "digest", "length"],
        ["20261001000000", gate.ORIGINAL_URL, "application/pdf", "200", "D1", "100"],
        ["bad", gate.ORIGINAL_URL, "application/pdf", "200", "D2", "100"],
        ["20261001000000", "https://example.invalid/file.pdf", "application/pdf", "200", "D3", "100"],
    ]
    assert len(gate.parse_cdx(json.dumps(rows).encode("utf-8"))) == 1
