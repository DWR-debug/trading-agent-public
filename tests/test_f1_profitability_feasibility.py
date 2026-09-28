from __future__ import annotations

from automation.f1_profitability_feasibility import _select_concept, _valid_fact, TAG_MAP

def test_fixed_tag_map_is_ex_ante_and_ordered() -> None:
    assert TAG_MAP["revenue"] == ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet")
    assert TAG_MAP["cogs"] == ("CostOfRevenue", "CostOfGoodsAndServicesSold")
    assert TAG_MAP["assets"] == ("Assets",)

def test_fact_selection_requires_exact_accession_and_report_date() -> None:
    filing = {"accession": "0000000000-25-000001", "report_date": "2025-12-31"}
    rows = [
        {"accn":"0000000000-25-000001","form":"10-K","start":"2025-01-01","end":"2025-12-31","fp":"FY","val":100,"unit":"USD"},
        {"accn":"0000000000-25-999999","form":"10-K","start":"2025-01-01","end":"2025-12-31","fp":"FY","val":900,"unit":"USD"},
    ]
    assert len(_valid_fact(rows, filing, instant=False)) == 1

def test_ambiguous_fixed_tag_does_not_silently_choose_a_value() -> None:
    filing = {"accession":"0000000000-25-000001", "report_date":"2025-12-31"}
    facts = {
        "facts": {"us-gaap": {
            "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": [
                {"accn":"0000000000-25-000001","form":"10-K","start":"2025-01-01","end":"2025-12-31","fp":"FY","val":100,"unit":"USD"},
                {"accn":"0000000000-25-000001","form":"10-K","start":"2025-01-01","end":"2025-12-31","fp":"FY","val":101,"unit":"USD"},
            ]}}}}
    }
    selected = _select_concept(facts, "revenue", filing, instant=False)
    assert selected["error"] == "AMBIGUOUS_REVENUE_RevenueFromContractWithCustomerExcludingAssessedTax"
    assert "row" not in selected

def test_future_filing_is_not_visible_to_prior_filing() -> None:
    filing = {"accession":"0000000000-25-000001", "report_date":"2025-12-31"}
    rows = [
        {"accn":"0000000000-25-000001","form":"10-K","start":"2025-01-01","end":"2025-12-31","fp":"FY","val":100,"unit":"USD"},
        {"accn":"0000000000-26-000001","form":"10-K","start":"2026-01-01","end":"2026-12-31","fp":"FY","val":999,"unit":"USD"},
    ]
    assert _valid_fact(rows, filing, instant=False)[0]["val"] == 100