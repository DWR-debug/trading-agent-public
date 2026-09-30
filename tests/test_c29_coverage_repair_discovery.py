from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import automation.c29_coverage_repair_discovery as module


def test_c29_repair_discovery_contract_is_fixed_and_non_authorizing() -> None:
    spec = json.loads(
        Path("research/preregistrations/c29_coverage_repair_discovery_2026_09_30.json")
        .read_text(encoding="utf-8")
    )
    assert spec["parent_trial_id"] == "T-2026-09-30-C29-COVERAGE-PIT"
    assert spec["candidate_pool"] == ["ICE", "MCK", "PNR", "ROP", "HUM", "CMG"]
    assert spec["replacement_rule"].startswith("Evaluate only data coverage")
    assert spec["governance"]["performance_evaluation"] is False
    assert spec["governance"]["holdout_evaluation"] is False
    assert spec["governance"]["asset_selection_by_performance"] is False
    assert spec["governance"]["candidate_ranking"] is False
    assert spec["governance"]["performance_authorized"] is False


def test_c29_repair_discovery_uses_first_coverage_valid_symbol(monkeypatch, tmp_path) -> None:
    counts = {"ICE": 3400, "MCK": 3500, "PNR": 4100, "ROP": 3200, "HUM": 4500, "CMG": 3600}

    def fake_loader(symbol, interval, requested, *, allow_partial, skip_invalid_ohlc, quality_report):
        assert interval == "1d"
        assert requested == module.RAW_FETCH
        assert allow_partial is True
        assert skip_invalid_ohlc is True
        quality_report["synthetic"] = 1
        start = datetime(2011, 1, 1, tzinfo=timezone.utc)
        return [
            SimpleNamespace(timestamp=start + timedelta(days=i))
            for i in range(counts[symbol])
        ]

    monkeypatch.setattr(module, "load_yahoo_history", fake_loader)

    result = module.run(tmp_path / "result.json")
    assert result["selected_replacement"] == "MCK"
    assert result["coverage_valid_candidates"] == ["MCK", "PNR", "HUM", "CMG"]
    assert result["selection_basis"] == "coverage_only_fixed_source_order"
    assert result["scientific_outcome"] == "NO_SCIENTIFIC_OUTCOME"
    assert result["performance_evaluation"] is False
    assert result["holdout_evaluation"] is False
    assert result["candidate_ranking"] is False
    assert result["candidate_selection"] is False
    assert result["performance_authorized"] is False
    assert result["safety"]["paper_only"] is True
