# Private Repository Vault

The private repository DWR-debug/trading-agent is designated as the project's vault / disaster-recovery repository.

## Roles

- DWR-debug/trading-agent-public: canonical active working repository, scientific compute source and operational source of truth.
- DWR-debug/trading-agent: private archive for recovery anchors, sensitive/private working material and selected historical snapshots.

The private repository is not a substitute for the public repository's current status, trial ledger or active research registry.

## Protection model

A vault anchor records:
- public master commit SHA;
- canonical status source SHA;
- critical governance/status fingerprints;
- safety state;
- anchor timestamp and provenance.

A future cross-repository mirror can use a repository-scoped token or GitHub App credential stored only as a GitHub secret. No credential belongs in either repository.

## Current anchor

See vault/public_master_anchor_2026-10-03.json.

## Operating rule

Scientific work proceeds in the public repository. The private repository is used for recovery, preservation of sensitive historical material and independent integrity reference.
