# Manual AI Input via LiteLLM

Manual AI input is a **task-contract/prompt layer**. LiteLLM is only the **transport layer**.

The bounded worker receives a versioned task contract, builds a deterministic repository-context bundle, and then either calls the fixed provider route directly or sends the same prompt through LiteLLM. LiteLLM does not decide whether a task is allowed, which provider is economically acceptable, or whether an output is scientific evidence.

Current fixed free-only LiteLLM routes:
- Groq: `groq/openai/gpt-oss-20b`
- OpenRouter Free: `openrouter/openrouter/free`
- Mistral: `mistral/mistral-small-latest`

Admission remains fail-closed on free-mode attestation, provider authentication and allowlist. Paid fallbacks and provider retries are disabled.

## Durable chat-generated request
For important research instructions, create or update an `ai_requests/AI-*.json` task. Its task fingerprint is recorded in the worker receipt.

## Interactive GitHub Actions input
Workflow: `.github/workflows/litellm-manual-groq-one-shot.yml`

Open the public repository's Actions tab, choose **Manual AI via Groq LiteLLM**, choose **Run workflow**, and paste the bounded research prompt into `manual_prompt`. The workflow uses a fixed information-timing context template, creates a temporary effective task, and sends it through Groq via LiteLLM. The raw prompt is not committed; its SHA-256 is included in the effective task.

## Boundary
Manual AI may generate hypotheses, literature synthesis, source/PIT designs and falsification tests. It may not perform or claim deterministic backtests, select assets/parameters/holdouts, alter gates, authorize performance, promote a candidate, or execute live trading.

Architecture: **human/chat instruction → task contract → fixed context → free-mode admission → LiteLLM fixed provider route → worker receipt → deterministic independent verification**.
