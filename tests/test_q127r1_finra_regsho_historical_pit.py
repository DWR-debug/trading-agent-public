from automation.q127r1_finra_regsho_historical_pit import (
    EXPECTED_HEADER,
    date_url,
    parse_file,
)

def test_fixed_file_url_pattern():
    assert date_url("2025-09-24").endswith("CNMSshvol20250924.txt")
    assert date_url("2024-02-05").endswith("CNMSshvol20240205.txt")

def test_parser_schema_and_numeric_fields():
    body = (
        b"Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n"
        b"20250924|SPGI|100.5|2|200.25|B,Q,N\n"
        b"20250924|NDAQ|0|0|4|Q\n"
    )
    header, rows, lines = parse_file(body)
    assert header == EXPECTED_HEADER
    assert rows["SPGI"]["ShortVolume"] == "100.5"
    assert rows["NDAQ"]["TotalVolume"] == "4"
    assert len(lines) == 3

def test_parser_accepts_bom():
    body = b"\xef\xbb\xbfDate|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n20250924|SPGI|1|0|2|Q\n"
    header, rows, _ = parse_file(body)
    assert header == EXPECTED_HEADER
    assert "SPGI" in rows

def test_parser_rejects_header_drift():
    import pytest
    with pytest.raises(RuntimeError, match="FINRA_SCHEMA_MISMATCH"):
        parse_file(b"Date|Symbol|ShortVolume|TotalVolume|Market\n")

def test_parser_rejects_invalid_numeric():
    import pytest
    with pytest.raises(RuntimeError, match="FINRA_NUMERIC_PARSE_ERROR"):
        parse_file(
            b"Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n"
            b"20250924|SPGI|oops|0|2|Q\n"
        )

def test_parser_rejects_negative_numeric():
    import pytest
    with pytest.raises(RuntimeError, match="FINRA_NUMERIC_RANGE_ERROR"):
        parse_file(
            b"Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n"
            b"20250924|SPGI|-1|0|2|Q\n"
        )

def test_parser_rejects_duplicate_symbol():
    import pytest
    with pytest.raises(RuntimeError, match="FINRA_DUPLICATE_SYMBOL"):
        parse_file(
            b"Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n"
            b"20250924|SPGI|1|0|2|Q\n"
            b"20250924|SPGI|2|0|4|Q\n"
        )
