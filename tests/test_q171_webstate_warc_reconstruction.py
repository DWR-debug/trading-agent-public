import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_q171_warc_infra_classification_is_explicit():
    text=(ROOT/"automation/q171_webstate_warc_reconstruction.py").read_text(encoding="utf-8")
    assert '"INFRA_ACCESS_BLOCKED"' in text
    assert "urllib.error.HTTPError" in text
    assert '"error_body_excerpt"' in text

def test_q171_warc_persist_has_no_performance_boundary_changes():
    text=(ROOT/"automation/q171_warc_persist.py").read_text(encoding="utf-8")
    assert "source_commit" in text
    assert "results" in text
    assert "receipt_fingerprint" in text
    for marker in ("performance","holdout_selection","candidate_ranking","promotion","live_execution"):
        assert marker in text

def test_q171_persisted_evidence_path_is_not_a_trigger_path():
    wf=(ROOT/".github/workflows/deep-frontier-source-feasibility.yml").read_text(encoding="utf-8")
    assert "research/evidence/q171_warc_reconstruction_latest.json" not in wf.split("paths:",1)[1].split("permissions:",1)[0]