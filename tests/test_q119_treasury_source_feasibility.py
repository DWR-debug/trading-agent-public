from automation.q119_treasury_source_feasibility import validate


def test_q119_source_validator_accepts_fixed_fields_and_pit_order():
    rows = [
        {
            "record_date": "2025-01-01",
            "auction_date": "2025-01-01",
            "cusip": "A",
            "security_type": "Note",
            "security_term": "10-Year",
            "high_yield": "4.20",
            "median_yield": "4.10",
            "low_yield": "4.00",
        },
        {
            "record_date": "2025-02-01",
            "auction_date": "2025-02-01",
            "cusip": "B",
            "security_type": "Note",
            "security_term": "10-Year",
            "high_yield": "4.10",
            "median_yield": "4.05",
            "low_yield": "4.00",
        },
    ]
    out = validate(rows)
    assert out["raw_row_count"] == 2
    assert out["compiled_row_count"] == 2
    assert out["future_mutation_invariance"] is True
