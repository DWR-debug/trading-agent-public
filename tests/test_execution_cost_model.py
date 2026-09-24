import pytest

from execution.cost_model import ExecutionCostModel, ExecutionCostModelError


def test_default_project_cost_model_is_15_bps_one_way():
    model = ExecutionCostModel()
    assert model.one_way_cost_rate == pytest.approx(0.0015)
    assert model.round_trip_transaction_cost(1000.0) == pytest.approx(3.0)


def test_execution_price_applies_slippage_symmetrically():
    model = ExecutionCostModel()
    assert model.execution_price(100.0, "BUY") == pytest.approx(100.05)
    assert model.execution_price(100.0, "SELL") == pytest.approx(99.95)


def test_half_spread_is_added_to_one_way_price_impact_and_cost():
    model = ExecutionCostModel(spread_bps=10.0)
    assert model.execution_price(100.0, "BUY") == pytest.approx(100.10)
    assert model.execution_price(100.0, "SELL") == pytest.approx(99.90)
    assert model.one_way_transaction_cost(1000.0) == pytest.approx(2.0)


def test_short_borrow_cost_is_deterministic():
    model = ExecutionCostModel(short_borrow_annual_bps=252.0)
    assert model.short_borrow_cost(1000.0, days=5) == pytest.approx(0.5)


def test_invalid_execution_parameters_fail_closed():
    with pytest.raises(ExecutionCostModelError):
        ExecutionCostModel(fee_bps=-1.0)
    with pytest.raises(ExecutionCostModelError):
        ExecutionCostModel(trading_days_per_year=0)
