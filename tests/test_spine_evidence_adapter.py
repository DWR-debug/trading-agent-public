from automation.spine_evidence_adapter import receipt_to_temporal_node, identity_record_to_node, state_transition_to_node

def receipt():
    return {
      "schema_version":1,"source_id":"S1","source_url":"https://example.org/source",
      "retrieved_at":"2026-01-02T00:00:00Z","available_at":"2026-01-01T23:00:00Z",
      "release_id":"R1","raw_fingerprint":"a"*64,"normalized_fingerprint":"b"*64,
      "pit_status":"DISCOVERY_ONLY","receipt_fingerprint":"c"*64
    }

def test_available_at_is_not_public_by_default():
    n=receipt_to_temporal_node(receipt())
    assert n["public_observed_at"] is None
    assert n["provenance_status"]=="PUBLIC_CLOCK_UNPROVEN"

def test_explicit_public_flag_promotes_available_at():
    n=receipt_to_temporal_node(receipt(),available_at_is_public_observation=True)
    assert n["public_observed_at"]=="2026-01-01T23:00:00Z"

def test_identity_and_state_nodes_are_structured():
    i=identity_record_to_node({
      "source_id":"S1","source_entity_id":"E1","canonical_entity_id":"C1",
      "mapping_version":"v1","valid_from":"2026-01-01T00:00:00Z","valid_to":None,
      "mapping_status":"FROZEN","evidence_fingerprint":"d"*64})
    s=state_transition_to_node({
      "state_id":"ST1","entity_id":"C1","state_before":"A","state_after":"B",
      "transition_observed_at":"2026-01-02T00:00:00Z","source_component":"S1",
      "revision_lineage":[],"historical_prefix_fingerprint":"e"*64})
    assert i["node_type"]=="I"
    assert s["node_type"]=="S"
