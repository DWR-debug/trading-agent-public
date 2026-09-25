from automation.project_state_freshness_check import freshness_errors


def test_consistent_state_and_checkpoint_are_green():
    state = {
        "repository": "DWR-debug/trading-agent-public",
        "master_commit": "abc",
        "engineering_notes": {
            "q016_execution_status": "COMPLETED",
            "q016_scientific_status": "DATA_INSUFFICIENT",
        },
    }
    checkpoint = {
        "repository": "DWR-debug/trading-agent-public",
        "master_commit_at_checkpoint_creation": "abc",
        "generated_at_utc": "2026-09-25T18:25:10Z",
        "q016": {
            "workflow_conclusion": "success",
            "aggregate_status": "DATA_INSUFFICIENT",
            "workflow_run_id": 36172112861,
            "result_fingerprint": "fingerprint",
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }

    assert freshness_errors(state, checkpoint) == []


def test_stale_running_q016_is_rejected():
    state = {
        "repository": "DWR-debug/trading-agent-public",
        "master_commit": "abc",
        "engineering_notes": {
            "q016_execution_status": "RUNNING",
            "q016_scientific_status": "NO_RESULT_YET",
        },
    }
    checkpoint = {
        "repository": "DWR-debug/trading-agent-public",
        "master_commit_at_checkpoint_creation": "abc",
        "generated_at_utc": "2026-09-25T18:25:10Z",
        "q016": {
            "workflow_conclusion": "success",
            "aggregate_status": "DATA_INSUFFICIENT",
            "workflow_run_id": 36172112861,
            "result_fingerprint": "fingerprint",
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }

    errors = freshness_errors(state, checkpoint)

    assert any("execution status is stale" in error for error in errors)
    assert any("scientific status is stale" in error for error in errors)
    assert any("36172112861" in error for error in errors)
    assert any("fingerprint" in error for error in errors)


def test_provenance_drift_is_rejected():
    state = {
        "repository": "DWR-debug/trading-agent-public",
        "master_commit": "old",
        "engineering_notes": {},
    }
    checkpoint = {
        "repository": "DWR-debug/trading-agent-public",
        "master_commit_at_checkpoint_creation": "new",
        "generated_at_utc": "2026-09-25T18:25:10Z",
        "q016": {},
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }

    errors = freshness_errors(state, checkpoint)

    assert any("master provenance drift" in error for error in errors)
