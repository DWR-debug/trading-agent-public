from automation.information_alpha_mechanism_discrimination_replication import (
    DEFAULT_END,
    DEFAULT_START,
    REFERENCE_END,
    REFERENCE_START,
    TASK_ID,
    _assert_temporal_disjointness,
)


def test_q016_window_is_exactly_one_year_and_precedes_q015():
    assert (DEFAULT_END - DEFAULT_START).days == 364
    assert (REFERENCE_END - REFERENCE_START).days == 364
    assert DEFAULT_END < REFERENCE_START
    assert TASK_ID == "Q-016-INFORMATION-ALPHA-MECHANISM-DISCRIMINATION-REPLICATION"


def test_q016_temporal_disjointness_guard():
    _assert_temporal_disjointness()


def test_q016_contract_constants():
    assert DEFAULT_START.isoformat() == "2024-09-25"
    assert DEFAULT_END.isoformat() == "2025-09-24"
    assert REFERENCE_START.isoformat() == "2025-09-25"
    assert REFERENCE_END.isoformat() == "2026-09-24"
