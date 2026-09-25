from __future__ import annotations

from automation.wide_search_probe import _classify, _event_summary


def test_wide_search_probe_classifies_stable_research_signal():
    values = [0.002] * 30 + [0.003] * 30
    assert _classify(values) == "DISCOVERY_SUPPORT"


def test_wide_search_probe_prunes_unstable_research_signal():
    values = [0.002] * 30 + [-0.003] * 30
    assert _classify(values) == "PRUNE_NO_RESEARCH_SUPPORT"


def test_event_summary_is_deterministic():
    result = _event_summary([0.01, -0.01, 0.02])
    assert result["count"] == 3
    assert result["hit_rate"] == 2 / 3
    assert result["median_return"] == 0.01
