from automation.live_market_observer import _corr, _lagged_corr


def test_corr_identical_series():
    assert _corr([1, 2, 3, 4], [1, 2, 3, 4]) == 1.0


def test_lagged_corr_uses_past_peer_values():
    assert _lagged_corr([1, 2, 4, 8, 16], [1, 2, 4, 8, 16], 1) > 0.99


def test_observation_output_is_valid_json(tmp_path, monkeypatch):
    import json
    from datetime import datetime, timedelta, timezone
    from types import SimpleNamespace

    from automation import live_market_observer

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candles = [
        SimpleNamespace(timestamp=start + timedelta(days=i), close=100.0 + i)
        for i in range(40)
    ]

    monkeypatch.setattr(
        live_market_observer,
        "load_yahoo_history",
        lambda *args, **kwargs: candles,
    )

    output = tmp_path / "observation.json"
    payload = live_market_observer.observe_universe(
        "benchmark",
        total=40,
        output=output,
    )

    parsed = json.loads(output.read_text(encoding="utf-8"))
    assert parsed["observation_fingerprint"] == payload["observation_fingerprint"]
    assert parsed["status"] == "OBSERVATION_ONLY"
