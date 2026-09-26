import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_decision_basis_is_current_and_separates_fact_from_next_action():
    md = (ROOT / "docs" / "DECISION_BASIS.md").read_text(encoding="utf-8")
    payload = json.loads(
        (ROOT / "research" / "evidence" / "decision_basis_latest.json").read_text(
            encoding="utf-8"
        )
    )
    assert "Was wissen wir?" in md
    assert "Was wissen wir nicht?" in md
    assert "Nächste Aktion" in md
    assert payload["current_stage"] == "Q020_PERFORMANCE_COMPLETED"
    assert payload["next_action"].startswith("Create a separate immutable Q020 performance authorization")
    assert payload["invariants"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
