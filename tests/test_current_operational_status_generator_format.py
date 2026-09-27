from pathlib import Path


def test_status_generator_has_no_escaped_backticks_or_trailing_hard_breaks():
    text = Path("automation/sync_current_operational_status.py").read_text(encoding="utf-8")
    assert "\\`" not in text
    assert "  \\n" not in text
