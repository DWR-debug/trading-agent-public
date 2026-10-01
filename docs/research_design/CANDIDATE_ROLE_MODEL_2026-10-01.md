# Candidate Role Model — 2026-10-01

## Purpose

This document defines **how** the current candidate families fit into the Trading Agent architecture and **what evidence role they must earn** before being combined.

It is not a performance ranking. It does not authorize performance, holdout selection, promotion or live execution.

## Fit to the project objective

The project objective is not maximum backtest return. The stated order is:

1. capital preservation;
2. controlled risk;
3. robust out-of-sample / holdout evidence;
4. regular and plannable cashflow;
5. efficient return;
6. long-term withdrawable income within safety limits.

That implies an architectural preference for **orthogonality, low turnover where the information clock is slow, explicit abstention/allocator states, and reproducible provenance**.

The current formal evidence does not establish a deployable candidate. The latest recorded formal result remains `performance_completed_no_arm_passed_all_13_gates`. The role model therefore governs research sequencing, not investment selection.

## What we actually use

### 1. Core selector

**H06-P2** is the current direct core-selector candidate.

Its scientific question is unusually clean: does sector residualization change the global ranking geometry relative to raw momentum without changing the underlying 15-name universe?

Its PIT contract is independently reconciled on 2,545 decision points, with the fixed 252-session lookback, 21-session skip, 15-symbol / 5-sector universe, and deterministic global 5/5 construction. The remaining readiness object is the exact frozen input bundle.

The appropriate use is therefore:

`raw global 5/5 control` vs `sector-residual global 5/5 treatment`

—not a blended signal and not a parameter search.

### 2. Event-information layer

**Q104:I22, Q109:I23 and Q109:I24** belong here.

These mechanisms depend on information arrival at specific public timestamps. Their natural contribution is therefore event-state information, event-driven exposure, or a filter/condition for a separately validated core.

They should not be forced into an always-on daily selector merely because they can be encoded as a number.

### 3. Slow institutional layer

**Q104:I19, Q104:I20, Q109:N1 and Q109:N2** belong here.

13F and N-PORT are slower disclosure channels. Their economically natural use is a persistent state or low-turnover conditioning signal, not a high-turnover trading trigger.

A strict clock separation is important: N-PORT and 13F are not silently interchangeable and should remain separately fingerprinted.

### 4. Regime / allocator layer

**Q104:I21, Q104:M6, Q119 and Q120** belong here initially.

The first purpose of these channels is to describe a market-wide, fiscal-liquidity or positioning regime that may later affect exposure, abstention or allocator decisions.

Q119 and Q120 should therefore be tested first as deterministic states, not presumed stock-selection alpha. Q119 has had a source-schema correction and needs a real retest. Q120 still needs historical archive and actual release-date PIT recovery, including exceptional publication schedules.

### 5. Composition layer

**Q104:R9 and Q118** are downstream infrastructure.

They must never be used to rescue a weak component. A bundle is a new research object with its own fingerprint, and every component must already satisfy its own data/PIT contract.

## Research sequence

The operating sequence is now:

**Core:** prepare the H06-P2 frozen input bundle → one-shot formal evaluation when governance prerequisites are fully bound.

**Feasibility:** close the real-source checks for I22 and Q119; advance Q120's release-date/archive audit.

**Expansion:** continue I19/I20/N1/N2/I23/I24 only when their data/PIT gates are cheap enough to add genuinely distinct information.

**Composition:** use Q118/R9 only after independent candidate validity exists.

This preserves the project philosophy:

**wide search → aggressive pruning → narrow formal validation**.

## Research hygiene

A candidate moves between roles only through a new preregistered hypothesis. A role assignment must never be changed because a performance result looked attractive.

Negative findings are retained as evidence. DATA_INVALID / DATA_INSUFFICIENT is a valid research outcome.

No part of this role model permits live trading.

## Machine-readable companion

`research/governance/candidate_role_map_2026_10_01.json`
is the machine-readable representation intended for future orchestration and audits.
