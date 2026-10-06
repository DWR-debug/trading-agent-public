# Top-4 Active Capacity Wave — 2026-10-06

## Zweck

Die automatische Forschungskapazität ist auf Q218, Q219, Q220 und Q221 konzentriert. Freie Ressourcen werden nur mit kandidatspezifischen, bounded source/PIT/structure workpacks belegt. Bereits erfolgreiche Source-Probes werden nicht als Füllarbeit wiederholt.

## Automatische Kapazität

- 3 Self-hosted Windows slots: parallel, bis zu drei unabhängige Top-4 candidates.
- GitHub-hosted x64: unabhängige Top-4 audit lane.
- GitHub-hosted ARM64: unabhängige Top-4 audit lane.
- Free AI fabric: vier candidate-specific adversarial reviews; output has no scientific authority.
- S10/Android: no scientific authority; only bounded mechanical support where useful.

## Reproducibility

Every Top-4 matrix job checks out `github.sha`, records `source_commit`, `workpack_contract_version`, `workpack_purpose`, `workpack_gate_paths` and a receipt fingerprint. This prevents a running job from silently switching to a later `master` state.

## Current workpacks

- **Q218:** SEC multi-channel source population using 10-K plus 8-K Item 2.02, acceptance timestamp census, then deterministic event pairing and amendment lineage.
- **Q219:** Q129 options PIT/source checks plus explicit breadth gate. Current verified Q129 release contains only SPY/QQQ/IWM; broader individual-equity coverage is not yet proven.
- **Q220:** SEC Financial Statement Notes archive schema plus as-filed XBRL concept freeze and narrative/structured mapping. Real 2009q1 archive uses `.tsv` members.
- **Q221:** USAspending publication-clock semantics, including agency-specific delay exceptions, plus recipient/entity mapping and transaction lineage.

## Research boundary

`PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `ORDERS_ENABLED=False`, `AUTOMATIC_PROMOTION=False`.

No Top-4 workpack performs return-based ranking, holdout selection, tuning, threshold/horizon search, promotion or live execution.

## Stale-run policy

The Top-4 workflow uses `cancel-in-progress: true` so obsolete workpacks are replaced when a newer gate state is committed. This is a provenance/efficiency rule, not a scientific conclusion.

## Negative evidence

Q219's currently verified breadth gate is unresolved rather than silently treated as broad coverage. Q220's first dedicated network probe hit SEC HTTP 403 under concurrent access while the existing historical census reached the same archive successfully; the workpack was hardened accordingly. Q221's public-clock source is valid for structure but historical applicability and agency exception classification remain gates.

## Automatic AI trigger

The Free AI Worker Fabric is triggered by changes to its worker implementation, candidate-specific Top-4 source gates and Top-4 task files. Each task declares its own immutable context so the worker does not depend on a fragile global mapping for new Top-4 reviews.
