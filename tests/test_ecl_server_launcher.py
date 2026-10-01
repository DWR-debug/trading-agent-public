from pathlib import Path
from automation.ecl_server_launcher import start

def test_supported_models_are_explicit():
    source=Path("automation/ecl_server_launcher.py").read_text(encoding="utf-8")
    assert "laya-typed-decisions" in source
    assert "kev-0.8b" in source
    assert "jeff" in source

def test_invalid_model_rejected(tmp_path):
    try:
        start("invalid", tmp_path, tmp_path, 8000, tmp_path/"o", tmp_path/"e", tmp_path/"p")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid model was accepted")
