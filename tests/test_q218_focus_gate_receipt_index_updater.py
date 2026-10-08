from pathlib import Path

def test_q218_index_updater_rejects_nonpositive_receipt(tmp_path, monkeypatch):
    import automation.q218_focus_gate_receipt_index_updater as updater
    monkeypatch.setattr(updater, "INDEX", tmp_path / "index.json")
    receipt = tmp_path / "receipt.json"
    receipt.write_text('{"candidate_id":"Q218","all_pairing_valid":false}', encoding="utf-8")
    import sys
    old = sys.argv
    sys.argv = ["x","--gate","event_pair","--run-id","1","--artifact-id","2","--artifact-digest","sha256:x","--receipt",str(receipt)]
    try:
        try: updater.main()
        except RuntimeError as exc: assert "RECEIPT_NOT_POSITIVE" in str(exc)
        else: raise AssertionError("non-positive receipt must fail closed")
    finally: sys.argv = old

def test_q218_updater_workflow_is_present():
    assert Path(".github/workflows/q218-focus-gate-receipt-index.yml").exists()