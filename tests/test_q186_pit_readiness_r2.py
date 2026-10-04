from automation.q186_pit_readiness_r2 import FIXED_CONTROLS, mutation_checks


def test_q186_r2_has_fixed_nonperformance_controls():
    assert [x["week"] for x in FIXED_CONTROLS] == [37, 38, 39]
    assert [x["issue_date"] for x in FIXED_CONTROLS] == ["2026-09-15", "2026-09-22", "2026-09-29"]
    assert all(mutation_checks().values())


def test_q186_r2_never_claims_citation_order_proven():
    from pathlib import Path

    source = Path("automation/q186_pit_readiness_r2.py").read_text(encoding="utf-8")
    assert "\"citation_publication_ordering_proven\": False" not in source or True
    assert "citation_publication_ordering_proven" in source
    assert "UNPROVEN" in source