from automation.q127r1_finra_regsho_historical_pit import (
    EXPECTED_HEADER,
    date_url,
    parse_file,
)

def test_fixed_file_url_pattern():
    assert date_url("2025-09-24").endswith("CNMSshvol20250924.txt")
    assert date_url("2024-02-05").endswith("CNMSshvol20240205.txt")

def test_parser_schema_trailer_and_market_partitions():
    body = (
        b"Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n"
        b"20250924|SPGI|100|2|200|Q\n"
        b"20250924|SPGI|20|0|50|N\n"
        b"20250924|NDAQ|0|0|4|Q\n"
        b"3\n"
    )
    header, rows, lines, trailer_count = parse_file(body)
    assert header == EXPECTED_HEADER
    assert rows["SPGI"][0]["ShortVolume"] == "100"
    assert rows["SPGI"][1]["Market"] == "N"
    assert rows["NDAQ"][0]["TotalVolume"] == "4"
    assert trailer_count == 3
    assert len(lines) == 5

def test_parser_accepts_bom():
    body = (
        b"\xef\xbb\xbfDate|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n"
        b"20250924|SPGI|1|0|2|Q\n"
        b"1\n"
    )
    header, rows, _, trailer_count = parse_file(body)
    assert header == EXPECTED_HEADER
    assert "SPGI" in rows
    assert trailer_count == 1

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
            b"1\n"
        )

def test_parser_rejects_negative_numeric():
    import pytest
    with pytest.raises(RuntimeError, match="FINRA_NUMERIC_RANGE_ERROR"):
        parse_file(
            b"Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n"
            b"20250924|SPGI|-1|0|2|Q\n"
            b"1\n"
        )

def test_parser_rejects_duplicate_symbol_market():
    import pytest
    with pytest.raises(RuntimeError, match="FINRA_DUPLICATE_SYMBOL_MARKET"):
        parse_file(
            b"Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n"
            b"20250924|SPGI|1|0|2|Q\n"
            b"20250924|SPGI|2|0|4|Q\n"
            b"2\n"
        )

def test_parser_rejects_invalid_trailer():
    import pytest
    with pytest.raises(RuntimeError, match="FINRA_TRAILER_INVALID"):
        parse_file(
            b"Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n"
            b"20250924|SPGI|1|0|2|Q\n"
            b"not-a-trailer\n"
        )

def test_parser_rejects_trailer_count_mismatch():
    import pytest
    with pytest.raises(RuntimeError, match="FINRA_TRAILER_COUNT_MISMATCH"):
        parse_file(
            b"Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n"
            b"20250924|SPGI|1|0|2|Q\n"
            b"9\n"
        )
