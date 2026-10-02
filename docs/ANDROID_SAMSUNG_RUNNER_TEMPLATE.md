# Samsung Android / Termux Runner Template

Reusable onboarding contract for additional Samsung/Android phones as Trading-Agent-OS resources.

## Reference architecture

Device -> Termux -> Ubuntu/proot -> GitHub self-hosted runner -> capability discovery -> typed smoke -> utility receipt -> central OS status -> receipt-gated routing.

An online runner alone does not prove that a phone is a usable AI/research resource.

## Default role

- bounded engineering / QA
- adversarial review
- deterministic reproduction
- optional local inference support

Never allowed for a phone worker: scientific evidence, performance authorization, holdout-based selection, candidate ranking, promotion, or live orders.

## Naming

Runner: `ANDROID-SAMSUNG-<MODEL>-<SHORTID>`

Labels: `android-phone,samsung,linux,ARM64`

Optional task label: `android-ecl` or `android-reproduction`.

## Fast onboarding

1. Prepare Termux and proot-distro.
2. Install Ubuntu userland.
3. Register using the template script; enter the GitHub runner registration token only when prompted.
4. Start the already-registered runner.
5. Run phone-side capability discovery and the typed smoke.
6. Run the fixed utility benchmark.
7. Let the central receipt synchronizer persist the sanitized result.
8. Route bounded work only after `ANDROID_PHONE_UTILITY_ACCEPTED`.

## Start after reboot

Do not re-register merely to restart an existing runner. Use:

```bash
proot-distro login ubuntu -- bash -lc 'cd /opt/android-actions-runner && ./run.sh'
```

The supplied `scripts/android_samsung_runner_start_template.sh` also attempts `termux-wake-lock` before starting the runner.

## Lessons from S10

- The phone-side runtime is the source of truth about local capability.
- Runner and local inference are separate processes.
- Bootstrap, health checks and inference have explicit bounds.
- Typed JSON is required before a utility receipt can be accepted.
- Long utility runs must not be cancelled by unrelated technical master pushes.
- The phone runner must not write directly into canonical OS state.
- Android reboot/Doze/Termux lifetime are runtime facts, not assumptions.

## Receipt chain

Runtime receipt -> utility receipt -> central OS status.

The central status must remain fail-closed and explicitly carry:

`scientific_evidence=false`

`performance_authorization=false`

`candidate_selection=false`

`candidate_ranking=false`

`promotion=false`

`live_execution=false`

## Device profile

Use `research/devices/android_phone_profile_template.json` as the starting point for a new Samsung phone.

Required metadata includes device ID, model, runner name/labels, ARM64 architecture, Termux/proot state, allowed roles, utility gate, and safety invariants.

## Why this exists

The template is designed to minimize integration time for later Samsung phones while retaining the S10 fail-closed, provenance and scientific-governance boundaries.