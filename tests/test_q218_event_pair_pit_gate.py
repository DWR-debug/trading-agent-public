from automation.q218_event_pair_pit_gate import pair_issuer

def E(**kw):
    x={"ten_k_accession":"10K1","ten_k_acceptance_datetime":"20250110120000","paired_8k_accession":"8K1","paired_8k_acceptance_datetime":"20250109120000","pair_lower_bound_acceptance":"20240109120000","paired_8k_form":"8-K","paired_8k_is_amendment":False}
    x.update(kw)
    return x

def test_valid():
    rows,s=pair_issuer({"cik":"1","paired_10k_events":[E()]})
    assert s["paired_count"]==1 and rows[0]["status"]=="PAIR_VALIDATED"

def test_equal_target_fails_closed():
    try:
        pair_issuer({"cik":"1","paired_10k_events":[E(paired_8k_acceptance_datetime="20250110120000")]})
    except SystemExit as exc:
        assert "Q218_EQUAL_TARGET_TIMESTAMP" in str(exc)
    else:
        raise AssertionError("expected equal-second temporal ambiguity rejection")

def test_after_target_fails():
    try:
        pair_issuer({"cik":"1","paired_10k_events":[E(paired_8k_acceptance_datetime="20250110120001")]})
    except SystemExit as exc:
        assert "Q218_PAIR_AFTER_TARGET" in str(exc)
    else:
        raise AssertionError("expected rejection")

def test_before_lower_fails():
    try:
        pair_issuer({"cik":"1","paired_10k_events":[E(paired_8k_acceptance_datetime="20240109115959")]})
    except SystemExit as exc:
        assert "Q218_PAIR_NOT_AFTER_LOWER" in str(exc)
    else:
        raise AssertionError("expected rejection")

def test_amended_fails():
    try:
        pair_issuer({"cik":"1","paired_10k_events":[E(paired_8k_form="8-K/A",paired_8k_is_amendment=True)]})
    except SystemExit as exc:
        assert "Q218_AMENDED_OR_INVALID_PAIR" in str(exc)
    else:
        raise AssertionError("expected rejection")

def test_duplicate_fails():
    e1=E(paired_8k_accession="8K",ten_k_acceptance_datetime="20250110120000",paired_8k_acceptance_datetime="20250109120000")
    e2=E(ten_k_accession="10K2",ten_k_acceptance_datetime="20260110120000",paired_8k_accession="8K",paired_8k_acceptance_datetime="20260109120000",pair_lower_bound_acceptance="20250110120000")
    try:
        pair_issuer({"cik":"1","paired_10k_events":[e1,e2]})
    except SystemExit as exc:
        assert "Q218_DUPLICATE_PAIR_ASSIGNMENT" in str(exc)
    else:
        raise AssertionError("expected rejection")
