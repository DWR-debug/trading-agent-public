from pathlib import Path
import json

import automation.s10_local_stack as stack
import automation.s10_systemone_bridge as bridge
from automation.s10_runtime import load_descriptor


def test_s10_release_arch_mapping():
    original = stack.platform.machine
    try:
        stack.platform.machine = lambda: "aarch64"
        assert stack._arch_suffix() == "arm64"
        stack.platform.machine = lambda: "x86_64"
        assert stack._arch_suffix() == "x64"
    finally:
        stack.platform.machine = original


def test_s10_descriptor_written_by_bootstrap_is_accepted(tmp_path):
    descriptor = tmp_path / "s10_interface.json"
    stack._write_descriptor(descriptor, "Qwen2.5-1.5B-Instruct")
    payload = json.loads(descriptor.read_text(encoding="utf-8"))
    assert "token" not in payload
    assert "credentials" not in payload
    loaded = load_descriptor(descriptor)
    assert loaded["available"] is True
    assert loaded["base_url"] == "http://127.0.0.1:8765"
    assert loaded["protocol_path"] == "/v1/systemone"


def test_bridge_dynamic_model_resolution_prefers_loaded_model(monkeypatch):
    monkeypatch.setattr(
        bridge,
        "MODEL",
        "S10-Qwen2.5-1.5B",
    )
    monkeypatch.setattr(
        bridge,
        "get_json",
        lambda _url: {"data": [{"id": "Qwen2.5-1.5B-Instruct"}]},
    )
    assert bridge.resolve_upstream_model() == "Qwen2.5-1.5B-Instruct"


def test_bridge_dynamic_model_resolution_keeps_configured_model_when_exact(monkeypatch):
    monkeypatch.setattr(
        bridge,
        "MODEL",
        "Qwen2.5-1.5B-Instruct",
    )
    monkeypatch.setattr(
        bridge,
        "get_json",
        lambda _url: {"data": [{"id": "Qwen2.5-1.5B-Instruct"}]},
    )
    assert bridge.resolve_upstream_model() == "Qwen2.5-1.5B-Instruct"


def test_s10_stack_source_is_local_only():
    source = Path("automation/s10_local_stack.py").read_text(encoding="utf-8")
    assert 'HOST = "127.0.0.1"' in source
    assert "trading-agent-public/S10-local-stack-bootstrap/1" in source
    assert "credentials_touched" in source


def test_s10_mobile_server_uses_bounded_memory_defaults():
    source = Path("automation/s10_local_stack.py").read_text(encoding="utf-8")
    assert '"--ctx-size", "2048"' in source
    assert '"--batch-size", "256"' in source
    assert '"--ubatch-size", "128"' in source
    assert '"--parallel", "1"' in source
    assert '"--seed", str(S10_SEED)' in source
    assert "S10_SEED = int(os.environ.get(\"S10_SEED\", \"42\"))" in source


def test_s10_worker_workflow_contains_bounded_watchdog():
    source = Path(".github/workflows/s10-phone-worker.yml").read_text(encoding="utf-8")
    assert "S10 watchdog: endpoint unavailable" in source
    assert "sleep 5" in source
    assert "cleanup()" in source


def test_s10_bridge_uses_tiny_smoke_response_budget():
    source = Path("automation/s10_systemone_bridge.py").read_text(encoding="utf-8")
    assert '"max_tokens": 48 if smoke_mode else 160' in source
