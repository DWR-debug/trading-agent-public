from automation.generate_resource_dashboard import infer_lane, infer_resource


def test_dashboard_lane_mapping_is_deterministic():
    assert infer_lane("Q121-R6 SEC Acceptance-Time Compilation") == "FORMAL READINESS"
    assert infer_lane("Q205 NLRB Source Feasibility") == "FRONTIER DISCOVERY"
    assert infer_lane("T052 Exact Master CI Gate") == "PLATFORM / GOVERNANCE"


def test_dashboard_resource_mapping_is_deterministic():
    assert infer_resource("Any", "job", "LHT-N133732") == "Windows self-hosted A"
    assert infer_resource("Any", "job", "LHT-N133732-2") == "Windows self-hosted B"
    assert infer_resource("Any", "job", "LHT-N133732-3") == "Windows self-hosted C"
    assert infer_resource("Free AI Worker Fabric", "worker", None) == "Free AI pool"
    assert infer_resource("T052 Exact Master CI Gate", "gate", None) == "GitHub-hosted CI"


def test_dashboard_resource_identity_never_grants_authority():
    assert infer_resource("Q205 NLRB Source Feasibility", "source_feasibility", None)
