import json
from pathlib import Path

import pytest

from automation.q067_fresh_coverage import _used_symbols


def test_q067_fixed_universe_is_disjoint_from_ledger():
    prereg = json.loads(
        Path("research/preregistrations/q067_fixed_mechanism_freeze_2026_09_28.json").read_text(
            encoding="utf-8"
        )
    )
    assert not (set(prereg["symbols"]) & _used_symbols())


def test_q067_coverage_contract_has_no_performance_authorization():
    prereg = json.loads(
        Path("research/preregistrations/q067_fixed_mechanism_freeze_2026_09_28.json").read_text(
            encoding="utf-8"
        )
    )
    assert prereg["governance"]["performance_trial_authorized"] is False
    assert prereg["governance"]["holdout_used_for_selection"] is False


def test_q067_missing_symbols_are_rejected(tmp_path):
    from automation.q067_fresh_coverage import run

    prereg = {
        "symbols": ["AAPL"],
        "coverage_trial_id": "TEST",
        "requested_candles": 1,
        "target_common_candles": 1,
        "governance": {
            "performance_trial_authorized": False,
            "holdout_used_for_selection": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    fake = tmp_path / "prereg.json"
    fake.write_text(json.dumps(prereg), encoding="utf-8")
    with pytest.raises(RuntimeError):
        run(fake, tmp_path / "out", tmp_path / "result.json")
