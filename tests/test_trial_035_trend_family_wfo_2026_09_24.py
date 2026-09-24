from automation.trial_035_trend_family_wfo_2026_09_24 import (
    FAMILIES, REFERENCE, STEP_SIZE, TEST_SIZE, TRAIN_SIZE,
    _select, _stats, _windows,
)

def test_wfo_window_geometry_is_fixed():
    assert (TRAIN_SIZE,TEST_SIZE,STEP_SIZE)==(1398,280,280)
    assert _windows()==(
        (1,0,1398,1678),
        (2,280,1678,1958),
        (3,560,1958,2238),
        (4,840,2238,2518),
        (5,1120,2518,2798),
    )

def test_family_selection_uses_training_profit_factor_then_return():
    training={
        FAMILIES[0]:[0.01,-0.01,0.02,-0.01],
        FAMILIES[1]:[0.02,-0.005,0.02,-0.005],
        FAMILIES[2]:[0.03,-0.02,0.01,-0.02],
    }
    result=_select(training)
    assert result["selected_family"] in FAMILIES
    assert result["rule"].startswith("highest training profit factor")

def test_stats_profit_factor_is_positive_for_positive_stream():
    result=_stats([0.01,0.02,-0.005,0.01],0,4)
    assert result["period_return"]>0
    assert result["profit_factor"]>1.0

def test_reference_is_not_a_selectable_family():
    assert REFERENCE not in FAMILIES
