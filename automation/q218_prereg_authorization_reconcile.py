    return prereg, auth, receipt


def existing_reconcile_is_current() -> tuple[bool, dict | None]:
    try:
        prereg = load(PREREG_PATH)
        auth = load(AUTH_PATH)
        receipt = load(RECEIPT_PATH)
    except (RuntimeError, json.JSONDecodeError):
        return False, None
    index = load(INDEX_PATH)
    indep = load(INDEP_PATH)
    if index.get("source_gate", {}).get("verified_positive_complete") is not True:
        return False, None
    if index.get("event_pair_gate", {}).get("verified_positive_complete") is not True:
        return False, None
    source_fp = index.get("source_gate", {}).get("receipt_fingerprint")
    event_fp = index.get("event_pair_gate", {}).get("receipt_fingerprint")
    if indep.get("status") != "Q218_INDEPENDENT_ARCHITECTURE_PIT_REPRODUCED":
        return False, None
    if indep.get("upstream_receipts", {}).get("source_receipt_fingerprint") != source_fp:
        return False, None
    if indep.get("upstream_receipts", {}).get("event_pair_receipt_fingerprint") != event_fp:
        return False, None
    if prereg.get("status") != "FROZEN_PREREGISTRATION_RECONCILED":
        return False, None
    if auth.get("authorized") is not False or auth.get("performance_execution_authorized") is not False:
        return False, None
    if receipt.get("status") != "Q218_FROZEN_PREREGISTRATION_AND_AUTHORIZATION_RECONCILED":
        return False, None
    if receipt.get("fingerprints", {}).get("source_gate") != source_fp:
        return False, None
    if receipt.get("fingerprints", {}).get("event_pair_gate") != event_fp:
        return False, None
    if receipt.get("fingerprints", {}).get("independent_pit") != indep.get("receipt_fingerprint"):
        return False, None
    if receipt.get("fingerprints", {}).get("preregistration") != prereg.get("preregistration_fingerprint"):
        return False, None
    if receipt.get("fingerprints", {}).get("authorization_reconcile") != auth.get("authorization_reconcile_fingerprint"):
        return False, None

    # When performance-preparation receipts exist, the G4 reconcile is not
    # current until those exact fingerprints are bound into the preregistration.
    if INPUT_BUNDLE_RECEIPT_PATH.is_file():
        bundle = load(INPUT_BUNDLE_RECEIPT_PATH)
        if bundle.get("status") != "INPUT_BUNDLE_FROZEN":
            return False, None
        bound = prereg.get("input_bundle") or {}
        if bound.get("bundle_fingerprint") != bundle.get("bundle_fingerprint"):
            return False, None
        if bound.get("artifact_sha256") != bundle.get("artifact_sha256"):
            return False, None
    if ROBUSTNESS_RECEIPT_PATH.is_file():
        robustness = load(ROBUSTNESS_RECEIPT_PATH)
        if robustness.get("status") != "PRE_PERFORMANCE_ROBUSTNESS_COMPLETED":
            return False, None
        bound = prereg.get("pre_performance_robustness") or {}
        for key in ("trial_id", "status", "artifact_sha256", "research_only", "screen_is_descriptive_only", "no_post_hoc_tuning", "receipt_fingerprint"):
            if bound.get(key) != robustness.get(key):
                return False, None
    if CANDIDATE_ROBUSTNESS_RECEIPT_PATH.is_file():
        candidate_gate = load(CANDIDATE_ROBUSTNESS_RECEIPT_PATH)
        if candidate_gate.get("status") != "PRE_FORMAL_ROBUSTNESS_COMPLETED":
            return False, None
        bound = prereg.get("candidate_robustness_gate") or {}
        if bound.get("receipt_fingerprint") != candidate_gate.get("receipt_fingerprint"):
            return False, None
    return True, receipt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=ROOT / "research")
    args = ap.parse_args()

    current, receipt = existing_reconcile_is_current()
    if current and receipt is not None:
        print(json.dumps({
            "status": receipt["status"],
            "trial_id": receipt["trial_id"],
            "preregistration_fingerprint": receipt["fingerprints"]["preregistration"],
            "receipt_fingerprint": receipt["receipt_fingerprint"],
            "performance_execution_authorized": False,
            "idempotent_reuse": True,
        }, sort_keys=True))
        return 0

    prereg, auth, receipt = build()