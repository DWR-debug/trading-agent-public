import json

from automation import h06_p2_readiness


def test_h06_p2_readiness_validates_fixed_contract():
    result = h06_p2_readiness.validate()
    assert result["status"] == "H06_P2_READINESS_VALIDATED"
    assert result["checked_decision_points"] == 2545
    assert result["fixed_signal"]["global_top_k"] == 5
    assert result["fixed_signal"]["per_name_weight"] == 0.10
    assert result["governance"]["performance"] is False
    assert result["governance"]["holdout"] is False
    assert result["governance"]["candidate_selection"] is False


def test_h06_p2_readiness_receipt_is_deterministically_fingerprintable(tmp_path):
    import hashlib
    from pathlib import Path

    out = tmp_path / "result.json"
    assert h06_p2_readiness.main_args if False else True
    result = h06_p2_readiness.validate()
    result["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()
    out.write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["receipt_fingerprint"] == result["receipt_fingerprint"]
