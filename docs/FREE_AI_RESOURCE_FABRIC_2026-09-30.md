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

### 4. Mistral Free Studio

Mistral currently offers a Free plan with limited chat/search/coding usage and
Mistral Studio. Mistral's API documentation states Studio is enabled in Free
mode by default and does not require a credit card to create an API key.

Operator action:
- create a Mistral account
- activate Studio Free
- create an API key
- add MISTRAL_API_KEY as a repository secret

The project should never enable automatic paid fallback.

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
