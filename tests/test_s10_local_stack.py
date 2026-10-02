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
