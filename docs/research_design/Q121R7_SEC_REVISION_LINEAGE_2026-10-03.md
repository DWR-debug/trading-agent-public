# Q121-R7 — SEC post-acceptance correction / revision-lineage gate

Status: preregistered design-only; execution blocked on a valid Q121-R6 receipt.

## Objective

Determine, on the fixed Q121 target-subject population, whether archived SEC complete-submission text explicitly exposes post-acceptance correction markers and correction dissemination timestamps that support a deterministic revision-lineage classification.

This gate is source/PIT-only. It does not evaluate trading performance, select assets, rank candidates, tune parameters, use holdout data, promote a strategy, or execute live orders.

## Upstream dependency

Q121-R6 must first produce an immutable receipt proving exhaustive header compilation over the verified Q121-R5 61,818-row population. No R7 execution is valid before that dependency exists.

## Frozen population

Window: 2024-02-05 through 2025-09-24.

Forms: SC 13D; SC 13G; SC 13D/A; SC 13G/A.

Target Subject CIKs are the eight fixed Q121 issuers used by R6. Subject identity must come from the validated Subject CIK field, not from accession-prefix or filer identity.

## Source contract

For every R6 target-subject event, retrieve the SEC complete submission text from the canonical archive path: /Archives/edgar/data/{filing-cik}/{accession-without-dashes}/{accession-without-dashes}.txt

Parse only explicitly represented fields: <ACCEPTANCE-DATETIME>, FILED AS OF DATE, DATE AS OF CHANGE, <SUBMISSION>, <CORRECTION>, and <TIMESTAMP>.

The parser fails closed on missing or contradictory identity/date fields.

## Revision-lineage contract

1. POST_ACCEPTANCE_CORRECTION_EXPLICIT: <CORRECTION> is present and <TIMESTAMP> is present and valid.
2. INITIAL_SUBMISSION: <SUBMISSION> is present and there is no correction marker.
3. AMENDMENT_SEPARATE_SUBMISSION: a fixed /A form; it is not automatically linked to a prior filing.
4. NO_EXPLICIT_REVISION_MARKER: no stronger explicit marker is available.

No lineage edge may be inferred from accession-number ordering, filing-time proximity, common filer CIK, common Subject CIK alone, similar form text, web page modification time, current search ordering, or missing/changed content hashes.

Where an explicit correction timestamp exists, record it as correction dissemination time and retain the raw header fingerprint.

## PIT contract

EDGAR acceptance time remains the Filer System acceptance clock. First-public-availability time is not treated as available merely because a filing can now be downloaded. Historical same-day PIT safety therefore remains false unless a separate independently validated source establishes first public availability.

## Acceptance criteria

R7 may pass only if every R6 target-subject event has a complete archive-text fetch; identity/date invariants hold; explicit correction markers are parsed deterministically; every parsed TIMESTAMP is validated as a correction dissemination timestamp; forbidden inference rules are absent; mutation tests cover missing/malformed markers and amendment-vs-correction distinction; and an independent re-reader reproduces the same classification multiset.

## Interpretation boundary

A successful R7 receipt proves only deterministic compilation of explicit SEC post-acceptance correction metadata for the fixed R6 population.

It does not establish first-public-availability time for initial submissions, universal same-day PIT safety, economic signal validity, trading performance, performance authorization, or promotion.

Safety: PAPER_ONLY=True; LIVE_TRADING_ENABLED=False; ORDERS_ENABLED=False; AUTOMATIC_PROMOTION=False.