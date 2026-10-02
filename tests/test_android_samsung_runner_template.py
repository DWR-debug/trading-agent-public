from pathlib import Path
import json

ROOT = Path(__file__).parents[1]


def test_android_samsung_profile_freezes_nonroot_and_memory_contract():
    payload = json.loads(
        (ROOT / "research/devices/android_phone_profile_template.json").read_text(encoding="utf-8")
    )
    assert payload["architecture"] == "ARM64"
    assert payload["runner_user"] != "root"
    assert payload["resource_preflight"]["gc_heap_hard_limit_hex"] == "40000000"
    assert payload["safety"]["live_trading_enabled"] is False


def test_android_samsung_start_template_is_nonroot_and_fail_closed():
    source = (
        ROOT / "scripts/android_samsung_runner_start_template.sh"
    ).read_text(encoding="utf-8")
    assert "--user" in source
    assert "DOTNET_GCHeapHardLimit" in source
    assert "ANDROID_PREFLIGHT=PASS" in source
    assert "Existing Android runner registration not found" in source


def test_android_samsung_registration_refuses_silent_reregistration():
    source = (
        ROOT / "scripts/android_samsung_runner_register_template.sh"
    ).read_text(encoding="utf-8")
    assert "refusing silent re-registration" in source
    assert "ANDROID_ALLOW_REREGISTER" in source
