from automation.q232_sec_ct_document_temporal_gate import temporal_anchor_hit


def test_temporal_anchor_requires_date_near_state_term():
    assert temporal_anchor_hit("Confidential treatment expires on March 31, 2020.") is True
    assert temporal_anchor_hit("Confidential treatment expires; no date is stated here.") is False


def test_temporal_anchor_rejects_distant_date():
    text = "2020-01-01 " + ("x" * 700) + " confidential treatment expires"
    assert temporal_anchor_hit(text) is False


from automation.q232_sec_ct_document_temporal_gate import declared_ct_document_name


def test_declared_ct_document_name_handles_sgml_field_order():
    complete = """
    <DOCUMENT>
    <FILENAME>filename1.pdf
    <TYPE>CT ORDER
    </DOCUMENT>
    """
    assert declared_ct_document_name(complete) == "filename1.pdf"
