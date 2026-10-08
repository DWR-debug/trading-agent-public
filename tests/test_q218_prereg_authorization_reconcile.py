from automation.q218_prereg_authorization_reconcile import build


def test_q218_reconcile_is_current_and_remains_non_authorizing():
    prereg, auth, receipt = build()
    assert receipt["status"] == "Q218_FROZEN_PREREGISTRATION_AND_AUTHORIZATION_RECONCILED"
    assert receipt["checks"]["source_gate_current"] is True
    assert receipt["checks"]["event_pair_gate_current"] is True
    assert receipt["checks"]["independent_pit_current"] is True
    assert prereg["governance"]["performance_trial_authorized"] is False
    assert auth["authorized"] is False
    assert auth["performance_execution_authorized"] is False
    assert receipt["fingerprints"]["preregistration"] == prereg["preregistration_fingerprint"]
    assert receipt["fingerprints"]["authorization_reconcile"] == auth["authorization_reconcile_fingerprint"]


def test_q218_reconcile_rejects_stale_upstream(monkeypatch):
    import automation.q218_prereg_authorization_reconcile as mod

    original = mod.load

    def fake_load(path):
        payload = original(path)
        if path == mod.INDEP_PATH:
            payload["upstream_receipts"]["event_pair_receipt_fingerprint"] = "stale"
        return payload

    monkeypatch.setattr(mod, "load", fake_load)
    try:
        mod.build()
    except RuntimeError as exc:
        assert "event fingerprint mismatch" in str(exc)
    else:
        raise AssertionError("stale Q218 upstream receipt was accepted")
