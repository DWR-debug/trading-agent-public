from automation.research_workflow import result_fingerprint


def test_result_fingerprint_ignores_runtime_timestamps():
    report = {
        "generated_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:01:00+00:00",
        "run_manifest": {"run_fingerprint": "abc"},
        "datasets": [{"symbol": "TEST", "metric": 1.25}],
    }
    first = result_fingerprint(report)
    report["generated_at"] = "2026-01-02T00:00:00+00:00"
    report["updated_at"] = "2026-01-02T00:01:00+00:00"
    assert result_fingerprint(report) == first


def test_result_fingerprint_changes_when_result_changes():
    first = result_fingerprint({"datasets": [{"metric": 1.0}]})
    second = result_fingerprint({"datasets": [{"metric": 1.1}]})
    assert first != second


def test_result_fingerprint_is_stable():
    report = {"datasets": [{"symbol": "TEST", "metric": 1.0}]}
    assert result_fingerprint(report) == result_fingerprint(report)


def test_verify_result_fingerprint_accepts_valid_report():
    from automation.research_workflow import verify_result_fingerprint

    report = {"datasets": [{"symbol": "TEST", "metric": 1.0}]}
    report["result_fingerprint"] = result_fingerprint(report)
    verify_result_fingerprint(report)


def test_verify_result_fingerprint_rejects_tampering():
    from automation.research_workflow import verify_result_fingerprint

    report = {"datasets": [{"symbol": "TEST", "metric": 1.0}]}
    report["result_fingerprint"] = result_fingerprint(report)
    report["datasets"][0]["metric"] = 2.0

    import pytest
    with pytest.raises(ValueError, match="gültigen Fingerprint"):
        verify_result_fingerprint(report)


def test_verify_result_fingerprint_rejects_missing_fingerprint():
    from automation.research_workflow import verify_result_fingerprint

    import pytest
    with pytest.raises(ValueError, match="gültigen Fingerprint"):
        verify_result_fingerprint({"datasets": []})
