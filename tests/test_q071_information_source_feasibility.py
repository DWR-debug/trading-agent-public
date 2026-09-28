import json
from pathlib import Path


DESIGN = Path(
    "research/exploration/q071_information_source_feasibility_2026_09_28.json"
)
DOC = Path(
    "docs/research_design/Q071-orthogonal-information-source-feasibility-2026-09-28.md"
)


def test_q071_is_design_only_and_ungrounded_for_performance():
    payload = json.loads(DESIGN.read_text(encoding="utf-8"))
    assert payload["status"] == "DESIGN_ONLY"
    assert len(payload["candidates"]) == 6
    assert [c["id"] for c in payload["candidates"]] == ["I1", "I2", "I3", "I4", "I5", "I6"]
    assert payload["governance"]["performance_trial_authorized"] is False
    assert payload["governance"]["no_family_ranking"] is True
    assert payload["governance"]["fresh_disjoint_validation_required"] is True
    assert payload["governance"]["coverage_before_pit"] is True
    assert payload["governance"]["pit_before_performance"] is True
    assert payload["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }


def test_q071_documents_match_design_scope():
    text = DOC.read_text(encoding="utf-8")
    assert "DESIGN_ONLY" in text
    for family in (
        "FINRA Reg SHO",
        "SEC Form 4",
        "ALFRED",
        "CFTC",
        "Wikimedia",
        "GDELT",
    ):
        assert family in text
    assert "No candidate is ranked" in text
    assert "No holdout selection" in text
