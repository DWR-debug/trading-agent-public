import json

import pytest

from automation.paper_30_day_experiment import (
    HORIZON_DAYS,
    Paper30DayExperimentError,
    run,
)


def _write_evidence(path, *, status="VALIDATED_PASS", holdout_used=False):
    payload = {
        "trial_id": "TEST-001",
        "strategy_id": "fixed-test-strategy",
        "status": status,
        "artifact_id": 1,
        "artifact_digest_sha256": "a" * 64,
        "report_fingerprint_sha256": "b" * 64,
        "manifest_fingerprint_sha256": "c" * 64,
        "code_commit_sha": "1234567",
        "research_count": 1000,
        "holdout_count": 300,
        "holdout_used_for_selection": holdout_used,
        "gates": [{"name": "gate", "passed": True}],
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_returns(path, values=None):
    values = values or [0.01] * HORIZON_DAYS
    path.write_text(
        json.dumps(
            {
                "strategy_id": "fixed-test-strategy",
                "daily_returns": values,
                "net_of_costs": True,
                "source": "synthetic-test",
            }
        ),
        encoding="utf-8",
    )


def test_run_30_day_compounds_net_returns(tmp_path):
    evidence = tmp_path / "evidence.json"
    returns = tmp_path / "returns.json"
    output = tmp_path / "report.json"
    checkpoint = tmp_path / "checkpoint.json"
    _write_evidence(evidence)
    _write_returns(returns)

    report = run(
        evidence_path=evidence,
        returns_path=returns,
        output_path=output,
        checkpoint_path=checkpoint,
        initial_capital_eur=10.0,
    )

    assert report["status"] == "COMPLETED"
    assert report["processed_days"] == 30
    assert report["final_equity_eur"] > 13.0
    assert report["maximum_drawdown_percent"] == 0.0
    assert output.exists()
    assert report["report_fingerprint"]


def test_checkpoint_resume_rejects_changed_input(tmp_path):
    evidence = tmp_path / "evidence.json"
    returns = tmp_path / "returns.json"
    output = tmp_path / "report.json"
    checkpoint = tmp_path / "checkpoint.json"
    _write_evidence(evidence)
    _write_returns(returns)

    partial = run(
        evidence_path=evidence,
        returns_path=returns,
        output_path=output,
        checkpoint_path=checkpoint,
        initial_capital_eur=10.0,
        max_days=10,
    )
    assert partial["status"] == "CHECKPOINTED"
    assert partial["processed_days"] == 10

    changed = [0.02] + [0.01] * 29
    _write_returns(returns, changed)
    with pytest.raises(Paper30DayExperimentError):
        run(
            evidence_path=evidence,
            returns_path=returns,
            output_path=output,
            checkpoint_path=checkpoint,
            initial_capital_eur=10.0,
            resume=True,
        )


def test_resume_completes_same_checkpoint(tmp_path):
    evidence = tmp_path / "evidence.json"
    returns = tmp_path / "returns.json"
    output = tmp_path / "report.json"
    checkpoint = tmp_path / "checkpoint.json"
    _write_evidence(evidence)
    _write_returns(returns, [0.0] * HORIZON_DAYS)

    run(
        evidence_path=evidence,
        returns_path=returns,
        output_path=output,
        checkpoint_path=checkpoint,
        initial_capital_eur=10.0,
        max_days=10,
    )
    report = run(
        evidence_path=evidence,
        returns_path=returns,
        output_path=output,
        checkpoint_path=checkpoint,
        initial_capital_eur=10.0,
        resume=True,
    )
    assert report["status"] == "COMPLETED"
    assert report["processed_days"] == 30
    assert report["final_equity_eur"] == 10.0


@pytest.mark.parametrize("status", ["VALIDATED_FAIL", "BLOCKED"])
def test_noneligible_evidence_is_fail_closed(tmp_path, status):
    evidence = tmp_path / "evidence.json"
    returns = tmp_path / "returns.json"
    output = tmp_path / "report.json"
    checkpoint = tmp_path / "checkpoint.json"
    _write_evidence(evidence, status=status)
    _write_returns(returns)

    with pytest.raises(Paper30DayExperimentError):
        run(
            evidence_path=evidence,
            returns_path=returns,
            output_path=output,
            checkpoint_path=checkpoint,
        )


def test_holdout_selection_is_fail_closed(tmp_path):
    evidence = tmp_path / "evidence.json"
    returns = tmp_path / "returns.json"
    output = tmp_path / "report.json"
    checkpoint = tmp_path / "checkpoint.json"
    _write_evidence(evidence, holdout_used=True)
    _write_returns(returns)

    with pytest.raises(Paper30DayExperimentError):
        run(
            evidence_path=evidence,
            returns_path=returns,
            output_path=output,
            checkpoint_path=checkpoint,
        )


def test_returns_must_be_exactly_30_days(tmp_path):
    evidence = tmp_path / "evidence.json"
    returns = tmp_path / "returns.json"
    output = tmp_path / "report.json"
    checkpoint = tmp_path / "checkpoint.json"
    _write_evidence(evidence)
    _write_returns(returns, [0.0] * 29)

    with pytest.raises(Paper30DayExperimentError):
        run(
            evidence_path=evidence,
            returns_path=returns,
            output_path=output,
            checkpoint_path=checkpoint,
        )
