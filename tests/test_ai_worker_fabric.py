import json
import pytest
from pathlib import Path
from automation.ai_worker_fabric import AIWorkerError, _local_attestation, build_prompt, load_task, preflight, run_task

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

def test_bom_prefixed_local_attestation_is_accepted(tmp_path):
    attestation = tmp_path / "ai_free_attestation.json"
    attestation.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "free_only": True,
                "paid_fallback_allowed": False,
                "personal_credit_fallback_allowed": False,
                "providers": ["gemini_cli"],
            }
        ),
        encoding="utf-8",
    )
    raw = attestation.read_bytes()
    attestation.write_bytes(b"\xef\xbb\xbf" + raw)
    env = {
        "AI_EXTERNAL_PROVIDER_ALLOWLIST": "true",
        "TRADING_AGENT_LOCAL_AI_MODE": "true",
        "TRADING_AGENT_AI_ATTESTATION": str(attestation),
    }
    result = _local_attestation("gemini_cli", env)
    assert result["present"] is True
    assert result["path"] == str(attestation)

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


def test_openrouter_free_preflight_is_code_enforced() -> None:
    env = {
        "AI_EXTERNAL_PROVIDER_ALLOWLIST": "true",
        "OPENROUTER_API_KEY": "dummy-key",
    }
    result = preflight("openrouter_free", env=env)
    assert result["available"] is True
    assert result["free_only"] is True
    assert result["free_mode_attested"] is True
    assert result["free_enforcement"] == "fixed_model_openrouter_free"
    assert result["binary"] is None


def test_openrouter_adapter_cannot_select_paid_model(monkeypatch) -> None:
    from automation import openrouter_free

    captured = {}

    class FakeResponse:
        status = 200

        def read(self, limit=None):
            return json.dumps(
                {
                    "id": "test-response",
                    "choices": [{"message": {"content": "bounded worker output"}}],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 7},
                }
            ).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(openrouter_free.urllib.request, "urlopen", fake_urlopen)
    result = openrouter_free.call_openrouter_free(
        "falsify this architecture",
        api_key="secret-test-key",
        timeout_seconds=11,
    )
    payload = json.loads(captured["request"].data.decode("utf-8"))
    assert payload["model"] == "openrouter/free"
    assert result["status"] == "SUCCESS"
    assert captured["timeout"] == 11
    assert captured["request"].headers["Authorization"] == "Bearer secret-test-key"


def test_build_prompt_assigns_independent_openrouter_role():
    prompt = build_prompt(task("openrouter_free"), "openrouter_free")
    assert "<provider_role>" in prompt
    assert "Do not seek consensus." in prompt


def test_gemini_command_is_pinned_to_free_flash_model():
    command = __import__("automation.ai_worker_fabric", fromlist=["command_for"]).command_for(
        "gemini_cli", "test prompt", binary="/usr/bin/gemini"
    )
    assert "--skip-trust" in command
    assert command[command.index("--model") + 1] == "gemini-3.7-flash"


def test_openrouter_request_excludes_reasoning_from_worker_output(monkeypatch) -> None:
    from automation import openrouter_free
    captured = {}

    class FakeResponse:
        status = 200
        def read(self, limit=None):
            return json.dumps({
                "id": "reasoning-excluded",
                "choices": [{"message": {"content": "answer"}}],
            }).encode("utf-8")
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setattr(openrouter_free.urllib.request, "urlopen", fake_urlopen)
    openrouter_free.call_openrouter_free("test", api_key="x")
    assert captured["payload"]["model"] == "openrouter/free"
    assert captured["payload"]["reasoning"]["exclude"] is True


def test_openrouter_rejects_tool_call_markup(monkeypatch) -> None:
    from automation import openrouter_free

    class FakeResponse:
        status = 200
        def read(self, limit=None):
            return json.dumps({
                "id": "tool-call-output",
                "choices": [{"message": {"content": "<|tool_call_start|>read(foo)<|tool_call_end|>"}}],
            }).encode("utf-8")
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        openrouter_free.urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(),
    )
    with pytest.raises(openrouter_free.OpenRouterFreeError):
        openrouter_free.call_openrouter_free("final answer only", api_key="x")


def test_mistral_free_preflight_requires_explicit_free_attestation():
    env = {
        "AI_EXTERNAL_PROVIDER_ALLOWLIST": "true",
        "MISTRAL_API_KEY": "dummy-key",
        "MISTRAL_FREE_MODE_CONFIRMED": "false",
    }
    result = preflight("mistral_api", env=env)
    assert result["available"] is False
    assert any("free-mode attestation" in reason for reason in result["reasons"])


def test_mistral_free_preflight_accepts_key_and_attestation():
    env = {
        "AI_EXTERNAL_PROVIDER_ALLOWLIST": "true",
        "MISTRAL_API_KEY": "dummy-key",
        "MISTRAL_FREE_MODE_CONFIRMED": "true",
    }
    result = preflight("mistral_api", env=env)
    assert result["available"] is True
    assert result["free_enforcement"] == "attestation_or_local_attestation"
    assert result["binary"] is None
    assert "provider executable not found" not in result["reasons"]


def test_mistral_lane_is_manual_dispatch_only():
    workflow = Path(__file__).parents[1] / ".github" / "workflows" / "ai-worker-fabric.yml"
    text = workflow.read_text(encoding="utf-8")
    assert "mistral_worker:" in text
    assert "github.event_name == 'workflow_dispatch'" in text


def test_q100_frontier_task_has_repository_context_and_safe_scope():
    task_path = Path(__file__).parents[1] / "ai_requests" / "AI-2026-09-30-Q100-FRONTIER-FEASIBILITY.json"
    payload = load_task(task_path)
    assert payload["providers"] == ["gemini_cli", "mistral_api", "openrouter_free"]
    assert payload["performance_authorized"] is False
    prompt = build_prompt(payload, "openrouter_free")
    assert "RESEARCH_FRONTIER_UNUSUAL" in prompt
    assert "q100_frontier_feasibility_synthesis.py" in prompt


def test_openrouter_is_event_driven_and_gemini_mistral_manual_only():
    workflow = Path(__file__).parents[1] / ".github" / "workflows" / "ai-worker-fabric.yml"
    text = workflow.read_text(encoding="utf-8")
    assert "provider: [openrouter_free]" not in text
    assert "gemini_worker:" in text
    assert "mistral_worker:" in text
    assert "schedule:" not in text
    assert "research/evidence/q187_q192_source_feasibility_latest.json" in text
    assert "github.event_name == 'workflow_dispatch'" in text
    assert "github.event.inputs.run_secondary_provider == 'true'" in text
    assert "GEMINI_ROTATION slot=" in text
    assert "MISTRAL_ROTATION slot=" in text
    assert "/ 21600 % 6" in text
    assert "AI-2026-09-30-Q102-REGIME-STATE-DESIGN" in text
    assert "research/evidence/q187_q192_source_feasibility_latest.json" in text
    assert "fromJSON(needs.plan_openrouter.outputs.tasks)" in text
    assert "github.event.inputs.task_id" in text
    assert "trading-agent-ai-openrouter-" in text
    assert "AI-2026-10-04-Q187-Q192-ADVERSARIAL" in text


def test_q102_regime_state_task_has_safe_scope():
    task_path = Path(__file__).parents[1] / "ai_requests" / "AI-2026-09-30-Q102-REGIME-STATE-DESIGN.json"
    payload = load_task(task_path)
    assert payload["providers"] == ["gemini_cli", "mistral_api", "openrouter_free"]
    assert payload["performance_authorized"] is False
    assert payload["holdout_selection"] is False
    assert payload["parameter_selection"] is False
    assert payload["asset_selection"] is False
    assert payload["threshold_selection"] is False
    assert payload["horizon_selection"] is False
    assert payload["research_gate_changes"] is False
    assert payload["promotion_decision"] is False
    assert payload["live_execution"] is False
    assert payload["paid_usage"] is False
    assert payload["allow_workspace_writes"] is False
    prompt = build_prompt(payload, "openrouter_free")
    assert "q102_regime_negative_evidence.py" in prompt
    assert "q103_rccsm_state_routing_integrity.py" in prompt


def test_q101_negative_evidence_task_has_safe_scope():
    task_path = Path(__file__).parents[1] / "ai_requests" / "AI-2026-09-30-Q101-NEGATIVE-EVIDENCE.json"
    payload = load_task(task_path)
    assert payload["providers"] == ["gemini_cli", "mistral_api", "openrouter_free"]
    assert payload["performance_authorized"] is False
    prompt = build_prompt(payload, "openrouter_free")
    assert "q101_negative_evidence_atlas.py" in prompt
    assert "EXTERNAL_RESEARCH_INSPIRATION_2026-09-30.md" in prompt


def test_nonlocal_gemini_quota_is_blocked_without_becoming_a_failure(monkeypatch, tmp_path):
    output = tmp_path / "quota.json"
    task_payload = task("gemini_cli")
    monkeypatch.setattr(
        "automation.ai_worker_fabric.preflight",
        lambda provider, env=None: {
            "provider": provider,
            "available": True,
            "binary": "/usr/bin/gemini",
            "free_only": True,
            "free_mode_attested": True,
            "local_mode": False,
            "local_attestation": {"present": False, "path": None},
            "free_enforcement": "attestation_or_local_attestation",
            "reasons": [],
        },
    )

    class Proc:
        returncode = 429
        stdout = ""
        stderr = "RESOURCE_EXHAUSTED: quota exceeded"

    monkeypatch.setattr(
        "automation.ai_worker_fabric.subprocess.run",
        lambda *args, **kwargs: Proc(),
    )
    result = run_task(
        task_payload,
        "gemini_cli",
        output,
        env={
            "AI_EXTERNAL_PROVIDER_ALLOWLIST": "true",
            "GEMINI_API_KEY": "dummy",
        },
    )
    assert result["status"] == "QUOTA_BLOCKED"
    assert result["returncode"] == 429


def test_q187_q192_ai_task_is_safe_and_event_driven():
    task_path = Path(__file__).parents[1] / "ai_requests" / "AI-2026-10-04-Q187-Q192-ADVERSARIAL.json"
    payload = load_task(task_path)
    assert payload["providers"] == ["openrouter_free"]
    assert payload["holdout_selection"] is False
    assert payload["parameter_selection"] is False
    assert payload["asset_selection"] is False
    assert payload["threshold_selection"] is False
    assert payload["horizon_selection"] is False
    assert payload["research_gate_changes"] is False
    assert payload["promotion_decision"] is False
    assert payload["live_execution"] is False
    assert payload["paid_usage"] is False
    assert payload["allow_workspace_writes"] is False
    context = __import__("automation.ai_worker_fabric", fromlist=["CONTEXT_FILES"]).CONTEXT_FILES["AI-2026-10-04-Q187-Q192-ADVERSARIAL"]
    assert "docs/research_design/Q187_Q192_SOURCE_PIT_WAVE_2026-10-04.md" in context
    assert "research/evidence/q187_q192_source_feasibility_latest.json" in context

def test_ai_workflow_run_triggers_only_after_successful_q187_source_workflow():
    workflow = Path(__file__).parents[1] / ".github" / "workflows" / "ai-worker-fabric.yml"
    text = workflow.read_text(encoding="utf-8")
    assert "workflow_run:" in text
    assert "Q187-Q192 Source Feasibility" in text
    assert "WORKFLOW_RUN_CONCLUSION" in text
    assert "conclusion == 'success'" in text
    assert "tasks = ['AI-2026-10-04-Q187-Q192-ADVERSARIAL']" in text
