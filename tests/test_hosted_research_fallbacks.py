from pathlib import Path
import json


def test_hosted_research_fallbacks_are_retired_and_fail_closed():
    for family in ("q068", "q070"):
        assert not Path(f".github/workflows/{family}-hosted-fallback.yml").exists()

    q068 = json.loads(
        Path("research/authorizations/q068_performance_2026_09_28.json").read_text(encoding="utf-8")
    )
    assert q068["authorized"] is False
    assert q068["performance_execution_authorized"] is False

    q070 = json.loads(
        Path("research/authorizations/q070_performance_2026_09_28.json").read_text(encoding="utf-8")
    )
    assert q070["authorized"] is False
    assert q070["performance_execution_authorized"] is False


def test_retired_hosted_fallback_triggers_are_not_executable_paths():
    for path in (
        "research/run_requests/q068_hosted_fallback.trigger",
        "research/run_requests/q070_hosted_fallback.trigger",
    ):
        assert Path(path).exists()
        text = Path(path).read_text(encoding="utf-8")
        assert "HOSTED_FALLBACK" in text or "hosted" in text.lower()
