from automation.q111_security_identity_contract import (
    canonical_security_key,
    deduplicate_rows,
    map_to_issuer,
    synthetic_contract,
)

def test_q111_synthetic_contract_passes():
    assert all(synthetic_contract().values())

def test_q111_cusip_is_primary_identity():
    assert canonical_security_key({
        "name_of_issuer": "Apple Inc.",
        "title_of_class": "Common Stock",
        "cusip": "037833100",
    }) == "CUSIP:037833100"

def test_q111_conflicting_duplicate_is_rejected():
    rows = [
        {"name_of_issuer":"A","cusip":"123456789","value":1},
        {"name_of_issuer":"A","cusip":"123456789","value":2},
    ]
    try:
        deduplicate_rows(rows)
    except ValueError as exc:
        assert str(exc).startswith("SECURITY_IDENTITY_CONFLICT")
    else:
        raise AssertionError("conflicting duplicate must be rejected")
