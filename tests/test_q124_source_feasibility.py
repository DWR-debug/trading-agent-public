from automation.q124_source_feasibility import build


def test_q124_source_feasibility_is_non_scientific():
    result = build()
    assert result["paper_only"] is True
    boundary = result["scientific_boundary"]
    assert boundary["performance_evaluation"] is False
    assert boundary["candidate_selection"] is False
    assert result["next_gate"] == "historical_archive_and_PIT_reconstruction"
