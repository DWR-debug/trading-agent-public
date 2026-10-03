# Q121-R1 — SEC Reverse Issuer Coverage for Beneficial-Ownership Filings

## Status

SOURCE FEASIBILITY / PIT-ONLY CORRECTION. No performance authorization.

## Falsification that triggered Q121-R1

The original Q121 compiler reads `data.sec.gov/submissions/CIK{issuer}`. SEC documentation describes that endpoint as the submission history for a filer/company CIK, while Schedule 13D/13G filings can be filed by a beneficial owner and identify a different subject issuer.

A concrete SEC filing shows the distinction: an SC 13G/A was filed by Goldman Sachs Group while the subject company was Opendoor Technologies. Therefore the original issuer-submission route cannot be treated as a complete issuer-level population.

The historical Q121 receipt is preserved as historical and is not retroactively upgraded.

## Objective

Establish a deterministic, public, issuer-oriented SEC source route that can enumerate Schedule 13D/13G filings for a fixed issuer independently of the issuer's own submission-history feed.

The primary source route is the SEC EDGAR company browse endpoint with a fixed issuer CIK, explicit form type and fixed date bounds. Results are paginated deterministically. A bounded sample of returned filing detail pages is then checked for subject-CIK identity, filer-CIK identity, form and acceptance-time availability.

## Fixed universe

The existing Q107 frozen universe is reused only for mechanism/source feasibility:

SPGI, NDAQ, AMP, RJF, WMB, VLO, DVN, EMN.

The CIK mapping is frozen at runtime from the SEC company-ticker registry and recorded in the immutable receipt. Any later formal study must preserve an ex-ante issuer CIK map.

## Fixed source contract

For each issuer and each form in:

- SC 13D
- SC 13G
- SC 13D/A
- SC 13G/A

query the SEC company browse route with:

- issuer CIK;
- fixed form type;
- `datea=20240205`;
- `dateb=20250924`;
- `owner=exclude`;
- `output=atom`;
- fixed page size;
- monotonically increasing `start` pagination.

The source response is hashed. Every discovered filing row preserves accession number, filing date, filing type and SEC filing-detail URL.

## Identity contract

A fixed sample of filing-detail pages is selected by deterministic ordinal positions only (first, middle, last when available). The detail page must expose:

- Subject CIK equal to the frozen target issuer CIK;
- Filed-by CIK separately;
- form equal to the requested form family;
- accepted timestamp available.

Any mismatch is fail-closed.

## PIT contract

The acceptance timestamp, not the filing-date display alone, is the PIT clock. A future formal event compiler must:

1. parse EDGAR acceptance timestamps explicitly as Eastern Time;
2. require filing-date equality with the acceptance calendar date;
3. classify 17:30 ET / 22:00 ET boundaries exactly;
4. map only to the first XNYS session strictly after the acceptance calendar date.

Q121-R1 itself does not calculate returns and does not use holdout information.

## Required next gate

If the reverse issuer route and identity sampling are structurally successful, the next gate is a separately frozen all-filing historical acquisition/acceptance-time compiler with independent reproduction.

A successful source feasibility receipt does not authorize performance.
