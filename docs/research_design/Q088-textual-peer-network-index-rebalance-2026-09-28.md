# Q088 — Textual Peer Network / Scheduled Rebalance Demand — 2026-09-28

**Status:** PREREGISTERED_DESIGN_ONLY / unranked  
**Issue:** #588

## C25 — SEC_MD&A_TEXT_PEER_COMOMENTUM

Inspired by Zhang, Qiao, Ge & Shen (2026), who construct cross-firm links from MD&A topic similarity and study linked-firm return predictability. citeturn748606search14

Project adaptation:
- public SEC 10-K/10-Q MD&A only;
- filing acceptance datetime is the PIT anchor;
- fixed issuer/security mapping;
- deterministic text representation;
- deterministic cosine similarity;
- graph formed only from completed filings available at decision time;
- peer signal = similarity-weighted prior peer return;
- next-session use only.

The representation, similarity rule, graph horizon and missing-text policy must be frozen before performance. No NLP-model, embedding or horizon search is allowed.

## M3 — SCHEDULED_INDEX_REBALANCE_DEMAND_SHOCK

Inspired by Nathan (2026), which studies anticipated ETF/index demand around scheduled rebalances. citeturn748606search12

Project adaptation:
- first feasibility target is Russell US reconstitution because official LSEG/FTSE Russell materials publish preliminary and final additions/deletions and explicit implementation dates. citeturn581583search0turn581583search1
- freeze public announcement timestamps and event dates;
- map changes through a fixed PIT security master;
- define a deterministic pre-announcement and effective-date pressure state;
- use only public information available at each cutoff.

No event-window search, index-family selection, sign search or outcome-conditioned event filtering.

## Feasibility sequence

1. Source/archive coverage.
2. PIT mutation tests.
3. Security/entity mapping.
4. Complete bundle freeze.
5. Separate authorization before performance.

No holdout selection, ranking, tuning, promotion or live execution.

## Safety

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
ORDERS_ENABLED=False  
AUTOMATIC_PROMOTION=False
