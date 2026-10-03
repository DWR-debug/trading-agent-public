from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_q171_warc_reconstruction_is_boundary_only():
    text = (ROOT / "automation/q171_webstate_warc_reconstruction.py").read_text(encoding="utf-8")
    assert "Range" in text
    assert "WARC-Date" in text
    assert "WARC-Target-URI" in text
    assert "payload_digest_matches_index" in text
    assert '"performance": False' in text
    assert '"live_execution": False' in text


def test_q171_warc_reconstruction_has_no_return_logic():
    text = (ROOT / "automation/q171_webstate_warc_reconstruction.py").read_text(encoding="utf-8").lower()
    assert "drawdown" not in text
    assert "profit" not in text
    assert "p&l" not in text


def test_q171_warc_infra_blocks_are_explicit_and_do_not_become_missing_data():
    text = (ROOT / "automation/q171_webstate_warc_reconstruction.py").read_text(encoding="utf-8")
    assert '"INFRA_ACCESS_BLOCKED"' in text
    assert "urllib.error.HTTPError" in text
    assert "error_body_excerpt" in text
    assert 'item["status"] not in {"WARC_RECONSTRUCTED", "INFRA_ACCESS_BLOCKED"}' in text
