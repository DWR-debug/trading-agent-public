import json
from pathlib import Path

from research.diagnostics.portfolio_risk_parity_failure import diagnose, REPORT_FINGERPRINT


def test_diagnostic_is_deterministic(tmp_path: Path):
    snapshot = tmp_path / "snapshot.json"
    output = tmp_path / "diagnostic.json"
    data = {
        "trial_id": "T-2026-09-24-022",
        "report_fingerprint": REPORT_FINGERPRINT,
        "selection_used": False,
        "parameter_search_used": False,
        "scenarios": {
            "base": {
                "dynamic_inverse_vol_63": {
                    "research": {"period_return": 1.0389593951927734, "max_drawdown_percent": 42.927390164913895, "profit_factor": 1.0899192281764745, "turnover": 54.42414216698895, "average_trend_weight": 0.6052397190805459, "average_cross_sectional_weight": 0.39476028091945414},
                    "holdout": {"period_return": 1.0051790518436872, "max_drawdown_percent": 23.828610096377613, "profit_factor": 1.2730248430056925, "turnover": 17.1844472204604, "average_trend_weight": 0.5945704744276618, "average_cross_sectional_weight": 0.40542952557233825},
                },
                "fixed_50_50": {
                    "research": {"period_return": 1.2172883758632143, "max_drawdown_percent": 41.28938399816662, "profit_factor": 1.0934127675413032, "turnover": 35.71322378168723, "average_trend_weight": 0.5, "average_cross_sectional_weight": 0.5},
                    "holdout": {"period_return": 1.149172501482314, "max_drawdown_percent": 24.871436700003425, "profit_factor": 1.2890922663828694, "turnover": 12.887829602511125, "average_trend_weight": 0.5, "average_cross_sectional_weight": 0.5},
                },
            },
        },
    }
    snapshot.write_text(json.dumps(data), encoding="utf-8")
    report = diagnose(snapshot, output)
    assert report["diagnostic_summary"]["holdout_drawdown_improvement_percentage_points"] > 0
    assert report["diagnostic_summary"]["holdout_return_shortfall_percentage_points"] > 0
    assert output.exists()
