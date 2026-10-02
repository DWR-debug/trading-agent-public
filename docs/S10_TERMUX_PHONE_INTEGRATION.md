# S10 dedicated phone / Termux runtime

## Canonical meaning

**S10 is the dedicated Android phone used as an independent Trading-Agent-OS resource. Termux is the runtime environment on that phone.**

The Windows self-hosted runners are separate infrastructure. The project must not infer S10 availability from a Windows process, Windows executable, or Windows memory reading.

**Current operational status (2026-10-02):** the dedicated phone runner completed the full bounded S10 benchmark successfully and the synchronized canonical receipt reports \`S10_UTILITY_ACCEPTED\` under contract \`2026-10-02-R3\`. This is an operational capability result only, not scientific trading evidence.

For future Samsung/Android devices, use \`docs/SAMSUNG_ANDROID_TERMUX_PHONE_TEMPLATE.md\` and \`scripts/samsung_termux_phone_runner_template.sh\`. S10 is the reference instance, not a model-specific integration path.

## Allowed role

S10 may provide bounded:
- hypothesis/adversarial research;
- evidence-critique support;
- source/logic review;
- deterministic engineering/QA assistance that is independently checked.

S10 output never becomes scientific evidence, performance authorization, candidate selection, promotion, or live execution.

## Live verification

The phone-side runtime is the authority for S10 capability discovery. Verification must establish:
1. Termux is active and usable;
2. the configured S10/agent runtime is actually present;
3. an explicit local interface exists for the intended task;
4. the interface can answer a bounded smoke request;
5. no credential material is exported in receipts.

Until this is established, S10 is **configured but capability-unresolved**, not a failed scientific resource. After acceptance, the receipt remains authoritative for routing until a newer receipt supersedes it.

## Bridge to the Trading Agent OS

The Windows side may consume S10 only through an explicitly configured private connection. Public internet endpoints and implicit discovery are rejected. The bridge is optional and fail-closed.

The first integration target is the isolated Evidence-Critic Lab. The existing fixed corpus and deterministic gold labels remain authoritative; S10 is measured as an additional worker, not as a source of labels.

## Termux bootstrap

Run the repository's phone-side discovery helper in Termux after the phone is online. The helper only emits sanitized runtime information and does not print arbitrary environment variables or secrets.

## GitHub Actions integration

After Termux/Ubuntu-userland is prepared and the runner is registered with the repository label \`s10-phone\`, \`.github/workflows/s10-phone-worker.yml\` executes the bounded phone lane on its configured schedule and on relevant master changes. Routing remains receipt-gated: a runner being online alone is not sufficient.

## Operator activation

Scheduled execution is enabled because the phone-side live verification has completed. Manual \`workflow_dispatch\` remains available after registration.

Required live evidence:
- runner label \`s10-phone\` is online;
- Termux/ARM64 worker starts successfully;
- discovery receipt identifies the configured S10 runtime;
- a bounded Evidence-Critic smoke run completes;
- no secrets appear in the receipt.

The latest successful acceptance run was GitHub Actions run \`37023821478\`; the synchronized operational state is in \`ops/s10_runtime_status.json\`.

## Utility acceptance

After a complete fixed-corpus run, the S10 worker emits \`s10_acceptance_receipt.json\`.
This receipt is operational only. It accepts S10 as a usable bounded worker when all of the
following are true:

- the fixed 36-case corpus was completed;
- all 36 responses have a valid typed verdict and all three probability fields;
- all 36 cases are scored without malformed/no-decision rows;
- six option-order checks produce no verdict changes;
- the endpoint remains loopback-only and a source commit is recorded;
- governance remains fail-closed.

The receipt deliberately does not judge trading performance, choose candidates, create
scientific evidence, authorize experiments, rank models, or promote anything.
