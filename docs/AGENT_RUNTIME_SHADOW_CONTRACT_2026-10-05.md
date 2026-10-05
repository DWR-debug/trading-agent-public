# Trading Agent Runtime — Paper/Shadow Integration Contract

Date: 2026-10-05  
Status: Engineering foundation only; non-authorizing

## Why build this now?

The scientific bottleneck is still historical source/PIT validity, not the
absence of an execution engine. Nevertheless, delaying all agent engineering
until a candidate is fully validated would create a second bottleneck later:
validated research would have no stable runtime interface.

The correct split is therefore:

Research -> frozen decision packet -> runtime validation -> paper/shadow intent -> append-only shadow ledger

The runtime can be built now because it does not need to know which candidate
will eventually pass. It only needs to enforce the boundary between a frozen
decision and any downstream paper simulation.

## Contract

A FrozenDecisionPacket carries:

- candidate identity;
- market-observation timestamp and decision timestamp;
- immutable input and decision fingerprints;
- a precomputed target exposure;
- permanent paper-only safety flags.

The runtime validates that:

1. the decision does not precede the market observation;
2. provenance fingerprints are present;
3. target exposure is bounded to [-1, +1];
4. PAPER_ONLY=True;
5. live trading is disabled;
6. order creation is disabled;
7. automatic promotion is disabled.

The runtime produces only a PaperIntent with route paper_shadow. It has no
broker client, order-submission method, candidate-selection method, promotion
method, return evaluation, holdout access, ranking logic or parameter search.

The agent_runtime/signal_adapter.py component can translate an already-frozen TradingSignal into the same decision packet, but only when the candidate ID, timestamps, fingerprints and a complete explicit HOLD/BUY/SELL exposure mapping are supplied by the caller. It never derives position sizing from confidence implicitly and never chooses a mapping itself.

The `agent_runtime/decision_adapter.py` layer accepts only the exact frozen-decision schema, rejects outcome/search fields, and adds a deterministic intent fingerprint. `agent_runtime/shadow_replay.py` verifies monotone decision-time order, uniqueness, and a reproducible intent-chain fingerprint. The `agent_runtime/shadow_ledger.py` component is the canonical append-only intent ledger, and `agent_runtime/shadow_coordinator.py` commits every accepted PaperIntent to it. The `agent_runtime/shadow_event_replay.py` component verifies exported SHADOW_INTENT_ACCEPTED events against stored fingerprints, global time order, uniqueness and non-authorizing flags. These are integration/provenance controls; they do not create scientific evidence.

## Research boundary

This package does not:

- select a candidate;
- tune a candidate;
- calculate or compare performance;
- consume holdout observations;
- create scientific evidence;
- authorize a research phase;
- promote a candidate;
- submit live or paper broker orders.

Existing paper-forward simulation remains the execution simulator. This runtime
is only the provenance/safety envelope around future validated integrations.

## Acceleration role

The intended speed gain is architectural rather than statistical:

- source/PIT research continues in parallel;
- Runner C can keep working on long candidate-specific reconstruction;
- candidate modules can later be adapted to one stable runtime packet;
- paper-forward integration can be tested independently of candidate selection;
- the scientific pipeline does not need to pause for runtime engineering.

## Safety

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
ORDERS_ENABLED=False  
AUTOMATIC_PROMOTION=False

This document and package provide no performance authorization.

The agent_runtime/shadow_coordinator.py layer is the final runtime admission boundary. It validates the immutable paper intent, invokes the existing portfolio risk controller for kill-switch/limit checks, and emits only a SHADOW_INTENT_ACCEPTED ledger event. It contains no broker/order API and does not create scientific evidence.
