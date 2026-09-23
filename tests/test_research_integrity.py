import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from automation.backtest_runner import run_all
from automation.research_run import code_version
from backtesting.models import Candle
from config.parameter_space import ParameterSpace
from data.market_store import MarketDataStore


def make_candles(count=50):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(
        Candle(
            timestamp=start + timedelta(minutes=i),
            open=100.0 + i,
            high=100.0 + i,
            low=100.0 + i,
            close=100.0 + i,
            volume=1000.0,
        )
        for i in range(count)
    )


def make_space():
    return ParameterSpace(
        momentum_lookbacks=[3],
        mean_reversion_windows=[5],
        mean_reversion_thresholds=[0.02],
        risk_per_trade_values=[0.01],
        leverage_values=[1.0],
    )


def test_resume_requires_matching_run_fingerprint(tmp_path):
    store = MarketDataStore(tmp_path / "data")
    store.save("TEST", "1h", make_candles())
    checkpoint = tmp_path / "checkpoint.json"

    run_all(
        [("TEST", "1h")],
        store=store,
        parameter_space=make_space(),
        optimizer_top_n=1,
        checkpoint_path=checkpoint,
        output_dir=tmp_path / "reports",
        run_fingerprint="fp-a",
    )

    with pytest.raises(RuntimeError, match="Run-Identität"):
        run_all(
            [("TEST", "1h")],
            store=store,
            parameter_space=make_space(),
            optimizer_top_n=1,
            checkpoint_path=checkpoint,
            output_dir=tmp_path / "reports",
            resume=True,
            run_fingerprint="fp-b",
        )

    report, _ = run_all(
        [("TEST", "1h")],
        store=store,
        parameter_space=make_space(),
        optimizer_top_n=1,
        checkpoint_path=checkpoint,
        output_dir=tmp_path / "reports",
        resume=True,
        run_fingerprint="fp-a",
    )

    assert report["run_fingerprint"] == "fp-a"


def test_resume_rejects_legacy_checkpoint_without_fingerprint(tmp_path):
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(
        json.dumps(
            {
                "run_type": "multi_dataset_research",
                "started_at": "2026-01-01T00:00:00+00:00",
                "status": "COMPLETED",
                "completed": [],
                "results": [],
                "report_path": str(tmp_path / "report.json"),
            }
        ),
        encoding="utf-8",
    )

    store = MarketDataStore(tmp_path / "data")
    store.save("TEST", "1h", make_candles())

    with pytest.raises(RuntimeError, match="Run-Identität"):
        run_all(
            [("TEST", "1h")],
            store=store,
            parameter_space=make_space(),
            optimizer_top_n=1,
            checkpoint_path=checkpoint,
            output_dir=tmp_path / "reports",
            resume=True,
            run_fingerprint="new-run",
        )


def test_local_code_version_uses_git_head_when_ci_sha_missing(monkeypatch):
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    monkeypatch.delenv("GIT_COMMIT_SHA", raising=False)

    def fake_check_output(*_args, **_kwargs):
        return "abc123" + chr(10)

    monkeypatch.setattr(
        "automation.research_run.subprocess.check_output",
        fake_check_output,
    )

    assert code_version() == "abc123"


def test_research_workflow_persists_gate_status(monkeypatch, tmp_path):
    import automation.research_workflow as workflow

    checkpoint = tmp_path / "checkpoint.json"
    report_path = tmp_path / "report.json"
    checkpoint.write_text(
        json.dumps(
            {
                "run_type": "multi_dataset_research",
                "started_at": "2026-01-01T00:00:00+00:00",
                "status": "COMPLETED",
                "completed": ["TEST::1h"],
                "results": [{"symbol": "TEST", "interval": "1h"}],
                "report_path": str(report_path),
            }
        ),
        encoding="utf-8",
    )

    class Store:
        def load(self, _symbol, _interval):
            return tuple(make_candles())

    monkeypatch.setattr(
        workflow,
        "build_run_identity",
        lambda *_args, **_kwargs: {"run_fingerprint": "fp-workflow"},
    )

    def fake_run_all(*_args, **_kwargs):
        return {
            "generated_at": "2026-01-01T00:00:00+00:00",
            "datasets": [{"symbol": "TEST", "interval": "1h"}],
        }, report_path

    monkeypatch.setattr(workflow, "run_all", fake_run_all)
    monkeypatch.setattr(
        workflow,
        "evaluate_research_gates",
        lambda *_args, **_kwargs: {
            "passed": False,
            "status": "BLOCKED",
            "gate_count": 7,
            "passed_count": 6,
            "failed_gates": ["holdout"],
            "gates": [],
        },
    )

    report, _ = workflow.run_research(
        [("TEST", "1h")],
        store=Store(),
        parameter_space=make_space(),
        output_dir=tmp_path / "reports",
        checkpoint_path=checkpoint,
        manifest_path=tmp_path / "manifest.json",
        data_manifest_path=None,
    )

    state = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert report["status"] == "BLOCKED"
    assert state["status"] == "COMPLETED"
    assert state["research_status"] == "BLOCKED"
    assert state["run_fingerprint"] == "fp-workflow"
    assert state["failed_gates"] == ["TEST 1h: holdout"]
    assert state["research_gates"]["TEST::1h"]["status"] == "BLOCKED"



def test_research_workflow_persists_statistical_diagnostics(
    monkeypatch,
    tmp_path,
):
    import automation.research_workflow as workflow

    report_path = tmp_path / "report.json"

    class Store:
        def load(self, _symbol, _interval):
            return tuple(make_candles())

    monkeypatch.setattr(
        workflow,
        "build_run_identity",
        lambda *_args, **_kwargs: {"run_fingerprint": "fp-statistics"},
    )

    monkeypatch.setattr(
        workflow,
        "run_all",
        lambda *_args, **_kwargs: (
            {
                "generated_at": "2026-01-01T00:00:00+00:00",
                "datasets": [
                    {
                        "symbol": "TEST",
                        "interval": "1h",
                        "optimization_candidate_count": 1280,
                        "optimization_reported_top_n": 5,
                        "walk_forward": {
                            "selection_profile": "score_max"
                        },
                        "holdout": {
                            "permutation_positive_tail_probability": 0.031,
                        },
                        "protocol": {
                            "permutation_trials": 1000,
                            "permutation_seed": 20260921,
                        },
                    }
                ],
            },
            report_path,
        ),
    )
    monkeypatch.setattr(
        workflow,
        "evaluate_research_gates",
        lambda *_args, **_kwargs: {
            "passed": True,
            "status": "PASSED",
            "gate_count": 7,
            "passed_count": 7,
            "failed_gates": [],
            "gates": [],
        },
    )

    report, _ = workflow.run_research(
        [("TEST", "1h")],
        store=Store(),
        parameter_space=ParameterSpace(),
        output_dir=tmp_path / "reports",
        checkpoint_path=tmp_path / "checkpoint.json",
        manifest_path=tmp_path / "manifest.json",
        data_manifest_path=None,
    )

    diagnostics = report["datasets"][0]["statistical_diagnostics"]
    assert diagnostics["multiple_testing"]["parameter_space_candidate_count"] == 1280
    assert diagnostics["multiple_testing"]["reported_top_n"] == 5
    assert diagnostics["multiple_testing"]["holdout_was_used_for_candidate_selection"] is False
    assert diagnostics["permutation"]["positive_tail_probability"] == 0.031
    assert diagnostics["permutation"]["diagnostic_only"] is True
    assert diagnostics["permutation"]["unadjusted"] is True



def test_research_workflow_persists_evidence_summary(
    monkeypatch,
    tmp_path,
):
    import automation.research_workflow as workflow

    report_path = tmp_path / "report.json"

    class Store:
        def load(self, _symbol, _interval):
            return tuple(make_candles())

    monkeypatch.setattr(
        workflow,
        "build_run_identity",
        lambda *_args, **_kwargs: {"run_fingerprint": "fp-evidence"},
    )
    monkeypatch.setattr(
        workflow,
        "run_all",
        lambda *_args, **_kwargs: (
            {
                "generated_at": "2026-01-01T00:00:00+00:00",
                "datasets": [
                    {"symbol": "A", "interval": "1h"},
                    {"symbol": "B", "interval": "1h"},
                ],
            },
            report_path,
        ),
    )
    gate_reports = iter(
        [
            {
                "passed": True,
                "status": "PASSED",
                "gate_count": 7,
                "passed_count": 7,
                "failed_gates": [],
                "gates": [],
            },
            {
                "passed": False,
                "status": "BLOCKED",
                "gate_count": 7,
                "passed_count": 6,
                "failed_gates": ["holdout"],
                "gates": [],
            },
        ]
    )
    monkeypatch.setattr(
        workflow,
        "evaluate_research_gates",
        lambda *_args, **_kwargs: next(gate_reports),
    )

    report, _ = workflow.run_research(
        [("A", "1h"), ("B", "1h")],
        store=Store(),
        parameter_space=ParameterSpace(),
        output_dir=tmp_path / "reports",
        checkpoint_path=tmp_path / "checkpoint.json",
        manifest_path=tmp_path / "manifest.json",
        data_manifest_path=None,
    )

    summary = report["evaluation_summary"]
    assert summary["dataset_count"] == 2
    assert summary["passed_dataset_count"] == 1
    assert summary["blocked_dataset_count"] == 1
    assert summary["evidence_scope"] == "multi_dataset"
    assert summary["single_backtest_decision"] is False
