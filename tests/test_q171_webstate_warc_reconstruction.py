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


def test_q171_warc_infra_classification_is_explicit():
    text = (ROOT / "automation/q171_webstate_warc_reconstruction.py").read_text(encoding="utf-8")
    assert '"INFRA_ACCESS_BLOCKED"' in text
    assert "urllib.error.HTTPError" in text
    assert '"error_body_excerpt"' in text


def test_q171_warc_persist_has_stable_material_receipt_shape():
    text = (ROOT / "automation/q171_warc_persist.py").read_text(encoding="utf-8")
    assert "source_commit" in text
    assert "results" in text
    assert "receipt_fingerprint" in text


def test_q171_persisted_evidence_path_does_not_trigger_deep_frontier():
    text = (ROOT / ".github/workflows/deep-frontier-source-feasibility.yml").read_text(encoding="utf-8")
    paths_section = text.split("paths:", 1)[1].split("permissions:", 1)[0]
    assert "research/evidence/q171_warc_reconstruction_latest.json" not in paths_section


def test_q171_persistence_uses_contents_publisher_not_worktree_switch():
    text = (ROOT / ".github/workflows/deep-frontier-source-feasibility.yml").read_text(encoding="utf-8")
    persist = text.split("Persist material Q171 WARC receipt", 1)[1].split("Upload source-feasibility receipt", 1)[0]
    assert "automation/github_contents_publish.py" in persist
    assert "git checkout --detach origin/master" not in persist
