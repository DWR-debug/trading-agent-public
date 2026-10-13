# Q220 — HTTP response representation sensitivity probe

**Registered:** 2026-10-13  
**Purpose:** test one narrow, falsifiable hypothesis about the 55/55 frozen primary-document hash mismatch: the population collector, PIT compiler, and Feed-forensics collector use different HTTP request profiles, and the current SEC endpoint may return a byte representation that varies with User-Agent, Accept, or repeated identical requests.

## Evidence motivating the probe

The frozen Q220 population contains 55 source-document SHA-256 mismatches. In the original population receipt, all 55 downloaded byte counts equal the frozen expected byte counts while every hash differs. In the later current-code PIT/compiler receipt, all 55 responses are exactly seven bytes longer than the same frozen expected lengths. This common-mode pattern is inconsistent with 55 unrelated record-specific parsing problems and supports a bounded test of HTTP representation and repeatability before more source downloads.

For the fixed SPGI 10-K accession 0000064040-19-000059, the prior receipts record:
- expected primary: 4,774,458 bytes, SHA-256 27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83;
- original population capture: 4,774,458 bytes, SHA-256 08039132d6d6d1692d1f7552193c70a04cad4c1dcadad1cfa3ca2b8b4efe3fdb;
- current primary in the later probe: 4,774,465 bytes, SHA-256 2693819652172f0c218394ef036eb3f4af95c2a7077f624f6efcd990df370172;
- original daily-Feed extracted inner TEXT body: 4,774,237 bytes, SHA-256 aa1f89efdf13029de9dd8f7eb020502dd518d4350513d4ef041ba67d902ef368;
- the original Feed submission identity (accession, CIK, form, filing date and PDS identity fields) matched, and exactly one closing TEXT tag existed. The proposed embedded-close truncation explanation was not supported for this sample.

Sources are pinned to the frozen fixture, the immutable single-feed summary, and the prior complete-submission run #38448795085 / artifact #11840230646. No frozen hash or population membership is changed by this registration.

## Fixed experiment

Exactly five requests target only:

https://www.sec.gov/Archives/edgar/data/64040/000006404019000059/spgi-20181231x10k.htm

Each request sets Accept-Encoding: identity and changes only the predeclared profile dimensions:
1. population User-Agent + population Accept (baseline);
2. PIT User-Agent + population Accept (User-Agent contrast);
3. population User-Agent + PIT Accept (Accept contrast);
4. forensic User-Agent + forensic Accept (combined observed profile);
5. repeat the exact baseline (repeatability control).

Limits: exactly 5 request slots, 5,900,000 bytes maximum response read, 30,000,000 bytes aggregate, 60-second request timeout and 1-second spacing. There are no retries, Feed archive downloads, complete-submission downloads, secondary accessions, cache-busting query parameters, or persisted response bodies. The receipt retains hashes, byte counts, edge digests/16-byte edge markers and bounded response metadata only.

## Frozen decision rules

- Any invalid input, non-200 response, oversized/truncated response, or incomplete five-request set yields HTTP_REPRESENTATION_PROBE_INCOMPLETE and a failed closed workflow.
- A complete set with different response body hashes or lengths across a one-variable profile comparison or between the two baseline requests yields HTTP_REPRESENTATION_VARIATION_OBSERVED.
- If all five complete body hashes and lengths match, the classification is HTTP_REPRESENTATION_INVARIANT_AT_PROBE_TIME.

Either complete classification is only a bounded provenance diagnostic. Neither is a source-vintage proof, a Q220 compiler pass, scientific evidence, performance authorization, or authority to change any source hash. If variable response bytes are observed, isolate the exact factor before considering any further retrieval. If responses are invariant, investigate the original population run's historical extraction/input lineage next instead of downloading another multi-gigabyte SEC Feed.

All scientific, performance, holdout-selection, ranking, tuning, promotion, orders and live-execution gates remain false. Paper-only remains mandatory.
