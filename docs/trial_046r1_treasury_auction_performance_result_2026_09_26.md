# T-2026-09-26-046R1-PERFORMANCE — Q020 Treasury Auction Performance

Status: NO_PROMOTION_EVIDENCE

Workflow: 36243099900
Artifact: 10905988662
Artifact SHA256: sha256:d219a32546752d62b09a9cf17fde147f620efe3a3ae524c840b4a79495d2cfc1
Result fingerprint: 0ee05b7933572b6f5e9307436e87844ff6ca92180d00e4139da0814e231b9952

## Evidence contract

The fixed Q020 Treasury 10-Year auction-demand signal was executed without parameter, asset, threshold, horizon, variant, or holdout selection.
The run used the validated Q020 frozen repair snapshot and the Q019 source/signals fingerprints.
The evaluation retained the preregistered research/holdout geometry, five rolling windows, cost scenarios, and paper-only safeguards.

## Result

The formal result is NO_PROMOTION_EVIDENCE. The complete immutable result JSON is preserved in Actions artifact 10905988662 and the compact provenance checkpoint in `research/checkpoints/t046r1_treasury_auction_performance_2026_09_26.json`.

Result interpretation is limited to the preregistered evidence contract. No promotion, tuning, or safety change follows from this run.

## Next step

Run failure/mechanism diagnosis as a new research question. Do not retune Q020 on the same evidence or reuse the holdout for selection.

Safety: PAPER_ONLY=True; LIVE_TRADING_ENABLED=False; orders_enabled=False; automatic_promotion=False.
