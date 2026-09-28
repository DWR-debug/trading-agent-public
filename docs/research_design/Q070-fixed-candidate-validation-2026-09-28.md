# Q070 — Fresh Validation of Q069 OHLCV Candidate Bank

**Date:** 2026-09-28  
**Status:** PREREGISTERED / DESIGN-ONLY  
**Issue:** #539

## Purpose

Q070 validates the fixed Q069 candidate bank on a new symbol-disjoint universe. Asset selection is restricted to a deterministic source-order coverage rule; no observed return, holdout result or parameter search may influence the selected symbols.

## Fixed candidate bank

- C7 LOW_MAX_21
- C8 LOW_IDIO_VOL_273
- C9 LONG_TERM_REVERSAL_756
- C10 TREND_EFFICIENCY_63
- C11 VOLUME_CONFIRMED_TREND_126

Definitions are inherited unchanged from Q069.

## Asset-selection rule

The source pool and ordering come from `automation/fixed_window_candidate_discovery.py`. Symbols already used in registered universes or the trial ledger are excluded. The first eight symbols that jointly satisfy the fixed 2011-01-01 through 2025-09-24 / 3500-common-session coverage contract are frozen for Q070.

This is coverage-only selection. It does not rank candidates by P&L and does not inspect holdout data.

## Validation sequence

1. Coverage discovery and canonical snapshot.
2. Point-in-time mutation tests on the frozen snapshot.
3. One-shot performance authorization only after both receipts pass.
4. Symmetric fixed-rule performance under the existing 13 gates.
5. Immutable evidence reconciliation.

## Scientific boundary

Q070 cannot alter any Q069 candidate definition, parameter, threshold, horizon, asset set after coverage selection, or gate. A failed data source results in a data-invalid/blocked outcome rather than silent replacement.

## Safety

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`ORDERS_ENABLED=False`  
`AUTOMATIC_PROMOTION=False`