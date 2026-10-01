from __future__ import annotations

import json

from automation import h06_p2_input_freeze as freeze


def test_freeze_contract_is_upstream_only():
    assert freeze.SAFETY == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }


def test_snapshot_verifier_rejects_wrong_fingerprint(tmp_path):
    root = tmp_path / "coverage"
    root.mkdir()
    (root / "snapshot_manifest.json").write_text(
        json.dumps({
            "universe": "validation_2026_09_25_sector_neutral_residual_momentum_repair",
            "snapshot_fingerprint": "wrong",
            "symbols": list(freeze.EXPECTED_SYMBOLS),
            "target_common_candles": 3500,
            "datasets": [],
        }),
        encoding="utf-8",
    )
    try:
        freeze.verify_snapshot(root)
    except RuntimeError as exc:
        assert str(exc) == "H06-P2 snapshot fingerprint mismatch"
    else:
        raise AssertionError("expected fail-closed fingerprint rejection")


def test_adjusted_close_url_is_bound_to_dividend_and_split_events(monkeypatch):
    seen = {}

    def fake_urlopen(req, timeout):
        seen["url"] = req.full_url
        payload = {
            "chart": {
                "result": [{
                    "timestamp": [1577885400, 1577971800],
                    "indicators": {"adjclose": [{"adjclose": [99.0, 100.0]}]},
                }]
            }
        }

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(payload).encode()

        return Response()

    monkeypatch.setattr(freeze.urllib.request, "urlopen", fake_urlopen)
    values = freeze.fetch_adjusted_close(
        "TXN",
        ["2020-01-01T13:30:00+00:00", "2020-01-02T13:30:00+00:00"],
    )
    assert values == [
        ("2020-01-01T13:30:00+00:00", 99.0),
        ("2020-01-02T13:30:00+00:00", 100.0),
    ]
    assert "events=div%2Csplits" not in seen["url"]
    assert "events=div%2Csplits" in seen["url"] or "events=div%2Csplits" in seen["url"].replace("%2C", ",")
