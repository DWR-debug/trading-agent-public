from __future__ import annotations

import json

import pytest

from automation.information_alpha_mechanism_discrimination import (
    GROUP_ORDER,
    MIN_CELL_OBSERVATIONS,
    _all_subset_r2,
    _r2_from_features,
    _shapley_from_subset_r2,
)


def _rows(n: int = 40) -> list[dict]:
    rows = []
    for i in range(n):
        x = float(i + 1)
        rows.append({
            "has_information_event": True,
            "features": {
                "event_count": x,
                "attention_score": 2.0 * x,
                "source_breadth": 3.0 * x,
                "article_count": 4.0 * x,
                "negative_goldstein": (-1.0) ** i * x,
                "mean_tone": (x % 7.0) - 3.0,
            },
            "market": {
                "SPY": {
                    "next_market_day_return": 0.01 * x,
                    "five_market_day_forward_return": 0.02 * x,
                },
                "TLT": {
                    "next_market_day_return": 0.005 * x,
                    "five_market_day_forward_return": 0.01 * x,
                },
                "GLD": {
                    "next_market_day_return": -0.004 * x,
                    "five_market_day_forward_return": -0.008 * x,
                },
            },
        })
    return rows


def test_q015_group_order_is_fixed():
    assert GROUP_ORDER == ("intensity_breadth", "severity", "tone")


def test_q015_minimum_cell_contract_is_fixed():
    assert MIN_CELL_OBSERVATIONS == 40


def test_q015_subset_models_are_complete():
    rows = _rows()
    values = _all_subset_r2(rows, "SPY", "next_market_day_return")
    assert set(values) == {
        "empty",
        "intensity_breadth",
        "severity",
        "tone",
        "intensity_breadth+severity",
        "intensity_breadth+tone",
        "severity+tone",
        "intensity_breadth+severity+tone",
    }


def test_q015_shapley_conserves_full_r2():
    subset = {
        "empty": 0.0,
        "intensity_breadth": 0.20,
        "severity": 0.10,
        "tone": 0.15,
        "intensity_breadth+severity": 0.25,
        "intensity_breadth+tone": 0.30,
        "severity+tone": 0.20,
        "intensity_breadth+severity+tone": 0.40,
    }
    shapley = _shapley_from_subset_r2(subset)
    assert sum(shapley.values()) == pytest.approx(0.40)


def test_q015_r2_is_bounded():
    rows = _rows()
    value = _r2_from_features(rows, "SPY", "next_market_day_return", GROUP_ORDER)
    assert 0.0 <= value <= 1.0
