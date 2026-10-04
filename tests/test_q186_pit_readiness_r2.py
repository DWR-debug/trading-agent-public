from automation.q186_pit_readiness_r2 import FIXED_CONTROLS, SOURCES, classify, mutation_checks


def test_q186_r2_has_fixed_nonperformance_controls():
    assert [x["week"] for x in FIXED_CONTROLS] == [37, 38, 39]
    assert [x["issue_date"] for x in FIXED_CONTROLS] == ["2026-09-15", "2026-09-22", "2026-09-29"]
    assert all(mutation_checks().values())
    assert all("url" in spec and spec["markers"] for spec in SOURCES.values())


def test_q186_r2_keeps_citation_ordering_explicitly_unproven():
    assert classify(200, []) == "PASS"
    assert mutation_checks()["future_citation_cannot_pass_pre_event_filter"] is True
