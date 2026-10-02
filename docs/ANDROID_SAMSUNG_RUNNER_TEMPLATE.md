# Samsung Android / Termux Runner Template

Reusable onboarding/runtime contract for additional Samsung phones as Trading-Agent-OS resources.

Architecture:
Device -> Termux -> Ubuntu/proot -> unprivileged runner -> capability discovery -> typed smoke -> utility receipt -> central OS status -> receipt-gated routing.

Mandatory rules:
1. Never start the GitHub runner from the root Ubuntu login. Use a dedicated unprivileged user.
2. Do not re-register an existing runner during reboot recovery.
3. On ARM64 Termux/proot, support a configurable DOTNET_GCHeapHardLimit for the runner process. Default: 40000000 (1 GiB hexadecimal).
4. Keep the GitHub runner and local inference processes separate.
5. Require a bounded runtime preflight before starting the runner: ARM64, runner identity, non-root user, available memory, free storage.
6. Use termux-wake-lock where available; treat Doze, battery saver, thermal throttling and process lifetime as runtime facts.
7. Never write registration tokens, API keys, OAuth material or other credentials into receipts or repository files.

Default identity:
Runner: ANDROID-SAMSUNG-<MODEL>-<SHORTID>
Labels: android-phone,samsung,linux,ARM64
Default runner user: androidrunner
Default runner root: /opt/android-actions-runner

Allowed role:
bounded QA, adversarial review, deterministic reproduction, optional local inference.

Scientific boundary:
Phone workers cannot independently create formal scientific evidence, authorize performance, select/rank candidates, select holdouts, change gates, promote models, or execute live orders.

Acceptance chain:
runtime preflight -> discovery -> typed smoke -> fixed utility benchmark -> utility receipt -> central OS status.

LISTENING FOR JOBS means transport readiness only. It does not mean UTILITY_ACCEPTED.

Samsung-specific onboarding must record, rather than assume:
Android version, Termux version, proot-distro version, model, ARM64 architecture, runner version/user/root, memory availability, free storage, local AI endpoint, battery/thermal/Doze observations when available, and the sanitized receipt fingerprint.

The S10 failure lessons are generalized here: root execution is rejected; CoreCLR memory initialization may need a bounded GC heap; runner identity and local inference identity are separate; Android runtime lifetime is volatile; central routing is receipt-gated.