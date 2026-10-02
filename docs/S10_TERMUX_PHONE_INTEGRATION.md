# S10 dedicated phone / Termux runtime

## Canonical meaning

**S10 is the dedicated Android phone used as an independent Trading-Agent-OS resource. Termux is the runtime environment on that phone.**

The Windows self-hosted runners are separate infrastructure. The project must not infer S10 availability from a Windows process, Windows executable, or Windows memory reading.

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

Until this is established, S10 is **configured but capability-unresolved**, not a failed scientific resource.

## Bridge to the Trading Agent OS

The Windows side may consume S10 only through an explicitly configured private connection. Public internet endpoints and implicit discovery are rejected. The bridge is optional and fail-closed.

The first integration target is the isolated Evidence-Critic Lab. The existing fixed corpus and deterministic gold labels remain authoritative; S10 is measured as an additional worker, not as a source of labels.

## Termux bootstrap

Run the repository's phone-side discovery helper in Termux after the phone is online. The helper only emits sanitized runtime information and does not print arbitrary environment variables or secrets.
