# External Research Inspiration — 2026-09-30

This document records current literature-based design inspiration only. These sources
are external context, not project evidence and not candidate rankings.

## State-dependent predictability

Cong, Feng, He and Wang (NBER Working Paper 35158, 2026) argue that return
predictability is asset-specific and state-dependent. Their framework identifies
different persistent "mosaics" where signals behave differently, rather than
assuming a single unconditional relation across all stocks.

Project use:
- investigate deterministic state descriptors as conditioning context rather than
  another optimizer;
- test whether an existing signal's failure is concentrated in identifiable,
  ex-ante states before changing the signal;
- keep state definitions fixed and avoid learning the state partition from holdout
  outcomes.

Source: https://www.nber.org/papers/w35158
SSRΝ: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6705515

## Pure-news residual

Didisheim, Kelly, Pourmohammadi and Tian (NBER Working Paper 35093, 2026)
report that news itself is partly predictable from prevailing stock
characteristics. After removing the predictable component, their "pure news"
residual has substantially stronger return predictability.

Project use:
- C31 should not stop at raw sentiment;
- first define an observable, PIT-safe baseline for expected news content;
- treat the residual as the actual experimental object;
- require a public historical corpus and stable article identifiers before formal
  admission.

Source: https://www.nber.org/papers/w35093
SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6610736

## Shareholder experience

Riley and Zhou (2026) reconstruct shareholder-weighted cumulative return,
average return and gain/loss experience from daily price and volume histories.
Their paper is especially useful because the signal can, in principle, be explored
with the project's existing OHLCV infrastructure without relying on proprietary
text feeds.

Project use:
- treat current-holder experience as distinct from raw momentum;
- examine whether existing Q082:C22-C25 mechanisms are best interpreted as
  behavioral-state variables rather than another return transform;
- investigate whether holder-experience state can serve as an ex-ante context
  variable for orthogonal information signals.

Source: https://www.sciencedirect.com/science/article/pii/S1057521926002942

## Risk-text peer propagation

Yuan and Zhang (2026) construct peer links from similarity in 10-K risk
disclosures and report return predictability through risk-similar peers.

Project use:
- maintain C30 as a peer-network mechanism, but explicitly test whether any
  eventual effect is driven by risk similarity rather than industry membership;
- preserve filing acceptance timestamps and amendment chains;
- avoid current-industry substitution.

Source: https://www.sciencedirect.com/science/article/pii/S092753982600068X

## Foreign-institution information flow

Twongirwe, Bakundana and Masimengo (2026) compare short-term foreign and domestic
institutional ownership changes and report different predictive relationships.

Project use:
- evaluate foreign/domestic ownership as an information-flow state;
- deduplicate against Q073:I7/Q078 institutional-ownership designs;
- preserve 13F publication lag and manager identity.

Source: https://www.sciencedirect.com/science/article/pii/S3050700626000654

## Anomaly timing / publication boundary

Bowles, Reed, Ringgenberg and Thornock (2026) report that some anomaly signals are
themselves predictable before their formal publication.

Project use:
- explicitly distinguish the economic signal date from the first public
  availability date;
- audit whether a supposedly PIT-safe feature embeds information that would only
  have been public later;
- treat early-information contamination as a first-class falsification test.

Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4939779

## Index-reconstitution demand

Kuo, Shiu and Zhang (2026) document price pressure around S&P 500 index
reconstitutions and discuss mechanical passive-flow channels.

Project use:
- retain M5 as an event-mechanics research branch rather than a generic momentum
  variable;
- preserve announcement/effective timestamps separately;
- look for pre-event versus post-effective asymmetry using only frozen public event
  information.

Source: https://link.springer.com/article/10.1007/s11156-026-01513-w

## Methodological rule

External literature may generate hypotheses, data contracts and falsification
tests. It does not authorize performance, alter gates, choose assets, choose
parameters or promote a candidate.

Safety:
PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
