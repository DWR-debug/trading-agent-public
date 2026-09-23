from automation.rolling_geometry_control import (
    LARGE_STEP,
    LARGE_TEST,
    LARGE_TRAIN,
    RESEARCH_END,
    SMALL_STEP,
    SMALL_TEST,
    SMALL_TRAIN,
)


def test_geometry_window_counts():
    assert (
        (RESEARCH_END - SMALL_TRAIN - SMALL_TEST) // SMALL_STEP + 1
        == 15
    )
    assert (
        (RESEARCH_END - LARGE_TRAIN - LARGE_TEST) // LARGE_STEP + 1
        == 5
    )


def test_large_test_span_matches_small_window_pairs():
    for large_index in range(1, 6):
        small_i = 2 * large_index + 4
        small_j = small_i + 1

        large_start = LARGE_TRAIN + (large_index - 1) * LARGE_STEP
        large_end = large_start + LARGE_TEST

        small_start = SMALL_TRAIN + (small_i - 1) * SMALL_STEP
        small_end = SMALL_TRAIN + (small_j - 1) * SMALL_STEP + SMALL_TEST

        assert small_start == large_start
        assert small_end == large_end
