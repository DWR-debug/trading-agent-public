from datetime import date

import pytest

from automation.q104_i22_independent_pit_reproduction import (
    END, FORMS, START, WINDOW, compile_population, receipt_fingerprint, reference_prefix, columnar_rows,
    validate_q107_policy_flags,
    validate_reproduction_code_sha,
)


def rows():
    return [
        {"form": "8-K", "filingDate": "2015-12-30", "acceptanceDateTime": "2015-12-30T18:00:00Z", "accessionNumber": "A1"},
        {"form": "8-K/A", "filingDate": "2015-12-31", "acceptanceDateTime": "2015-12-31T18:00:00Z", "accessionNumber": "A2"},
        {"form": "10-Q", "filingDate": "2020-12-30", "acceptanceDateTime": "2020-12-30T18:00:00Z", "accessionNumber": "A3"},
        {"form": "13F-HR", "filingDate": "2020-12-30", "acceptanceDateTime": "2020-12-30T18:00:00Z", "accessionNumber": "EXCLUDED-FORM"},
        {"form": "10-K", "filingDate": "2025-12-01", "acceptanceDateTime": "2025-12-01T18:00:00Z", "accessionNumber": "AFTER-END"},
    ]


def test_independent_compiler_uses_fixed_forms_and_cutoff():
    output = compile_population(rows(), date(2021, 1, 5))
    assert output["filing_count"] == 3
    assert {item["accession"] for item in output["events"]} == {"A1", "A2", "A3"}
    assert {item["form"] for item in output["events"]}.issubset(FORMS)
    assert output["decision_session_count"] == len(output["arrival_density_20"])


def test_future_acceptance_cannot_mutate_an_earlier_prefix():
    cutoff = date(2020, 12, 31)
    before = compile_population(rows(), cutoff)
    future = {"form": "8-K", "filingDate": "2021-01-04", "acceptanceDateTime": "2021-01-04T12:00:00Z", "accessionNumber": "FUTURE"}
    assert compile_population(rows() + [future], cutoff) == before


def test_input_order_invariance():
    assert compile_population(rows(), END) == compile_population(list(reversed(rows())), END)


def test_prefix_projection_matches_direct_cutoff_compile():
    full = compile_population(rows(), END)
    for cutoff in (date(2015, 12, 31), date(2020, 12, 31), END):
        assert compile_population(rows(), cutoff) == reference_prefix(full, cutoff)


def test_columnar_rows_do_not_invent_missing_acceptance_clock():
    payload = {"form": ["8-K", "10-Q"], "filingDate": ["2020-01-02", "2020-04-03"], "accessionNumber": ["A", "B"]}
    result = columnar_rows(payload, filter_window=True)
    assert len(result) == 2
    assert result[0]["acceptanceDateTime"] is None
    assert result[1]["acceptanceDateTime"] is None


def test_receipt_fingerprint_detects_mutation():
    payload = {"status": "REVIEW_ONLY", "count": 8}
    fp = receipt_fingerprint(payload)
    assert receipt_fingerprint({**payload, "receipt_fingerprint": fp}) == fp
    assert receipt_fingerprint({**payload, "count": 9, "receipt_fingerprint": fp}) != fp


def test_fixed_contract_constants_are_not_performance_authority():
    assert START == date(2011, 1, 1)
    assert END == date(2025, 9, 24)
    assert WINDOW == 20


def q107_policy_objects():
    false_receipt_flags = {
        "performance_evaluation": False,
        "oos_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "holdout_used_for_selection": False,
    }
    safety = {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    q107 = {
        **false_receipt_flags,
        "scientific_outcome": "COVERAGE_PASSED_NO_PERFORMANCE_EVIDENCE",
        "safety": dict(safety),
    }
    manifest = {
        "governance": {
            **false_receipt_flags,
            "performance_trial_authorized": False,
            "automatic_promotion": False,
        },
        "safety": dict(safety),
    }
    return q107, manifest


def test_q107_policy_flags_are_read_from_their_actual_schema_locations():
    q107, manifest = q107_policy_objects()
    # q107_coverage_result.json has top-level policy flags, while the canonical
    # snapshot manifest nests the matching flags under governance.
    assert "governance" not in q107
    validate_q107_policy_flags(q107, manifest)


def test_q107_receipt_policy_gate_fails_closed_when_top_level_flag_is_true():
    q107, manifest = q107_policy_objects()
    q107["holdout_evaluation"] = True
    with pytest.raises(RuntimeError, match="Q107_GOVERNANCE_GATE_MISMATCH"):
        validate_q107_policy_flags(q107, manifest)


def test_q107_manifest_policy_gate_fails_closed_when_promotion_is_enabled():
    q107, manifest = q107_policy_objects()
    manifest["governance"]["automatic_promotion"] = True
    with pytest.raises(RuntimeError, match="Q107_MANIFEST_GOVERNANCE_GATE_MISMATCH"):
        validate_q107_policy_flags(q107, manifest)


def test_q107_safety_gates_fail_closed_for_either_frozen_input():
    q107, manifest = q107_policy_objects()
    manifest["safety"]["live_trading_enabled"] = True
    with pytest.raises(RuntimeError, match="Q107_MANIFEST_SAFETY_GATE_MISMATCH"):
        validate_q107_policy_flags(q107, manifest)



def test_reproduction_code_sha_requires_full_immutable_commit():
    assert validate_reproduction_code_sha("a" * 40) == "a" * 40
    with pytest.raises(ValueError):
        # argparse's argument type raises ArgumentTypeError, a ValueError subclass.
        validate_reproduction_code_sha("main")
