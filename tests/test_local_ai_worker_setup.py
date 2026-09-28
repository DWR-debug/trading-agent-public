from pathlib import Path

def test_local_ai_setup_disables_credit_fallback():
    text = Path("scripts/enable_local_ai_worker.ps1").read_text(encoding="utf-8")
    assert '"useG1Credits"] = $false' in text
    assert '"paid_fallback_allowed = $false"' not in text
    assert "paid_fallback_allowed = \\$false" in text
    assert "personal_credit_fallback_allowed = \\$false" in text
