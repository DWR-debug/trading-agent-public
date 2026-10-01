from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from automation.coverage_candidate_discovery_repair import (
    CANDIDATE_POOL,
    run_discovery,
)


def test_repair_pool_is_sorted_unique_and_disjoint_contract_is_checked(monkeypatch, tmp_path):
    assert CANDIDATE_POOL == tuple(sorted(CANDIDATE_POOL))
    assert len(CANDIDATE_POOL) == len(set(CANDIDATE_POOL))

    def fake_loader(symbol, interval, total, **kwargs):
        count = 3520 if symbol == CANDIDATE_POOL[2] else 3000
        return [
            SimpleNamespace(
                timestamp=datetime(2010, 1, 1),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000.0,
            )
            for _ in range(count)
        ]

    monkeypatch.setattr(
        "automation.coverage_candidate_discovery_repair.load_yahoo_history",
        fake_loader,
    )
    monkeypatch.setattr(
        "automation.coverage_candidate_discovery_repair.list_universes",
        lambda: (),
    )
    report = run_discovery(output=tmp_path / "repair.json")
    assert report["coverage_valid_candidates"] == [CANDIDATE_POOL[2]]
    assert report["next_deterministic_candidate"] == CANDIDATE_POOL[2]
    assert report["performance_evaluation"] is False
    assert report["holdout_evaluation"] is False
    assert report["selection_used"] is False
    assert report["governance"]["performance_authorized"] is False


def test_repair_is_fail_closed_on_overlap(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "automation.coverage_candidate_discovery_repair.list_universes",
        lambda: (
            SimpleNamespace(symbols=(CANDIDATE_POOL[0],)),
        ),
    )
    try:
        run_discovery(output=tmp_path / "repair.json")
    except RuntimeError as exc:
        assert "overlaps an existing universe" in str(exc)
    else:
        raise AssertionError("overlap must fail closed")
