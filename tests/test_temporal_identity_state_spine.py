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


from automation.temporal_identity_state_spine import (
    validate_temporal_record,
    validate_identity_record,
    validate_state_transition,
)

def test_temporal_record_requires_public_boundary():
    record={
        "source_id":"S1","source_record_id":"R1",
        "event_time":"2026-01-01T12:00:00Z",
        "public_observed_at":"2026-01-01T13:00:00Z",
        "retrieved_at":"2026-01-01T13:01:00Z",
        "revision_time":"2026-01-02T00:00:00Z",
        "clock_semantics":"public",
    }
    out=validate_temporal_record(record)
    assert out["public_observed_at"].startswith("2026-01-01T13:00:00")

def test_temporal_record_rejects_public_after_retrieval():
    record={
        "source_id":"S1","source_record_id":"R1",
        "event_time":"2026-01-01T12:00:00Z",
        "public_observed_at":"2026-01-01T14:00:00Z",
        "retrieved_at":"2026-01-01T13:01:00Z",
        "revision_time":"2026-01-02T00:00:00Z",
        "clock_semantics":"public",
    }
    try:
        validate_temporal_record(record)
    except ValueError:
        return
    raise AssertionError("invalid temporal ordering accepted")

def test_identity_validity_interval_is_checked():
    record={
        "source_id":"S1","source_entity_id":"E1","canonical_entity_id":"C1",
        "mapping_version":"v1","valid_from":"2026-01-02T00:00:00Z",
        "valid_to":"2026-01-01T00:00:00Z","mapping_status":"FROZEN",
        "evidence_fingerprint":"a"*64,
    }
    try:
        validate_identity_record(record)
    except ValueError:
        return
    raise AssertionError("invalid identity interval accepted")

def test_state_transition_rejects_noop():
    record={
        "state_id":"S1","entity_id":"C1","state_before":"A","state_after":"A",
        "transition_observed_at":"2026-01-01T00:00:00Z","source_component":"SRC",
        "revision_lineage":[],"historical_prefix_fingerprint":"b"*64,
    }
    try:
        validate_state_transition(record)
    except ValueError:
        return
    raise AssertionError("no-op state transition accepted")

def test_historical_nodes_are_reported_but_do_not_fail_current_candidate_integrity():
    out=compile_spine(base(),relation(),specs(),registry())
    assert out["graph_integrity"]["current_candidate_reference_integrity_ok"] is True
