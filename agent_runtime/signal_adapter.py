"""Explicit adapter from a validated signal object to a paper-only decision packet.

The mapping is deliberately injected by the caller. This module does not
choose a strategy, candidate, threshold, exposure, or position size.
"""

from __future__ import annotations

from agent_runtime.paper_intent import FrozenDecisionPacket, PaperIntentError
from strategies.signals import SignalType, TradingSignal


def signal_to_packet(
    signal: TradingSignal,
    *,
    decision_time_utc: str,
    market_observation_time_utc: str,
    input_fingerprint: str,
    decision_fingerprint: str,
    exposure_by_signal: dict[SignalType, float],
) -> FrozenDecisionPacket:
    if not isinstance(signal, TradingSignal):
        raise PaperIntentError("signal must be a TradingSignal")
    required = {SignalType.HOLD, SignalType.BUY, SignalType.SELL}
    if set(exposure_by_signal) != required:
        raise PaperIntentError("exposure_by_signal must define HOLD, BUY and SELL exactly")

    target = exposure_by_signal[signal.signal]
    packet = FrozenDecisionPacket(
        candidate_id=signal.symbol + ":" + decision_fingerprint,
        symbol=signal.symbol,
        decision_time_utc=decision_time_utc,
        market_observation_time_utc=market_observation_time_utc,
        input_fingerprint=input_fingerprint,
        decision_fingerprint=decision_fingerprint,
        target_exposure=target,
        metadata={"signal_type": signal.signal.value},
    )
    return packet.validate()
