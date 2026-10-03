from pathlib import Path
ROOT = Path(__file__).parents[1]
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


def test_scheduler_has_no_literal_newline_in_plan_dictionary_separator():
    text = (ROOT / "automation" / "research_os_scheduler.py").read_text(encoding="utf-8")
    assert '},\\n    "resource_policy"' not in text


def test_s10_fresh_successful_run_is_a_bounded_presence_signal(monkeypatch, tmp_path):
    import json
    from datetime import datetime, timezone
    import automation.research_os_scheduler as scheduler
    path = tmp_path / "ops" / "s10_runtime_status.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({
        "eligible": True,
        "receipt_status": "S10_UTILITY_ACCEPTED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "utility_task_status": "S10_UTILITY_REVIEW_COMPLETED",
    }), encoding="utf-8")
    monkeypatch.setattr(scheduler, "S10_OS_STATUS_PATH", path)
    monkeypatch.setattr(scheduler, "S10_ACCEPTANCE_PATH", tmp_path / "missing.json")
    state = scheduler._s10_resource_state()
    assert state["eligible"] is True
    assert state["presence_signal"] == "fresh_successful_s10_run"
    assert state["presence_signal_fresh"] is True


def test_s10_stale_success_receipt_does_not_route(monkeypatch, tmp_path):
    import json
    from datetime import datetime, timezone, timedelta
    import automation.research_os_scheduler as scheduler
    path = tmp_path / "ops" / "s10_runtime_status.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({
        "eligible": True,
        "receipt_status": "S10_UTILITY_ACCEPTED",
        "generated_at_utc": (datetime.now(timezone.utc) - timedelta(hours=7)).isoformat(),
    }), encoding="utf-8")
    monkeypatch.setattr(scheduler, "S10_OS_STATUS_PATH", path)
    monkeypatch.setattr(scheduler, "S10_ACCEPTANCE_PATH", tmp_path / "missing.json")
    state = scheduler._s10_resource_state()
    assert state["eligible"] is False
    assert state["presence_signal_fresh"] is False
