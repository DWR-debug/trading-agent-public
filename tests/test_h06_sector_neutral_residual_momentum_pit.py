from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone

from automation.h06_sector_neutral_residual_momentum_pit import (
    RESEARCH_CANDLES,
    SYMBOLS,
    _signal,
    _mutate_future,
    run,
)


def _write_dataset(root, n=3500):
    base = datetime(2010, 1, 1, tzinfo=timezone.utc)
    for symbol_index, symbol in enumerate(SYMBOLS):
        path = root / symbol
        path.mkdir(parents=True)
        with (path / "1d.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
            for i in range(n):
                close = 100.0 + i * (0.1 + symbol_index * 0.01)
                writer.writerow([
                    (base + timedelta(days=i)).isoformat(),
                    close - 1.0,
                    close + 1.0,
                    close - 2.0,
                    close,
                    1000.0 + i,
                ])


def test_signal_is_invariant_to_future_and_next_session_mutations(tmp_path):
    root = tmp_path / "datasets"
    _write_dataset(root)
    assets = __import__(
        "automation.h06_sector_neutral_residual_momentum_pit",
        fromlist=["_load"],
    )._load(root)
    index = 1000
    original = _signal(assets, index)
    assert original == _signal(_mutate_future(assets, index, include_next=False), index)
    assert original == _signal(_mutate_future(assets, index, include_next=True), index)


def test_run_is_exhaustive_over_research_decision_points(tmp_path):
    root = tmp_path / "datasets"
    _write_dataset(root)
    out = tmp_path / "pit.json"
    coverage = {
        "coverage": {"status": "COVERAGE_READY"},
        "governance": {"performance_trial_authorized": False, "holdout_evaluation": False},
        "fingerprint": "coverage-fp",
        "snapshot_fingerprint": "snapshot-fp",
    }
    coverage_path = tmp_path / "coverage.json"
    coverage_path.write_text(__import__("json").dumps(coverage), encoding="utf-8")
    report = run(root, out, coverage_path)
    assert report["status"] == "PIT_PASSED"
    assert report["checked_decision_points"] == RESEARCH_CANDLES - 252 - 1
    assert report["governance"]["performance_evaluation"] is False
    assert report["governance"]["performance_trial_authorized"] is False
    assert report["governance"]["holdout_evaluation"] is False
    assert report["checks"]["prefix_truncation_checks_passed"] is True
    assert report["checks"]["future_mutation_checks_passed"] is True
    assert report["checks"]["next_session_mutation_checks_passed"] is True
