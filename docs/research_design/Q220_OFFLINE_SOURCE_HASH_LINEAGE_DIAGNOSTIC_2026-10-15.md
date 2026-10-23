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


## Original expected-hash capture provenance — offline audit, 2026-10-15

The initial population run and the later body-bearing submission audit were inspected using existing run logs and artifacts only. No SEC request was made for this audit.

### What the original population run actually preserved

- Original population run: [#38155914188](https://github.com/DWR-debug/trading-agent-public/actions/runs/38155914188), checkout `ce80a06b713c26bd636ef954e51b69458deaa3e5`, result generated at **2026-10-11 17:36:13 UTC**, immutable artifact [#11710195878](https://github.com/DWR-debug/trading-agent-public/actions/runs/38155914188/artifacts/11710195878).
- The run-time code in `automation/q220_as_filed_xbrl_population_gate.py` selects the primary filename, issues `fetch(f"{base}/{primary}")`, then records `primary_document_sha256=sha256(p)` and `primary_document_bytes=len(p)`. For the target SPGI 2019 accession the committed row is 4,774,458 bytes and expected SHA-256 `27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83`.
- The capture artifact contains a JSON receipt, not the response body. Its per-row entry contains the hash and length but no raw bytes, per-document HTTP timestamp, ETag, or response metadata sufficient to reconstruct the received entity. The runner stdout retained only the aggregate success summary; it did not retain per-accession bytes or response metadata.
- `primary_document_source=company_submissions_recent` identifies the filename-selection route, not the response-body vintage. The field `raw_archive_as_filed=true` was emitted by the population code, but the persisted evidence does not independently establish that the bytes fetched from the current accession URL were the immutable bytes originally accepted by EDGAR.

### Later artifact scope — what it does and does not establish

The same run's separate route artifact [#11712140975](https://github.com/DWR-debug/trading-agent-public/actions/runs/38155914188/artifacts/11712140975) was generated at **2026-10-11 18:49:19 UTC**. It is an eight-issuer route sample of recent original 10-Ks; the SPGI row is the 2025 accession `0000064040-25-000052`, not the 2019 target. It therefore cannot be used as a second timestamped body/hash observation for the 2019 target.

The later Complete Submission Representation Audit [run #38619590525](https://github.com/DWR-debug/trading-agent-public/actions/runs/38619590525) did retain exact bounded `<DOCUMENT>` blocks for three samples in immutable capture artifact [#11921560717](https://github.com/DWR-debug/trading-agent-public/actions/runs/38619590525/artifacts/11921560717), and its separate offline verification artifact [#11922195517](https://github.com/DWR-debug/trading-agent-public/actions/runs/38619590525/artifacts/11922195517) confirms deterministic replay with zero network requests. Those are present-day Complete-submission representations captured on 2026-10-14, not a retained body from the original 2026-10-11 direct-primary response.

For the SPGI 2019 target, the verified block contains a `<TEXT>` body of **4,774,237 bytes** with SHA-256 `aa1f89efdf13029de9dd8f7eb020502dd518d4350513d4ef041ba67d902ef368`; the original expected primary hash is 4,774,458 bytes. The Complete-submission body reproduces the previously extracted original-Feed TEXT hash, but neither reproduces the frozen expected hash. It must not be relabeled as the same whole-primary byte representation.

### Provenance conclusion

The frozen expected hash was computed from the direct primary URL response during the original run; however, its original response bytes were not retained. Existing artifacts can reproduce several later, different body representations but cannot recover or independently hash the exact original response bytes. The evidence supports **missing original-body provenance**, not a proved correct replacement hash and not a proved universal explanation for all 55 rows.

The four observed whole-primary hashes remain distinct, all 55 source-hash failures remain unresolved, and Q220 remains blocked. The population must not be rerun or restarted for this question. No frozen hash, population member, compiler rule, production join, or research gate was changed.
