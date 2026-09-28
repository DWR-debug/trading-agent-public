from pathlib import Path

def test_local_ai_setup_disables_credit_fallback():
    text = Path("scripts/enable_local_ai_worker.ps1").read_text(encoding="utf-8")
    assert '"UseG1Credits": false' in text
    assert "paid_fallback_allowed = $false" in text
    assert "personal_credit_fallback_allowed = $false" in text


def test_local_ai_settings_are_written_without_utf8_bom():
    text = Path("scripts/enable_local_ai_worker.ps1").read_text(encoding="utf-8")
    assert "UTF8Encoding($false)" in text
    assert "[System.IO.File]::WriteAllText($settingsPath, $settingsText, $utf8NoBom)" in text
    assert "Set-Content -Encoding UTF8 $settingsPath" not in text
