# Q104:I22 — immutable reconciliation pin repair

**Date:** 2026-10-14
**Blocked independent reproduction:** https://github.com/DWR-debug/trading-agent-public/actions/runs/38524502869
**Blocked diagnostic fingerprint:** 3a0eb2f656f11833d47d1aa28c78786c90c2f642471318cd0e076e2344b23c38

## Root cause

The independent reproduction is pinned to compiler run #38274043682, source commit 65c879498e3f5d494e1d6c9749418bc0bf137a31, and reconciliation fingerprint 058bba7fd9aebb9d30cc5294fc71548ebe9bd9f11d5ee38a558936b29ecfb9a0. It also downloads the x64 and ARM64 compiler artifacts from that same run.

The reproduction code nevertheless read the mutable file research/evidence/q104_i22_cross_arch_reconciliation_latest.json. Subsequent successful compiler runs replace that latest pointer with different run IDs and fingerprints. Run #38524502869 therefore stopped with I22_RECONCILIATION_PIN_MISMATCH before any HTTP/source request (request_count=0, downloaded_bytes=0). This is an implementation/provenance defect, not a negative PIT finding and not a successful independent reproduction.

## Repair

The original 1,853-byte receipt from run #38274043682 is preserved byte-for-byte as research/evidence/q104_i22_cross_arch_reconciliation_38274043682.json. The independent reproduction now reads that versioned file, with a unit test guarding against regressions to the mutable latest pointer.

The Q107 coverage fingerprint and snapshot, Q108 integration receipt, fixed issuers/forms/window, acceptance-time rule and existing mutation tests remain unchanged. A future successful run is still only a non-authorizing independent PIT/compiler reproduction and must pass the separately required mechanism non-overlap review. Performance, holdout selection, ranking, tuning, promotion, orders and live execution remain prohibited.