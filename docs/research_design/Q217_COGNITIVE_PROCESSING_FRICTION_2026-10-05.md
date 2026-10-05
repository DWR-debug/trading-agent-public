# Q217 — Cognitive Processing Friction

**Status:** Discovery-only. No performance, holdout selection, ranking, tuning, promotion or live execution.

## Mechanism
Du & Tang's 2026 work models cognitive load as a constraint on information processing rather than merely treating information as a timestamp or raw text signal. Q217 turns that insight into a deterministic discovery candidate: separate text complexity, information quantity, boilerplate and structural complexity, and test whether a distinct processing-friction component remains after fixed size/quantity controls.

## PIT
Use the earliest admissible SEC public filing boundary and freeze the historical filing prefix. Amendments, later normalized text, and future document versions cannot rewrite the historical observation.

## Non-overlap
Q131-R1 already studies disclosure complexity as a moderator of turnover/short-horizon continuation/reversal. Q217 may remain separate only if its processing-friction decomposition is empirically distinct from Q131's complexity dimensions. Otherwise Q217 must merge back into Q131 rather than create another duplicate text family. Q214 is disclosure-similarity/risk structure; Q211 is patent semantics; Q204 is information-arrival speed.

## Cheap falsifiers
1. Document length alone explains the state.
2. Boilerplate alone explains the state.
3. Random or calendar-preserving text permutation leaves the result unchanged.
4. Fixed liquidity/investor-sophistication controls eliminate the separation.
5. No stable mechanism across predeclared document types.
6. Future-text/amendment injection changes the historical prefix.

## Gates
SEC historical archive completeness; accepted/public clock; immutable filing prefix; deterministic feature compiler; complexity/quantity/boilerplate/structure separability; fixed issuer/security mapping; amendment lineage; independent PIT reproduction.

## Literature status
The cited arXiv paper is v2, revised 15 August 2026 (not a first submission in 2026). The paper reports an information-processing framework in which processing load depends on content and representation/interface; its literature results motivate discovery but are not project evidence. citeturn823297search5turn823297academia54

Priority **P1**. If separability fails, persist `MERGE_INTO_Q131` or `PRUNED`, not a weak standalone candidate.