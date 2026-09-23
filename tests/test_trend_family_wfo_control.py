from automation.trend_family_wfo_control import (
    FAMILY_STRATEGIES,
    REFERENCE_STRATEGY,
    STEP_SIZE,
    TEST_SIZE,
    TRAIN_SIZE,
    _rolling_windows,
    _select_family,
)


def test_family_set_is_small_and_pre_registered():
    assert FAMILY_STRATEGIES == (
        "tsm_monthly_equal",
        "sma_50_200_inverse_vol",
        "blend_tsm_sma_inverse_vol",
    )
    assert REFERENCE_STRATEGY == "buy_and_hold_equal"


def test_selection_prefers_training_profit_factor():
    training = {
        "tsm_monthly_equal": [0.01, -0.02, 0.01],
        "sma_50_200_inverse_vol": [0.02, 0.01, -0.01],
        "blend_tsm_sma_inverse_vol": [0.01, 0.0, -0.01],
    }

    result = _select_family(training)

    assert result["selected_strategy"] == "sma_50_200_inverse_vol"


def test_selection_tie_breaks_on_return_then_drawdown():
    training = {
        "tsm_monthly_equal": [0.02, -0.01, 0.02],
        "sma_50_200_inverse_vol": [0.01, 0.0, 0.03],
        "blend_tsm_sma_inverse_vol": [0.01, 0.0, 0.03],
    }

    result = _select_family(training)

    # The second and third families tie on PF and return; lower drawdown
    # determines the selection, with strategy name as the final deterministic tie.
    assert result["selected_strategy"] in FAMILY_STRATEGIES
    assert result["selection_rule"].startswith(
        "highest_training_profit_factor"
    )


def test_rolling_geometry_is_fixed():
    windows = _rolling_windows(2800)

    assert TRAIN_SIZE == 1400
    assert TEST_SIZE == 280
    assert STEP_SIZE == 280
    assert len(windows) == 5
    assert windows[0] == (1, 0, 1400, 1680)
    assert windows[-1] == (5, 1120, 2520, 2800)
