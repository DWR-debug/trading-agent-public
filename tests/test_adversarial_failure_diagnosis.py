import json
from pathlib import Path

from automation.adversarial_failure_diagnosis import diagnose


def test_t040_diagnosis_is_non_selective_and_broad_negative():
    evidence = Path(
        "research/evidence/trial_040_network_momentum_repair_2026_09_24.json"
    )
    report = diagnose(evidence)

    assert report["status"] == "DIAGNOSTIC_ONLY"
    assert report["diagnosis_class"] == (
        "broad_negative_with_control_deterioration"
    )
    assert report["failed_gate_count"] >= 10
    assert report["baseline_delta"]["research_return_vs_control"] < 0.0
    assert report["baseline_delta"]["holdout_return_vs_control"] < 0.0
    assert report["safety"]["paper_only"] is True
    assert report["safety"]["live_trading_enabled"] is False
    assert report["safety"]["automatic_promotion"] is False
    assert "no_holdout_selection" in report["non_actions"]


def test_diagnosis_fingerprint_is_deterministic_for_same_evidence(tmp_path):
    evidence = Path(
        "research/evidence/trial_040_network_momentum_repair_2026_09_24.json"
    )
    first = diagnose(evidence)
    second = diagnose(evidence)
    assert first["fingerprint"] == second["fingerprint"]
    assert first["source"]["report_fingerprint"] == (
        "912d51447862ba7118dacde2f8acba6c3cce407adec64ea10cbf3aa48661bb65"
    )
