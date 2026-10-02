from automation.q120_cftc_source_feasibility import validate


def test_q120_validator_accepts_fixed_contract_rows():
    rows = [
        {
            "market_and_exchange_names": "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE",
            "report_date_as_yyyy_mm_dd": "2026-01-06",
            "cftc_contract_market_code": "13874A",
            "open_interest_all": "1000",
            "asset_mgr_positions_long": "600",
            "asset_mgr_positions_short": "300",
            "lev_money_positions_long": "700",
            "lev_money_positions_short": "200",
        }
    ]
    out = validate(rows)
    assert out["row_count"] == 1
    assert out["contract_code"] == "13874A"
    assert out["required_fields_complete"] is True


def test_q120_validator_normalizes_upstream_contract_whitespace_and_case():
    rows = [
        {
            "market_and_exchange_names": "  e-mini s&p 500 - chicago mercantile exchange  ",
            "report_date_as_yyyy_mm_dd": "2026-01-06",
            "cftc_contract_market_code": " 13874a ",
            "open_interest_all": "1000",
            "asset_mgr_positions_long": "600",
            "asset_mgr_positions_short": "300",
            "lev_money_positions_long": "700",
            "lev_money_positions_short": "200",
        }
    ]
    out = validate(rows)
    assert out["contract_code"] == "13874A"


def test_q120_validator_still_rejects_wrong_contract_identity():
    rows = [
        {
            "market_and_exchange_names": "E-MINI S&P 500 STOCK INDEX",
            "report_date_as_yyyy_mm_dd": "2026-01-06",
            "cftc_contract_market_code": "99999A",
            "open_interest_all": "1000",
            "asset_mgr_positions_long": "600",
            "asset_mgr_positions_short": "300",
            "lev_money_positions_long": "700",
            "lev_money_positions_short": "200",
        }
    ]
    try:
        validate(rows)
    except RuntimeError as exc:
        assert str(exc) == "Q120_UNEXPECTED_CONTRACT_CODE"
    else:
        raise AssertionError("wrong contract identity must remain fail-closed")

def test_q120_validator_accepts_official_product_name_variant_when_contract_code_matches():
    rows = [
        {
            "market_and_exchange_names": "E-Mini S&P 500 Stock Index",
            "report_date_as_yyyy_mm_dd": "2026-01-06",
            "cftc_contract_market_code": "13874A",
            "open_interest_all": "1000",
            "asset_mgr_positions_long": "600",
            "asset_mgr_positions_short": "300",
            "lev_money_positions_long": "700",
            "lev_money_positions_short": "200",
        }
    ]
    out = validate(rows)
    assert out["contract_code"] == "13874A"
    assert out["observed_market_names"] == ["E-MINI S&P 500 STOCK INDEX"]
