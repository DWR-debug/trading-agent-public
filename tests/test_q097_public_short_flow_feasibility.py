from automation.q097_public_short_flow_feasibility import Observation, beneficial_ownership_state, form144_state, ftd_state, short_interest_state


def sample_records() -> list[Observation]:
    return [
        Observation('AAA', '2026-01-15', '2026-01-20', 10.0, 'src-a'),
        Observation('AAA', '2026-01-15', '2026-01-25', 12.0, 'src-a', revision=1),
        Observation('AAA', '2026-02-15', '2026-03-01', 20.0, 'src-b'),
        Observation('BBB', '2026-01-15', '2026-01-20', 99.0, 'src-c'),
    ]


def test_future_publication_does_not_change_as_of_state() -> None:
    base = sample_records()
    mutated = base + [Observation('AAA', '2027-01-01', '2027-01-02', 9999.0, 'future')]
    assert ftd_state(base, 'AAA', '2026-01-25') == ftd_state(mutated, 'AAA', '2026-01-25') == 12.0


def test_revision_visibility_is_publication_bounded() -> None:
    rows = sample_records()
    assert short_interest_state(rows, 'AAA', '2026-01-22') == 10.0
    assert short_interest_state(rows, 'AAA', '2026-01-25') == 12.0
    assert short_interest_state(rows, 'AAA', '2026-02-28') == 12.0
    assert short_interest_state(rows, 'AAA', '2026-03-01') == 20.0


def test_unknown_security_is_neutral() -> None:
    rows = sample_records()
    assert beneficial_ownership_state(rows, 'ZZZ', '2026-12-31') == 0.0


def test_form144_uses_same_pit_contract() -> None:
    rows = sample_records()
    assert form144_state(rows, 'AAA', '2026-01-24') == 10.0
    assert form144_state(rows, 'AAA', '2026-01-25') == 12.0

def test_same_publication_and_revision_conflict_fails_closed() -> None:
    rows = [
        Observation("AAA", "2026-01-15", "2026-01-20", 10.0, "src-a"),
        Observation("AAA", "2026-01-15", "2026-01-20", 11.0, "src-b"),
    ]
    try:
        ftd_state(rows, "AAA", "2026-01-21")
    except ValueError as exc:
        assert str(exc) == "CONFLICTING_SAME_PUBLICATION_REVISION"
    else:
        raise AssertionError("conflicting same-publication revision was not rejected")


def test_future_mutation_is_inert_for_all_q097_states() -> None:
    base = sample_records()
    mutated = base + [Observation("AAA", "2030-01-01", "2030-01-02", 9999.0, "future")]
    checks = [
        ftd_state,
        short_interest_state,
        beneficial_ownership_state,
        form144_state,
    ]
    for state_fn in checks:
        assert state_fn(base, "AAA", "2026-02-01") == state_fn(mutated, "AAA", "2026-02-01")
