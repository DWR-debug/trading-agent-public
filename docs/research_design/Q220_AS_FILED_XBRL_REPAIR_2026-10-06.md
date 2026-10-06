# Q220 — Clean historical as-filed SEC-XBRL repair

The previous Q220 gate is not promoted. It checked a single flattened Financial Statement and Notes archive schema. The clean repair therefore changes the authoritative lineage route to raw historical SEC filing artifacts.

The SEC describes the Financial Statement and Notes Data Sets as "as filed", but also says the data are flattened and do not reflect all metadata available in the filings. Q220 needs the omitted lineage: acceptance time, accession identity, filing-local taxonomy, narrative TextBlock facts and presentation relationships.

## Frozen source contract

- Universe: SPGI, NDAQ, AMP, RJF, WMB, VLO, DVN, EMN with fixed CIKs.
- Window: 2019-01-01 through 2025-09-24.
- Event population: original 10-K. 10-K/A remains separate amendment/correction state.
- PIT clock: SEC archived acceptance datetime.
- Raw artifacts: quarterly full-index row, header, index.json, primary HTML, extension XSD, presentation linkbase, available XBRL instance.
- Narrative primitive: filing-local ix:nonNumeric concepts whose local name ends in TextBlock.
- Structural primitive: filing-local presentation relationships.
- Structured controls: fixed exact QNames; no label, embedding, or taxonomy-neighbor substitution.

## Gates

1. Historical full-index population coverage.
2. Raw archive recovery per accession.
3. Acceptance datetime recovery.
4. Primary document + extension taxonomy + presentation recovery.
5. Deterministic TextBlock extraction and Presentation mapping.
6. Explicit 10-K/10-K/A separation.
7. Immutable artifact fingerprints.
8. Mutation/future-data checks and independent reproduction before any performance phase.

## Orchestration

The Top-4 Q220 lane performs local contract QA only. A bounded route probe runs every six hours on hosted x64 slot 1; the complete historical population runs on the self-hosted research pool under a single concurrency group. This avoids repeated SEC network scans every 15 minutes.

## Re-upgrade rule

Q220 remains blocked from performance authorization until the raw as-filed population and deterministic TextBlock/Presentation lineage gates pass, followed by an unchanged independent reproduction.

Sources:
- https://www.sec.gov/data-research/sec-markets-data/financial-statement-notes-data-sets
- https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
