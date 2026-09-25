from automation.information_alpha_redundancy import (
    DEFAULT_ASSETS,
    FIXED_FEATURES,
    MECHANISM_GROUPS,
    _feature_matrix,
)

def observation(value: float) -> dict:
    return {
        "features": {feature: value for feature in FIXED_FEATURES},
        "market": {
            symbol: {
                "next_market_day_return": value,
                "five_market_day_forward_return": value / 2.0,
            }
            for symbol in DEFAULT_ASSETS
        },
    }

def test_q013_feature_matrix_is_complete_and_deterministic():
    observations = [observation(float(i)) for i in range(1, 21)]
    matrix = _feature_matrix(observations, FIXED_FEATURES)
    assert set(matrix) == set(FIXED_FEATURES)
    for left in FIXED_FEATURES:
        assert set(matrix[left]) == set(FIXED_FEATURES)
        assert matrix[left][left] == 1.0

def test_q013_mechanism_groups_are_fixed():
    assert MECHANISM_GROUPS["intensity_breadth"] == ("event_count", "attention_score", "source_breadth", "article_count")
    assert MECHANISM_GROUPS["severity"] == ("negative_goldstein",)
    assert MECHANISM_GROUPS["tone"] == ("mean_tone",)
