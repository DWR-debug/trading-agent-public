# Q214 — Disclosure-Implied Forward-Beta / Risk-Structure State

## Status
Discovery-only design. No performance, holdout selection, ranking, tuning, promotion or live execution is authorized by this document.

## Literature basis

Dyer, Roulstone & Van Buskirk, *Disclosure Similarity and Future Stock Return Comovement*, Management Science 70(7), 4762–4780 (2024), DOI 10.1287/mnsc.2023.4915, reports that similarity in mandatory corporate disclosures is associated with future stock-return comovement and can improve forward-looking market-beta estimation. The study uses machine-readable SEC 10-K/10-Q filings. citeplaceholder

A separate 2026 study reports disclosure similarity also predicts bond comovement, with stronger effects under higher information asymmetry and policy uncertainty. This supports the broader interpretation that disclosure structure can encode evolving common-risk exposure, although that evidence uses a non-US equity/bond setting and is not transferred as performance evidence. citeplaceholder

## Project hypothesis

Mandatory filing similarity may provide a forward-looking risk-structure state that is useful for position-risk estimation even when it is not used as a return signal. This is intentionally separated from Q088's similarity-weighted peer-return mechanism.

The target is not "which stock wins"; it is "which holdings are likely to move together next" based on currently public disclosure structure.

## Initial deterministic construction

1. Use only accepted, historical 10-K/10-Q filing prefixes.
2. Exclude amendments unless a separate correction-lineage contract explicitly proves their contemporaneous public availability.
3. Build a frozen filing representation using deterministic token/cosine similarity first; no model selection or embedding search.
4. Produce a disclosure-implied pairwise similarity matrix from the information available at each historical boundary.
5. Convert the matrix into a forward-beta/co-movement risk state for a pre-declared portfolio or candidate basket.
6. Compare the disclosure-implied risk state with a frozen historical-only return covariance baseline. This is a diagnostic/risk-state comparison, not an alpha ranking.
7. Preserve the state as a meta-layer candidate for the existing reliability/risk orchestration; it may not alter a frozen trading trial retroactively.

## Non-overlap

- Q088: uses text similarity to build a peer-return/comomentum signal. Q214 is risk-only and does not use peer returns as a predictor.
- Q131: disclosure-complexity vector. Q214 measures cross-firm semantic proximity and implied future co-movement, not complexity.
- Q211: patent semantic information. Q214 uses mandatory financial-report disclosure structure for portfolio risk, not patent text.
- Q213: news-disagreement elasticity. Q214 is a slower structural co-movement state, not intraday event disagreement.

## Cheap falsifiers

- random pair-map permutation;
- filing-date permutation within firm;
- text-token permutation preserving filing lengths;
- future-filing injection;
- amendment leakage injection;
- comparison against simple sector/market beta baselines;
- stability under deterministic text normalization.

## Feasibility gates

1. SEC filing archive completeness for the frozen historical horizon.
2. Exact accepted/publication clock and amendment exclusion contract.
3. Fixed issuer/security mapping.
4. Deterministic similarity compiler with frozen representation.
5. Historical-only covariance evaluation protocol.
6. Independent reproduction on a separate implementation/universe.
7. Only after those gates may a formal risk-state trial be considered.

## Expected value

Priority: **P1-RISK**.

Rationale: public source is already in the project's SEC stack; construction is deterministic; the signal is orthogonal to price-only alpha; potential use is inside portfolio risk/reliability rather than as another momentum branch.

Scientific boundary remains closed until the candidate-specific PIT and independent reproduction contracts pass.
