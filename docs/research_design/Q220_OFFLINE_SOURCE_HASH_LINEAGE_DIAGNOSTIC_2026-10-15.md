# Q220 — offline source-hash lineage diagnostic

**Registered:** 2026-10-15  
**Mode:** bounded offline forensic synthesis; not scientific evidence or performance research  
**Candidate status:** `BLOCKED`; the historical representation/PIT gate remains closed.

## Frozen identity

- Candidate: Q220, fixed eight-issuer source population, 55 frozen records.
- Population receipt: `158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543`.
- Original fixture receipt: `c7fc53c9ef2daaef9caee29c0ba1084602c0bf4b24c6d2a13cb812b7b592c075`.
- Current committed compiler receipt: `1ca885190d7b277c809ac8a6c3386a637e7750df6bb51755260c9bd7351f868d`, pinned to the receipt generated at 2026-10-15 04:41:43 UTC.
- Target accession: `0000064040-19-000059`, issuer CIK `0000064040`, Form 10-K, filed 2019-02-13, `spgi-20181231x10k.htm`.
- Expected source-document hash: `27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83` for 4,774,458 bytes.

## Pinned whole-document observations

| Evidence | SHA-256 | Bytes | Interpretation |
|---|---|---:|---|
| Original forensics receipt | `08039132d6d6d1692d1f7552193c70a04cad4c1dcadad1cfa3ca2b8b4efe3fdb` | 4,774,458 | Historic capture observation; does not prove authoritative vintage |
| Five-response HTTP sensitivity probe, run 38590133217 | `fc7dfedd605cdbc9e497bb0c0bc306c74e3f90493a68fb6025d762540ef600f3` | 4,774,457 | Five complete responses were identical across the pinned request profiles and repeat |
| Current compiler observation | `ccd9060d023c3ca8e5fc5d3fd43a67c394dfd97ef1e42a72f71c4ca630cd2f63` | 4,774,465 | Later response recorded by the current compiler |
| Single-feed boundary observation, run 38446029194 | `2693819652172f0c218394ef036eb3f4af95c2a7077f624f6efcd990df370172` | 4,774,465 | Separate bounded observation |

The four whole-document hashes have the same pinned URL and the same `Last-Modified` value (`Wed, 13 Feb 2019 11:02:53 GMT`) in their respective records. The frozen expected hash has not been reproduced. A stable `Last-Modified` header is not proof that the entity body is historically identical or that any capture is the authoritative source vintage.

Other content hashes, such as an embedded full-submission member and extracted Inline XBRL TextBlock, have different byte scopes and are never counted as whole-document hashes.

## Execution contract

The workflow reads only these pinned immutable inputs:
- Forensics run 38254139755, artifact 11749259509.
- Header-only evidence run 38258251764, artifact 11751436149.
- Five-response HTTP sensitivity run 38590133217, artifact 11907246485.
- The compiler and summary JSON already committed in this repository.

It must not request another SEC Feed or primary document, rewrite any expected hash, change population membership, restart the census, or patch the compiler to turn the result green. Both x64 and ARM64 must reproduce the same deterministic analysis fingerprint before a committed evidence receipt is published.

## Decision boundary

A successful workflow means only that the frozen inputs and deterministic diagnostic reproduced across architectures. The expected hash remains unreproduced; source-vintage identity remains unproven; all 55 compiler failures remain unresolved; Q220 historical PIT and independent reproduction gates remain closed. No performance, holdout-selection, ranking, tuning, promotion, orders, or live execution is authorized.

`PAPER_ONLY=true`; `LIVE_TRADING_ENABLED=false`; `ORDERS_ENABLED=false`; `AUTOMATIC_PROMOTION=false`.
