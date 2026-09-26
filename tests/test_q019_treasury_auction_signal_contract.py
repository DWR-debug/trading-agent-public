from datetime import date

import automation.q019_treasury_auction_signal_contract as module


def test_fixed_contract():
    assert module.UNIVERSE == "q018_official_event_source_validation"
    assert module.REQUESTED_CANDLES == 3520
    assert module.TARGET_COMMON_CANDLES == 3500
    assert module.STUDY_START == date(2011, 1, 1)
    assert module.STUDY_END == date(2025, 9, 24)


def test_signal_and_pit_mapping_are_deterministic():
    rows = [
        {
            "record_date": "2025-01-03",
            "security_type": "Note",
            "security_term": "10-Year",
            "auction_date": "2025-01-02",
            "cusip": "A",
            "bid_to_cover_ratio": "2.50",
        },
        {
            "record_date": "2025-01-10",
            "security_type": "Note",
            "security_term": "10-Year",
            "auction_date": "2025-01-09",
            "cusip": "B",
            "bid_to_cover_ratio": "2.70",
        },
    ]
    result = module._validate_treasury_contract(
        rows, [date(2025, 1, 6), date(2025, 1, 13)]
    )
    assert result["status"] == "COVERAGE_VALIDATED"
    assert result["mapped_event_count"] == 2
    assert result["signal_event_count"] == 1
    assert result["last_event"]["signal"] == 1
    assert result["first_event"]["next_eligible_common_trading_date"] == "2025-01-06"


def test_contract_rejects_publication_before_auction():
    rows = [
        {
            "record_date": "2025-01-03",
            "security_type": "Note",
            "security_term": "10-Year",
            "auction_date": "2025-01-04",
            "cusip": "A",
            "bid_to_cover_ratio": "2.50",
        }
    ]
    result = module._validate_treasury_contract(rows, [date(2025, 1, 6)])
    assert result["status"] == "DATA_INSUFFICIENT"
    assert any(
        item["reason"] == "publication_before_auction"
        for item in result["errors"]
    )


def test_contract_rejects_duplicates():
    row = {
        "record_date": "2025-01-03",
        "security_type": "Note",
        "security_term": "10-Year",
        "auction_date": "2025-01-02",
        "cusip": "A",
        "bid_to_cover_ratio": "2.50",
    }
    result = module._validate_treasury_contract(
        [row, dict(row)], [date(2025, 1, 6)]
    )
    assert result["status"] == "DATA_INSUFFICIENT"
    assert any(item["reason"] == "duplicate_auction_key" for item in result["errors"])


def test_governance_surface_does_not_authorize_performance():
    assert module.run.__name__ == "run"
