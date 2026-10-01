from automation.q114_13f_manager_transitions import (
    canonical_security_key, compile_transitions, deduplicate_positions, synthetic_contract
)

def test_q114_synthetic_contract():
    assert all(synthetic_contract().values())

def test_q114_conflicting_duplicate_fails():
    rows=[
      {"manager_cik":"1","accession":"A","acceptance_datetime":"2026-01-01T00:00:00+00:00","period_of_report":"2025-12-31","name_of_issuer":"A","title_of_class":"Common","cusip":"123456789","shares":"1","reported_value":"1"},
      {"manager_cik":"1","accession":"A","acceptance_datetime":"2026-01-01T00:00:00+00:00","period_of_report":"2025-12-31","name_of_issuer":"A","title_of_class":"Common","cusip":"123456789","shares":"2","reported_value":"1"}
    ]
    try:
        deduplicate_positions(rows)
    except ValueError as exc:
        assert str(exc).startswith("Q114_POSITION_CONFLICT")
    else:
        raise AssertionError("conflicting position duplicate must fail")
