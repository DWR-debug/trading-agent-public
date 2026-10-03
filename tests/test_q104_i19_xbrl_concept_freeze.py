import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/"research/preregistrations/q104_i19_xbrl_concept_freeze_2026_10_03.json"

def test_i19_exact_concepts_and_formula_are_frozen():
    s=json.loads(SPEC.read_text(encoding="utf-8"))
    assert s["xbrl_concepts"] == {
        "net_income_loss":"us-gaap:NetIncomeLoss",
        "operating_cash_flow":"us-gaap:NetCashProvidedByUsedInOperatingActivities",
        "assets":"us-gaap:Assets",
    }
    assert s["formula"]["accrual_amount"]=="NetIncomeLoss - NetCashProvidedByUsedInOperatingActivities"
    assert "((Assets_current + Assets_prior) / 2)" in s["formula"]["accrual_intensity"]

def test_i19_is_fail_closed_and_non_performance():
    s=json.loads(SPEC.read_text(encoding="utf-8"))
    assert s["fact_contract"]["selection_rule"].endswith("No concept substitution is allowed.")
    assert s["missingness"].startswith("If any required concept")
    assert s["governance"]["performance_authorized"] is False
    assert s["safety"]["paper_only"] is True
