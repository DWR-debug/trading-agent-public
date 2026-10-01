from automation.q112_sec_security_identity import extract_fields, synthetic_contract


def test_q112_synthetic_contract_passes():
    assert all(synthetic_contract().values())


def test_q112_13f_resolves_by_cusip():
    xml = b"""<informationTable xmlns="urn:13f"><infoTable><nameOfIssuer>Apple Inc.</nameOfIssuer><titleOfClass>Common Stock</titleOfClass><cusip>037833100</cusip></infoTable></informationTable>"""
    out = extract_fields("13F", xml)
    assert out["canonical_security_key"] == "CUSIP:037833100"


def test_q112_nport_resolves_by_cusip():
    xml = b"""<nport><invstOrSec><name>Microsoft Corp.</name><title>Common Stock</title><identifiers><identifier><CUSIP>594918104</CUSIP></identifier></identifiers></invstOrSec></nport>"""
    out = extract_fields("N-PORT", xml)
    assert out["canonical_security_key"] == "CUSIP:594918104"


def test_q112_form4_resolves_by_ticker_issuer_and_keeps_cik():
    xml = b"""<ownershipDocument><issuer><issuerCik>0000320193</issuerCik><issuerName>Apple Inc.</issuerName><issuerTradingSymbol>AAPL</issuerTradingSymbol></issuer><nonDerivativeTable><nonDerivativeTransaction><securityTitle><value>Common Stock</value></securityTitle></nonDerivativeTransaction></nonDerivativeTable></ownershipDocument>"""
    out = extract_fields("FORM-4", xml)
    assert out["canonical_security_key"] == "TICKER:AAPL|ISSUER:APPLE INC"
    assert out["issuer_cik"] == "0000320193"
