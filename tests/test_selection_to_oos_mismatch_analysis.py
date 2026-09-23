import json

from automation.selection_to_oos_mismatch_analysis import (
    _json_safe,
    _mismatch_matrix,
    _pearson,
    _rank_bands,
    _spearman,
)


def _row(
    rank,
    training_profit,
    oos_profit,
    candidate_count=100,
):
    oos_positive = oos_profit > 0
    return {
        "symbol": "SPY",
        "geometry": "small",
        "window_index": rank,
        "selection_candidate_count": candidate_count,
        "raw_score_rank": rank,
        "selection_score": float(candidate_count - rank),
        "runner_up_score_gap": 0.1,
        "selected_vs_best_raw_score_gap": -float(rank - 1),
        "training_profit_eur": training_profit,
        "training_return_percent": training_profit,
        "training_profit_factor": 1.5,
        "training_trade_count": 20,
        "training_positive": training_profit > 0,
        "training_pf_pass": True,
        "oos_profit_eur": oos_profit,
        "oos_return_percent": oos_profit,
        "oos_profit_factor": 1.2 if oos_positive else 0.8,
        "oos_positive": oos_positive,
        "oos_pf_pass": oos_positive,
        "symbol": "SPY",
        "interval": "1d",
    }



def test_json_safe_serializes_infinite_metrics():
    payload = {
        "profit_factor": float("inf"),
        "nested": [float("-inf"), float("nan")],
    }

    safe = _json_safe(payload)

    assert safe["profit_factor"] == "inf"
    assert safe["nested"] == ["-inf", None]
    json.dumps(safe, allow_nan=False)

def test_mismatch_matrix_counts_training_vs_oos():
    rows = [
        _row(1, 10.0, 5.0),
        _row(2, 10.0, -2.0),
        _row(3, -1.0, 4.0),
        _row(4, -1.0, -3.0),
    ]

    result = _mismatch_matrix(rows)

    assert result["training_positive__oos_positive"]["count"] == 1
    assert result["training_positive__oos_nonpositive"]["count"] == 1
    assert result["training_nonpositive__oos_positive"]["count"] == 1
    assert result["training_nonpositive__oos_nonpositive"]["count"] == 1


def test_rank_bands_partition_without_overlap():
    rows = [
        _row(1, 10.0, 1.0),
        _row(2, 8.0, 2.0),
        _row(6, 6.0, -1.0),
        _row(11, 4.0, 1.0),
        _row(99, 1.0, -1.0),
    ]

    bands = _rank_bands(rows)

    assert sum(item["evaluation_count"] for item in bands) == len(rows)
    assert bands[0]["rank_min"] == 1
    assert bands[-1]["rank_max"] == 100
    assert all(
        bands[index]["rank_max"] + 1 == bands[index + 1]["rank_min"]
        for index in range(len(bands) - 1)
    )


def test_correlations_are_deterministic():
    x = [1.0, 2.0, 3.0, 4.0]
    y = [10.0, 20.0, 30.0, 40.0]

    assert _pearson(x, y) == 1.0
    assert _spearman(x, y) == 1.0
