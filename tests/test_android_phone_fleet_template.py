from pathlib import Path
import json

def test_android_phone_registry_has_unique_slots_and_governance():
    data = json.loads(Path("ops/android_phone_resources.json").read_text(encoding="utf-8"))
    assert data["acceptance_contract_version"] == "2026-10-02-R3"
    assert data["governance"]["paper_only"] is True
    assert data["governance"]["live_trading_enabled"] is False
    assert data["governance"]["orders_enabled"] is False
    assert data["governance"]["automatic_promotion"] is False
    devices = data["devices"]
    assert devices
    ids = [d["resource_id"] for d in devices]
    labels = [d["runner_label"] for d in devices]
    assert len(ids) == len(set(ids))
    assert len(labels) == len(set(labels))
    for device in devices:
        assert device["architecture"] == "ARM64"
        assert device["runner_label"].startswith("samsung-phone-")
        assert device["descriptor_path"].startswith("~/.trading-agent/")

def test_android_phone_template_is_not_model_specific():
    doc = Path("docs/SAMSUNG_ANDROID_TERMUX_PHONE_TEMPLATE.md").read_text(encoding="utf-8")
    script = Path("scripts/samsung_termux_phone_runner_template.sh").read_text(encoding="utf-8")
    assert "SAMSUNG-PHONE-01" in doc or "SAMSUNG-PHONE-01" in Path("ops/android_phone_resources.json").read_text(encoding="utf-8")
    assert "PHONE_RESOURCE_ID" in script
    assert "PHONE_RUNNER_LABEL" in script
    assert "s10-phone" not in script
    assert "S10_RUNNER_TOKEN" not in script
    assert "PHONE_RUNNER_TOKEN" in script
