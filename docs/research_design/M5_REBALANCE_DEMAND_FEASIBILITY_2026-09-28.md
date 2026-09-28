# M5 — Benchmark Demand Shock Clock Feasibility — 2026-09-28

## Status

DESIGN / MACHINE-FEASIBILITY COMPLETE

M5 is a scheduled-event adaptation, not a performance result. It uses public
index-reconstitution announcements and effective dates as an information
channel.

## Fixed event semantics

Each immutable event record contains:

- stable event identifier;
- security symbol;
- action: ADD (+1) or DELETE (-1);
- publication timestamp;
- effective timestamp.

An event is visible at decision time t only when publication timestamp <= t.
Only events whose effective timestamp is still in the future are eligible for
the scheduled-demand state.

For a security with several publicly announced revisions for the same future
effective date, the latest revision already published at decision time
supersedes earlier revisions. Two contradictory revisions at an identical
publication timestamp fail closed.

The state therefore has no tuned event window:

next_known_rebalance_state(symbol, t) = action of the next publicly known
effective rebalance event for symbol at t.

No +/- one-day, +/- five-day or other event-window search is permitted.

## Data feasibility gate

FTSE Russell publicly publishes reconstitution schedules and related
additions/deletions. The 2026 Russell US schedule uses semi-annual June and
December reconstitutions, with the December 2026 preliminary lists on
2026-11-13 and implementation on 2026-12-11.

Those current official schedules establish the public information channel.
Historical performance use still requires an archive-completeness audit for:

1. historical public announcement documents;
2. publication timestamps and document versions;
3. symbol/identifier mapping through time;
4. preliminary versus final revision handling;
5. immutable preservation and fingerprints.

No performance evaluation occurs in this feasibility layer.

## PIT tests

The machine suite verifies that:

- future publication content cannot alter an as-of state;
- preliminary announcements can be superseded by later public revisions;
- same-timestamp conflicts fail closed;
- invalid event identity and impossible time order fail closed.

## External source basis

LSEG / FTSE Russell publishes the Russell US Indexes reconstitution calendar
and public additions/deletions around reconstitution events. Current 2026
schedules are used only to establish source feasibility, not as project
performance evidence.

## Safety

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
