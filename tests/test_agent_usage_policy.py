from automation.agent_usage_policy import authorize_agent_usage


def test_paid_agent_usage_is_denied():
    result = authorize_agent_usage(
        free_quota_available=True,
        estimated_paid_cost_usd=0.01,
    )
    assert result.allowed is False


def test_without_free_quota_is_denied():
    result = authorize_agent_usage(free_quota_available=False)
    assert result.allowed is False


def test_free_quota_can_be_used_without_paid_spend():
    result = authorize_agent_usage(free_quota_available=True)
    assert result.allowed is True
