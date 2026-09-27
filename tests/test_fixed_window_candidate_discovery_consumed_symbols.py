
def test_fixed_window_discovery_skips_symbols_already_claimed_by_universes(monkeypatch, tmp_path):
    timestamps = [f"{year:04d}-01-01T13:30:00+00:00" for year in range(1900, 5400)]
    class Universe:
        def __init__(self, symbols):
            self.symbols = tuple(symbols)
            self.priority = 1
            self.name = "used"

    used = Universe(discovery.CANDIDATE_POOL[:3])
    monkeypatch.setattr(discovery, "list_universes", lambda: (used,))
    calls = []
    monkeypatch.setattr(
        discovery,
        "_window_timestamps",
        lambda symbol: (calls.append(symbol) or (timestamps, {})),
    )

    report = discovery.run_discovery(
        output=tmp_path / "discovery.json",
        symbol_limit=3,
        workers=2,
    )

    assert calls == list(discovery.CANDIDATE_POOL[3:6])
    assert report["excluded_existing_universe_symbols"] == list(discovery.CANDIDATE_POOL[:3])
    assert report["eligible_candidate_pool"] == list(discovery.CANDIDATE_POOL[3:6])
    assert report["candidate_pool"] == list(discovery.CANDIDATE_POOL)
    assert report["performance_evaluation"] is False
    assert report["holdout_evaluation"] is False
    assert report["selection_used"] is False
