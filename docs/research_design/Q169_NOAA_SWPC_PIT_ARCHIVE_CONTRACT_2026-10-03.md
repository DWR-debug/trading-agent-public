# Q169 NOAA SWPC PIT Archive Contract — 2026-10-03

## Objective

Establish whether the NOAA SWPC channel has a reproducible historical information clock suitable for a future point-in-time candidate study.

The probe is intentionally narrower than a performance study. It verifies official archive reachability, historical file identity, embedded Issue Time, and provider-documented cancellation/correction semantics.

## Fixed archive boundary

Primary archive:
https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/geoalerts/2025/10/

Fixed sample files:

- 20251014GEOA.txt
- 20251015GEOA.txt

The sample is not selected after observing market outcomes. These dates are frozen solely as an archive-integrity probe.

## Information-clock rule

The signal clock is the provider's embedded Issued UTC timestamp. A state may only be considered observable after that timestamp in any future formal study.

The archive file's storage/retrieval time is not substituted for provider Issue Time.

## Revision and cancellation rule

NOAA's Notifications Timeline documents that alerts are plotted at Issue Time, that warnings may be extended, and that cancellations can retract products or end a previously valid warning. It also documents archived alert timelines and the existence of an SWPC product archive.

The present R1 probe verifies the documentation and archive sample, but it does not claim that candidate-specific revision lineage is fully reconstructed.

## Candidate-specific gate still open

Q169 remains non-PIT-validated until both are independently frozen:

1. a fixed operationally-sensitive sector exposure map;
2. a reproducible revision/cancellation lineage for the exact product-state compiler used by the candidate.

No returns, holdouts, asset selection, ranking, parameter search, threshold search, promotion, or live execution are performed.

## Free-resource constraint

Only public NOAA/SWPC/NCEI sources are used. No paid archive or proprietary feed is required or authorized.
