from automation.generate_resource_dashboard import capacity_pipeline


def test_capacity_pipeline_has_one_non_authorizing_plan_per_configured_resource():
    configured = [
        {"name": "Windows self-hosted A"},
        {"name": "Windows self-hosted B"},
        {"name": "Windows self-hosted C"},
        {"name": "GitHub-hosted Ubuntu x64"},
        {"name": "GitHub-hosted ARM64"},
        {"name": "Free AI pool"},
        {"name": "Bounded Agent Queue"},
        {"name": "Codespaces fallback"},
        {"name": "Paper Forward / Shadow"},
        {"name": "Dashboard / GitHub Pages"},
    ]
    work = [{
        "resource": "Windows self-hosted B",
        "task": "Top-4 Candidate Research Capacity",
        "job": "Windows Top-4 Q218",
    }]
    ai = [{"provider": "groq_free", "status": "RATE_LIMITED"}]
    os_state = {"top_candidate_capacity_overlay": {}}

    rows = capacity_pipeline(configured, work, ai, os_state)
    assert len(rows) == len(configured)
    assert [row["resource"] for row in rows] == [row["name"] for row in configured]
    b = next(row for row in rows if row["resource"] == "Windows self-hosted B")
    assert b["current_active"] is True
    assert "Top-4 Candidate Research Capacity" in b["current"]
    assert b["pipeline_authority"] == "non-authorizing; planned routing only"
    ai_row = next(row for row in rows if row["resource"] == "Free AI pool")
    assert ai_row["mode"] == "PROVIDER_GATED"
    assert all(row["planned_next"] for row in rows)
