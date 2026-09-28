from __future__ import annotations

from automation.q069_candidate_bank import CANDIDATES, MIN_HISTORY_INDEX
from automation.fixed_window_candidate_discovery import _prior_research_symbols

EXPECTED_CANDIDATES = (
    "C7_LOW_MAX_21",
    "C8_LOW_IDIO_VOL_273",
    "C9_LONG_TERM_REVERSAL_756",
    "C10_TREND_EFFICIENCY_63",
    "C11_VOLUME_CONFIRMED_TREND_126",
)


def test_q089_candidate_bank_is_exact_q069() -> None:
    assert CANDIDATES == EXPECTED_CANDIDATES


def test_q089_history_contract_is_unchanged() -> None:
    assert MIN_HISTORY_INDEX["C7_LOW_MAX_21"] == 21
    assert MIN_HISTORY_INDEX["C8_LOW_IDIO_VOL_273"] == 273
    assert MIN_HISTORY_INDEX["C9_LONG_TERM_REVERSAL_756"] == 756
    assert MIN_HISTORY_INDEX["C10_TREND_EFFICIENCY_63"] == 63
    assert MIN_HISTORY_INDEX["C11_VOLUME_CONFIRMED_TREND_126"] == 146


def test_global_prior_research_exclusion_is_available() -> None:
    used = _prior_research_symbols()
    assert isinstance(used, set)

def test_q089_coverage_entrypoint_does_not_require_undefined_input_bundle(tmp_path, monkeypatch) -> None:
    import automation.q089_coverage_pit as q089

    monkeypatch.setattr(q089, "ROOT", tmp_path)
    monkeypatch.setattr(
        q089,
        "run_discovery",
        lambda **_: {"selected_coverage_batch": tuple(q089.CANDIDATE_POOL[:8]), "fingerprint": "disc-fp"},
    )
    monkeypatch.setattr(
        q089,
        "snapshot_from_preregistration",
        lambda spec, output_root, **kwargs: {
            "status": "COVERAGE_PASSED",
            "snapshot_fingerprint": "snapshot-fp",
            "coverage": {"common_calendar_count": q089.TARGET},
        },
    )

    result = q089.coverage()
    assert result["selected"] == q089.CANDIDATE_POOL[:8]
    assert (tmp_path / "research" / "evidence" / "q089_coverage_result.json").exists()


def test_q089_preregister_builds_result_fingerprint_receipt(monkeypatch, tmp_path):
    import json
    import automation.q089_coverage_pit as q089

    monkeypatch.setattr(q089, "ROOT", tmp_path)
    evidence = tmp_path / "research" / "evidence"
    preregs = tmp_path / "research" / "preregistrations"
    governance = tmp_path / "research" / "governance"
    for path in (evidence, preregs, governance, tmp_path / "automation", tmp_path / "execution", tmp_path / "config"):
        path.mkdir(parents=True, exist_ok=True)

    (evidence / "q089_coverage_result.json").write_text(
        json.dumps({
            "trial_id": q089.COVERAGE_ID,
            "status": "COVERAGE_PASSED",
            "result_fingerprint": "coverage-fp",
            "snapshot_fingerprint": "snapshot-fp",
            "source_discovery": {"fingerprint": "discovery-fp"},
        }),
        encoding="utf-8",
    )
    (evidence / "q089_pit_result.json").write_text(
        json.dumps({
            "trial_id": q089.PIT_ID,
            "status": "PIT_PASSED",
            "result_fingerprint": "pit-fp",
        }),
        encoding="utf-8",
    )
    (evidence / "q089_input_freeze_result.json").write_text(
        json.dumps({
            "trial_id": q089.INPUT_ID,
            "status": "INPUT_BUNDLE_FROZEN",
            "bundle_fingerprint": "bundle-fp",
        }),
        encoding="utf-8",
    )
    freeze = {
        "schema_version": "1.0",
        "trial_id": q089.COVERAGE_ID,
        "status": "COVERAGE_PASSED",
        "symbols": list(("AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH")),
    }
    (evidence / "q089_asset_freeze.json").write_text(json.dumps(freeze), encoding="utf-8")

    registry = {
        "schema_version": 1,
        "name": "active_research_registry",
        "policy": {"only_listed_performance_trials_may_be_authorized": True},
        "active_trials": [{
            "code": "089",
            "trial_id": None,
            "class": "fresh_validation",
            "state": "PLANNED",
            "performance_authorization_allowed": False,
        }],
    }
    (governance / "active_research_registry.json").write_text(json.dumps(registry), encoding="utf-8")

    for path in (
        tmp_path / "automation/q089_performance.py",
        tmp_path / "automation/q069_candidate_bank.py",
        tmp_path / "execution/cost_contract.py",
        tmp_path / "config/settings.py",
    ):
        path.write_text("fixture", encoding="utf-8")

    prereg = q089.preregister()
    coverage_receipt = next(
        item for item in prereg["identity_contract"]["required_receipts"]
        if item["role"] == "coverage"
    )
    assert coverage_receipt["fingerprint_key"] == "result_fingerprint"
    assert coverage_receipt["expected_data_contract_key"] == "coverage_result_fingerprint"
