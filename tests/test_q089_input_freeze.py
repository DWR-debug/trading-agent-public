from __future__ import annotations

import csv
import json

from automation.q089_input_freeze import freeze


def _write_snapshot(root, symbols):
    manifest = {
        "trial_id": "T-2026-09-28-089-COVERAGE",
        "symbols": list(symbols),
        "target_common_candles": 2,
        "snapshot_fingerprint": "snapshot-test-fp",
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "snapshot_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    for symbol in symbols:
        path = root / "datasets" / symbol
        path.mkdir(parents=True)
        with (path / "1d.csv").open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
            writer.writerow(["2026-01-01T00:00:00+00:00", 1, 1, 1, 1, 1])
            writer.writerow(["2026-01-02T00:00:00+00:00", 1, 1, 1, 1, 1])


def test_q089_input_freeze_persists_adjusted_close(monkeypatch, tmp_path) -> None:
    import automation.q089_input_freeze as module

    def fake_fetch(symbol, timestamps):
        return [(timestamps[0], 10.0), (timestamps[1], 11.0)]

    monkeypatch.setattr(module, "fetch_adjusted_close", fake_fetch)
    coverage = tmp_path / "coverage"
    output = tmp_path / "bundle"
    result = tmp_path / "result.json"
    _write_snapshot(coverage, ("AAA", "BBB"))

    receipt = freeze(coverage, output, result)

    assert receipt["trial_id"] == "T-2026-09-28-089-INPUT-FREEZE"
    assert receipt["status"] == "INPUT_BUNDLE_FROZEN"
    assert receipt["bundle_fingerprint"]
    assert (output / "input_bundle_manifest.json").exists()
    assert (output / "AAA" / "adjusted_close.csv").exists()
    assert (output / "BBB" / "adjusted_close.csv").exists()
