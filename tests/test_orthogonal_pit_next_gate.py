from automation.orthogonal_pit_next_gate import NEXT_GATES, compile_state


def test_source_ready_candidates_require_immutable_historical_binding_before_pit():
    assert NEXT_GATES["Q195"] == "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT"
    assert NEXT_GATES["Q196"] == "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT"
    assert NEXT_GATES["Q197"] == "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT"
    assert NEXT_GATES["Q199"] == "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT"
    assert NEXT_GATES["Q201"] == "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT"


def test_compiler_marks_current_source_probes_as_provisional():
    result = compile_state()
    current = {item["candidate_id"]: item for item in result["candidates"]}
    for candidate_id in ["Q195", "Q196", "Q197", "Q199", "Q201"]:
        assert current[candidate_id]["source_readiness_durability"] == "PROVISIONAL_LIVE_PROBE_ONLY"
        assert current[candidate_id]["execution_authorized"] is False
        assert current[candidate_id]["performance_allowed"] is False
        assert current[candidate_id]["next_gate"] == "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT"


def test_global_boundary_remains_closed():
    result = compile_state()
    assert result["status"] == "NEXT_LOGICAL_GATES_COMPILED_NO_PERFORMANCE"
    assert result["global_boundary"]["performance_authorized"] is False
    assert result["global_boundary"]["holdout_selection"] is False
    assert result["global_boundary"]["ranking"] is False
    assert result["global_boundary"]["tuning"] is False
    assert result["global_boundary"]["promotion"] is False
    assert result["global_boundary"]["live_execution"] is False

def test_new_literature_candidates_are_source_first_and_non_authorizing():
    assert NEXT_GATES["Q202"] == "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT"
    assert NEXT_GATES["Q203"] == "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT"
    assert NEXT_GATES["Q204"] == "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT"
    result = compile_state()
    current = {item["candidate_id"]: item for item in result["candidates"]}
    for candidate_id in ["Q202", "Q203", "Q204"]:
        assert current[candidate_id]["source_or_pit_receipt"] is not None
        assert current[candidate_id]["execution_authorized"] is False
        assert current[candidate_id]["performance_allowed"] is False
        assert current[candidate_id]["next_gate"] == "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT"

