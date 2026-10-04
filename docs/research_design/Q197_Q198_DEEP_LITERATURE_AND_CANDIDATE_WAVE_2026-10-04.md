# Q197-Q198 Deep Literature & Candidate Wave — 2026-10-04

## Q197 — government-demand shock propagation

Research motivation: public-procurement events can carry information about expected demand and firm prospects, while shocks involving government customers have documented spillovers through economically connected firms. This wave treats that literature only as mechanism motivation; it does not constitute evidence for this candidate.

Relevant literature located:
- "Trading on government contracts: The investment potential of public procurement awards" (Economics Letters, 2025): reports an association between contract awards and subsequent stock performance and examines contract size.
- Research on government procurement and stock-market synchronicity reports lower synchronicity around procurement information, with stronger effects for larger contracts.
- Research on firms' government-customer exposure links government relationships to stock-price crash-risk properties.
- Evidence from a government ban affecting ZTE documents spillovers to suppliers, customers and competitors.

Official source path:
- USAspending provides a public API with award, recipient and transaction endpoints and explicitly states that its endpoints currently do not require authorization.
- The API exposes a last-update endpoint and a data dictionary. These are source-feasibility inputs only; they do not prove historical point-in-time reconstruction.

Scientific gate:
The decisive issue is not whether USAspending contains award dates. The decisive issue is whether a historical observer can know the award state at the exact public-information boundary used by the strategy. A future database correction must not alter the historical prefix. Award/action dates therefore cannot be substituted for public-observation timestamps without an independently justified contract.

## Q198 — Federal Register public-inspection → publication → effective stage gap

Official Federal Register/NARA guidance states that documents that publish in the daily Federal Register must be filed for public inspection at least one business day before publication, and that the public-inspection record carries a day/hour filing notation. The official filed version is the controlling record; online posting can occur later. This makes public inspection a potentially earlier and more precise information boundary than publication.

The Federal Register also provides a public API, and current documents expose publication metadata. The research design therefore separates:
1. official public-inspection filing timestamp;
2. Federal Register publication date;
3. explicit effective date.

The event-time contract must use the official filing time, not the later online-posting time, and must fail closed where filing time, correction lineage or document identity cannot be reconstructed.

## Governance

Both candidates are design/source-feasibility only. No market returns are read, no candidate ranking or asset selection is permitted, and no performance authorization exists. The next gate is a fixed historical archive/clock census followed by independent event-time reproduction.

Primary official references:
- https://api.usaspending.gov/docs/endpoints
- https://api.usaspending.gov/
- https://www.federalregister.gov/developers/documentation/api/v1
- https://www.archives.gov/federal-register/faqs
