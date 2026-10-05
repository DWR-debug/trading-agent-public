from __future__ import annotations

import json
from pathlib import Path

from automation.s10_adaptive_mechanical_research_qa import MODES, main

ROOT = Path(__file__).resolve().parents[1]


def test_s10_adaptive_modes_are_bounded():
    assert len(MODES) == 5
    assert len(set(MODES)) == 5


def test_s10_adaptive_qa_passes_locally(tmp_path, monkeypatch):
    out = tmp_path / "receipt.json"
    monkeypatch.setenv("GITHUB_SHA", "test-sha")
    monkeypatch.setenv("RUNNER_NAME", "S10-test")
    monkeypatch.setenv("RUNNER_ARCH", "ARM64")
    monkeypatch.setenv("GITHUB_RUN_NUMBER", "1")
    monkeypatch.setattr(
        "sys.argv",
        [
            "s10_adaptive_mechanical_research_qa",
            "--repo-root",
            str(ROOT),
            "--output",
            str(out),
        ],
    )
    assert main() == 0
    receipt = json.loads(out.read_text(encoding="utf-8"))
    assert receipt["status"] == "S10_ADAPTIVE_QA_PASSED"
    assert receipt["scientific_boundary"]["performance"] is False
    assert receipt["scientific_boundary"]["live_execution"] is False
