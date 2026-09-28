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
        lambda spec, output_root: {
            "status": "COVERAGE_PASSED",
            "snapshot_fingerprint": "snapshot-fp",
            "coverage": {"common_calendar_count": q089.TARGET},
        },
    )

    result = q089.coverage()
    assert result["selected"] == q089.CANDIDATE_POOL[:8]
    assert (tmp_path / "research" / "evidence" / "q089_coverage_result.json").exists()
