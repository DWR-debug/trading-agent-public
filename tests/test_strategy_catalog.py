from research.strategy_catalog import current_strategy_registry


def test_catalog_keeps_rejected_and_blocked_evidence_visible():
    registry = current_strategy_registry()
    assert registry.get("TRIAL_014_LONG_SHORT_LEVERAGE").status == "REJECTED"
    assert registry.get("CORE_50_50_VOL_BUDGET").status == "BLOCKED"
    assert registry.graveyard()
