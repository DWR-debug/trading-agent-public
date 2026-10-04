from __future__ import annotations

import json
from pathlib import Path

from automation.s10_mechanical_research_qa import SAFETY, main

ROOT = Path(__file__).resolve().parents[1]

def test_s10_mechanical_qa_is_non_authorizing():
    source = (ROOT / "automation/s10_mechanical_research_qa.py").read_text(encoding="utf-8")
    for marker in ("S10_MECHANICAL_QA_PASSED", "performance", "holdout_selection", "live_execution"):
        assert marker in source

def test_s10_mechanical_qa_checks_candidate_inventories(tmp_path, monkeypatch):
    out = tmp_path / "receipt.json"
    monkeypatch.setenv("GITHUB_SHA", "abc123")
    monkeypatch.setenv("RUNNER_NAME", "S10-test")
    monkeypatch.setattr(
        "sys.argv",
        [
            "s10_mechanical_research_qa",
            "--repo-root",
            str(ROOT),
            "--output",
            str(out),
        ],
    )
    assert main() == 0
    receipt = json.loads(out.read_text(encoding="utf-8"))
    assert receipt["status"] == "S10_MECHANICAL_QA_PASSED"
    assert receipt["safety"] == SAFETY
    assert receipt["scientific_boundary"]["performance"] is False
