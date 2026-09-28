from pathlib import Path

import automation.fixed_window_candidate_discovery as discovery


def test_fixed_window_discovery_reuses_first_symbol_fetch(monkeypatch, tmp_path):
    timestamps = [f"2020-01-{i:02d}T13:30:00+00:00" for i in range(1, 32)]
    # The implementation needs 3500 distinct sessions; keep the test compact
    # by using a deterministic synthetic range of exactly the required size.
    timestamps = [f"{i:04d}-01-01T13:30:00+00:00" for i in range(3500)]
    calls = []

    monkeypatch.setattr(discovery, "list_universes", lambda: ())
    monkeypatch.setattr(discovery, "_prior_research_symbols", lambda: set())
    monkeypatch.setattr(discovery, "_window_timestamps", lambda symbol: (calls.append(symbol) or (timestamps, {})))

    report = discovery.run_discovery(
        output=tmp_path / "discovery.json",
        symbol_limit=12,
        workers=4,
    )

    assert report["selected_common_count"] == 3500
    assert len(report["selected_coverage_batch"]) == 12
    assert set(calls) == set(discovery.CANDIDATE_POOL[:12])
    assert len(calls) == len(set(calls))
    assert report["performance_evaluation"] is False
    assert report["holdout_evaluation"] is False
    assert report["selection_used"] is False
    assert Path(tmp_path / "discovery.json").exists()



def test_prior_research_symbols_include_closed_q070_universe():
    used = discovery._prior_research_symbols()
    assert {"SPG", "CCI", "EQIX", "ESS", "ARE", "WY", "PLD", "KIM"} <= used


def test_candidate_pool_excludes_q070_symbols():
    used = discovery._prior_research_symbols()
    remaining = [s for s in discovery.CANDIDATE_POOL if s not in used]
    assert all(s not in {"SPG", "CCI", "EQIX", "ESS", "ARE", "WY", "PLD", "KIM"} for s in remaining)
