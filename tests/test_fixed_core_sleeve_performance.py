import copy
import json
from pathlib import Path

import pytest

from automation.fixed_core_sleeve_performance import (
    EXPECTED_GATES,
    EXPECTED_UNIVERSES,
    _cs_weights,
    _fp,
    _load_prereg,
    _load_assets,
    _rolling,
    _stats,
    _validate_pit,
    run,
)
from automation.publish_t052_result import publish
from backtesting.models import Candle


def _assets(count=3500):
    from datetime import datetime, timedelta, timezone
    origin = datetime(2011, 1, 1, tzinfo=timezone.utc)
    symbols = ("A", "B", "C", "D")
    return {
        symbol: tuple(
            Candle(
                timestamp=origin + timedelta(days=i),
                open=100.0 + i + offset,
                high=100.0 + i + offset,
                low=100.0 + i + offset,
                close=100.0 + i + offset,
                volume=1000.0,
            )
            for i in range(count)
        )
        for offset, symbol in enumerate(symbols)
    }


def test_cs_weights_are_fixed_top2_long_only():
    weights = _cs_weights(_assets())
    assert len(weights) == 3500
    assert all(sum(row.values()) <= 1.0 + 1e-12 for row in weights)
    assert all(
        value in {0.0, 0.5}
        for row in weights[280:3500]
        for value in row.values()
    )


def test_stats_and_rolling_are_deterministic():
    values = [0.01, -0.005, 0.02, -0.01] * 700
    assert _stats(values, 0, 2798) == _stats(values, 0, 2798)
    rolling = _rolling(values)
    assert len(rolling) == 5
    assert sum(item["day_count"] for item in rolling) == 2798


def test_t052_preregistration_is_safe_and_fixed():
    spec = _load_prereg(
        Path(
            "research/preregistrations/"
            "trial_052_fixed_core_sleeve_performance_2026_09_27.json"
        )
    )
    assert spec["trial_id"] == "T-2026-09-27-052"
    assert spec["data_contract"]["research_periods"] == 2798
    assert spec["data_contract"]["holdout_periods"] == 700
    assert spec["governance"]["parameter_search"] is False
    assert spec["governance"]["asset_selection_by_performance"] is False
    assert spec["governance"]["holdout_used_for_selection"] is False
    assert spec["safety"]["orders_enabled"] is False


def test_stats_empty_is_explicitly_empty():
    result = _stats([], 0, 1)
    assert result["day_count"] == 0
    assert result["period_return"] == 0.0


def test_t052_preregistration_rejects_contract_drift(tmp_path):
    source = json.loads(
        Path(
            "research/preregistrations/"
            "trial_052_fixed_core_sleeve_performance_2026_09_27.json"
        ).read_text(encoding="utf-8")
    )
    for name, mutate in (
        ("cost", lambda spec: spec["cost_contract"].update(fee_rate=0.002)),
        ("signal", lambda spec: spec["signal_contracts"]["cs_momentum_12_1_top2"].update(top_n=3)),
        ("universe", lambda spec: spec["universes"][0]["symbols"].reverse()),
    ):
        candidate = copy.deepcopy(source)
        mutate(candidate)
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(candidate), encoding="utf-8")
        with pytest.raises(RuntimeError):
            _load_prereg(path)


def test_snapshot_rejects_failed_coverage_before_loading(tmp_path, monkeypatch):
    import automation.fixed_core_sleeve_performance as runner

    manifest_path = tmp_path / "snapshot_manifest.json"
    manifest_path.write_text(
        json.dumps({
            "status": "COVERAGE_PASSED",
            "universe": "validation_2026_09_27_fixed_candidate_batch",
            "source": "yahoo_chart",
            "interval": "1d",
            "symbols": ["A"],
            "target_common_candles": 3500,
            "coverage": {"common_calendar_count": 3499, "errors": {}},
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        runner,
        "load_frozen_snapshot",
        lambda path: pytest.fail("snapshot data must not load after coverage failure"),
    )
    with pytest.raises(ValueError, match="coverage preflight"):
        _load_assets(
            manifest_path,
            {
                "universe": "validation_2026_09_27_fixed_candidate_batch",
                "symbols": ["A"],
            },
        )


def test_snapshot_accepts_canonical_manifest_contract(tmp_path, monkeypatch):
    import automation.fixed_core_sleeve_performance as runner

    assets = {"A": _assets()["A"]}
    manifest_path = tmp_path / "snapshot_manifest.json"
    manifest_path.write_text(
        json.dumps({
            "status": "COVERAGE_PASSED",
            "universe": "validation_2026_09_27_fixed_candidate_batch",
            "source": "yahoo_chart",
            "interval": "1d",
            "symbols": ["A"],
            "target_common_candles": 3500,
            "coverage": {"common_calendar_count": 3704, "errors": {}},
            "governance": {
                "performance_evaluation": False,
                "holdout_evaluation": False,
                "selection_used": False,
            },
            "safety": {
                "paper_only": True,
                "live_trading_enabled": False,
                "orders_enabled": False,
                "automatic_promotion": False,
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "load_frozen_snapshot", lambda path: assets)
    assert _load_assets(
        manifest_path,
        {
            "universe": "validation_2026_09_27_fixed_candidate_batch",
            "symbols": ["A"],
        },
    ) == assets


def test_fresh_pit_mutation_checks_pass_on_fixed_signal_paths():
    result = _validate_pit(_assets())
    assert result["status"] == "PIT_PASSED"
    assert result["trend_sma_50_200"]["checked_decisions"] > 0
    assert result["cs_momentum_12_1_top2"]["checked_rebalances"] > 0


def test_run_stops_before_performance_when_pit_fails(monkeypatch):
    import automation.fixed_core_sleeve_performance as runner

    spec = {
        "universes": [
            {
                "trial_id": "T-2026-09-27-049",
                "universe": "validation_2026_09_27_fixed_candidate_batch",
                "symbols": ["A", "B", "C", "D"],
            },
            {
                "trial_id": "T-2026-09-27-050",
                "universe": "validation_2026_09_27_fixed_candidate_batch_02",
                "symbols": ["A", "B", "C", "D"],
            },
        ],
    }
    monkeypatch.setattr(runner, "_load_prereg", lambda path: spec)
    monkeypatch.setattr(runner, "_load_assets", lambda *args: _assets())
    monkeypatch.setattr(
        runner,
        "_validate_pit",
        lambda assets: (_ for _ in ()).throw(RuntimeError("PIT failed")),
    )
    monkeypatch.setattr(
        runner,
        "_evaluate",
        lambda *args: pytest.fail("performance must not run after PIT failure"),
    )
    manifests = {
        "T-2026-09-27-049": Path("t049.json"),
        "T-2026-09-27-050": Path("t050.json"),
    }
    with pytest.raises(RuntimeError, match="PIT failed"):
        run(Path("prereg.json"), manifests, Path("unused.json"))


def test_publisher_rejects_tampered_report_before_mutating_evidence(tmp_path):
    result_path = tmp_path / "result.json"
    result_path.write_text(
        json.dumps({
            "trial_id": "T-2026-09-27-052",
            "status": "COMPLETED",
            "report_fingerprint": "tampered",
        }),
        encoding="utf-8",
    )
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text('{"trials": []}\n', encoding="utf-8")
    result_doc_path = tmp_path / "result.md"
    result_doc_path.write_text("placeholder", encoding="utf-8")
    with pytest.raises(RuntimeError, match="fingerprint"):
        publish(
            result_path,
            ledger_path,
            result_doc_path,
            tmp_path / "checkpoint.json",
            tmp_path / "state.json",
            tmp_path / "decision.json",
        )
    assert json.loads(ledger_path.read_text(encoding="utf-8")) == {"trials": []}
    assert not (tmp_path / "checkpoint.json").exists()


def test_publisher_records_only_the_four_fixed_cells_without_promotion(tmp_path, monkeypatch):
    trial_governance = {
        "selection_used": False,
        "parameter_search": False,
        "asset_search": False,
        "threshold_search": False,
        "horizon_search": False,
        "variant_search": False,
        "holdout_used_for_selection": False,
        "automatic_promotion": False,
    }
    safety = {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    cell = {
        "gates": {key: False for key in EXPECTED_GATES},
        "all_gates_passed": False,
    }
    universes = {
        expected["trial_id"]: {
            "universe": expected["universe"],
            "symbols": expected["symbols"],
            "snapshot_fingerprint": "a" * 64,
            "pit": {"status": "PIT_PASSED"},
            "trend_sma_50_200": copy.deepcopy(cell),
            "cs_momentum_12_1_top2": copy.deepcopy(cell),
        }
        for expected in EXPECTED_UNIVERSES
    }
    result = {
        "trial_id": "T-2026-09-27-052",
        "status": "COMPLETED",
        "code_version": "test-commit",
        "governance": trial_governance,
        "safety": safety,
        "universes": universes,
    }
    result["report_fingerprint"] = _fp(result)
    result_path = tmp_path / "result.json"
    result_path.write_text(json.dumps(result), encoding="utf-8")
    result_doc_path = tmp_path / "result.md"
    result_doc_path.write_text(result["report_fingerprint"], encoding="utf-8")
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text('{"trials": []}\n', encoding="utf-8")
    state_path = tmp_path / "state.json"
    state_path.write_text("{}\n", encoding="utf-8")
    decision_path = tmp_path / "decision.json"
    decision_path.write_text("{}\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_SHA", "test-commit")
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")

    publish(
        result_path,
        ledger_path,
        result_doc_path,
        tmp_path / "checkpoint.json",
        state_path,
        decision_path,
    )

    entry = json.loads(ledger_path.read_text(encoding="utf-8"))["trials"][0]
    assert entry["outcome"]["all_cells_passed"] is False
    assert len(entry["outcome"]["cells"]) == 4
    assert entry["safety"] == safety
    assert all(cell["all_gates_passed"] is False for cell in entry["outcome"]["cells"].values())
