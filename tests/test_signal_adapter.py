from __future__ import annotations

import pytest

from agent_runtime.signal_adapter import signal_to_packet
from agent_runtime.paper_intent import PaperIntentError
from strategies.signals import SignalType, TradingSignal


def _signal(kind: SignalType) -> TradingSignal:
    return TradingSignal(
        symbol="SPY",
        signal=kind,
        confidence=0.8,
        reason="test",
    )


def _exposure():
    return {
        SignalType.HOLD: 0.0,
        SignalType.BUY: 1.0,
        SignalType.SELL: -1.0,
    }


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        (SignalType.HOLD, 0.0),
        (SignalType.BUY, 1.0),
        (SignalType.SELL, -1.0),
    ],
)
def test_signal_mapping_is_explicit(kind, expected):
    packet = signal_to_packet(
        _signal(kind),
        decision_time_utc="2026-10-05T12:00:00Z",
        market_observation_time_utc="2026-10-05T11:59:00Z",
        input_fingerprint="input",
        decision_fingerprint="decision",
        exposure_by_signal=_exposure(),
    )
    assert packet.target_exposure == expected


def test_signal_mapping_does_not_use_confidence_implicitly():
    packet = signal_to_packet(
        _signal(SignalType.BUY),
        decision_time_utc="2026-10-05T12:00:00Z",
        market_observation_time_utc="2026-10-05T11:59:00Z",
        input_fingerprint="input",
        decision_fingerprint="decision",
        exposure_by_signal=_exposure(),
    )
    assert packet.target_exposure == 1.0
    assert packet.metadata["signal_type"] == "BUY"


def test_signal_mapping_requires_complete_mapping():
    with pytest.raises(PaperIntentError):
        signal_to_packet(
            _signal(SignalType.BUY),
            decision_time_utc="2026-10-05T12:00:00Z",
            market_observation_time_utc="2026-10-05T11:59:00Z",
            input_fingerprint="input",
            decision_fingerprint="decision",
            exposure_by_signal={SignalType.BUY: 1.0},
        )
