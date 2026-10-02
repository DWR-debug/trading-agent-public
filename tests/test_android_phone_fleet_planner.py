from automation.android_phone_fleet_planner import SLOTS, build_plan


def test_slots_are_unique():
    assert set(SLOTS) == {"01", "02", "03"}
    assert len(set(SLOTS.values())) == 3


def test_discovery_failure_routes_nothing(monkeypatch, tmp_path):
    registry = tmp_path / "registry.json"
    registry.write_text(
        '{"devices":[{"enabled":true,"runner_label":"samsung-phone-01"}]}',
        encoding="utf-8",
    )

    def unavailable(*args, **kwargs):
        raise FileNotFoundError("gh unavailable")

    monkeypatch.setattr(
        "automation.android_phone_fleet_planner.subprocess.check_output",
        unavailable,
    )

    plan = build_plan(registry, "DWR-debug/trading-agent-public")

    assert plan["status"] == "RUNNER_DISCOVERY_UNAVAILABLE"
    assert plan["fail_closed"] is True
    assert plan["routable_slots"] == {"01": False, "02": False, "03": False}
    assert plan["performance_authorization"] is False
    assert plan["promotion"] is False
