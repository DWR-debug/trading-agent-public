from automation.q040_official_event_source_feasibility import PROBES, PIT_CLASS, _probe

def test_q040_probe_order_is_fixed():
    assert [item[0] for item in PROBES] == ["SEC", "BLS", "BEA", "CFTC", "TREASURY"]
    assert len(PROBES) == 5
    assert set(PIT_CLASS) == {item[0] for item in PROBES}

def test_q040_access_error_is_recorded_not_promoted(monkeypatch):
    def fail(*args, **kwargs):
        raise __import__("urllib").error.HTTPError("https://example.invalid", 403, "Forbidden", {}, None)
    monkeypatch.setattr("automation.q040_official_event_source_feasibility.urllib.request.urlopen", fail)
    row = _probe("SEC", "https://example.invalid", ("acceptanceDateTime",))
    assert row["access_status"] == "HTTP_ERROR"
    assert row["http_status"] == 403
    assert row["pit_status"] == "ACCEPTANCE_BOUND_PENDING_PUBLIC_AVAILABILITY_GAP"
