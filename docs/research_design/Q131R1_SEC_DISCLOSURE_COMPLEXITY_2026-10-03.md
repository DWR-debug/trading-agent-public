# Q131-R1 — Deterministic SEC Disclosure-Complexity Source Contract

## Status

SOURCE/PIT FEASIBILITY ONLY. No performance authorization.

## Objective

Freeze an ex-ante, reproducible SEC disclosure-complexity measurement vector for Q131.

Q131 asks whether disclosure complexity changes the relationship between turnover and short-horizon continuation/reversal. This track stops before any return calculation, state thresholding, ranking or tuning.

## Fixed universe

Q107 frozen symbols:

SPGI, NDAQ, AMP, RJF, WMB, VLO, DVN, EMN.

## Fixed filing window

2025-09-22 through 2025-09-24, selected before source retrieval.

## Fixed forms

8-K, 8-K/A, 10-Q, 10-Q/A, 10-K, 10-K/A.

## Fixed structural complexity vector

For each recovered SEC filing, preserve:

1. acceptance datetime from the SEC filing header;
2. filer CIK;
3. subject/registrant CIK when present in the SEC header; if the issuer filing header does not expose a separate subject section, the daily-index filer CIK is the issuer identity;
4. accession number and filing date;
5. filing form;
6. SEC filing-detail `Documents` count;
7. SEC-listed primary-document size in bytes;
8. number of rows in the SEC `Data Files` section;
9. whether the primary document is marked `iXBRL`.

The vector is descriptive. No scalar score is created and no threshold is estimated.

## PIT boundary

The acceptance datetime is the event clock. Historical publication/revision limitations are preserved explicitly. This track does not establish same-day formal model-use safety.

## Determinism / mutation tests

Parsing is invariant to HTML whitespace and row-order changes. A future-dated filing cannot enter the fixed historical window.

## Scientific boundary

No prices, returns, holdout selection, candidate ranking, parameter search, performance authorization, promotion or live execution are allowed.
