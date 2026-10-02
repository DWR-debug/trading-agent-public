from pathlib import Path

def test_samsung_template_is_generic_and_secret_safe():
    doc = Path("docs/SAMSUNG_ANDROID_TERMUX_PHONE_TEMPLATE.md").read_text(encoding="utf-8")
    script = Path("scripts/samsung_termux_phone_runner_template.sh").read_text(encoding="utf-8")
    assert "S10 ist die Referenzimplementierung" in doc
    assert "S11/S12" in doc
    assert "PHONE_RESOURCE_ID" in script
    assert "PHONE_RUNNER_LABEL" in script
    assert "registration token" in script.lower()
    assert "unset TOKEN" in script
    assert "ANDROID-PHONE" in script
    assert "s10-phone" not in script
    assert "S10_RUNNER_TOKEN" not in script
    assert "PHONE_RUNNER_TOKEN" in script

def test_s10_template_reference_is_pinned():
    doc = Path("docs/SAMSUNG_ANDROID_TERMUX_PHONE_TEMPLATE.md").read_text(encoding="utf-8")
    for value in ("127.0.0.1:8765", "127.0.0.1:8080", "2026-10-02-R3"):
        assert value in doc
