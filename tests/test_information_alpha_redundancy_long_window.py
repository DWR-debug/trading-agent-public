from datetime import date

import pytest

from automation.information_alpha_redundancy_long_window import (
    DEFAULT_END,
    DEFAULT_START,
    MIN_EVENT_WINDOWS,
    MIN_TOTAL_OBSERVATIONS,
)


def test_q014_window_is_exactly_365_calendar_days():
    assert (DEFAULT_END - DEFAULT_START).days == 364


def test_q014_fixed_data_contract_thresholds():
    assert MIN_TOTAL_OBSERVATIONS == 80
    assert MIN_EVENT_WINDOWS == 40


def test_q014_rejects_non_365_day_window_without_network():
    from automation.information_alpha_redundancy_long_window import run_q014

    with pytest.raises(ValueError):
        run_q014(
            date(2025, 9, 26),
            date(2026, 9, 24),
            output_dir="/tmp/q014-test",
        )
