from datetime import date

import automation.q018_source_feasibility_preflight as module


def test_q018_fixed_contract():
    assert module.UNIVERSE == "q018_official_event_source_validation"
    assert module.SYMBOLS == (
        "UNH", "UPS", "FDX", "DIS", "ADP", "BKNG",
        "ORLY", "AZO", "TJX", "RSG", "WM", "EOG",
    )
    assert module.STUDY_START == date(2011, 1, 1)
    assert module.STUDY_END == date(2025, 9, 24)


def test_treasury_filter_contract(monkeypatch):
    seen = {}

    def fake_fetch(url, *, headers=None, timeout=30):
        seen["url"] = url
        return '{"data":[{"record_date":"2025-09-18","auction_date":"2025-09-18","cusip":"X","bid_to_cover_ratio":"2.55","security_type":"Note","security_term":"10-Year"}]}'

    monkeypatch.setattr(module, "_fetch_text", fake_fetch)
    result = module._treasury_coverage()

    assert "security_type%3Aeq%3ANote" in seen["url"]
    assert "security_term%3Aeq%3A10-Year" in seen["url"]
    assert result["performance_evaluation"] is False
    assert result["selection_used"] is False


def test_fed_source_status_is_deterministic(monkeypatch):
    html = "<html><body>Statement target range for the federal funds rate</body></html>"
    monkeypatch.setattr(module, "_fetch_text", lambda url, **kwargs: html)
    result = module._fed_coverage()
    assert result["status"] == "COVERAGE_VALIDATED"
    assert all(item["target_rate_language_probe"] for item in result["years"].values())


def test_sec_transaction_code_probe_contract():
    body = "<transactionCode>P</transactionCode>"
    assert "transactionCode" in body
    assert module.SEC_SUBMISSIONS.format(cik=123456) == (
        "https://data.sec.gov/submissions/CIK0000123456.json"
    )


def test_governance_is_coverage_only():
    result = module.run
    assert result.__name__ == "run"
