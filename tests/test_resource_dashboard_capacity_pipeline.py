from automation.generate_resource_dashboard import capacity_pipeline


def test_capacity_pipeline_publishes_one_policy_row_per_configured_resource():
    configured = [{"name": x} for x in [
        "Windows self-hosted A", "Windows self-hosted B", "Windows self-hosted C",
        "GitHub-hosted Ubuntu x64", "GitHub-hosted ARM64", "Free AI pool",
        "Bounded Agent Queue", "Codespaces fallback", "Paper Forward / Shadow",
        "Dashboard / GitHub Pages"]]
    work = [{"resource":"Windows self-hosted B","task":"Top-4 Candidate Research Capacity","job":"Windows Top-4 Q218"}]
    ai = [{"provider":"groq_free","status":"RATE_LIMITED"}]
    rows = capacity_pipeline(configured, work, ai, {"top_candidate_capacity_overlay": {}})
    assert len(rows) == len(configured)
    assert [x["resource"] for x in rows] == [x["name"] for x in configured]
    b = next(x for x in rows if x["resource"]=="Windows self-hosted B")
    assert b["current_active"] is True
    assert "Top-4 Candidate Research Capacity" in b["current"]
    assert b["pipeline_authority"] == "non-authorizing; planned routing only"
    ai_row = next(x for x in rows if x["resource"]=="Free AI pool")
    assert ai_row["mode"] == "PROVIDER_GATED"
    assert all(x["planned_next"] for x in rows)
