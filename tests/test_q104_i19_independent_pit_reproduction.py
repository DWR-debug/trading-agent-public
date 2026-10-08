from pathlib import Path

def test_independent_reproducer_has_no_primary_compiler_import():
    source = Path("automation/q104_i19_independent_pit_reproduction.py").read_text(encoding="utf-8")
    assert "q104_i19_xbrl_pit_compiler" not in source
    assert "compile_issuer_state" not in source


def test_independent_reproducer_fails_closed_without_inputs(tmp_path, monkeypatch):
    import automation.q104_i19_independent_pit_reproduction as r
    monkeypatch.setattr(r, "RECEIPT", tmp_path / "missing-receipt.json")
    monkeypatch.setattr(r, "BUNDLE", tmp_path / "missing-bundle.json")
    try:
        r.inputs()
    except RuntimeError as exc:
        assert "INPUT_MISSING" in str(exc)
    else:
        raise AssertionError("missing upstream inputs must fail closed")
