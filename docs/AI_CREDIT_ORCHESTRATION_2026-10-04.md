# AI Credit Orchestration — 2026-10-04

## Purpose

Provide a deterministic control layer for scarce free AI capacity. The controller predicts reset boundaries only when they are documented or observed, and otherwise reports the state as unknown or conservatively estimated.

## Provider facts

- OpenRouter Free: 50 requests/day and 20 requests/minute on free models. The daily wall-clock reset is not stated in the provider material used by this project, so an exact reset time is never inferred from the cap alone.
- Gemini API: request limits are measured per project; the Requests-Per-Day quota resets at midnight Pacific Time. This gives an exact daily reset boundary but not an exact remaining balance.
- Mistral: Free mode includes monthly usage; API limits are shown per model/account and can include requests-per-second and tokens-per-minute limits. The account-specific monthly reset is not inferred unless observed.
- GitHub Copilot: included AI credits reset at 00:00 UTC on the first day of each calendar month. The project reserves four sessions/month and is currently exhausted for October 2026.

## Algorithm

For each provider at time t:

1. Read the immutable provider policy.
2. Read the latest provider observations from worker receipts.
3. If an observed quota block expires after t, mark the provider BLOCKED and use that exact blocked_until_utc.
4. If a provider has a documented calendar reset but no observable remaining balance, mark it PREFLIGHT_REQUIRED; publish the exact future reset separately, but do not admit the task automatically.
5. If a recent 429 exists without an exact reset value, assign a conservative cooldown and label it conservative_estimate.
6. Rank compatible tasks by information_value / estimated_cost, penalized by duplicate-context risk.
7. Assign only to a provider that is actually eligible under the above rules. Prefer OpenRouter for automated free reasoning, with secondary providers requiring explicit preflight/manual admission.
8. Keep live provider preflight as the final gate.
9. Never let AI-credit state change scientific evidence, candidate ranking, performance authorization, promotion or live execution.

## Event model

The scheduler itself is deterministic and cheap. A periodic scheduler run does not imply an AI call. Its output is committed only when its material decision_fingerprint changes, preventing clock-driven repository churn.

The AI worker is event-driven: a new or materially changed task context may trigger one bounded review. Unchanged context does not trigger another call merely because time elapsed.

## Quota telemetry

Every AI worker receipt records an observation timestamp. Rate-limit responses can include a provider-specific quota_block with the observed/parsed cooldown. This feeds the next scheduler cycle without exposing keys.

## Free-only safety

Paid usage is disabled. No paid fallback, overage, automatic promotion or live execution is permitted. AI output is worker material only and is never scientific evidence by itself.

## Sources

OpenRouter free limits: https://openrouter.ai/pricing/ and https://openrouter.ai/blog/tutorials/how-to-get-the-lowest-cost-llm-inference-on-openrouter/

Gemini rate limits: https://ai.google.dev/gemini-api/docs/rate-limits

Mistral limits and Free mode: https://docs.mistral.ai/admin/billing-usage/usage-limits

GitHub Copilot monthly reset: https://docs.github.com/en/copilot/reference/copilot-billing/license-changes
