from __future__ import annotations

from pathlib import Path


def test_local_ai_verifier_is_fail_closed() -> None:
    text = Path("scripts/verify_local_ai_worker.ps1").read_text(encoding="utf-8")
    assert "UseG1Credits" in text
    assert "false\\b" in text.lower()
    assert "LOCAL_AI_READINESS=READY" in text
    assert "PERSONAL_G1_CREDITS_DISABLED=True" in text


def test_local_ai_bootstrap_and_verifier_paths_are_present() -> None:
    text = Path(".github/workflows/permanent-pc-research-loop.yml").read_text(encoding="utf-8")
    assert 'enable_local_ai_worker.ps1' in text
    assert 'verify_local_ai_worker.ps1' in text
