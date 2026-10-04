# Q205 — Labor-Representation Certification Shock — 2026-10-05

## Purpose

Add a materially orthogonal public-information mechanism to the frontier: labor-representation election/certification outcomes from the National Labor Relations Board (NLRB).

This is a discovery candidate only. No return-based ranking, performance, tuning, holdout selection, promotion or live execution is allowed.

## Why it is orthogonal

Q205 targets an employment-governance shock rather than market-state momentum, SEC filing arrival, procurement demand, clinical-trial disclosure, patent publication or public-information latency. The economic mechanism is a change in collective-bargaining status and bargaining power at an employer.

Academic event-study evidence exists for union election effects on firm equity value, but that literature motivates the mechanism only; it is not project evidence.

## Source feasibility lead

The NLRB publishes a **Recent Election Results** dataset with case number, employer, tally issued date, status, votes, eligible voters, union outcome and voting-unit information. The site reports more than 35,000 election records and exposes historical pagination.

The NLRB also publishes **Election Reports** and states that elections are counted in the month in which the outcome is certified.

## Initial event contract

The event is the earliest reproducible public NLRB result/certification state for a fixed employer. Where no exact time-of-day is provable, the implementation must use the next regular trading-session boundary and must not infer an intraday timestamp.

Employer-to-issuer mapping must be frozen before any market outcome is read.

## Falsification priority

1. Historical pagination/archive completeness.
2. Public-clock semantics versus certification date.
3. Employer-to-issuer identity resolution and collision tests.
4. Later case-state mutation / correction lineage.
5. Independent reconstruction from a second retrieval path.

A failure of any of these gates is a valid scientific stop.

## Literature basis

- DiNardo et al., *Long-Run Impacts of Unions on Firms: New Evidence from Financial Markets*, NBER Working Paper 14709; published in the Quarterly Journal of Economics (2012).
- NLRB official election-result and election-report sources.

The literature does not justify assuming direction, magnitude, or persistence for this project's universe.
