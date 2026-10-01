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


def test_q114_amendment_is_preserved_and_cutoff_controls_visibility():
    from datetime import datetime, timezone
    from automation.q114_13f_manager_transitions import latest_position_as_of
    rows=[
      {"manager_cik":"1","accession":"ORIG","acceptance_datetime":"2026-05-01T10:00:00+00:00","period_of_report":"2026-03-31","name_of_issuer":"A","title_of_class":"Common","cusip":"123456789","shares":"100","reported_value":"10000"},
      {"manager_cik":"1","accession":"AMEND","acceptance_datetime":"2026-05-10T10:00:00+00:00","period_of_report":"2026-03-31","name_of_issuer":"A","title_of_class":"Common","cusip":"123456789","shares":"120","reported_value":"12000"}
    ]
    early=latest_position_as_of(rows, datetime(2026,5,5,tzinfo=timezone.utc))
    late=latest_position_as_of(rows, datetime(2026,5,11,tzinfo=timezone.utc))
    assert early[0].accession=="ORIG" and early[0].shares == 100
    assert late[0].accession=="AMEND" and late[0].shares == 120
