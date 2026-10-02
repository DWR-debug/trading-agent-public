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



def test_accepted_online_phone_routes_to_utility(monkeypatch, tmp_path):
    registry = tmp_path / "ops" / "android_phone_resources.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        '{"devices":[{"enabled":true,"runner_label":"samsung-phone-01"}]}',
        encoding="utf-8",
    )
    status_dir = tmp_path / "ops" / "android_phone_runtime_status"
    status_dir.mkdir(parents=True)
    (status_dir / "SAMSUNG-PHONE-01.json").write_text(
        '{"status":"ANDROID_PHONE_UTILITY_ACCEPTED","eligible":true}',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "automation.android_phone_fleet_planner.discover_online_labels",
        lambda repository: ({"samsung-phone-01"}, "RUNNER_DISCOVERY_OK"),
    )
    plan = build_plan(registry, "DWR-debug/trading-agent-public")
    assert plan["slot_modes"]["01"] == "utility"
    assert plan["routable_slots"]["01"] is True
    assert plan["receipt_states"]["01"] == "ACCEPTED_RECEIPT"


def test_online_unaccepted_phone_routes_to_acceptance(monkeypatch, tmp_path):
    registry = tmp_path / "ops" / "android_phone_resources.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        '{"devices":[{"enabled":true,"runner_label":"samsung-phone-01"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "automation.android_phone_fleet_planner.discover_online_labels",
        lambda repository: ({"samsung-phone-01"}, "RUNNER_DISCOVERY_OK"),
    )
    plan = build_plan(registry, "DWR-debug/trading-agent-public")
    assert plan["slot_modes"]["01"] == "acceptance"
    assert plan["routable_slots"]["01"] is True
    assert plan["receipt_states"]["01"] == "NO_RUNTIME_RECEIPT"
