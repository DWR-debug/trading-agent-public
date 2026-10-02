from pathlib import Path
import pytest

from automation import s10_systemone_bridge as bridge


def test_bridge_binds_loopback():
    assert bridge.HOST == "127.0.0.1"
    assert bridge.PORT == 8765
    assert bridge.LLAMA_BASE.startswith("http://127.0.0.1:")
    assert bridge.S10_SEED == 271828


def test_extract_json_object_accepts_contract():
    raw = '{"choice":"SUPPORTED","probabilities":{"SUPPORTED":0.8,"REFUTED":0.1,"INSUFFICIENT":0.1}}'
    assert bridge.extract_json_object(raw)["choice"] == "SUPPORTED"


@pytest.mark.parametrize(
    "raw",
    [
        '{"choice":"UNKNOWN","probabilities":{"SUPPORTED":0.5,"REFUTED":0.2,"INSUFFICIENT":0.3}}',
        '{"choice":"SUPPORTED","probabilities":{"SUPPORTED":2,"REFUTED":-0.1,"INSUFFICIENT":-0.9}}',
        '{"choice":"SUPPORTED","probabilities":{"SUPPORTED":0.9,"REFUTED":0.9,"INSUFFICIENT":0.1}}',
        "not json",
    ],
)
def test_extract_json_object_rejects_invalid_contract(raw):
    with pytest.raises(ValueError):
        bridge.extract_json_object(raw)


def test_build_prompt_canonicalizes_verdict_option_order():
    payload = {
        "state": {"claim": "C", "evidence": "E", "domain": "D"},
        "questions": {
            "verdict": {
                "criteria": {
                    "INSUFFICIENT": "I",
                    "SUPPORTED": "S",
                    "REFUTED": "R",
                }
            }
        },
    }
    prompt = bridge.build_prompt(payload)
    assert '"SUPPORTED": "S", "REFUTED": "R", "INSUFFICIENT": "I"' in prompt


def test_bridge_request_pins_reproducible_seed():
    source = Path("automation/s10_systemone_bridge.py").read_text(encoding="utf-8")
    assert 'S10_SEED = int(os.environ.get("S10_SEED", "271828"))' in source
    assert '"seed": S10_SEED' in source
    assert '"top_k": 1' in source
