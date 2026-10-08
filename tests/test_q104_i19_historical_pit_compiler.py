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
