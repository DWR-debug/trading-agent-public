"""Fail-closed optional LiteLLM transport for the project's free-only AI workers.

LiteLLM is deliberately only a transport/interface layer. Admission is still
controlled by the project's free-mode attestation and fixed provider route.
This module never configures provider fallbacks, retries, model discovery, or
paid routing.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from typing import Any

from automation.free_mode_attestation import validate_free_mode_attestation

MAX_TOKENS = 3200
TEMPERATURE = 0.2
USER_AGENT = "DWR-debug/trading-agent-public-free-ai"

# LiteLLM needs its own provider prefix. OpenRouter's free router itself is
# also named "openrouter/free", hence the intentional double prefix below:
# first openrouter/ selects the LiteLLM provider; the remainder is sent to
# OpenRouter as its model identifier.
PROVIDER_CONTRACTS: dict[str, dict[str, Any]] = {
    "openrouter_free": {
        "litellm_model": "openrouter/openrouter/free",
        "api_model": "openrouter/free",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "attestation_required": False,
    },
    "groq_free": {
        "litellm_model": "groq/openai/gpt-oss-20b",
        "api_model": "openai/gpt-oss-20b",
        "api_base": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "attestation_required": True,
    },
    "mistral_api": {
        "litellm_model": "mistral/mistral-small-latest",
        "api_model": "mistral-small-latest",
        "api_base": "https://api.mistral.ai/v1",
        "api_key_env": "MISTRAL_API_KEY",
        "attestation_required": True,
    },
}


class LiteLLMFreeError(ValueError):
    """Raised when the fixed LiteLLM free-only contract is violated."""


def supported_providers() -> tuple[str, ...]:
    return tuple(PROVIDER_CONTRACTS)


def transport_contract(provider: str) -> dict[str, Any]:
    if provider not in PROVIDER_CONTRACTS:
        raise LiteLLMFreeError(f"LiteLLM is not supported for provider: {provider}")
    return dict(PROVIDER_CONTRACTS[provider])


def admission(provider: str, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    if provider not in PROVIDER_CONTRACTS:
        raise LiteLLMFreeError(f"LiteLLM is not supported for provider: {provider}")
    runtime = dict(os.environ if env is None else env)
    contract = PROVIDER_CONTRACTS[provider]
    policy = validate_free_mode_attestation(provider, runtime)
    reasons = list(policy["reasons"])

    key_env = contract["api_key_env"]
    if not runtime.get(key_env, "").strip():
        reason = f"{key_env} is missing"
        if reason not in reasons:
            reasons.append(reason)

    return {
        "eligible": not reasons,
        "provider": provider,
        "litellm_model": contract["litellm_model"],
        "api_model": contract["api_model"],
        "api_base": contract["api_base"],
        "free_only": True,
        "free_mode_attested": bool(policy["free_mode_attested"]),
        "paid_usage_allowed": False,
        "paid_fallback_allowed": False,
        "personal_credit_fallback_allowed": False,
        "retries_allowed": False,
        "reasons": reasons,
    }


def _value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _content_from_response(response: Any) -> str:
    choices = _value(response, "choices")
    if not isinstance(choices, list) or not choices:
        raise LiteLLMFreeError("LiteLLM response contains no choices.")

    message = _value(choices[0], "message")
    content = _value(message, "content")

    if isinstance(content, list):
        parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, Mapping) and isinstance(part.get("text"), str)
        ]
        content = "\n".join(part for part in parts if part)

    if not isinstance(content, str) or not content.strip():
        refusal = _value(message, "refusal")
        suffix = f" refusal={refusal!r}" if refusal else ""
        raise LiteLLMFreeError(f"LiteLLM response contains no textual content.{suffix}")

    if "<|tool_call_start|>" in content:
        raise LiteLLMFreeError("LiteLLM returned tool-call syntax instead of final worker material.")

    return content[-20_000:]


def _safe_error(exc: BaseException, api_key: str) -> str:
    message = f"{type(exc).__name__}: {exc}"
    if api_key:
        message = message.replace(api_key, "[REDACTED]")
    return message[-12_000:]


def _status_code(exc: BaseException) -> int | None:
    value = getattr(exc, "status_code", None)
    if isinstance(value, int):
        return value
    response = getattr(exc, "response", None)
    value = getattr(response, "status_code", None)
    return value if isinstance(value, int) else None


def call_litellm_free(
    provider: str,
    prompt: str,
    *,
    api_key: str,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    if provider not in PROVIDER_CONTRACTS:
        raise LiteLLMFreeError(f"LiteLLM is not supported for provider: {provider}")
    if not api_key.strip():
        raise LiteLLMFreeError(f"{PROVIDER_CONTRACTS[provider]['api_key_env']} is missing.")
    if not prompt.strip():
        raise LiteLLMFreeError("Prompt must not be empty.")
    if timeout_seconds < 1:
        raise LiteLLMFreeError("timeout_seconds must be positive.")

    contract = PROVIDER_CONTRACTS[provider]
    try:
        import litellm
    except ImportError as exc:
        raise LiteLLMFreeError(
            "LiteLLM package is not installed; fail-closed without inference."
        ) from exc

    completion = getattr(litellm, "completion", None)
    if not callable(completion):
        raise LiteLLMFreeError("Installed LiteLLM package does not expose completion().")

    system_message = (
        "You are a bounded research-support worker. Return final worker material only. "
        "Do not emit tool calls, hidden reasoning, or instructions to use external tools. "
        "Never claim deterministic validation, performance evidence, promotion, or live-trading authorization."
    )
    try:
        response = completion(
            model=contract["litellm_model"],
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            api_key=api_key,
            api_base=contract["api_base"],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            timeout=timeout_seconds,
            num_retries=0,
        )
    except Exception as exc:
        status = _status_code(exc)
        result_status = "RATE_LIMITED" if status == 429 else "FAILED_PROVIDER"
        return {
            "status": result_status,
            "returncode": status,
            "content": "",
            "error": _safe_error(exc, api_key),
        }

    content = _content_from_response(response)
    return {
        "status": "SUCCESS",
        "returncode": 0,
        "content": content,
        "error": "",
        "response_id": _value(response, "id"),
        "response_model": _value(response, "model"),
        "usage": _value(response, "usage") if isinstance(_value(response, "usage"), Mapping) else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contracts", action="store_true")
    parser.add_argument("--preflight", choices=supported_providers())
    args = parser.parse_args()

    if args.contracts:
        print(json.dumps(PROVIDER_CONTRACTS, sort_keys=True, indent=2))
        return 0

    if args.preflight:
        result = admission(args.preflight)
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0 if result["eligible"] else 2

    parser.error("Choose --contracts or --preflight.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
