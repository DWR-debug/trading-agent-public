# Q104:I19 — CIK-role lineage diagnostic: one frozen residual (2026-10-12)

**Disposition:** `CIK_ROLE_LINEAGE_OBSERVED_GATE_UNRESOLVED`  
**Candidate:** `Q104:I19`  
**Scope:** Retrospective adjudication of one already-executed, accession-pinned diagnostic. No source request was made for this memo.

## Immutable evidence reference

- Original workflow: [Q104 I19 Frozen CIK-Role Lineage Diagnostic, run #38268214126](https://github.com/DWR-debug/trading-agent-public/actions/runs/38268214126), completed successfully on 2026-10-12.
- Retained workflow artifact: [artifact 11755667121](https://github.com/DWR-debug/trading-agent-public/actions/runs/38268214126/artifacts/11755667121), `q104-i19-cik-role-lineage-diagnostic-38268214126-1`. It contains `38268214126/receipt.json`; artifact retention is finite.
- Receipt fingerprint: `fced71e722d65b6ec82a489e74d9e926a17414643bd79a09cd1caa67ee7b8294`.
- SHA-256 of the original extracted JSON bytes: `a2966ed0bca54954f788622cb7653e002f704e055715b9027e875117b8b0637d`.
- Frozen upstream source census: run #38168441086; shard `2024-2025-09`; shard-receipt fingerprint `2500f2ee3f07258a9525cd6e7018fd67f380cf0244028c5948866d55c835794e`.
- Pinned SEC Form 13F quarterly archive: `01mar2024-31may2024_form13f.zip`; expected and observed size 78,174,865 bytes; SHA-256 `fe723ad7d3e58f7e5f0bb3d5e46158c4c3bacc8a23a69b2d6eef3c97782d5cf8`; the run verified byte identity.
- The diagnostic recorded 78,255,719 total source-download bytes and nine bounded EDGAR header probes. Those are historical run facts, not authorization to repeat any requests.

## Observed field disagreement

Frozen accession: `0001493152-24-018939`  
Form: `13F-HR`  
Filing date: `2024-05-13`  
Period of report: `2024-03-31`

| Evidence field/path | Observed value | Diagnostic meaning |
|---|---|---|
| Frozen SEC bulk `submission.tsv` CIK | `0001960050` | CIK stored in the quarterly archive row |
| Accession-prefix CIK | `0001493152` | Candidate directory CIK derived from the accession prefix; not validated as filer CIK |
| EDGAR header filer CIK consensus | `0002094379` | Same parsed filer CIK across all six successful header-route observations |
| EDGAR `ACCEPTANCE-DATETIME` | `2024-05-13T16:57:35` | Consistent event timestamp across the three header formats observed |
| Embedded XML CIKs found by the frozen extraction contract | none | This parse supplied no embedded CIK-role corroboration |

The archive row CIK `0001960050` and EDGAR header filer CIK `0002094379` do not match. The three routes requested under each of these two CIK paths returned HTTP 200 and yielded identical response bytes by route type:

| Route | Response bytes | SHA-256 | Observed result |
|---|---:|---|---|
| `*-index-headers.html` | 3,025 | `491ba892234db82a8d7816aa75f957c7129ce1fdde84343b91ce3e697c3876d0` | HTTP 200; accession, form, header filer CIK, filing date and acceptance time parsed |
| `*.hdr.sgml` | 852 | `5d83495f6252488d8a947885c99da3f66841cbcc367419b4b590bd30559eaf8c` | HTTP 200; same parsed identity/time fields |
| `*.txt` header prefix | 8,192 | `6f4b616d36fffd4a0c8c7c8837bf87b4288584f2184ed972a8834b648518540b` | Bounded header prefix captured; same parsed identity/time fields |

The same three route types returned HTTP 404 and zero response-body bytes when the path used accession-prefix CIK `0001493152`. The observed route outcomes are consistent with a path-namespace problem in this one case, but they do not establish what semantic role the bulk-row CIK represents or prove that a new CIK-substitution rule is correct.

The one complete-submission response retrieved in that prior diagnostic was 56,716 bytes, SHA-256 `df64e6708b688f253f3945caf1bfb1109c866e14d6a11b632ee0b2e917d0e403`. Its observed `Last-Modified` header was `Tue, 24 Feb 2026 11:00:52 GMT`, later than the filing's 2024 acceptance timestamp. This current representation is not contemporaneous evidence of the filing's first public observation time.

## Adjudication

This one-case trace proves only that the frozen bulk row and currently returned official EDGAR header values disagree on the CIK field, while the header routes returned the same parsed filer CIK. It does **not** prove a general CIK mapping, legal-role equivalence, accession ownership semantics for the full population, historical PIT validity, or the first-public-observation time.

Do not:
- substitute the accession prefix, archive-row CIK, or header CIK for another namespace by assumption;
- generalize from this single accession, infer a legal role from numeric similarity, or modify frozen candidate/security identity rules;
- change the frozen 53-residual census, repair its receipts, or start the Q104:I19 PIT compiler / independent reproduction on this result alone;
- issue another SEC request for this already-probed diagnostic merely to refresh the observation.

## Gate and safety state

The original receipt explicitly recorded:

- `identity_discrepancy_resolved = false`
- `candidate_identity_gate_cleared = false`
- `historical_pit_gate_cleared = false`
- `acceptance_time_gate_cleared = false`
- `frozen_population_changed = false`
- `scientific_evidence = false`
- `performance_authorization = false`
- `holdout_selection = false`
- `ranking = false`
- `tuning = false`
- `promotion = false`
- `live_execution = false`
- `paper_only = true`; `live_trading_enabled = false`; `orders_enabled = false`

**Decision:** keep Q104:I19 blocked on the seven frozen CIK/form identity conflicts and ten complete-submission HTTP 404 records (alongside the separately reviewed 36-row non-destructive date-mismatch sidecar). The original artifact is the full receipt source; this memo is a durable summary of that already observed result, not a replacement receipt or new scientific evidence.
