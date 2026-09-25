from pathlib import Path

from automation.cross_trial_failure_diagnosis import diagnose, diagnose_current


def test_cross_trial_diagnosis_is_bound_to_fixed_historical_set():
    result = diagnose(
        Path("research/evidence/trial_ledger.json")
    )
    assert result["status"] == "DIAGNOSTIC_ONLY"
    assert [t["trial_id"] for t in result["trial_summaries"]] == [
        "T-2026-09-24-022",
        "T-2026-09-24-023",
        "T-2026-09-24-025",
        "T-2026-09-24-027",
        "T-2026-09-24-028",
    ]
    assert result["salvageable_observations"]["t028_per_sleeve_volatility_budget"] is True
    assert "no_holdout_selection" in result["non_actions"]


def test_cross_trial_diagnosis_fingerprint_is_deterministic():
    result1 = diagnose(Path("research/evidence/trial_ledger.json"))
    result2 = diagnose(Path("research/evidence/trial_ledger.json"))
    assert result1["fingerprint"] == result2["fingerprint"]
    assert result1["next_research_question"].startswith(
        "Before another return-generating strategy family"
    )


def test_current_cross_trial_diagnosis_covers_t041_to_t045():
    result = diagnose_current(Path("research/evidence/trial_ledger.json"))
    assert result["status"] == "DIAGNOSTIC_ONLY"
    assert result["source"]["trial_ids"] == [
        "T-2026-09-24-041",
        "T-2026-09-24-042",
        "T-2026-09-25-043",
        "T-2026-09-25-044",
        "T-2026-09-25-045",
    ]
    assert result["source"]["performance_valid_trial_count"] == 4
    assert result["source"]["data_invalid_trial_count"] == 1

    summaries = {item["trial_id"]: item for item in result["trial_summaries"]}
    assert "research_risk_gate" in summaries["T-2026-09-25-044"]["failure_modes"]
    assert summaries["T-2026-09-25-043"]["failure_modes"] == [
        "data_validity_failure"
    ]

    patterns = result["cross_trial_patterns_by_id"]
    assert patterns["research_risk_gate_recurrence"] == [
        "T-2026-09-24-041",
        "T-2026-09-24-042",
        "T-2026-09-25-044",
        "T-2026-09-25-045",
    ]
    assert patterns["risk_gate_any_stage_recurrence"] == patterns[
        "research_risk_gate_recurrence"
    ]
    assert patterns["oos_stability_recurrence"] == [
        "T-2026-09-24-041",
        "T-2026-09-24-042",
        "T-2026-09-25-045",
    ]
    assert patterns["control_relative_non_deterioration_recurrence"] == [
        "T-2026-09-24-041",
        "T-2026-09-24-042",
        "T-2026-09-25-044",
        "T-2026-09-25-045",
    ]
    assert patterns["data_validity_failure"] == ["T-2026-09-25-043"]
    assert patterns["positive_holdout_not_sufficient"] == [
        "T-2026-09-24-041",
        "T-2026-09-24-042",
        "T-2026-09-25-044",
        "T-2026-09-25-045",
    ]

    assert result["interpretation"]["research_risk_gate_recurrence_count"] == 4
    assert result["interpretation"]["oos_stability_recurrence_count"] == 3
    assert result["interpretation"][
        "control_relative_non_deterioration_count"
    ] == 4
    assert result["interpretation"]["positive_holdout_count"] == 4
    assert "orthogonal information/alpha mechanism" in result[
        "next_research_question"
    ]
