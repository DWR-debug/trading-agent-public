# Deep Public Digital / Physical Frontier — 2026-10-03

This wave extends discovery into operational telemetry and scientific event systems that have their own timestamps and are not constructed from market prices.

## Q166 — Package-download shock × software issuer exposure

PyPI Stats exposes daily download time series and is sourced from public PyPI download data. The current service retains 180 days; the underlying BigQuery tables are documented as a larger free historical source. This is promising as a technology-adoption state, but CI/CD traffic and mirrors create measurement error. The first gate must quantify those distortions and freeze a package-to-issuer map.

## Q167 — Scientific-publication burst × R&D exposure

Crossref provides a public REST API with deposited scholarly metadata, including publication and deposit/update dates. A mechanically defined burst in publications or technical output can be mapped to a fixed issuer R&D universe only through predeclared author/affiliation or funding relationships. Publication date and deposit/index timestamps must not be conflated.

## Q168 — Seismic shock × geographic industrial exposure

USGS's Earthquake Catalog exposes machine-readable event times in UTC and supports date-constrained queries. A candidate state can combine unusual seismic events with a frozen operating-location map. The event origin time is not automatically the same as the time the market could observe the final event record, so the information boundary must use the earliest proven public timestamp or next-session use.

## Q169 — Space-weather shock × operationally sensitive sector

NOAA SWPC publishes alerts, warnings and product archives, and the notification timeline records issue times plus corrections/cancellations. This permits a clean event-state design for sectors exposed to satellite, radio, power-grid or aviation disturbances, provided those exposures are frozen independently of future returns.

## Q170 — Wildfire/thermal anomaly × geographic industrial exposure

NASA FIRMS provides active-fire products and an archive. It explicitly notes that near-real-time observations may later be replaced by standard science-quality data. The PIT contract therefore has to distinguish initial public availability from later scientific revision and never use revised detections to backfill an earlier decision point.

## Falsification ideas

Use only fixed event definitions and no return-based tuning. Examples:
- future-dated package-download rows must not alter earlier daily states;
- future Crossref deposits must not alter a previously frozen publication state;
- newly revised earthquake event metadata must not change an earlier public state unless its revision timestamp is later than the decision point;
- NOAA SWPC cancellations must terminate only from the time the cancellation was public;
- FIRMS NRT-to-science-quality replacements must not leak later quality information backward.

All five remain discovery-only and require independent source/PIT feasibility before any formal study.
