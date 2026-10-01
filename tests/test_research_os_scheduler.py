from automation.research_os_scheduler import TRACKS


def test_q119_treasury_demand_shape_is_registered_as_deterministic_frontier():
    track = next(
        item for item in TRACKS
        if item["id"] == "ROS-TRACK-H-TREASURY-DEMAND-SHAPE"
    )
    assert track["lane"] == "deterministic_frontier"
    assert track["source_ids"] == ["SRC-TREASURY"]
    assert track["next_gate"] == "historical_archive_field_completeness_pit_probe"
