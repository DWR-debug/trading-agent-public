from automation.coverage_candidate_discovery import (
    CANDIDATE_POOL,
    run_discovery,
)


def test_candidate_pool_is_fixed_and_unique():
    assert len(CANDIDATE_POOL) == len(set(CANDIDATE_POOL))
    assert CANDIDATE_POOL == tuple(sorted(CANDIDATE_POOL))


def test_discovery_selects_first_coverage_valid_candidate(monkeypatch, tmp_path):
    def fake_loader(symbol, interval, total, **kwargs):
        count = 3520 if symbol in {CANDIDATE_POOL[2], CANDIDATE_POOL[4]} else 3000
        return [
            type("Bar", (), {
                "timestamp": __import__("datetime").datetime(2010, 1, 1),
                "open": 100.0, "high": 101.0, "low": 99.0,
                "close": 100.5, "volume": 1000.0,
            })()
            for _ in range(count)
        ]

    monkeypatch.setattr(
        "automation.coverage_candidate_discovery.load_yahoo_history",
        fake_loader,
    )
    report = run_discovery(output=tmp_path / "discovery.json")

    assert report["performance_evaluation"] is False
    assert report["holdout_evaluation"] is False
    assert report["selection_used"] is False
    assert report["coverage_valid_candidates"] == [
        CANDIDATE_POOL[2],
        CANDIDATE_POOL[4],
    ]
    assert report["next_deterministic_candidate"] == CANDIDATE_POOL[2]
