from automation.research_os_scheduler import TRACKS


def test_q119_treasury_demand_shape_is_registered_as_deterministic_frontier():
    track = next(
        item for item in TRACKS
        if item["id"] == "ROS-TRACK-H-TREASURY-DEMAND-SHAPE"
    )
    assert track["lane"] == "deterministic_frontier"
    assert track["source_ids"] == ["SRC-TREASURY"]
    assert track["next_gate"] == "historical_archive_field_completeness_pit_probe"

 
def test_q120_cftc_positioning_is_registered_as_deterministic_frontier():
    track = next(
        item for item in TRACKS
        if item["id"] == "ROS-TRACK-I-CFTC-POSITIONING"
    )
    assert track["lane"] == "deterministic_frontier"
    assert track["source_ids"] == ["SRC-CFTC-TFF"]
    assert track["next_gate"] == "historical_archive_release_date_pit_probe"

 
def test_research_os_scheduler_module_is_syntactically_parseable():
    from pathlib import Path
    import ast

    source = (
        Path(__file__).parents[1] / "automation" / "research_os_scheduler.py"
    ).read_text(encoding="utf-8")
    ast.parse(source)
