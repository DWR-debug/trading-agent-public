from automation.risk_layer_drawdown_speed_2026_09_23 import (
    CASES,
    RAPID_THRESHOLD_DAYS,
    RESEARCH_COUNT,
    _consensus,
    _window_bounds,
)


def test_fixed_window_contract():
    assert RESEARCH_COUNT == 2798
    assert RAPID_THRESHOLD_DAYS == 31
    assert len(_window_bounds()) == 5
    assert _window_bounds()[0] == (0, 559)
    assert _window_bounds()[-1] == (2236, 2798)
    assert [case["artifact_id"] for case in CASES] == [
        10751817990,
        10740188093,
        10745697729,
        10753545703,
    ]


def test_consensus_rule_uses_per_dataset_rapid_slow_contrast():
    def case(rapid, slow, rapid_onset, slow_onset):
        return {
            "rapid": {
                "delayed_or_never_rate": rapid,
                "onset_day_already_de_risked_rate": rapid_onset,
            },
            "slow": {
                "delayed_or_never_rate": slow,
                "onset_day_already_de_risked_rate": slow_onset,
            },
        }

    cases = {
        "validation_1": case(1.0, 0.0, 0.0, 1.0),
        "validation_2": case(1.0, 0.0, 0.0, 1.0),
        "validation_3": case(0.5, 0.5, 0.5, 0.5),
        "validation_4": case(1.0, 1.0, 0.0, 1.0),
    }
    result = _consensus(cases)
    assert result["replication_counts"]["rapid_more_delayed_than_slow"] == 2
    assert result["replication_counts"]["rapid_less_onset_active_than_slow"] == 3
    assert result["decision_rule"].startswith("replicated_rapid_drawdown_onset_undercoverage:")


def test_consensus_can_remain_negative():
    def case():
        return {
            "rapid": {
                "delayed_or_never_rate": 0.4,
                "onset_day_already_de_risked_rate": 0.6,
            },
            "slow": {
                "delayed_or_never_rate": 0.6,
                "onset_day_already_de_risked_rate": 0.4,
            },
        }

    result = _consensus({f"validation_{i}": case() for i in range(1, 5)})
    assert result["replication_counts"]["rapid_more_delayed_than_slow"] == 0
    assert result["replication_counts"]["rapid_less_onset_active_than_slow"] == 0
    assert result["decision_rule"].startswith("no_replicated_rapid_drawdown_onset_contrast:")
