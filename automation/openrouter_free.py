"""Hard-wired Free-only OpenRouter API adapter.

The adapter exposes no model-selection input and accepts only the provider's
openrouter/free router. It performs one bounded request and never retries onto a
paid model or provider.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
FREE_MODEL = "openrouter/free"
MAX_TOKENS = 3200
TEMPERATURE = 0.2
USER_AGENT = "DWR-debug/trading-agent-public-free-ai"


class OpenRouterFreeError(ValueError):
    """Raised when the fixed free-only OpenRouter contract is violated."""


def call_openrouter_free(
    prompt: str,
    *,
    api_key: str,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    if not api_key.strip():
        raise OpenRouterFreeError("OPENROUTER_API_KEY is missing.")
    if not prompt.strip():
        raise OpenRouterFreeError("Prompt must not be empty.")
    if timeout_seconds < 1:
        raise OpenRouterFreeError("timeout_seconds must be positive.")

    payload = {
        "model": FREE_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a bounded research-support worker. "
                    "Return final worker material only. Do not emit tool calls, tool-call syntax, "
                    "hidden reasoning, or instructions to use external tools. Never claim deterministic "
                    "validation, performance evidence, promotion, or live-trading authorization."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "reasoning": {"exclude": True},
    }
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "X-Title": "Trading Agent Free Research Worker",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read(120_000).decode("utf-8", errors="replace")
            status = int(response.status)
    except urllib.error.HTTPError as exc:
        detail = exc.read(12_000).decode("utf-8", errors="replace")
        if exc.code in {402, 429}:
            return {
                "status": "RATE_LIMITED" if exc.code == 429 else "FAILED_PROVIDER",
                "returncode": exc.code,
                "content": "",
                "error": f"OpenRouter HTTP {exc.code}: {detail}",
            }
        raise OpenRouterFreeError(f"OpenRouter HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise OpenRouterFreeError(f"OpenRouter network error: {exc.reason}") from exc

    if status < 200 or status >= 300:
        raise OpenRouterFreeError(f"Unexpected OpenRouter HTTP status {status}.")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise OpenRouterFreeError("OpenRouter returned non-JSON output.") from exc

    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise OpenRouterFreeError("OpenRouter response contains no choices.")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                text_parts.append(part["text"])
        content = "\n".join(text_parts)
    if isinstance(content, str) and "<|tool_call_start|>" in content:
        raise OpenRouterFreeError("OpenRouter returned tool-call syntax instead of a final worker handoff.")
    if not isinstance(content, str) or not content.strip():
        # Some reasoning-capable free models may return a non-empty refusal
        # instead of answer text; treat that as provider failure rather than
        # converting hidden/internal fields into worker evidence.
        refusal = message.get("refusal") if isinstance(message, dict) else None
        detail = f" refusal={refusal!r}" if refusal else ""
        raise OpenRouterFreeError(f"OpenRouter response contains no textual content.{detail}")

    usage = data.get("usage")
    return {
        "status": "SUCCESS",
        "returncode": 0,
        "content": content[-20_000:],
        "error": "",
        "response_id": data.get("id"),
        "usage": usage if isinstance(usage, dict) else None,
    }
