from automation.q218_publish_focus_gate_receipt import performance_boundary_is_closed


def test_q218_publisher_accepts_event_pair_receipt_schema_with_closed_performance():
    receipt = {
        "performance_authorization": False,
        "promotion": False,
        "live_execution": False,
    }
    assert performance_boundary_is_closed(receipt) is True


def test_q218_publisher_accepts_explicit_scientific_boundary_schema():
    receipt = {
        "scientific_boundary": {"performance_authorized": False},
    }
    assert performance_boundary_is_closed(receipt) is True


def test_q218_publisher_rejects_conflicting_open_performance_boundary():
    receipt = {
        "scientific_boundary": {"performance_authorized": True},
        "performance_authorization": False,
    }
    assert performance_boundary_is_closed(receipt) is False


def test_q218_publisher_rejects_missing_or_non_boolean_performance_boundary():
    assert performance_boundary_is_closed({}) is False
    assert performance_boundary_is_closed({"performance_authorization": "false"}) is False
