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
    assert NEXT_GATES["Q224"] == "SEC_EDGAR_MODERN_LOG_ARCHIVE_AND_DETERMINISTIC_REQUEST_TO_FILING_MAPPING"
    assert NEXT_GATES["Q227"] == "SEC_FOIA_HISTORICAL_LOG_ARCHIVE_AND_DETERMINISTIC_REQUEST_TO_ISSUER_MAPPING"
    result = compile_state()
    current = {item["candidate_id"]: item for item in result["candidates"]}
    for candidate_id in ["Q202", "Q203", "Q204"]:
        assert current[candidate_id]["source_or_pit_receipt"] is not None
        assert current[candidate_id]["execution_authorized"] is False
        assert current[candidate_id]["performance_allowed"] is False
        assert current[candidate_id]["next_gate"] == "IMMUTABLE_HISTORICAL_SNAPSHOT_REQUIRED_BEFORE_PIT"



def test_new_top_candidates_are_registered_but_source_first():
    for candidate_id in ["Q218", "Q219", "Q220", "Q221"]:
        assert candidate_id in NEXT_GATES
    result = compile_state()
    current = {item["candidate_id"]: item for item in result["candidates"]}
    for candidate_id in ["Q218", "Q219", "Q220", "Q221"]:
        assert current[candidate_id]["source_feasibility_required"] is True
        assert current[candidate_id]["source_or_pit_receipt"] is None
        assert current[candidate_id]["execution_authorized"] is False
        assert current[candidate_id]["performance_allowed"] is False


def test_q222_is_registered_source_first_and_non_authorizing():
    assert NEXT_GATES["Q222"] == "HISTORICAL_SEC_IMPLEMENTATION_EVIDENCE_CLOCK_AND_ENTITY_MAPPING"
    result = compile_state()
    current = {item["candidate_id"]: item for item in result["candidates"]}
    assert current["Q222"]["source_or_pit_receipt"] is None
    assert current["Q222"]["source_feasibility_required"] is True
    assert current["Q222"]["execution_authorized"] is False
    assert current["Q222"]["performance_allowed"] is False


def test_q205_is_visible_to_next_gate_compiler_without_authority():
    result = compile_state()
    current = {item["candidate_id"]: item for item in result["candidates"]}
    assert "Q205" in current
    for candidate_id in ["Q224", "Q227"]:
        assert current[candidate_id]["source_feasibility_required"] is True
        assert current[candidate_id]["source_or_pit_receipt"] is None
        assert current[candidate_id]["execution_authorized"] is False
        assert current[candidate_id]["performance_allowed"] is False
    assert current["Q205"]["execution_authorized"] is False
    assert current["Q205"]["performance_allowed"] is False


def test_q229_q230_are_registered_source_first_and_non_authorizing():
    for candidate_id, expected_gate in [
        ("Q229", "HISTORICAL_CFPB_PUBLIC_RELEASE_AND_ISSUER_MAPPING"),
        ("Q230", "FREE_TRACE_HISTORICAL_PANEL_AND_ISSUER_MAPPING"),
    ]:
        assert NEXT_GATES[candidate_id] == expected_gate
    result = compile_state()
    current = {item["candidate_id"]: item for item in result["candidates"]}
    for candidate_id in ["Q229", "Q230"]:
        assert current[candidate_id]["source_readiness_durability"] == "PROVISIONAL_LIVE_PROBE_ONLY"
        assert current[candidate_id]["source_or_pit_receipt"] is not None
        assert current[candidate_id]["execution_authorized"] is False
        assert current[candidate_id]["performance_allowed"] is False


def test_q231_is_registered_source_first_and_non_authorizing():
    assert NEXT_GATES["Q231"] == "HISTORICAL_SEC_FOIA_PUBLICATION_CLOCK_AND_ISSUER_MAPPING"
    result = compile_state()
    current = {item["candidate_id"]: item for item in result["candidates"]}
    assert current["Q231"]["source_feasibility_required"] is True
    assert current["Q231"]["execution_authorized"] is False
    assert current["Q231"]["performance_allowed"] is False
