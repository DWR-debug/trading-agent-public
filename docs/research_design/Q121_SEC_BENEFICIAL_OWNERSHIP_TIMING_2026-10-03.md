# Q121 — SEC Beneficial-Ownership Disclosure Timing State

## Status

DISCOVERY / PIT-ONLY. No performance authorization.

## Hypothesis

The administrative timing of Schedule 13D/13G disclosures may contain a distinct information state for the next eligible trading session.

The SEC extended the EDGAR filing cut-off for Schedule 13D, Schedule 13G and their amendments from 17:30 to 22:00 Eastern Time effective February 5, 2024. The SEC documentation states that these filings can retain the same Filing Date as the Received Date after 17:30 and can be disseminated until 22:00 ET. This creates a discrete, institutionally defined timing boundary.

A 2026 working paper reports a marked increase in post-17:30 Schedule 13G filings after the reform. That observation motivates the hypothesis but is not evidence of return predictability.

## Fixed construction

Scope:
- SC 13D
- SC 13G
- SC 13D/A
- SC 13G/A

Study period:
2024-02-05 through 2025-09-24.

Local timezone:
America/New_York.

Event classes:
- STANDARD_DAY: accepted before 17:30 ET.
- LATE_DAY_SAME_DATE: accepted at/after 17:30 ET and no later than 22:00 ET, with filing date equal to the acceptance calendar date.
- OUT_OF_CONTRACT: all remaining observations; fail-closed and excluded.

The signal boundary is deliberately next-session only. The project makes no assumption that the exact SEC web-publication second equals the EDGAR acceptance second. The SEC itself states that filings are often available within 1–3 minutes but that no first-public-availability timestamp exists and the lag is not guaranteed.

## Discovery output

For each fixed issuer:
1. preserve every accession independently;
2. map the event to the first XNYS session strictly after the acceptance calendar date;
3. record counts of standard-day and late-day events per issuer/session;
4. expose a fixed 20-XNYS-session descriptive arrival state;
5. retain source hashes and mutation-test results.

No return, holdout, performance, or candidate-ranking field is consulted by the compiler.

## Falsification / gate sequence

1. source/archive completeness;
2. exact form coverage;
3. timezone/boundary correctness;
4. filing-date consistency;
5. security/issuer identity;
6. synthetic mutation suite;
7. independent reproduction;
8. only then consider a separate coverage/PIT study.

## Prohibitions

No asset selection, threshold search, horizon search, parameter fitting, holdout selection, ranking, promotion or live execution.

A future performance study must use a fresh symbol-disjoint universe and a new preregistration.
