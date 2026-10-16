# Q221 — exact FPDS URL Wayback CDX metadata probe R1

**Preregistered:** 2026-10-16T12:15:45Z  
**Mode:** one-shot archive-index metadata feasibility  
**Request scope:** four exact URLs and four maximum HTTP requests; no origin or replay access.

## Why this is a distinct route

The previously preregistered Arquivo.pt TimeMap query for these same four FPDS Atom URLs returned HTTP 404 for all four keys. That result was a metadata-route failure, not a source no-hit and not evidence that the archive never captured the URLs. SAM.gov remains unavailable for a probe because the protected project API-key preflight found no configured key. This work therefore tests only the independent Internet Archive Wayback CDX index, using the exact four frozen URL values from the Arquivo.pt R2 preregistration.

The official Wayback CDX documentation says the endpoint returns capture-index metadata, supports an exact URL match by default, and requires the url parameter to be URL-encoded when the original URL contains a query string. The probe makes that matching mode explicit and does not expand to prefixes, domains, neighboring query strings, or additional transaction keys.

## Frozen, bounded method

The probe reads the four records and original URLs from the preregistered input contract and validates their exact keys against the canonical 348-row Q221 boundary manifest before any network access. It sends exactly one HTTPS GET to the Wayback CDX endpoint per exact original URL, for at most four requests. It asks for timestamp, original, mimetype, statuscode, digest, and length as JSON metadata, with a 1,000-row per-URL limit.

Each response is capped at 512 KiB, all responses together at 2 MiB; timeout is 45 seconds, request starts are separated by at least one second, automatic retries are zero, and redirects are not followed. Response bodies are parsed in memory only. The receipt contains bounded capture metadata, response byte counts and SHA-256 digests, not raw response bodies. There are no requests to FPDS, Arquivo.pt, SAM.gov, USAspending, SEC, Common Crawl, or any Wayback replay URL; no archive payload is downloaded.

## Interpretation boundary

A valid CDX row proves at most that the archive index returned capture metadata for that exact URL. Its timestamp is an archive observation, **not** the transaction's first-public timestamp. Even a status-200 capture requires a separate preregistered replay inspection to verify the exact PIID, modification number, action date and recipient tuple in the archived payload. A valid header-only response is a no-capture result for this exact CDX query only; it is not proof of historical absence from other URLs or public channels. HTTP errors, timeouts, malformed responses or response-limit violations are incomplete lookups and cannot be classified as no-hit.

The frozen 348-row population and all target keys remain unchanged. Historical first-public time remains unproven for 348/348 rows; 247 recipient-to-issuer mappings remain unfrozen. All research/performance gates remain closed. Paper-Only, zero live orders, no performance authorization, no holdout selection, no ranking, no tuning and no promotion remain enforced.

## Official and frozen references

- Internet Archive, Wayback CDX Server API documentation: https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md
- Frozen Q221 boundary manifest: research/evidence/q221_historical_public_boundary_latest.json
- Prior Arquivo.pt query contract: research/preregistrations/q221_arquivo_pt_fpds_timemap_probe_r2_2026_10_16.json
- Prior Arquivo.pt R2 receipt: research/evidence/q221_arquivo_pt_fpds_timemap_r2_latest.json
- SAM.gov credential preflight: https://github.com/DWR-debug/trading-agent-public/actions/runs/38896450256

