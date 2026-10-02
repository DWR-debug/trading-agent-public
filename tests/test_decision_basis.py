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
    assert "Übergeordnetes Ziel" in md
    assert "Aktuelle Evidenzgrenze" in md
    assert "Nächste Schritte" in md
    assert "Unveränderliche Grenzen" in md
    assert payload["schema_version"] == "2.1"
    assert payload["project_goal"]
    assert payload["next_action"]
    assert payload["safety"]["paper_only"] is True
    assert payload["safety"]["live_trading_enabled"] is False
    assert payload["safety"]["orders_enabled"] is False
    assert payload["safety"]["automatic_promotion"] is False
    assert payload["scientific_status"]["performance_authorization_allowed"] is False
    assert payload["scientific_status"]["promotion_allowed"] is False
