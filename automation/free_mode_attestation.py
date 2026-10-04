"""Fail-closed free-mode attestation policy for external AI workers.

This module never proves provider billing state automatically. It turns an
explicit operator assertion (plus fixed provider routing and API-key presence)
into a deterministic admission gate. Secrets are never returned in results.
"""

from __future__ import annotations

import json
import os
from typing import Any

TRUE_VALUES = {"1", "true", "yes", "on"}

PROVIDER_CONTRACTS: dict[str, dict[str, Any]] = {
    "gemini_cli": {
        "attestation_env": "GEMINI_FREE_MODE_CONFIRMED",
        "auth_env": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        "fixed_model": "gemini-3.7-flash",
        "attestation_required": True,
        "attestation_type": "operator_account_tier_assertion",
    },
    "mistral_api": {
        "attestation_env": "MISTRAL_FREE_MODE_CONFIRMED",
        "auth_env": ("MISTRAL_API_KEY",),
        "fixed_model": "mistral-small-latest",
        "attestation_required": True,
        "attestation_type": "operator_account_tier_assertion",
    },
    "groq_free": {
        "attestation_env": "GROQ_FREE_MODE_CONFIRMED",
        "auth_env": ("GROQ_API_KEY",),
        "fixed_model": "openai/gpt-oss-20b",
        "attestation_required": True,
        "attestation_type": "operator_account_tier_assertion",
    },
    "openrouter_free": {
        "attestation_env": None,
        "auth_env": ("OPENROUTER_API_KEY",),
        "fixed_model": "openrouter/free",
        "attestation_required": False,
        "attestation_type": "provider_fixed_zero_price_route",
    },
}

def _truth(value: object) -> bool:
    return isinstance(value, str) and value.strip().lower() in TRUE_VALUES

def validate_free_mode_attestation(
    provider: str, env: dict[str, str] | None = None
) -> dict[str, Any]:
    if provider not in PROVIDER_CONTRACTS:
        raise ValueError(f"Unknown AI provider: {provider}")
    runtime = dict(os.environ if env is None else env)
    spec = PROVIDER_CONTRACTS[provider]
    reasons: list[str] = []

    if not _truth(runtime.get("AI_EXTERNAL_PROVIDER_ALLOWLIST")):
        reasons.append("AI_EXTERNAL_PROVIDER_ALLOWLIST is not confirmed")

    if not any(bool(runtime.get(name)) for name in spec["auth_env"]):
        reasons.append("provider authentication is not available")

    attested = True
    if spec["attestation_required"]:
        attested = _truth(runtime.get(spec["attestation_env"]))
        if not attested:
            reasons.append(
                f"required free-mode attestation {spec['attestation_env']} is not confirmed"
            )
    else:
        attested = spec["fixed_model"] == "openrouter/free"

    return {
        "eligible": not reasons,
        "provider": provider,
        "fixed_model": spec["fixed_model"],
        "free_mode_attested": attested,
        "attestation_required": spec["attestation_required"],
        "attestation_type": spec["attestation_type"],
        "attestation_env": spec["attestation_env"],
        "paid_usage_allowed": False,
        "paid_fallback_allowed": False,
        "personal_credit_fallback_allowed": False,
        "reasons": reasons,
    }

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=sorted(PROVIDER_CONTRACTS), required=True)
    args = parser.parse_args()
    result = validate_free_mode_attestation(args.provider)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["eligible"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
