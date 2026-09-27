from datetime import datetime, timedelta, timezone

from automation.q039_price_only_alpha_pit import (
    SYMBOLS,
    _a1_tsm_consensus,
    _a2_cs_top2,
    _a3_residual_top2,
    _a5_low_beta_top2,
    run,
)


def _bars(n=400):
    base = datetime(2020, 1, 1, tzinfo=timezone.utc)
    return [
        type(
            "Bar",
            (),
            {
                "timestamp": base + timedelta(days=i),
                "open": 100.0 + i * 0.1,
                "high": 101.0 + i * 0.1,
                "low": 99.0 + i * 0.1,
                "close": 100.0 + i * 0.1,
                "volume": 1000.0,
            },
        )()
        for i in range(n)
    ]


def test_signals_use_fixed_price_only_rules():
    closes = {
        symbol: [100.0 + i * (position + 1) for i in range(400)]
        for position, symbol in enumerate(SYMBOLS)
    }
    assert _a1_tsm_consensus(closes["IVE"], 300) == 1
    top = _a2_cs_top2(closes, 300)
    assert len(top) == 2
    assert set(top) <= set(SYMBOLS)
    assert len(_a3_residual_top2(closes, 300)) == 2
    assert len(_a5_low_beta_top2(closes, 300)) == 2


def test_mutation_harness_stays_pit(monkeypatch, tmp_path):
    root = tmp_path / "datasets"
    for symbol in SYMBOLS:
        path = root / symbol
        path.mkdir(parents=True)
        bars = _bars()
        with (path / "1d.csv").open("w", encoding="utf-8") as handle:
            handle.write("timestamp,open,high,low,close,volume\n")
            for bar in bars:
                handle.write(
                    f"{bar.timestamp.isoformat()},{bar.open},{bar.high},"
                    f"{bar.low},{bar.close},{bar.volume}\n"
                )

    # This fixture is intentionally short; replace the runner loader just for
    # direct PIT behavior testing below by using a 3500-row deterministic series.
    root2 = tmp_path / "datasets3500"
    for symbol in SYMBOLS:
        path = root2 / symbol
        path.mkdir(parents=True)
        bars = _bars(3500)
        with (path / "1d.csv").open("w", encoding="utf-8") as handle:
            handle.write("timestamp,open,high,low,close,volume\n")
            for bar in bars:
                handle.write(
                    f"{bar.timestamp.isoformat()},{bar.open},{bar.high},"
                    f"{bar.low},{bar.close},{bar.volume}\n"
                )

    report = run(root2, tmp_path / "report.json")
    assert report["status"] == "PIT_PASSED"
    assert report["future_mutation_checks_passed"] is True
    assert report["next_session_mutation_checks_passed"] is True
