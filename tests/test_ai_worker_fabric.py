import json
import pytest
from automation.ai_worker_fabric import AIWorkerError, build_prompt, load_task, preflight, run_task

def task(provider="gemini_cli"):
    return {
        "schema_version": 1, "task_id": "AI-TEST-001", "providers": [provider],
        "scope": "bounded research design",
        "prompt": "Review the current research architecture and identify one falsifiable next step.",
        "max_runtime_minutes": 5,
        "deterministic_compute": False, "holdout_selection": False, "parameter_selection": False,
        "asset_selection": False, "threshold_selection": False, "horizon_selection": False,
        "research_gate_changes": False, "promotion_decision": False, "live_execution": False,
        "paid_usage": False, "research_decision": False, "allow_workspace_writes": False,
    }

def test_load_task_requires_ai_namespace(tmp_path):
    path = tmp_path / "task.json"; payload = task(); payload["task_id"] = "BAD-001"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(AIWorkerError): load_task(path)

def test_free_only_preflight_is_fail_closed():
    result = preflight("gemini_cli", env={})
    assert result["available"] is False
    assert result["free_only"] is True
    assert result["reasons"]

def test_claude_never_uses_api_key_as_free_proof():
    env = {"AI_EXTERNAL_PROVIDER_ALLOWLIST": "true", "ANTHROPIC_API_KEY": "present-but-not-a-free-proof", "CLAUDE_FREE_MODE_CONFIRMED": "false"}
    result = preflight("claude_cli", env=env)
    assert result["available"] is False
    assert "provider free-mode attestation is missing" in result["reasons"]

def test_build_prompt_contains_safety_invariants():
    prompt = build_prompt(task())
    assert "PAPER_ONLY=True" in prompt
    assert "LIVE_TRADING_ENABLED=False" in prompt
    assert "Do not claim validation or promotion." in prompt

def test_run_task_writes_skip_receipt(tmp_path):
    output = tmp_path / "result.json"
    result = run_task(task(), "gemini_cli", output, env={})
    assert result["status"] == "SKIPPED"
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["worker_output_is_scientific_evidence"] is False
    assert saved["safety"]["orders_enabled"] is False

def test_unknown_provider_rejected():
    with pytest.raises(AIWorkerError): preflight("unknown", env={})
