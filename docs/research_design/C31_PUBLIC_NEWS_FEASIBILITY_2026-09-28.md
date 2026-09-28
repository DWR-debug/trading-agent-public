# C31 — Public News Persistence Feasibility — 2026-09-28

## Status

DESIGN / MACHINE-FEASIBILITY COMPLETE

C31 is re-scoped from a proprietary sentiment reproduction to a deterministic
public-data adaptation. It is not a reproduction of RavenPack and creates no
project performance evidence.

## Source decision

The GDELT Global Knowledge Graph is publicly accessible and provides stable
record identifiers and document-level tone/context information. GDELT also
publishes raw data files and describes the database as free and open.

For strict point-in-time handling, the project uses a conservative observed_at
boundary: a news record becomes visible only at or after the GDELT
observation/processing timestamp carried by the source record. A later
publication timestamp inferred from article metadata is not used to move a
record backward in time.

This makes the feasibility contract conservative: it may delay information
relative to the article's true publication time, but it avoids injecting a
post hoc publication timestamp into an earlier decision.

## Fixed persistence construction

1. Ingest immutable records with stable record ID, observed timestamp,
   symbol/entity mapping, and document-level tone.
2. At decision time, retain only records with observed_at <= t.
3. Aggregate visible article tone by UTC observation date.
4. Compute same-sign persistence as the fraction of adjacent non-zero daily
   tone pairs retaining sign.
5. Compute two fixed states:
   - short persistence over the latest 5 observed news days;
   - long persistence over the latest 21 observed news days.
6. C31 state = short persistence - long persistence.

No lookback search, sentiment threshold search, source ranking, entity filter
search, event-window search, portfolio weighting search or alternative text
model is permitted after this freeze.

## PIT contract

The machine-feasibility suite enforces:

- future records cannot change an as-of state;
- t+1 records cannot enter t;
- duplicate source identifiers fail closed;
- insufficient historical coverage fails closed.

## Remaining data gate

Before any performance authorization, the repository must demonstrate:

1. reproducible historical GDELT archive retrieval;
2. stable entity-to-symbol mapping for the actual fresh universe;
3. complete source-record preservation before transformation;
4. coverage statistics for each issuer across the study window;
5. immutable source-bundle fingerprint;
6. PIT verification against the persisted bundle.

The current layer deliberately does not solve entity mapping. This is important:
a public source without a reproducible security mapping would still be an invalid
research input.

## External-source basis

The GDELT project states that its database is 100% free and open, and its GKG
documentation describes unique record identifiers and broad content-analysis
measures including document tone. The project treats these external facts as
source feasibility, not as evidence for C31 profitability.

## Safety

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
