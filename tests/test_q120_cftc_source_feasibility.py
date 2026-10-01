from automation.q120_cftc_source_feasibility import validate


def test_q120_validator_accepts_fixed_contract_rows():
    rows = [
        {
            "market_and_exchange_names": "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE",
            "report_date_as_yyyy_mm_dd": "2026-01-06",
            "cftc_contract_market_code": "13874A",
            "open_interest_all": "1000",
            "asset_mgr_positions_long_all": "600",
            "asset_mgr_positions_short_all": "300",
            "lev_money_positions_long_all": "700",
            "lev_money_positions_short_all": "200",
        }
    ]
    out = validate(rows)
    assert out["row_count"] == 1
    assert out["contract_code"] == "13874A"
    assert out["required_fields_complete"] is True
