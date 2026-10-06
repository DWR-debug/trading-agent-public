from pathlib import Path
from automation.q220_as_filed_xbrl_population_gate import TARGET_ISSUERS,WINDOW_START,WINDOW_END,ROUTE_QUARTERS,choose_presentation_source,concept_spec,ix_textblocks,xsd_metadata,presentation_metadata
ROOT=Path(__file__).parents[1]

def test_q220_population_window_and_identity_are_frozen():
    assert WINDOW_START.isoformat()=="2019-01-01"; assert WINDOW_END.isoformat()=="2025-09-24"
    assert list(TARGET_ISSUERS)==["SPGI","NDAQ","AMP","RJF","WMB","VLO","DVN","EMN"]
    assert TARGET_ISSUERS["SPGI"]=="0000064040"; assert TARGET_ISSUERS["EMN"]=="0000915389"

def test_q220_textblock_rule_is_deterministic():
    html=b'<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xmlns:c="http://example.invalid/custom"><ix:nonNumeric name="c:RiskFactorsTextBlock" contextRef="C1" id="f1">text</ix:nonNumeric><ix:nonNumeric name="c:NotAParagraph" contextRef="C1">x</ix:nonNumeric></html>'
    assert ix_textblocks(html)==[{"qname":"c:RiskFactorsTextBlock","local_name":"RiskFactorsTextBlock","namespace":"http://example.invalid/custom","context_ref":"C1","fact_id":"f1"}]

def test_q220_xsd_and_presentation_metadata_are_extractable():
    xsd=b'<xsd:schema targetNamespace="http://example.invalid/custom"><xsd:element name="RiskFactorsTextBlock"/><xsd:element name="OperatingIncome"/></xsd:schema>'
    pre=b'<link:presentationLink xlink:role="http://example.invalid/role"><link:presentationArc xlink:from="c:Root" xlink:to="c:RiskFactorsTextBlock"/></link:presentationLink>'
    xm=xsd_metadata(xsd); pm=presentation_metadata(pre)
    assert xm["target_namespace"]=="http://example.invalid/custom"
    assert "RiskFactorsTextBlock" in xm["textblock_elements"]
    assert pm["presentation_arc_count"]==1
    assert any("RiskFactorsTextBlock" in x for x in pm["endpoints"])

def test_q220_concept_spec_forbids_substitution_and_performance_authority():
    spec=concept_spec()
    assert spec["structured_side"]["substitution_allowed"] is False
    assert len(spec["structured_side"]["exact_numeric_qnames"])==5
    assert spec["pit_clock"].startswith("SEC acceptance datetime")
    assert spec["candidate_id"]=="Q220"
    gate=(ROOT/"automation/q220_as_filed_xbrl_population_gate.py").read_text(encoding="utf-8")
    assert 'performance_authorization":False' in gate

def test_top4_q220_lane_uses_contract_qa_not_network_scan():
    text=(ROOT/"automation/top4_candidate_capacity.py").read_text(encoding="utf-8")
    assert "tests/test_q220_as_filed_xbrl_population_gate.py" in text
    assert "q220_fsn_schema_gate" not in text


def test_q220_presentation_mapping_resolves_loc_labels_to_concepts():
    pre=b'''<link:presentationLink><link:loc xlink:label="l1" xlink:href="custom.xsd#RiskFactorsTextBlock"/><link:loc xlink:label="l2" xlink:href="custom.xsd#Root"/><link:presentationArc xlink:from="l2" xlink:to="l1"/></link:presentationLink>'''
    pm=presentation_metadata(pre)
    assert pm["loc_count"]==2
    assert "RiskFactorsTextBlock" in pm["loc_concepts"]


def test_q220_route_includes_fiscal_year_end_q4():
    assert ROUTE_QUARTERS[0] == (2024, 4)
    assert ROUTE_QUARTERS[-3:] == ((2025, 1), (2025, 2), (2025, 3))


def test_q220_windows_receipt_publish_uses_powershell_not_bash():
    workflow = (ROOT / '.github/workflows/q220-as-filed-xbrl-population.yml').read_text(encoding='utf-8')
    publish = workflow.split('      - name: Publish population receipt', 1)[1].split('      - uses: actions/upload-artifact@v6', 1)[0]
    assert 'shell: powershell' in publish
    assert 'shell: bash' not in publish
    assert 'github_contents_publish.py' in publish


def test_q220_presentation_source_falls_back_to_inline_xbrl_instance():
    items=["dvn-20241231.htm","dvn-20241231.xsd","dvn-20241231_htm.xml","FilingSummary.xml"]
    assert choose_presentation_source(items) == ("dvn-20241231_htm.xml", "xbrl_instance_embedded_presentation")


def test_q220_presentation_source_prefers_dedicated_linkbase():
    items=["foo.htm","foo.xsd","foo_htm.xml","foo_pre.xml"]
    assert choose_presentation_source(items) == ("foo_pre.xml", "dedicated_presentation_linkbase")


def test_q220_prefixed_qname_matches_sec_presentation_fragment():
    import re
    gate = (ROOT / 'automation/q220_as_filed_xbrl_population_gate.py').read_text(encoding='utf-8')
    assert 'return f"{prefix}_{local}"' in gate
    assert 'qname_fragment(q)' in gate


def test_q220_mapping_completion_uses_qnames_after_qname_normalization():
    gate = (ROOT / "automation/q220_as_filed_xbrl_population_gate.py").read_text(encoding="utf-8")
    assert "len(hits)>=len(qnames)" in gate
    assert "len(hits)>=len(locals_)" not in gate
