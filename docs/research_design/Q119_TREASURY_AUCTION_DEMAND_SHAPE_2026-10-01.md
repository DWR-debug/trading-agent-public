# Q119 — Treasury Auction Demand-Shape State

Status: DESIGN-ONLY / FEASIBILITY

Q119 isolates a dimension not represented by Q104:M6: the shape of the publicly observable Treasury auction demand schedule rather than aggregate demand strength.

Fixed construction:
- upper spread = high yield minus median yield
- lower spread = median yield minus low yield
- shape delta = upper spread minus lower spread
- state = UPPER_WIDE, LOWER_WIDE, or FLAT

The construction uses only Treasury-published fields, requires no fitted coefficient and has no threshold/parameter search. The public-information boundary is record_date.

Q119 is a sibling mechanism to Q104:M6; it does not retune or replace that candidate.

Required next gates: historical archive coverage, publication/record-date semantics, source/PIT mutation tests, and independent reproducibility. No performance, holdout, search, ranking, promotion, or live execution is permitted.

Sources:
- U.S. Treasury Securities Auctions Data: https://fiscaldata.treasury.gov/datasets/treasury-securities-auctions-data/
- TreasuryDirect Auction Search: https://www.treasurydirect.gov/auctions/auction-query/
- Somogyi, Wallen & Xu, What Treasury Auctions Reveal About Investor Demand (2026 revision).