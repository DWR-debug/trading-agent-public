from __future__ import annotations
import json
from pathlib import Path
from automation.s10_adaptive_mechanical_research_qa import MODES, main
ROOT=Path(__file__).resolve().parents[1]
def test_modes_are_distinct_and_bounded():
    assert len(MODES)==5 and len(set(MODES))==5
def test_adaptive_qa_is_non_authorizing(tmp_path,monkeypatch):
    out=tmp_path/"receipt.json"
    monkeypatch.setenv("GITHUB_SHA","test")
    monkeypatch.setenv("RUNNER_NAME","S10-test")
    monkeypatch.setenv("RUNNER_ARCH","ARM64")
    monkeypatch.setenv("GITHUB_RUN_NUMBER","1")
    monkeypatch.setattr("sys.argv",["qa","--repo-root",str(ROOT),"--output",str(out)])
    assert main()==0
    r=json.loads(out.read_text())
    assert r["status"]=="S10_ADAPTIVE_QA_PASSED"
    assert r["scientific_boundary"]["performance"] is False


def test_negative_evidence_mode_uses_canonical_governance(monkeypatch, tmp_path):
    out = tmp_path / "receipt.json"
    monkeypatch.setenv("GITHUB_SHA", "test")
    monkeypatch.setenv("RUNNER_NAME", "S10-test")
    monkeypatch.setenv("RUNNER_ARCH", "ARM64")
    monkeypatch.setenv("GITHUB_RUN_NUMBER", "4")
    monkeypatch.setattr("sys.argv", ["qa", "--repo-root", str(ROOT), "--output", str(out)])
    assert main() == 0
    receipt = json.loads(out.read_text())
    assert receipt["mode"] == "NEGATIVE_EVIDENCE_DEDUP"
    assert receipt["status"] == "S10_ADAPTIVE_QA_PASSED"
