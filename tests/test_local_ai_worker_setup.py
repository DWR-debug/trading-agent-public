from pathlib import Path

def test_local_ai_setup_disables_credit_fallback():
    text = Path("scripts/enable_local_ai_worker.ps1").read_text(encoding="utf-8")
    assert '"UseG1Credits": false' in text
    assert "paid_fallback_allowed = $false" in text
    assert "personal_credit_fallback_allowed = $false" in text


def test_local_ai_smoke_reader_accepts_windows_powershell_utf8_bom():
    text = Path("automation/local_ai_smoke.py").read_text(encoding="utf-8")
    assert 'path.read_text(encoding="utf-8-sig")' in text
    setup = Path("scripts/enable_local_ai_worker.ps1").read_text(encoding="utf-8")
    assert "Set-Content -Encoding UTF8 $settingsPath -Value $settingsText" in setup
    assert "New-Object System.Text.UTF8Encoding" not in setup


def test_local_ai_smoke_reports_g1_parse_state():
    text = Path("automation/local_ai_smoke.py").read_text(encoding="utf-8")
    assert "g1_setting_value" in text
    assert "g1_settings_error" in text
    assert 'encoding="utf-8-sig"' in text
