from automation.q148_r1_wpsr_source_clock import (
    FIXED_SERIES_LABEL,
    normalize_label,
    parse_table4_row,
    CONTROLS,
)


def test_fixed_series_label_is_frozen():
    assert FIXED_SERIES_LABEL == "Commercial (Excluding SPR)"


def test_normalize_series_label_removes_footnote_suffix():
    assert normalize_label("Commercial (Excluding SPR)³") == normalize_label(FIXED_SERIES_LABEL)
    assert normalize_label(" Commercial (Excluding SPR)3 ") == normalize_label(FIXED_SERIES_LABEL)


def test_parse_table4_row_finds_one_fixed_series_under_crude_oil():
    body = (
        "Product / Region,Current Week,Last Week,Difference\n"
        "Crude Oil,500.0,510.0,-10.0\n"
        "Commercial (Excluding SPR)3,300.0,305.0,-5.0\n"
        "East Coast (PADD 1),10.0,11.0,-1.0\n"
    ).encode("utf-8")
    result = parse_table4_row(body)
    assert result["series_label_cell"] == "Commercial (Excluding SPR)3"
    assert result["parent_context_row"][0] == "Crude Oil"
    assert result["column_count"] == 4


def test_parse_table4_row_fails_closed_on_duplicate_series():
    import pytest

    body = (
        "Product / Region,Current Week\n"
        "Crude Oil,500\n"
        "Commercial (Excluding SPR),300\n"
        "Other,100\n"
        "Commercial (Excluding SPR),301\n"
    ).encode("utf-8")
    with pytest.raises(RuntimeError, match="SERIES_ROW_MATCH_COUNT:2"):
        parse_table4_row(body)


def test_controls_are_fixed_and_outcome_independent():
    assert [c["control_id"] for c in CONTROLS] == [
        "ordinary_2025_09_24",
        "holiday_2025_09_04",
        "documented_correction_2026_08_26",
    ]
    for control in CONTROLS:
        assert "return" not in str(control).lower()
        assert "price" not in str(control).lower()
