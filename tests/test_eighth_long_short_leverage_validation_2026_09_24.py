import pytest

from automation.eighth_long_short_leverage_validation_2026_09_24 import (
    _normalized_weights,
    _portfolio_rows,
)


class Bar:
    def __init__(self, timestamp, open_, close):
        self.timestamp = timestamp
        self.open = open_
        self.close = close


def test_normalized_weights_never_exceed_one_gross_exposure():
    bars = tuple(Bar(i, 100.0 + i, 100.0 + i) for i in range(3500))
    assets = {f"A{i}": bars for i in range(4)}

    weights = _normalized_weights(assets, long_short=True)

    for row in weights:
        assert sum(abs(value) for value in row.values()) <= 1.0 + 1e-12


def test_portfolio_rows_produce_expected_pit_return_count():
    bars = tuple(Bar(i, 100.0, 100.0) for i in range(3500))
    assets = {"A": bars, "B": bars}
    weights = tuple({"A": 0.5, "B": 0.5} for _ in range(3500))

    rows = _portfolio_rows(assets, weights)

    assert len(rows) == 3498
    assert all(row["base_return"] == pytest.approx(0.0) for row in rows)
    assert all(row["gross_exposure"] == pytest.approx(1.0) for row in rows)
