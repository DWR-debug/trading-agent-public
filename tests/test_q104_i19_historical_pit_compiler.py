from automation.q104_i19_historical_pit_compiler import local_name, numeric_clean


def test_numeric_clean_applies_parentheses_sign_and_scale():
    assert numeric_clean("(1,200)", "", "0") == "-1200"
    assert numeric_clean("12", "-", "3") == "-12000"


def test_local_name_normalizes_qname_forms():
    assert local_name("us-gaap:Assets") == "assets"
    assert local_name("{http://www.xbrl.org/2003/instance}context") == "context"


def test_historical_compiler_imports_as_preperformance_only():
    from automation.q104_i19_historical_pit_compiler import CUTOFF, START
    assert START.isoformat() == "2013-07-01"
    assert CUTOFF.isoformat() == "2025-09-24"


def test_missing_census_fails_closed(tmp_path, monkeypatch):
    import automation.q104_i19_historical_pit_compiler as compiler
    monkeypatch.setattr(compiler, "CENSUS", tmp_path / "missing.json")
    try:
        compiler.require_census()
    except RuntimeError as exc:
        assert "CENSUS_RECEIPT_MISSING" in str(exc)
    else:
        raise AssertionError("historical compiler must require the positive census receipt")



def test_rejects_legacy_source_only_census_without_acceptance_time_join():
    import pytest
    from automation.q104_i19_historical_pit_compiler import validate_census_receipt

    legacy = {
        "candidate_id": "Q104:I19",
        "status": "13F_HISTORICAL_CUSIP_IDENTITY_CENSUS_COMPLETED_SOURCE_ONLY",
        "completed_shards": ["2013-2017", "2018-2021", "2022-2025-09"],
        "archive_count": 50,
        "identity_conflicts": [],
    }
    with pytest.raises(RuntimeError, match="CENSUS_NOT_CLOCK_COMPLETE"):
        validate_census_receipt(legacy)
