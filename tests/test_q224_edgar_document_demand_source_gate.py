from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "automation" / "q224_edgar_document_demand_source_gate.py"


def _module():
    spec = importlib.util.spec_from_file_location("q224_gate", SPEC)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_q224_fixed_modern_controls_and_schema_contract():
    m = _module()
    assert list(m.CONTROLS) == ["2020-05-19", "2022-12-30", "2025-06-30"]
    assert all(url.endswith(".zip") for url in m.CONTROLS.values())
    assert m.EXPECTED == {"uri_path"}
    assert m.EXPECTED_TIME == {"_time", "time"}
    assert m.URI_RE.search("/Archives/edgar/data/1067701/000106770120000046/") is not None


def test_q224_gate_is_non_authorizing():
    text = SPEC.read_text(encoding="utf-8")
    for token in (
        '"performance_authorized": False',
        '"holdout_selection_allowed": False',
        '"ranking_allowed": False',
        '"tuning_allowed": False',
        '"promotion_allowed": False',
        '"live_execution_allowed": False',
        '"same_session_use": False',
        '"legacy_modern_splice_attempted": False',
    ):
        assert token in text
