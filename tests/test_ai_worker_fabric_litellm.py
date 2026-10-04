import json

from automation import ai_worker_fabric


def _task(provider="groq_free"):
    return {
        "schema_version": 1,
        "task_id": "AI-TEST-LITELLM-TRANSPORT",
        "providers": [provider],
        "prompt": "Return a bounded compatibility handoff.",
        "scope": "tests only",
        "max_runtime_minutes": 5,
        "performance_authorized": False,
        "deterministic_compute": False,
        "holdout_selection": False,
        "parameter_selection": False,
        "asset_selection": False,
        "threshold_selection": False,
        "horizon_selection": False,
        "research_gate_changes": False,
        "promotion_decision": False,
        "live_execution": False,
        "paid_usage": False,
        "research_decision": False,
        "allow_workspace_writes": False,
    }


def test_litellm_opt_in_routes_without_direct_provider_fallback(monkeypatch, tmp_path):
    calls = []

    monkeypatch.setattr(
        ai_worker_fabric,
        "preflight",
        lambda provider, env=None: {
            "provider": provider,
            "available": True,
            "litellm_transport_enabled": True,
            "free_mode_attested": True,
            "reasons": [],
        },
    )
    monkeypatch.setattr(
        ai_worker_fabric,
        "context_fingerprint",
        lambda task: "test-context",
    )

    def fake_litellm(provider, prompt, *, api_key, timeout_seconds):
        calls.append(("litellm", provider, api_key, timeout_seconds))
        return {
            "status": "SUCCESS",
            "returncode": 0,
            "content": "bounded worker output",
            "error": "",
            "response_id": "litellm-test",
            "response_model": "openai/gpt-oss-20b",
            "usage": {"prompt_tokens": 5, "completion_tokens": 7},
        }

    monkeypatch.setattr(ai_worker_fabric, "call_litellm_free", fake_litellm)

    import automation.groq_free as groq_free
    monkeypatch.setattr(
        groq_free,
        "call_groq_free",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("direct Groq adapter must not be used in LiteLLM mode")
        ),
    )

    output = tmp_path / "receipt.json"
    result = ai_worker_fabric.run_task(
        _task(),
        "groq_free",
        output,
        env={
            "AI_EXTERNAL_PROVIDER_ALLOWLIST": "true",
            "GROQ_API_KEY": "dummy-key",
            "GROQ_FREE_MODE_CONFIRMED": "true",
            "TRADING_AGENT_LITELLM_TRANSPORT": "true",
        },
    )

    assert result["status"] == "SUCCESS"
    assert result["command_binary"] == "litellm"
    assert result["litellm_model"] == "groq/openai/gpt-oss-20b"
    assert result["api_model"] == "openai/gpt-oss-20b"
    assert result["litellm_transport_enabled"] is True
    assert calls == [("litellm", "groq_free", "dummy-key", 60)]
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["worker_output_is_scientific_evidence"] is False
    assert saved["safety"]["live_trading_enabled"] is False


def test_litellm_flag_defaults_off(monkeypatch):
    env = {
        "AI_EXTERNAL_PROVIDER_ALLOWLIST": "true",
        "GROQ_API_KEY": "dummy-key",
        "GROQ_FREE_MODE_CONFIRMED": "true",
    }

    result = ai_worker_fabric.preflight("groq_free", env=env)

    assert result["litellm_transport_enabled"] is False
    assert result["available"] is True
    assert result["free_enforcement"] == "fixed_model_groq_free_with_attestation"


def test_enabled_litellm_fails_closed_when_package_missing(monkeypatch):
    class Missing:
        @staticmethod
        def find_spec(name):
            assert name == "litellm"
            return None

    monkeypatch.setattr(ai_worker_fabric.importlib, "util", Missing)

    result = ai_worker_fabric.preflight(
        "groq_free",
        env={
            "AI_EXTERNAL_PROVIDER_ALLOWLIST": "true",
            "GROQ_API_KEY": "dummy-key",
            "GROQ_FREE_MODE_CONFIRMED": "true",
            "TRADING_AGENT_LITELLM_TRANSPORT": "true",
        },
    )

    assert result["available"] is False
    assert any("LiteLLM package is not installed" in reason for reason in result["reasons"])
