from __future__ import annotations

import json
from pathlib import Path

from automation.candidate_robustness_gate import validate_candidate
from automation.q185_q186_source_feasibility import mutation_checks as source_mutations
from automation.q185_q186_pit_readiness_r1 import mutation_checks as pit_mutations

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "research/frontier/q185_q186_candidate_wave_2026_10_04.json"


def test_q185_q186_inventory_contracts_are_pre_formal() -> None:
    payload = json.loads(INVENTORY.read_text(encoding="utf-8"))
    assert payload["priority"] == "A"
    ids = {item["id"] for item in payload["candidates"]}
    assert ids == {"Q185", "Q186"}
    for candidate in payload["candidates"]:
        result = validate_candidate(candidate, INVENTORY.as_posix())
        assert result["status"] == "PRE_FORMAL_ROBUSTNESS_COMPLETED"
        assert result["formalization_allowed"] is False
        assert result["performance_authorization"] is False


def test_source_mutations_are_fail_closed() -> None:
    assert all(source_mutations().values())


def test_pit_mutations_are_fail_closed() -> None:
    assert all(pit_mutations().values())


def test_no_candidate_has_performance_fields() -> None:
    payload = json.loads(INVENTORY.read_text(encoding="utf-8"))
    forbidden = {
        "performance", "performance_rank", "candidate_rank", "return",
        "returns", "pnl", "drawdown", "winner", "selected",
        "holdout_selection", "performance_authorization",
    }
    for candidate in payload["candidates"]:
        assert not (forbidden & candidate.keys())



def test_windows_reproduction_is_separate_and_fork_guarded():
    from pathlib import Path
    main = Path(".github/workflows/q185-q186-source-feasibility.yml").read_text(encoding="utf-8")
    windows = Path(".github/workflows/q185-q186-windows-reproduction.yml").read_text(encoding="utf-8")
    assert "windows_reproduction:" not in main
    assert "self-hosted" not in main
    assert "self-hosted" in windows
    assert "github.event.pull_request.head.repo.full_name == github.repository" in windows
    assert "continue-on-error: true" not in windows
