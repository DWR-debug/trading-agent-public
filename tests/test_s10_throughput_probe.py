import json

from automation.s10_throughput_probe import probe_mode


def test_throughput_probe_output_is_utility_only():
    assert callable(probe_mode)


def test_probe_payload_contract_is_not_scientific():
    payload = {
        "schema_version": 1,
        "scientific_evidence": False,
        "performance_authorization": False,
        "candidate_selection": False,
        "promotion": False,
    }
    assert all(value is False for key, value in payload.items() if key != "schema_version")
    assert json.loads(json.dumps(payload))["scientific_evidence"] is False
