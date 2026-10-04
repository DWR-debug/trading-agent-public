from __future__ import annotations

from pathlib import Path


def test_local_ai_verifier_is_fail_closed() -> None:
    text = Path("scripts/verify_local_ai_worker.ps1").read_text(encoding="utf-8")
    assert "UseG1Credits" in text
    assert '"(?:UseG1Credits|useG1Credits)"' in text or '"UseG1Credits"' in text
    assert '=> false' not in text.lower()
    assert 'write-output "personal_g1_credits_disabled=true"' in text.lower()
    assert "LOCAL_AI_READINESS=READY" in text
    assert "PERSONAL_G1_CREDITS_DISABLED=True" in text


def test_local_ai_bootstrap_and_verifier_paths_are_in_isolated_worker() -> None:
    text = Path(".github/workflows/windows-local-ai-worker.yml").read_text(encoding="utf-8")
    assert 'enable_local_ai_worker.ps1' in text
    assert 'verify_local_ai_worker.ps1' in text
    permanent = Path(".github/workflows/permanent-pc-research-loop.yml").read_text(encoding="utf-8")
    assert "local_ai_worker:" not in permanent
    assert "local_ai_smoke:" not in permanent


def test_local_ai_verifier_uses_segmented_windows_paths_and_real_regex() -> None:
    text = Path("scripts/verify_local_ai_worker.ps1").read_text(encoding="utf-8")
    assert 'Join-Path $env:USERPROFILE ".gemini"' in text
    assert 'Join-Path $geminiDir "antigravity-cli"' in text
    assert 'Join-Path $agyConfigDir "settings.json"' in text
    assert '"(?:UseG1Credits|useG1Credits)"\\s*:\\s*false\\b' in text
