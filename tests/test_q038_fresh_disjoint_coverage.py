from __future__ import annotations

from datetime import datetime, timedelta, timezone

from automation.q038_fresh_disjoint_coverage import CANDIDATE_POOL, run_coverage


def test_q038_candidate_pool_is_fixed_and_unique():
    assert CANDIDATE_POOL == (
        "IVE", "IWL", "DLN", "DHS", "DON", "DES", "USRT", "ITB"
    )
    assert len(CANDIDATE_POOL) == len(set(CANDIDATE_POOL)) == 8


def test_q038_accepts_only_source_order_candidates_with_common_calendar(monkeypatch, tmp_path):
    base = datetime(2010, 1, 1, tzinfo=timezone.utc)
    full = [base + timedelta(days=i) for i in range(3500)]
    short = [base + timedelta(days=i) for i in range(3499)]

    def fake_universes():
        return ()

    def fake_loader(symbol, interval, total, **kwargs):
        timestamps = short if symbol == "DHS" else full
        return [
            type(
                "Bar",
                (),
                {
                    "timestamp": ts,
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.5,
                    "volume": 1000.0,
                },
            )()
            for ts in timestamps
        ]

    monkeypatch.setattr(
        "automation.q038_fresh_disjoint_coverage.list_universes",
        fake_universes,
    )
    monkeypatch.setattr(
        "automation.q038_fresh_disjoint_coverage.load_yahoo_history",
        fake_loader,
    )

    report = run_coverage(output=tmp_path / "coverage.json")

    assert report["status"] == "DATA_INSUFFICIENT"
    assert report["accepted_symbols"] == ["IVE", "IWL", "DLN", "DON", "DES", "USRT", "ITB"]
    assert report["common_calendar_count"] == 3500
    assert report["performance_evaluation"] is False
    assert report["holdout_evaluation"] is False
    assert report["selection_used"] is False


def test_q038_fails_closed_on_consumed_symbol_overlap(monkeypatch, tmp_path):
    class U:
        symbols = ("IVE",)

    monkeypatch.setattr(
        "automation.q038_fresh_disjoint_coverage.list_universes",
        lambda: (U(),),
    )
    try:
        run_coverage(output=tmp_path / "coverage.json")
    except RuntimeError as exc:
        assert "overlaps an existing registered universe" in str(exc)
    else:
        raise AssertionError("expected consumed-symbol overlap to fail closed")
