# Q186 PIT-R3 — Conservative Citation Visibility Contract

## Purpose

Strengthen Q186's point-in-time contract without treating a bulk-data citation field as a public-observation timestamp.

For a backward citation edge used in the pre-event technology graph, the conservative route admits the edge only when the exact citation is evidenced in the public grant document of the citing patent and the citing patent's grant date is strictly earlier than the upstream patent grant date.

## Frozen rule

Eligible only when:
1. the citing patent document is independently identified;
2. the exact citation is present in that public grant document;
3. the citing patent grant date is strictly earlier than the upstream grant date;
4. same-day ties are excluded;
5. source identity/content can be frozen by URL/document hash;
6. later bulk refreshes, assignments, corrections or withdrawals cannot rewrite the frozen prefix.

The conservative public boundary is the citing patent grant date. This may reduce coverage; that loss must be measured, not optimized away.

## Remaining gates

Historical grant/citation coverage, document retrieval completeness, correction/withdrawal lineage, assignee-to-issuer mapping, independent reproduction and the resulting coverage loss remain unresolved.

No performance, ranking, tuning, holdout selection, promotion or live execution is permitted.
