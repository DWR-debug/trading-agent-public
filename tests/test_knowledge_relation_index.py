from automation.knowledge_relation_index import build_index


def _contract():
    return {
        "status": "ACTIVE_METADATA_ONLY",
        "reusable_components": [{"id": "C1", "status": "READY"}],
        "candidate_component_links": [
            {"candidate": "Q218", "component": "C1", "role": "source"},
            {"candidate": "Q220", "component": "C1", "role": "source"},
        ],
        "candidate_relations": [
            {"from": "Q218", "to": "Q220", "edge": "shares_clock_and_filing_substrate"}
        ],
        "discovery_motifs": [],
        "orchestration_rules": {"shared_component_rule": "reuse"},
    }


def _specs():
    return {"candidates": [{"id": "Q218"}, {"id": "Q220"}]}


def test_shared_component_is_grouped_and_safe():
    out = build_index(_contract(), _specs())
    assert out["shared_component_groups"][0]["candidates"] == ["Q218", "Q220"]
    assert out["candidate_relations"][0]["from"] == "Q218"
    assert out["safety"]["performance"] is False
    assert out["safety"]["ranking"] is False


def test_result_is_deterministic():
    a = build_index(_contract(), _specs())
    b = build_index(_contract(), _specs())
    assert a["content_fingerprint"] == b["content_fingerprint"]


def test_contract_candidates_not_present_are_reported():
    c = _contract()
    c["candidate_component_links"].append(
        {"candidate": "Q999", "component": "C1", "role": "historical"}
    )
    out = build_index(c, _specs())
    assert out["unresolved_contract_candidates"] == ["Q999"]
