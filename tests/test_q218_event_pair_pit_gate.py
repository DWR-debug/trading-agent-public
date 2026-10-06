from automation.q218_event_pair_pit_gate import pair_issuer

def E(**kw):
    x={"ten_k_accession":"10K1","ten_k_acceptance_datetime":"20250110120000",
       "paired_8k_accession":"8K1","paired_8k_acceptance_datetime":"20250109120000",
       "pair_lower_bound_acceptance":"20240109120000","paired_8k_form":"8-K",
       "paired_8k_is_amendment":False}
    x.update(kw)
    return x

def I(events, candidates):
    return {"cik":"1","paired_10k_events":events,"eligible_8k_events":candidates}

def C(accession="8K1", stamp="20250109120000", form="8-K"):
    return {"form":form,"is_eligible_earnings_release_8k":True,
            "acceptance_datetime":stamp,"accession":accession}

def test_valid():
    rows,s=pair_issuer(I([E()],[C()]))
    assert s["paired_count"]==1 and rows[0]["status"]=="PAIR_VALIDATED"

def test_equal_target_timestamp_fails_closed():
    try:
        pair_issuer(I([E(paired_8k_acceptance_datetime="20250110120000")],[C()]))
    except SystemExit as exc:
        assert "Q218_EQUAL_TARGET_TIMESTAMP" in str(exc)
    else:
        raise AssertionError

def test_pair_after_target_fails():
    try:
        pair_issuer(I([E(paired_8k_acceptance_datetime="20250110120001")],[C()]))
    except SystemExit as exc:
        assert "Q218_PAIR_AFTER_TARGET" in str(exc)
    else:
        raise AssertionError

def test_pair_before_lower_fails():
    try:
        pair_issuer(I([E(paired_8k_acceptance_datetime="20240109115959")],[C()]))
    except SystemExit as exc:
        assert "Q218_PAIR_NOT_AFTER_LOWER" in str(exc)
    else:
        raise AssertionError

def test_amended_fails():
    try:
        pair_issuer(I([E(paired_8k_form="8-K/A",paired_8k_is_amendment=True)],[C()]))
    except SystemExit as exc:
        assert "Q218_AMENDED_OR_INVALID_PAIR" in str(exc)
    else:
        raise AssertionError

def test_duplicate_fails():
    events=[
        E(paired_8k_accession="8K",ten_k_accession="10K1",ten_k_acceptance_datetime="20250110120000",paired_8k_acceptance_datetime="20250109120000",pair_lower_bound_acceptance=None),
        E(paired_8k_accession="8K",ten_k_accession="10K2",ten_k_acceptance_datetime="20260110120000",paired_8k_acceptance_datetime="20250109120000",pair_lower_bound_acceptance=None),
    ]
    candidates=[C(accession="8K",stamp="20250109120000")]
    try:
        pair_issuer(I(events,candidates))
    except SystemExit as exc:
        assert "Q218_DUPLICATE_PAIR_ASSIGNMENT" in str(exc)
    else:
        raise AssertionError

def test_independent_selection_uses_latest_eligible_8k():
    issuer=I(
        [E(paired_8k_accession="8K2",paired_8k_acceptance_datetime="20250109120000")],
        [C("8K1","20250108120000"),C("8K2","20250109120000")]
    )
    rows,s=pair_issuer(issuer)
    assert s["paired_count"]==1
    assert rows[0]["paired_8k_accession"]=="8K2"

def test_independent_selection_rejects_wrong_selected_pair():
    issuer=I(
        [E(paired_8k_accession="8K1",paired_8k_acceptance_datetime="20250108120000")],
        [C("8K1","20250108120000"),C("8K2","20250109120000")]
    )
    try:
        pair_issuer(issuer)
    except SystemExit as exc:
        assert "Q218_NONDETERMINISTIC_SELECTED_PAIR" in str(exc)
    else:
        raise AssertionError
