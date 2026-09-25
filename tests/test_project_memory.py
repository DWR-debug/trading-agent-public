import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_project_memory_contains_urgency_success_pressure_chain():
    memory = json.loads(
        (ROOT / "research" / "evidence" / "project_memory_checkpoint.json").read_text(
            encoding="utf-8"
        )
    )
    model = memory["urgency_success_pressure_model"]

    assert model["context"] == ["family_urgency", "no_available_capital"]
    assert model["causal_chain"] == [
        "family_urgency + no_available_capital",
        "higher_perceived_success_pressure",
        "higher_risk_of_time_pressure_risk_seeking_overfitting_premature_selection_or_scientific_shortcuts",
    ]
    assert "never_relax_gates_or_increase_live_financial_risk_due_to_pressure" in model[
        "system_response"
    ]
    assert "More pressure -> more process discipline, not weaker evidence." == model[
        "principle"
    ]


def test_project_memory_binds_deadline_and_courage_rule():
    memory = json.loads(
        (ROOT / "research" / "evidence" / "project_memory_checkpoint.json").read_text(
            encoding="utf-8"
        )
    )

    assert memory["anchored_milestone"]["deadline"] == "2026-10-25"
    assert memory["courage_curve"]["current_level"] == "M2"
    assert memory["courage_curve"]["current_multiplier"] == 4
    assert "never increases courage level by itself" in memory["courage_curve"][
        "promotion_rule"
    ]
