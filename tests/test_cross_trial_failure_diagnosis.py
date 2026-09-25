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
    assert result["trial_summaries"][-1]["trial_id"] == "T-2026-09-25-045"
    assert "data_validity_failure" in result["cross_trial_patterns_by_id"]
    assert "risk_gate_recurrence" in result["cross_trial_patterns_by_id"]
    assert "oos_stability_recurrence" in result["cross_trial_patterns_by_id"]
    assert result["next_research_question"].startswith(
        "Before reserving another performance trial"
    )
