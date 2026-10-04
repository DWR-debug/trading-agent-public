from automation.free_mode_attestation import validate_free_mode_attestation


def test_groq_requires_explicit_free_attestation():
    env = {
        "AI_EXTERNAL_PROVIDER_ALLOWLIST": "true",
        "GROQ_API_KEY": "not-a-real-key",
    }
    result = validate_free_mode_attestation("groq_free", env)
    assert result["eligible"] is False
    assert result["free_mode_attested"] is False
    assert "GROQ_FREE_MODE_CONFIRMED" in result["reasons"][0]


def test_groq_passes_only_after_operator_attestation():
    env = {
        "AI_EXTERNAL_PROVIDER_ALLOWLIST": "true",
        "GROQ_API_KEY": "not-a-real-key",
        "GROQ_FREE_MODE_CONFIRMED": "true",
    }
    result = validate_free_mode_attestation("groq_free", env)
    assert result["eligible"] is True
    assert result["paid_usage_allowed"] is False
    assert result["paid_fallback_allowed"] is False


def test_openrouter_free_route_does_not_need_provider_tier_secret():
    env = {
        "AI_EXTERNAL_PROVIDER_ALLOWLIST": "true",
        "OPENROUTER_API_KEY": "not-a-real-key",
    }
    result = validate_free_mode_attestation("openrouter_free", env)
    assert result["eligible"] is True
    assert result["fixed_model"] == "openrouter/free"


def test_missing_allowlist_stays_fail_closed():
    env = {"GROQ_API_KEY": "not-a-real-key", "GROQ_FREE_MODE_CONFIRMED": "true"}
    result = validate_free_mode_attestation("groq_free", env)
    assert result["eligible"] is False
    assert "AI_EXTERNAL_PROVIDER_ALLOWLIST" in result["reasons"][0]
