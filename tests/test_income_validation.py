import pytest

from portfolio.income_validation import (
    IncomeValidationError,
    IncomeValidationPolicy,
    evaluate_income_viability,
    evaluate_sequence_risk,
)


def test_payout_requires_new_high_water_mark_and_never_consumes_floor() -> None:
    policy = IncomeValidationPolicy(
        payout_fraction=0.50,
        payout_interval_periods=2,
        sequence_window_periods=None,
    )

    result = evaluate_income_viability((0.10, 0.0, 0.0, 0.10), policy)

    assert result.total_payout_eur == 27.5
    assert result.payout_count == 1
    assert result.scheduled_payout_period_count == 2
    assert result.zero_payout_periods == 1
    assert result.final_equity_eur == 577.5
    assert result.minimum_post_payout_equity_eur >= 500.0
    assert result.floor_violation_count == 0
    assert result.minimum_floor_headroom_eur >= 0.0
    assert result.maximum_drawdown_percent_after_withdrawals == pytest.approx(100.0 * (1.0 - 577.5 / 605.0))


def test_losses_create_floor_violations_but_never_trigger_withdrawals() -> None:
    policy = IncomeValidationPolicy(
        payout_fraction=1.0,
        payout_interval_periods=1,
        sequence_window_periods=None,
    )

    result = evaluate_income_viability((-0.05, -0.10, 0.0), policy)

    assert result.total_payout_eur == 0.0
    assert result.payout_count == 0
    assert result.zero_payout_periods == 3
    assert result.floor_violation_count == 3
    assert result.minimum_equity_eur < 500.0
    assert result.minimum_post_payout_equity_eur < 500.0


def test_fee_and_slippage_are_explicit_period_costs() -> None:
    policy = IncomeValidationPolicy(
        payout_interval_periods=2,
        fee_fraction_per_period=0.01,
        slippage_fraction_per_period=0.01,
        sequence_window_periods=None,
    )

    result = evaluate_income_viability((0.10, 0.0), policy)

    assert round(result.total_cost_eur, 8) == 21.78
    assert result.total_payout_eur == 0.0
    assert round(result.final_equity_eur, 8) == 528.22


def test_sequence_risk_uses_equal_length_historical_start_points() -> None:
    policy = IncomeValidationPolicy(
        payout_interval_periods=3,
        sequence_window_periods=6,
    )

    scenarios = evaluate_sequence_risk(
        (0.10, 0.0, 0.0, -0.05, 0.0, 0.05, 0.02, 0.0),
        policy,
    )

    assert len(scenarios) == 3
    assert {item.start_period_index for item in scenarios} == {1, 2, 3}
    assert all(item.window_periods == 6 for item in scenarios)


def test_sequence_metrics_are_exposed_on_main_result() -> None:
    policy = IncomeValidationPolicy(
        payout_interval_periods=2,
        sequence_window_periods=4,
    )

    result = evaluate_income_viability((0.05, 0.0, 0.05, 0.0, -0.01), policy)

    assert result.sequence_start_count == 2
    assert result.sequence_worst_total_payout_eur is not None
    assert result.sequence_lower_quantile_total_payout_eur is not None
    assert result.sequence_worst_drawdown_percent is not None


def test_invalid_policy_and_returns_fail_closed() -> None:
    try:
        IncomeValidationPolicy(fee_fraction_per_period=1.0)
    except IncomeValidationError:
        pass
    else:
        raise AssertionError("Invalid cost policy was accepted.")

    try:
        evaluate_income_viability((float("nan"),))
    except IncomeValidationError:
        pass
    else:
        raise AssertionError("Non-finite return was accepted.")
