import json
from pathlib import Path


def test_q067_performance_preregistration_is_fixed_and_unranked():
    p = json.loads(
        Path("research/preregistrations/q067_performance_2026_09_28.json").read_text(
            encoding="utf-8"
        )
    )
    assert p["status"] == "PREREGISTERED_PERFORMANCE"
    assert p["symbols"] == ["ANSS", "ROP", "NVR", "ZION", "SLB", "EIX", "K", "CCL"]
    assert p["governance"]["parameter_search"] is False
    assert p["governance"]["family_ranking"] is False
    assert p["governance"]["selection"] is False
    assert p["governance"]["holdout_used_for_selection"] is False
    assert p["governance"]["automatic_promotion"] is False
    assert len(p["arms"]) == 3


def test_q067_formal_workflows_use_trusted_self_hosted_runner():
    for relative in (
        ".github/workflows/q067-coverage-pit.yml",
        ".github/workflows/q067-fixed-mechanism-performance.yml",
    ):
        text = Path(relative).read_text(encoding="utf-8")
        assert "runs-on: [self-hosted, trading-agent-research]" in text
        assert "windows-latest" not in text

def test_q067_workflows_preserve_paper_only_and_no_selection_guards():
    coverage = Path(".github/workflows/q067-coverage-pit.yml").read_text(encoding="utf-8")
    performance = Path(".github/workflows/q067-fixed-mechanism-performance.yml").read_text(encoding="utf-8")
    combined = coverage + "\n" + performance
    assert "PAPER_ONLY" in combined
    assert "LIVE_TRADING_ENABLED" in combined
    assert "ORDERS_ENABLED" in combined
    assert "AUTOMATIC_PROMOTION" in combined
    assert "selection" in combined
