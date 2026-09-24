import pytest

from execution.cost_contract import (
    ExecutionCostCompatibilityError,
    ResearchExecutionCostContract,
    paper_broker_research_compatibility,
    validate_research_cost_compatibility,
)


def test_research_cost_contract_is_15_bps_one_way():
    contract = ResearchExecutionCostContract()
    contract.validate()
    assert contract.total_one_way_bps == pytest.approx(15.0)
    assert contract.total_round_trip_bps == pytest.approx(30.0)


def test_research_cost_compatibility_accepts_backtest_defaults():
    validate_research_cost_compatibility(
        fee_rate=0.001,
        slippage_rate=0.0005,
    )


def test_research_cost_compatibility_fails_closed_on_fee_drift():
    with pytest.raises(ExecutionCostCompatibilityError):
        validate_research_cost_compatibility(
            fee_rate=0.0005,
            slippage_rate=0.0005,
        )


def test_research_cost_compatibility_fails_closed_on_slippage_drift():
    with pytest.raises(ExecutionCostCompatibilityError):
        validate_research_cost_compatibility(
            fee_rate=0.001,
            slippage_rate=0.0001,
        )


def test_paper_broker_legacy_default_is_explicitly_flagged():
    status = paper_broker_research_compatibility()
    assert status["paper_broker_default_fee_bps"] == pytest.approx(5.0)
    assert status["paper_broker_default_slippage_bps"] == pytest.approx(5.0)
    assert status["research_compatible"] is False
    assert status["status"] == "LEGACY_BROKER_DEFAULT_NOT_RESEARCH_COMPATIBLE"



def test_paper_broker_can_opt_in_to_research_cost_contract():
    from execution.paper_broker import PaperBroker

    broker = PaperBroker(cost_contract=ResearchExecutionCostContract())

    assert broker.fee_rate == pytest.approx(0.001)
    assert broker.slippage_rate == pytest.approx(0.0005)
