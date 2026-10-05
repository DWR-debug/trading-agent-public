from __future__ import annotations

import pytest

from agent.paper_execution import PaperExecutionAdapter, TradeIntent
from agent.runtime import AgentRuntimeError, FrozenCandidate


def candidate() -> FrozenCandidate:
    return FrozenCandidate.from_mapping(
        {
            "schema_version": 1,
            "frozen": True,
            "candidate_id": "PAPER-ADAPTER-TEST-V1",
            "freeze_ref": "paper-adapter-test-v1",
            "initial_capital_eur": 2000.0,
            "risk_per_trade": 0.01,
            "leverage": 1.0,
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
        }
    )


def test_open_is_paper_only_and_uses_research_cost_contract() -> None:
    adapter = PaperExecutionAdapter(candidate())
    result = adapter.open(
        TradeIntent(
            symbol="TEST",
            side="BUY",
            entry_price=100.0,
            stop_price=98.0,
        )
    )
    assert result["security"]["status"] == "PAPER_ONLY"
    assert result["execution"]["status"] == "PAPER_FILLED"
    assert adapter.broker.fee_rate == pytest.approx(0.001)
    assert adapter.broker.slippage_rate == pytest.approx(0.0005)


def test_mark_to_market_updates_risk_state() -> None:
    adapter = PaperExecutionAdapter(candidate())
    adapter.open(
        TradeIntent(
            symbol="TEST",
            side="BUY",
            entry_price=100.0,
            stop_price=98.0,
        )
    )
    result = adapter.mark_to_market({"TEST": 99.0})
    assert result["account"]["equity"] < 2000.0
    assert result["portfolio_risk"]["open_positions"] == 1


def test_close_releases_position() -> None:
    adapter = PaperExecutionAdapter(candidate())
    adapter.open(
        TradeIntent(
            symbol="TEST",
            side="BUY",
            entry_price=100.0,
            stop_price=98.0,
        )
    )
    result = adapter.close("TEST", 101.0)
    assert result["execution"]["status"] == "PAPER_CLOSED"
    assert result["portfolio_risk"]["open_positions"] == 0


def test_adapter_rejects_invalid_side() -> None:
    adapter = PaperExecutionAdapter(candidate())
    with pytest.raises(AgentRuntimeError, match="BUY or SELL"):
        adapter.open(
            TradeIntent(
                symbol="TEST",
                side="MAYBE",
                entry_price=100.0,
                stop_price=98.0,
            )
        )
