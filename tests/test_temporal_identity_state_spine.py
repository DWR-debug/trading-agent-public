from automation.temporal_identity_state_spine import compile_spine

def base():
    return {
        "status":"ACTIVE_METADATA_ONLY",
        "temporal_contract":{"required_fields":[]},
        "identity_contract":{"required_fields":[]},
        "state_contract":{"required_fields":[]},
        "composition_rules":{"composite_candidate_requires_new_contract":True},
        "high_value_patterns":["x"],
    }

def relation():
    return {
        "reusable_components":[{"id":"CLOCK","status":"READY"}],
        "candidate_component_links":[
            {"candidate":"Q218","component":"CLOCK","role":"clock"},
            {"candidate":"Q220","component":"CLOCK","role":"clock"},
        ],
        "candidate_relations":[{"from":"Q218","to":"Q220","edge":"shares_clock"}],
    }

def specs():
    return {"candidates":[{"id":"Q218"},{"id":"Q220"}]}

def registry():
    return {"source_lattice":[{"id":"S1"}]}

def test_shared_dependency_priority():
    out=compile_spine(base(),relation(),specs(),registry())
    assert out["shared_component_groups"][0]["component"]=="CLOCK"
    assert out["shared_component_groups"][0]["routing_priority"]==2
    assert out["graph_integrity"]["component_ref_integrity_ok"]

def test_endpoint_integrity_is_fail_closed():
    r=relation()
    r["candidate_relations"][0]["to"]="Q999"
    out=compile_spine(base(),r,specs(),registry())
    assert not out["graph_integrity"]["relation_endpoint_integrity_ok"]

def test_spine_is_non_authorizing():
    out=compile_spine(base(),relation(),specs(),registry())
    assert out["safety"]["performance"] is False
    assert out["safety"]["live_execution"] is False
