import json
import sys
import types

import pytest

from automation.litellm_free import (
    LiteLLMFreeError,
    admission,
    call_litellm_free,
    transport_contract,
)


def test_exact_litellm_model_contracts():
    assert transport_contract("openrouter_free")["litellm_model"] == "openrouter/openrouter/free"
    assert transport_contract("groq_free")["litellm_model"] == "groq/openai/gpt-oss-20b"
    assert transport_contract("mistral_api")["litellm_model"] == "mistral/mistral-small-latest"


def test_gemini_is_not_silently_rerouted_through_litellm():
    with pytest.raises(LiteLLMFreeError):
        transport_contract("gemini_cli")


def test_groq_admission_stays_fail_closed_without_attestation():
    result = admission(
        "groq_free",
        {
            "AI_EXTERNAL_PROVIDER_ALLOWLIST": "true",
            "GROQ_API_KEY": "dummy-key",
        },
    )
    assert result["eligible"] is False
    assert result["paid_usage_allowed"] is False
    assert result["paid_fallback_allowed"] is False
    assert result["retries_allowed"] is False


def test_openrouter_admission_uses_fixed_zero_price_route():
    result = admission(
        "openrouter_free",
        {
            "AI_EXTERNAL_PROVIDER_ALLOWLIST": "true",
            "OPENROUTER_API_KEY": "dummy-key",
        },
    )
    assert result["eligible"] is True
    assert result["litellm_model"] == "openrouter/openrouter/free"


def test_litellm_call_uses_fixed_route_and_zero_retries(monkeypatch):
    captured = {}

    class FakeResponse:
        id = "test-response"
        model = "openai/gpt-oss-20b"
        choices = [{"message": {"content": "bounded worker output"}}]
        usage = {"prompt_tokens": 5, "completion_tokens": 7}

    def fake_completion(**kwargs):
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setitem(sys.modules, "litellm", types.SimpleNamespace(completion=fake_completion))

    result = call_litellm_free(
        "groq_free",
        "falsify this",
        api_key="secret-test-key",
        timeout_seconds=11,
    )
    assert result["status"] == "SUCCESS"
    assert captured["model"] == "groq/openai/gpt-oss-20b"
    assert captured["api_base"] == "https://api.groq.com/openai/v1"
    assert captured["num_retries"] == 0
    assert captured["timeout"] == 11
    assert captured["api_key"] == "secret-test-key"
    assert "fallbacks" not in captured


def test_litellm_failure_redacts_api_key(monkeypatch):
    def fake_completion(**kwargs):
        raise RuntimeError("provider rejected key secret-test-key")

    monkeypatch.setitem(sys.modules, "litellm", types.SimpleNamespace(completion=fake_completion))

    result = call_litellm_free(
        "groq_free",
        "test",
        api_key="secret-test-key",
    )
    assert result["status"] == "FAILED_PROVIDER"
    assert "secret-test-key" not in result["error"]
    assert "[REDACTED]" in result["error"]


def test_litellm_normalizes_list_content(monkeypatch):
    class FakeResponse:
        choices = [{"message": {"content": [{"type": "text", "text": "one"}, {"type": "text", "text": "two"}]}}]

    monkeypatch.setitem(
        sys.modules,
        "litellm",
        types.SimpleNamespace(completion=lambda **kwargs: FakeResponse()),
    )
    result = call_litellm_free("mistral_api", "test", api_key="key")
    assert result["content"] == "one\ntwo"


def test_litellm_rejects_tool_call_syntax(monkeypatch):
    class FakeResponse:
        choices = [{"message": {"content": "<|tool_call_start|>read(foo)<|tool_call_end|>"}}]

    monkeypatch.setitem(
        sys.modules,
        "litellm",
        types.SimpleNamespace(completion=lambda **kwargs: FakeResponse()),
    )
    with pytest.raises(LiteLLMFreeError):
        call_litellm_free("openrouter_free", "test", api_key="key")


def test_litellm_contract_is_json_serializable():
    json.dumps(transport_contract("openrouter_free"), sort_keys=True)
