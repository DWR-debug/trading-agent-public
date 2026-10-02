from automation.q104_xbrl_concept_freeze_audit import audit


def test_q104_xbrl_concept_audit_reports_missing_freeze_without_selection():
    result = audit()
    assert result["scientific_boundary"]["concept_selection"] is False
    assert result["scientific_boundary"]["performance"] is False
    assert set(result["blocked_candidates"]) == {"Q104:I19", "Q104:I20"}
