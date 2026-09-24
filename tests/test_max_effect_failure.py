import json
from pathlib import Path

from research.diagnostics.max_effect_failure import diagnose, REPORT_FINGERPRINT


def test_max_effect_failure_diagnosis_is_descriptive(tmp_path: Path):
    snapshot = {
        "trial_id": "T-2026-09-24-023",
        "report_fingerprint": REPORT_FINGERPRINT,
        "selection_used": False,
        "parameter_search_used": False,
        "selection_month_count": 167,
        "base_total_turnover": 154.0,
        "research": {
            "return_percent": 285.8384653467733,
            "drawdown_percent": 24.627086363044526,
            "rolling_profitable_window_ratio": 0.8,
            "max_edge_daily": 0.00014367672845823338,
        },
        "holdout": {
            "return_percent": 38.851229257201214,
            "drawdown_percent": 16.258926604304648,
            "oos_to_research_return_ratio": 0.13592022756653033,
            "max_edge_daily": -0.00004064077951666479,
        },
    }
    source = tmp_path / "snapshot.json"
    output = tmp_path / "diagnostic.json"
    source.write_text(json.dumps(snapshot), encoding="utf-8")

    result = diagnose(source, output)

    assert result["findings"]["research_drawdown_excess_over_gate_pp"] > 14.0
    assert result["findings"]["holdout_drawdown_excess_over_gate_pp"] > 6.0
    assert result["findings"]["oos_ratio_shortfall_vs_gate"] > 0.11
    assert result["findings"]["research_edge_bps_per_day"] > 1.4
    assert result["findings"]["holdout_edge_bps_per_day"] < -0.4
    assert result["findings"]["edge_change_holdout_minus_research_bps_per_day"] < -1.8
    assert result["safety"]["paper_only"] is True
    assert output.exists()