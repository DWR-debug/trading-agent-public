from pathlib import Path
from tempfile import TemporaryDirectory
import csv
import json

from automation.h06_mechanism_replication import _run


SYMBOLS = (
    "MU", "ADBE", "CRM", "ABT", "BMY", "BAX",
    "PH", "ROK", "DOV", "CPB", "SJM", "CAG", "EXC", "SRE", "CMS",
)


def _write_snapshot(root: Path) -> None:
    manifest = {
        "universe": "validation_2026_09_26_h06_mechanism_replication",
        "research_candles_used": 2798,
        "holdout_candles_unused": 702,
        "governance": {"holdout_used_for_selection": False},
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    header = ("timestamp", "open", "high", "low", "close", "volume")
    for symbol_index, symbol in enumerate(SYMBOLS):
        symbol_dir = root / symbol
        symbol_dir.mkdir(parents=True)
        with (symbol_dir / "1d.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            for index in range(3500):
                price = 100.0 + symbol_index + (
                    index * (0.01 + symbol_index * 0.0001)
                )
                # Valid ISO-like unique timestamp strings; only ordering and
                # cross-symbol identity are required by the diagnostic.
                timestamp = f"2020-01-01T00:{index // 60:02d}:{index % 60:02d}+00:00"
                writer.writerow(
                    (timestamp, price, price, price, price, 1000.0)
                )


def test_h06_mechanism_is_research_only_and_holdout_blind():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_snapshot(root)
        result = _run(root, root / "manifest.json")

    assert result["findings"]["aggregate"]["decision_count"] == 2546
    assert result["source"]["holdout_candles_used"] == 0
    assert result["governance"]["forward_returns_used"] is False
    assert result["governance"]["pnl_used"] is False
    assert result["governance"]["holdout_used"] is False
    assert result["governance"]["performance_trial_authorized"] is False
    assert result["governance"]["automatic_promotion"] is False
    assert "period_return" not in json.dumps(result)


def test_h06_temporal_windows_are_five_and_complete():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_snapshot(root)
        result = _run(root, root / "manifest.json")

    windows = result["findings"]["temporal_windows"]
    assert len(windows) == 5
    assert sum(window["decision_count"] for window in windows) == 2546
