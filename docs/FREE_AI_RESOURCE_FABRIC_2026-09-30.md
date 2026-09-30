# Free AI Resource Fabric — Trading Agent
Stand: 2026-09-30

## Policy

Paid API/agent budget remains 0 USD.

External AI can only run when the selected access path is demonstrably free-only.
No paid fallback, no overage and no personal-credit fallback.

AI output is worker material, never scientific evidence.

## Current usable paths

### 1. Gemini on the Windows research PC

The local Gemini CLI is installed and has previously passed the local free-only
attestation. Its current state was quota-exhausted, so it must not be spammed
until the provider reset.

Operator action:
- keep Google login on the persistent Windows user profile
- keep the local free-only attestation
- do not add a paid fallback

### 2. Gemini Developer API / AI Studio

Google currently documents a free tier for selected Gemini API models, including
Gemini 3.7 Flash. Google states that free-tier content may be used to improve
products, so only public/non-sensitive research context is sent through this
path.

Operator action:
- create a Gemini API key in Google AI Studio
- add it to GitHub repository Secrets as GEMINI_API_KEY
- add AI_EXTERNAL_PROVIDER_ALLOWLIST=true
- add GEMINI_FREE_MODE_CONFIRMED=true

The project's AI worker remains fail-closed when any of these are missing.

Source:
https://ai.google.dev/gemini-api/docs/pricing

### 3. OpenRouter Free

Current OpenRouter Free plan:
- no subscription/card required to start
- 25+ free models
- 50 requests/day
- free-model collection changes over time

This is useful as a diversified model pool rather than a single-model dependency.

Operator action:
- create an OpenRouter account
- create an API key
- keep only free models / free routing
- add OPENROUTER_API_KEY as a GitHub repository secret

The adapter must enforce provider/model identifiers with :free routing and reject
paid models.

Source:
https://openrouter.ai/pricing
https://openrouter.ai/collections/free-models

### 4. Mistral Free Studio / API

Mistral's current Free mode enables Studio API access without a credit card and
provides included monthly API usage, subject to rate and usage limits. The API
key itself is not plan-scoped, so pay-as-you-go must remain disabled for this
project's zero-paid-budget policy.

The fabric uses the fixed `mistral-small-latest` model and a separate free-mode
attestation. That makes Mistral an independent bounded reasoning/adversarial worker,
not a consensus voter and not a deterministic evidence source.

Operator action:
- create a Mistral account and use Studio Free
- create an API key
- keep pay-as-you-go disabled
- add `MISTRAL_API_KEY` as a GitHub repository secret
- add `MISTRAL_FREE_MODE_CONFIRMED=true` as a GitHub repository secret

The worker skips Mistral unless both the key and explicit free-mode attestation are present.
There is no automatic paid fallback.

Operationally, Mistral runs in its own bounded workflow lane. Within that lane,
one deterministic 6-hour rotation selects exactly one of the three standing AI
research tasks per cycle; the choice is time-based and never derived from
performance, holdout results or candidate preference. The other AI providers remain
independently parallel. This avoids free-tier burst 429s and keeps the Mistral
resource useful without exhausting it on duplicate reviews. A 429 is recorded as
a provider-rate-limit state, never retried through a paid route, and never treated
as scientific evidence.

Source:
https://mistral.ai/pricing/
https://docs.mistral.ai/getting-started/quickstarts/developer/first-api-request

## 5. Claude

Keep Claude separate from API billing.

Use only:
- an explicitly free local CLI/account path on the Windows PC, or
- a future free-only path that passes the project's attestation.

Never use Anthropic API billing under the 0 USD project policy.

## 6. Copilot Free — reserved for October 2026

Project rule:
- start at 2026-10-01 00:00 UTC
- maximum four sessions/month
- maximum 12 AI credits/session
- one concurrent worker
- no paid fallback

The project intentionally spends this resource on high-value code review /
architecture tasks, not routine generation.

## Quota-aware scheduling

The permanent research loop remains active every 30 minutes, but quota-limited AI
calls are deliberately decoupled from that heartbeat. Hosted/local Gemini runs use
one deterministic task slot per 6-hour cycle. Mistral uses the same 6-hour cadence
with its own deterministic one-task rotation. Claude and OpenRouter remain the
parallel higher-throughput review paths. A provider rate-limit is recorded and
never converted into paid usage or repeated immediately.

## Research role separation

Gemini:
- broad synthesis / coding / multi-step critique

OpenRouter:
- model-diverse adversarial second opinions

Mistral:
- independent coding/design critique and extraction

Claude:
- separate adversarial reasoning path when free access exists

Copilot:
- scarce code-maintenance resource

Local phone models:
- cheap always-on first-pass classification/extraction

Deterministic runner:
- sole authority for actual computation, evidence and gates
