# Q072 — Information-Source Candidate Bank — 2026-09-28

## Status

**DESIGN_ONLY**. No candidate has been ranked, backtested, selected or promoted by Q072.

Q072 converts the successful Q071 source-feasibility sweep into explicit candidate mechanisms. The intent is to obtain information orthogonal to the existing price-only alpha families.

## Candidate set

| ID | Mechanism | Core information channel | PIT anchor |
|---|---|---|---|
| I1A | Abnormal short-volume shock | FINRA Reg SHO | daily file public-availability |
| I1B | Short-volume shock × same-day return | FINRA + price | daily file public-availability |
| I2A | Insider purchase breadth | SEC Form 4 | EDGAR acceptance datetime |
| I2B | Insider purchase dollar imbalance | SEC Form 4 | EDGAR acceptance datetime |
| I3A | First-vintage macro revision | ALFRED | vintage date |
| I4A | COT crowding change | CFTC | actual public-release date |
| I5A | Wikipedia attention shock | Wikimedia | completed day |
| I6A | Media negativity/attention shock | GDELT | archived export |
| X1 | Insider purchase + low/normal attention | SEC + Wikimedia | max of source cutoffs |
| X2 | Short-flow vs insider-flow disagreement | FINRA + SEC | max of source cutoffs |

The set is deliberately unranked.

## Why the mechanisms are plausible

Classic research finds short-selling activity can predict future returns; one line of interpretation is informed trading, while other work highlights liquidity provision and reversal channels. citeturn714199search0turn714199search5

Classic insider-trading studies consistently distinguish open-market purchases from less informative transaction classes, making Form 4 transaction coding materially important for a clean candidate. citeturn296228search2turn296228search8

Vintage-aware macro data can retain information that is erased by later revisions; this is precisely why ALFRED-style point-in-time reconstruction matters. citeturn714199search3turn987085search2

Wikipedia pageviews have been studied as an investor-attention proxy, while media-tone work—including recent GDELT-based research—suggests that abnormal tone/attention can contain return information. These are hypotheses for this project, not established evidence for our universe. citeturn714199search8turn714199search4

CFTC COT provides a long historical positioning record and explicitly distinguishes report dates from release dates, which makes it usable only with a separate public-availability ledger. citeturn987085search3turn987085search6

## Research sequence

Each candidate must pass:

1. source coverage/schema;
2. exact public-availability PIT contract;
3. frozen entity/universe mapping;
4. mutation PIT;
5. only then a separately authorized fresh disjoint performance trial.

No holdout selection or post-hoc sign/threshold choice is permitted.

## Unusual approaches retained

X1 tests whether insider information has different predictive content when public attention is not simultaneously elevated.

X2 treats disagreement between two independent information-flow channels as a state variable rather than assuming one source dominates the other.

Both are exploratory and require separate preregistration before performance testing.
