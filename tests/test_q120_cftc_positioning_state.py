from automation.q120_cftc_positioning_state import compile_state, synthetic_contract


def test_q120_synthetic_contract():
    assert all(synthetic_contract().values())


def test_q120_fails_closed_on_report_release_order():
    row = {
        "market_and_exchange_names": "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE",
        "cftc_contract_market_code": "13874A",
        "report_date": "2026-02-10",
        "release_date": "2026-02-06",
        "open_interest_all": 1000,
        "asset_mgr_positions_long_all": 600,
        "asset_mgr_positions_short_all": 300,
        "lev_money_positions_long_all": 700,
        "lev_money_positions_short_all": 200,
    }
    try:
        compile_state(row)
    except ValueError as exc:
        assert str(exc) == "Q120_PIT_RELEASE_BEFORE_REPORT"
    else:
        raise AssertionError("release date before report date must fail closed")


def test_q120_contract_uses_fixed_contract_identity():
    row = {
        "market_and_exchange_names": "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE",
        "cftc_contract_market_code": "13874A",
        "report_date": "2026-02-10",
        "release_date": "2026-02-13",
        "open_interest_all": 1000,
        "asset_mgr_positions_long_all": 600,
        "asset_mgr_positions_short_all": 300,
        "lev_money_positions_long_all": 500,
        "lev_money_positions_short_all": 400,
    }
    out = compile_state(row)
    assert out["contract"] == "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE"
    assert out["positioning_state"] == "LEVERAGED_MORE_LONG"
