# Q220 — HTTP representation sensitivity result

**Workflow:** [run #38590133217](https://github.com/DWR-debug/trading-agent-public/actions/runs/38590133217)  
**Immutable artifact:** [q220-http-representation-sensitivity-38590133217-1](https://github.com/DWR-debug/trading-agent-public/actions/runs/38590133217/artifacts/11907246485)  
**Receipt fingerprint:** `870aa4fdae7eda932bb8f50ebb9eab1a7781ee503fb5120dea5b0f099e4fd65c`  
**Request fingerprint:** `211b2afacf8eddf0b8b56aaf9ee7896e14d5788ba88e9ada0d98be101158f0e2`  
**Request sequence:** `2026-10-14T15:29:01Z`  
**Status:** `HTTP_REPRESENTATION_INVARIANT_AT_PROBE_TIME`

## Result

The fixed five-request diagnostic completed with five complete HTTP 200 responses to the same pinned SPGI 10-K primary-document URL. The preregistered contrasts varied User-Agent and Accept profiles and included an exact repeat of the baseline.

- All five response bodies had **4,774,457 bytes** and SHA-256 `fc7dfedd605cdbc9e497bb0c0bc306c74e3f90493a68fb6025d762540ef600f3`.
- Total bytes read: **23,872,285**, under the 30,000,000-byte aggregate cap; each response was below the 5,900,000-byte cap.
- No response bodies were persisted.
- No profile comparison and no baseline-repeat comparison differed.
- The observed body matched none of the frozen expected, prior-captured, prior-current, or Feed-extracted hashes/lengths.
- Frozen population and source-receipt fingerprints remained unchanged.

## Interpretation

The bounded observation does not support User-Agent/Accept profile variation or simple repeatability variation as the explanation for this accession's historical hash discrepancy **at probe time**. It does not establish which historical source vintage generated the frozen expected bytes, prove that the current response was the originally captured representation, validate the other 54 mismatches, or resolve any PIT/first-public boundary.

The next useful step is offline tracing of the original population capture/extraction and expected-hash generation lineage. Do not repeat the probe, fetch another primary document, redownload the multi-gigabyte SEC Feeds, rewrite expected hashes, or restart the census.

## Gates

The 55/55 primary-document hash mismatches remain unresolved. The Q220 historical-prefix/PIT compiler and independent reproduction gates remain closed. No source pins, population membership, or production joins changed. No performance authorization, holdout selection, ranking, tuning, promotion, orders, or live execution is authorized.

`PAPER_ONLY=true`; `LIVE_TRADING_ENABLED=false`; `ORDERS_ENABLED=false`; `AUTOMATIC_PROMOTION=false`.
