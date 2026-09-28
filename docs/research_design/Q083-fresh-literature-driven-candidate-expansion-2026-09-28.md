# Q083 — Fresh Literature-Driven Candidate Expansion — 2026-09-28

**Status:** PREREGISTERED_DESIGN_ONLY / unranked  
**Issue:** #582

## Research objective

Q083 expands the candidate frontier using mechanisms identified from recent empirical work and public-data feasibility. The purpose is to create materially new hypotheses rather than another parameter sweep of existing sleeves.

No performance evaluation, holdout inspection for selection, ranking, tuning, promotion or live execution is authorized by Q083 itself.

## Candidate bank

### C22 — OVERNIGHT_JUMP_REVERSAL_Z63

**Source:** Bahcivan, Dam & Gonenc, *Journal of Behavioral and Experimental Finance*, September 2026, DOI 10.1016/j.jbef.2026.101220.

At decision close t:

- overnight return g_t = Open_t / Close_{t-1} - 1;
- compute the median and MAD of the previous 63 completed overnight returns g_{t-63} ... g_{t-1};
- robust z_t = (g_t - median) / (1.4826 * MAD), with deterministic zero-MAD handling;
- fixed score = -z_t.

A later fixed-rule trial would rank cross-sectionally and use the two highest scores on the long side. No jump threshold, sign search or horizon search is allowed.

This is an adaptation, not a replication: the project uses a robust daily normalization and next-session tradability boundary rather than copying the paper's event-detection machinery.

**Primary risks:** exact timing of the overnight boundary, stale/adjusted prices, extreme-value sensitivity and potential overlap with the already tested A6 overnight/daytime mechanism. The purpose of the robust normalization is to make the distinction explicit and testable rather than to add a tuned threshold.

### C23 — PEER_DEVIATION_SALIENCE_LS21

**Source:** Grebe, *Finance Research Letters*, September 2026, DOI 10.1016/j.frl.2026.110360.

At decision close t:

- calculate each asset's prior 21-session close-to-close return;
- calculate the cross-sectional median of those returns;
- define peer deviation D_i,t = R_i,t - median(R_.,t);
- fixed long-short score = -D_i,t;
- later fixed-rule implementation: long the two most negative deviations and short the two most positive deviations, with equal absolute weights and gross exposure <= 1.0.

The paper uses analyst-linked peers and studies asymmetric relations across the return distribution. This project adaptation uses the canonical cross-sectional universe as a deterministic peer proxy and is therefore hypothesis generation, not replication.

**Primary risks:** common-mode contamination of the peer proxy, crowding in extreme deviations and possible conceptual overlap with short-horizon reversal. The latter must be measured descriptively after the feasibility stage rather than resolved by tuning.

### I16 — FOREIGN_INSTITUTIONAL_13F_CHANGE

**Source:** Twongirwe, Bakundana & Masimengo, *Finance Research Open*, September 2026, DOI 10.1016/j.finr.2026.100154.

The paper reports that changes in short-term foreign institutional ownership have predictive content for subsequent U.S. stock returns, while the authors state that their underlying data cannot be shared.

Project adaptation:

- use only public SEC 13F filings;
- classify manager domicile from frozen filing-header metadata;
- aggregate quarter-over-quarter ownership changes for foreign-domiciled managers;
- anchor availability to EDGAR acceptance datetime;
- never use a filing before that public-availability timestamp;
- use a fixed cross-sectional ranking only after coverage and mutation-PIT pass.

Because the source paper's underlying dataset is unavailable, feasibility and reproducibility are explicit blockers rather than assumptions.

### M1 — DIVIDEND_PAYMENT_PRESSURE_STATE

**Source:** Hartzmark & Solomon, *American Economic Review*, 2025, DOI 10.1257/aer.20231725.

This is a market-level pressure state rather than a stock-level alpha sleeve.

At each decision time, use only dividend payment information already announced by that time. A later implementation would aggregate the announced cash-payment pressure over a fixed upcoming payment horizon and normalize it to a frozen market-cap denominator.

The intended use is a later allocator/exposure study because the mechanism is market-wide and may be more appropriate as a state variable than as a cross-sectional selection signal.

## Required feasibility sequence

1. Synthetic/code-level PIT mutation tests for C22 and C23.
2. Public-source accessibility checks for the literature and SEC/AEA channels.
3. Historical coverage audit and exact public-availability PIT contract for I16 and M1.
4. Freeze a fresh symbol-disjoint universe and complete input bundle.
5. Separately authorize any performance trial.
6. Evaluate under the unchanged 13-gate evidence contract.
7. Reconcile immutable evidence before interpretation.

## Governance

- No parameter search.
- No threshold search.
- No asset search.
- No horizon search.
- No variant search.
- No holdout selection.
- No family ranking.
- No automatic promotion.
- No live execution.

All candidate definitions and monotonic directions must be frozen before performance authorization.

## Safety

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
ORDERS_ENABLED=False  
AUTOMATIC_PROMOTION=False

## External references

- https://www.sciencedirect.com/science/article/pii/S2214635026000821
- https://www.sciencedirect.com/science/article/pii/S1544612326008883
- https://www.sciencedirect.com/science/article/pii/S3050700626000654
- https://www.aeaweb.org/articles?id=10.1257/aer.20231725
