# Q121-R2 — SEC Daily EDGAR Index Independent Reconciliation

## Status

INDEPENDENT SOURCE-ROUTE RECONCILIATION / PIT-ONLY. No performance authorization.

## Objective

Independently cross-check the Q121-R1 issuer-oriented beneficial-ownership filing route using a second SEC indexing architecture: the EDGAR daily master index.

Q121-R1 enumerates filings through the SEC company-browse route. Q121-R2 deliberately does not treat that route as authoritative. Instead it uses the Q121-R1 deterministic anchor set only as an ex-ante, mechanically defined comparison sample and verifies each anchor's membership in the historical daily master index for its filing date.

The filing header is then checked again for subject/filer identity and acceptance timestamp.

## Fixed universe and forms

Universe: Q107 frozen symbols:

SPGI, NDAQ, AMP, RJF, WMB, VLO, DVN, EMN.

Window: 2024-02-05 through 2025-09-24.

Forms:

- SC 13D
- SC 13G
- SC 13D/A
- SC 13G/A

## Independent source contract

Primary independent index route:

`https://www.sec.gov/Archives/edgar/daily-index/{YYYY}/QTR{1..4}/master.{YYYYMMDD}.idx`

For every Q121-R1 deterministic anchor (first/middle/last per issuer/form where available):

1. Read the historical master index for the anchor's filing date.
2. Parse the exact accession entry and verify filing date and form.
3. Verify the master-index CIK equals the filing's Filed-By CIK.
4. Re-fetch the SEC filing header and verify Subject CIK equals the target issuer CIK.
5. Preserve the raw master-index response hash and raw header hash.

The daily-index route is architecturally distinct from the issuer-browse query and therefore supplies an independent membership check.

## What this proves

A successful receipt proves that a deterministic sample of Q121-R1's returned filings is independently recoverable from SEC daily master indexes and that the issuer/filer identity is coherent.

It does **not** prove that the complete Q121-R1 filing population is exhaustive. Population-level equivalence would require a separate frozen all-window index compiler, which remains a subsequent gate.

## PIT contract

The daily index is a filing-date membership source, not a publication clock.

Acceptance time is taken from the filing header. This track preserves acceptance timestamps but does not claim exact historical first-publication timing, immutable archive-revision lineage, or same-day model-use safety.

## Scientific boundary

No prices, returns, holdout selection, ranking, tuning, performance, promotion or live execution are read or created.

A source/PIT reconciliation receipt cannot authorize performance.
