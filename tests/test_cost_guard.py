from automation.cost_guard import (
    ResearchBudget,
    DEFAULT_BUDGET,
    deterministic_research_allowed,
)


def test_default_budget_is_one_usd():
    assert DEFAULT_BUDGET.total_usd == 1.0
    assert DEFAULT_BUDGET.max_round_usd == 0.25
    assert DEFAULT_BUDGET.max_rounds == 4


def test_round_is_approved_within_budget():
    budget = ResearchBudget()
    assert budget.approve_round(0.20)
    assert budget.approve_round(0.20)
    assert budget.rounds_used == 2
    assert budget.committed_usd == 0.40


def test_round_is_rejected_above_per_round_limit():
    assert not ResearchBudget().approve_round(0.26)


def test_round_is_rejected_above_total_budget():
    budget = ResearchBudget()
    for _ in range(4):
        assert budget.approve_round(0.25)

    assert budget.committed_usd == 1.0
    assert not budget.approve_round(0.01)


def test_round_count_is_hard_limited():
    budget = ResearchBudget()

    for _ in range(4):
        assert budget.approve_round(0.20)

    assert budget.rounds_used == 4
    assert not budget.approve_round(0.20)


def test_non_finite_costs_are_rejected():
    budget = ResearchBudget()

    for value in (float("nan"), float("inf"), float("-inf")):
        try:
            budget.approve_round(value)
        except ValueError:
            pass
        else:
            raise AssertionError("Nicht-endliche Kosten wurden akzeptiert.")


def test_negative_costs_are_rejected():
    budget = ResearchBudget()
    try:
        budget.approve_round(-0.01)
    except ValueError:
        return

    raise AssertionError("Negative Kosten wurden akzeptiert.")


def test_rejected_round_does_not_consume_budget():
    budget = ResearchBudget()

    assert not budget.approve_round(0.26)
    assert budget.rounds_used == 0
    assert budget.committed_usd == 0.0

    assert budget.approve_round(0.20)
    assert budget.rounds_used == 1
    assert budget.committed_usd == 0.20


def test_deterministic_research_is_local():
    assert deterministic_research_allowed()
