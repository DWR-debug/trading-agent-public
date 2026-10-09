# Q104:I19 and Q218 — Literature-Overlap Audit

**Audit date:** 2026-10-09  
**Purpose:** research triage and interpretation guardrail only. This document does not amend a frozen candidate contract, preregistration, trial, receipt, outcome, or authorization. It is not scientific performance evidence.

## Executive determination

| Candidate | Closest prior art located | Overlap assessment | What remains defensible |
|---|---|---|---|
| **Q218 — Mandatory/voluntary disclosure gap** | Heater, Reichmann & Zhu (SSRN posted 2026-09-29), plus the 2026 *Off Script* paper | **HIGH mechanism overlap** | A specific 10-K / Item 2.02 8-K channel, a deterministic hash-based measurement, and a different preregistered event clock/outcome. These are operational differences, not proof of a new underlying mechanism. |
| **Q104:I19 — Institutional demand × accrual state** | Alldredge, Caglayan & Upadhyay (first published 2026-01-05) | **HIGH hypothesis-level overlap; construct/timing difference** | Public, delayed 13F disclosed holdings transitions interacting with a precisely frozen SEC XBRL accrual-intensity state. The extent to which this disclosed-position proxy adds information beyond the known institution-by-accrual relationship remains unproven. |

**Disposition:** Continue the existing receipt-gated data/PIT work. Do not describe either economic interaction as literature-novel on the evidence currently available. Do not tune, redefine, rank, or promote either candidate to make it look more distinct. Any genuinely different mechanism must be a separate future preregistration, not a retroactive edit to these frozen trials.

## 1. Q218 — mandatory versus voluntary disclosure

### Closest prior art

John C. Heater, Doron Reichmann, and Boyan Zhu, *Saying it Once or Twice: The Semantic Wedge between Mandatory and Voluntary Performance Disclosure*, dated 2026-09-28 and posted to SSRN on 2026-09-29:  
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7537906

The abstract studies semantic differences between the required MD&A in a Form 10-K and voluntary disclosures during the earnings-call presentation. It decomposes the gap into topic coverage and framing, and reports that larger gaps are associated with negative return drift following the 10-K; its abstract attributes that drift to selective topic-coverage differences rather than framing differences. This posting predates the Q218 frozen performance contract dated 2026-10-08.

A second relevant paper is *Off Script: When Earnings Calls and Filings Tell Different Stories* (Journal of Behavioral Finance, 2026):  
https://doi.org/10.1080/15427560.2026.2667513

Its abstract examines divergence between earnings-call and 10-K MD&A tone/readability, using 22,366 matched pairs from 1,762 firms over 2006–2025, and reports post-disclosure return predictability. This is additional evidence that cross-channel disclosure divergence is an established nearby research area, not an untouched mechanism.

### Q218 frozen design versus the prior art

The repository's frozen Q218 contract is `research/governance/q218_performance_contract_2026_10_08.json`. It specifies:

- Required Form 10-K versus voluntary Form 8-K Item 2.02; closure occurs at the later of the two SEC acceptance timestamps.
- Deterministic 64-bucket SHA-256 hashed unigram/bigram construction, with topic-coverage gap, unigram-frequency omission asymmetry, and bigram-framing gap.
- The first eligible XNYS session strictly after pair closure; a signed two-sided open-to-close return for that session, with no ex-ante directional sign.
- A frozen eight-issuer population and 13 event pairs in the published deterministic result: `research/evidence/q218_deterministic_performance_result_latest.json`.

This differs from the SSRN paper in disclosure venue (8-K Item 2.02 instead of earnings-call presentation), representation (fixed token hashes instead of sentence-level transformer embeddings and a Blinder–Oaxaca decomposition), and the presently frozen short event outcome versus the paper's reported post-10-K drift. The available abstract does not establish that these differences yield incremental economic information.

**Verdict:** mechanism novelty is **not established**. The most defensible description is a fixed-rule measurement/channel extension of a known cross-channel-disclosure-gap hypothesis. The observed 13 pairs are insufficient on their own to establish general predictive value or incremental information versus the prior literature. No direction or performance conclusion is inferred here.

### Q218 next-gate rule

1. Preserve the already frozen performance contract and its completed result as historical, preregistered evidence; do not relabel or alter the result because prior art has been found.
2. Keep the prepared independent fresh-symbol replication's separate authorization gate fail-closed. A parent-trial authorization is not a replication authorization. Do not start replication performance until the exact replication trial has its own valid immutable authorization and the current formal gates reconcile positively.
3. Before making a novelty claim, document the incremental claim precisely: what the 8-K channel and acceptance-clock construction measure that is not already implied by the 10-K/earnings-call literature. Literature comparison alone does not authorize performance, holdout access, selection, ranking, tuning, or promotion.
4. Treat this paper as prior art for the 2026-10-08 frozen trial; its public posting date predates that trial's preregistration/performance contract. This is a novelty/interpretation correction, not a retroactive change to the trial.

## 2. Q104:I19 — institutional demand × accrual state

### Closest prior art

Dallin M. Alldredge, Mustafa O. Caglayan, and Arun Upadhyay, *Short-term institutional trading and return predictability in high-accrual stocks*, first published 2026-01-05, *Journal of Financial Research*, DOI 10.1111/jfir.70041:  
https://onlinelibrary.wiley.com/doi/10.1111/jfir.70041

The abstract reports return predictability from short-term institutional selling and short-selling activity among high-accrual firms, and reports that short-term institutional investors predict future earnings surprises when operating accruals are high. The core institution-by-accrual interaction is therefore established prior art as of the Q104:I19 concept freeze on 2026-10-03.

### Q104:I19 frozen design versus the prior art

The frozen design is documented in `docs/research_design/Q104_I19_EXACT_XBRL_CONCEPT_FREEZE_2026-10-03.md` and `research/preregistrations/q104_i19_xbrl_concept_freeze_2026_10_03.json`. It uses:

- Quarterly publicly disclosed Form 13F positions and manager/security transitions, anchored to each filing's SEC acceptance boundary—not a claim to observe institutional trades in real time.
- Three fixed US-GAAP facts: `NetIncomeLoss`, `NetCashProvidedByUsedInOperatingActivities`, and `Assets`; accrual amount is net income less operating cash flow, divided by average current/prior-period assets.
- A fixed institutional transition count state (`INCREASE + NEW` minus `DECREASE + EXIT`) joined to the XBRL state only after its applicable public-acceptance boundary.
- An eight-issuer frozen universe, a historical 2013-07-01 through 2025-09-24 study boundary, and fail-closed treatment of missing facts, period alignment, amendments, and future observations.

The most meaningful distinction is the **publicly disclosed, delayed 13F holdings-transition proxy and its explicit point-in-time clock**, rather than observed short-term trading/short-sale activity. That is a measurement and information-availability distinction; it does not make the underlying institution × accrual hypothesis new. Moreover, quarterly disclosed holdings changes are not interchangeable with actual short-horizon trading flows.

**Verdict:** the broad interaction is **not novel**. A more limited extension claim may be defensible if the receipt-backed PIT reconstruction and independent reproduction establish that the 13F disclosure-clock version is well-defined and genuinely distinct in measurement. No incremental predictive value is established by this literature audit or by source/PIT readiness.

### Q104:I19 next-gate rule

1. Let the currently active historical 13F census finish; require the exact acceptance-time joins, all prescribed shards, archive fingerprints, and issuer/security identity checks to pass.
2. Run the already defined historical PIT compiler only from a valid positive census receipt. Then require the independent reproduction to reproduce cutoff-level states, row-order invariance, and future-observation exclusion.
3. Reconcile the frozen preregistration and authorization only after those receipts are complete. Source completeness or PIT correctness is not performance evidence, and neither implies permission for a performance run.
4. Do not add new concepts, thresholds, assets, horizons, or signal variants to distinguish Q104:I19 from prior art. Any new mechanism or materially different contract requires its own separately frozen trial.

## 3. Research-OS implications

- Literature novelty and data/PIT validity are separate axes. The prior-art findings do not invalidate a correctly recorded deterministic source/PIT receipt, but they narrow what may be claimed about originality.
- Store this audit as explanatory research context; it must not be treated as a receipt, scientific result, authorization, ranking, or promotion signal.
- A capacity slot, successful workflow, 100% milestone, or completed preregistration/authorization reconciliation does not mean the candidate as a whole is scientifically validated.
- The dashboard should name the **exact completed milestone** and **next gate**, and show novelty/overlap status separately from implementation progress.
- Continue the existing focus on Q104:I19 and Q218. Do not open parallel candidate work simply to consume available compute. Preserve PAPER_ONLY and all existing authorization boundaries.

## Sources and project records

- Heater, Reichmann & Zhu (2026), SSRN 7537906: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7537906
- *Off Script: When Earnings Calls and Filings Tell Different Stories* (2026): https://doi.org/10.1080/15427560.2026.2667513
- Alldredge, Caglayan & Upadhyay (2026), DOI 10.1111/jfir.70041: https://onlinelibrary.wiley.com/doi/10.1111/jfir.70041
- Q218 frozen contract: https://github.com/DWR-debug/trading-agent-public/blob/master/research/governance/q218_performance_contract_2026_10_08.json
- Q218 performance record: https://github.com/DWR-debug/trading-agent-public/blob/master/research/evidence/q218_deterministic_performance_result_latest.json
- Q218 preregistration/authorization reconcile: https://github.com/DWR-debug/trading-agent-public/blob/master/research/evidence/q218_prereg_authorization_reconcile_latest.json
- Q104:I19 XBRL concept freeze: https://github.com/DWR-debug/trading-agent-public/blob/master/docs/research_design/Q104_I19_EXACT_XBRL_CONCEPT_FREEZE_2026-10-03.md
- Q104:I19 concept preregistration: https://github.com/DWR-debug/trading-agent-public/blob/master/research/preregistrations/q104_i19_xbrl_concept_freeze_2026_10_03.json
- Q104:I19 current code path for the census: https://github.com/DWR-debug/trading-agent-public/blob/master/automation/q104_i19_13f_historical_identity_census.py
