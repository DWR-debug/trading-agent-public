# Workflow Lifecycle and Repository Cleanup — 2026-10-03

## Objective

Reduce duplicate scheduling, eliminate obsolete recurring load and preserve historical reproducibility.

The repository currently contains 172 workflow files. Many historical Q-series workflows remain after their scientific paths were retired.

Cleanup policy:
- do not delete scientific evidence;
- do not rewrite historical trial receipts;
- do not move a workflow unless its current role is explicitly classified;
- disable recurring schedules before considering archival;
- keep one canonical active implementation per operational function.

## Canonical active lanes

- hosted deterministic frontier;
- hosted research failover;
- permanent Windows local research;
- hosted Windows Continuous QA;
- current status synchronizer;
- bounded agent queue and control plane;
- authenticated free-AI worker fabric;
- S10 receipt/worker path;
- current Q119/Q120/Q121 and explicitly active feasibility workflows;
- immutable trial/evidence reconciliation workflows required by the active registry.

## Immediate cleanup completed in this branch

S10 runtime diagnostics are now manual-only. The recurring daily schedule was redundant with the receipt-gated S10 presence model and consumed the dedicated phone-runner slot without creating scientific evidence.

The actual Continuous QA workflow runs on GitHub-hosted windows-latest with one bounded repo_qa lane and consumes zero self-hosted research slots. The status generator has been aligned with that architecture.

## Next archive tranche

The old Q014–Q095 one-shot/legacy workflow family should be reviewed against active_research_registry.json. For each retired path:
1. confirm RETIRED or PERMANENTLY_BLOCKED status;
2. remove recurring triggers first;
3. preserve YAML in a non-runnable archive location only where forensic reconstruction benefits;
4. keep evidence and trial ledger untouched;
5. update project integrity and workflow-lint tests in the same change.

This must not be a blind mass deletion.

## Private repository protection architecture

DWR-debug/trading-agent is designated as a vault / disaster-recovery repository, not a compute source.

Recommended contents:
- immutable public-master anchors;
- hashes/fingerprints of critical governance and status files;
- private design notes or working material that should not be public;
- recovery manifests;
- selected historical snapshots that are expensive to reconstruct.

The public repository remains the canonical working tree and scientific compute source.

A future public-to-private mirror needs a separately configured GitHub App or repository-scoped token stored as a secret. This branch does not claim that such automatic mirroring is enabled.

## Guardrails

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False

No cleanup may create performance authorization or select a research arm.
