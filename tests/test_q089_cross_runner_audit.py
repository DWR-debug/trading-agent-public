from automation.q089_cross_runner_audit import compare

def _receipt(symbols,fp):
    return {"trial_id":"T-2026-09-28-089-COVERAGE","status":"COVERAGE_PASSED","symbols":symbols,"universe":"validation_2026_09_28_q089_clean_q069","common_calendar_count":3704,"snapshot_fingerprint":fp}

def test_cross_runner_agreement_can_pass_with_fingerprint_variance(tmp_path):
    left=tmp_path/"left.json"; right=tmp_path/"right.json"
    left.write_text(__import__("json").dumps(_receipt(["A","B","C"],"fp-a")))
    right.write_text(__import__("json").dumps(_receipt(["A","B","C"],"fp-b")))
    result=compare(left,right)
    assert result["structural_cross_runner_agreement"] is True
    assert result["snapshot_fingerprint_variance"] is True
    assert result["governance"]["performance_trial_authorized"] is False

def test_cross_runner_selection_difference_is_not_silently_hidden(tmp_path):
    left=tmp_path/"left.json"; right=tmp_path/"right.json"
    left.write_text(__import__("json").dumps(_receipt(["A","B","C"],"fp-a")))
    right.write_text(__import__("json").dumps(_receipt(["A","B","D"],"fp-b")))
    result=compare(left,right)
    assert result["selection_agreement"] is False
    assert result["structural_cross_runner_agreement"] is False
