from automation.research_orchestrator import _state_snapshot


def test_snapshot_is_safe_and_credit_free_by_default():
    snapshot = _state_snapshot(
        mode="observe",
        universe="benchmark",
        status="OBSERVATION_ONLY",
    )
    assert snapshot["safety"] == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
    }
    assert snapshot["agent_usage"]["paid_api_budget_usd"] == 0.0
    assert snapshot["agent_usage"]["auto_paid_api_calls"] is False


def test_t039_research_is_coverage_gated(monkeypatch, tmp_path):
    from automation import research_orchestrator

    calls = []

    def fake_preflight(preregistration, *, output_root):
        calls.append(("preflight", str(preregistration), str(output_root)))
        return {
            "status": "coverage_passed",
            "universe": "validation_2026_09_24_network_momentum_t039",
            "coverage_fingerprint": "coverage-fp",
            "output": str(tmp_path / "coverage.json"),
        }

    def fake_trial(coverage_path, output_path, preregistration):
        calls.append(("trial", str(coverage_path), str(output_path)))
        return {
            "status": "BLOCKED",
            "report_fingerprint": "report-fp",
        }

    monkeypatch.setattr(research_orchestrator, "run_preflight", fake_preflight)
    monkeypatch.setattr(research_orchestrator, "run_t039_trial", fake_trial)

    snapshot = research_orchestrator.run(
        mode="research",
        universe="validation_2026_09_24_network_momentum_t039",
        output_root=tmp_path,
    )

    assert calls[0][0] == "preflight"
    assert calls[1][0] == "trial"
    assert snapshot["status"] == "BLOCKED"
    assert snapshot["safety"]["orders_enabled"] is False


def test_discover_coverage_mode_is_safe(monkeypatch, tmp_path):
    from automation import research_orchestrator

    monkeypatch.setattr(
        research_orchestrator,
        "run_discovery",
        lambda output: {
            "coverage_valid_candidates": ["BIV"],
            "fingerprint": "discovery-fp",
        },
    )
    snapshot = research_orchestrator.run(
        mode="discover_coverage",
        output_root=tmp_path,
    )
    assert snapshot["status"] == "CANDIDATES_AVAILABLE"
    assert snapshot["safety"]["orders_enabled"] is False


def test_q013_mode_is_exposed():
    import automation.research_orchestrator as research_orchestrator

    assert any(
        isinstance(value, tuple) and "discover_information_alpha_redundancy" in value
        for value in research_orchestrator.main.__code__.co_consts
    )