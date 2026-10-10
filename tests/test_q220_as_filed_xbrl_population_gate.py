from pathlib import Path
from automation.q220_as_filed_xbrl_population_gate import TARGET_ISSUERS,WINDOW_START,WINDOW_END,ROUTE_QUARTERS,choose_presentation_source,concept_spec,ix_textblocks,xsd_metadata,presentation_metadata,console_summary,primary_document_from_index,choose_primary
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

def test_q220_windows_receipt_publish_uses_cmd_not_powershell():
    workflow = (ROOT / '.github/workflows/q220-as-filed-xbrl-population.yml').read_text(encoding='utf-8')
    publish = workflow.split('      - name: Publish population receipt', 1)[1].split('      - uses: actions/upload-artifact@v6', 1)[0]
    assert 'shell: cmd' in publish
    assert 'shell: powershell' not in publish
    assert 'github_contents_publish.py' in publish

def test_q220_presentation_source_falls_back_to_inline_xbrl_instance():
    items=["dvn-20241231.htm","dvn-20241231.xsd","dvn-20241231_htm.xml","FilingSummary.xml"]
    assert choose_presentation_source(items) == ("dvn-20241231_htm.xml", "xbrl_instance_embedded_presentation")

def test_q220_presentation_source_prefers_dedicated_linkbase():
    items=["foo.htm","foo.xsd","foo_htm.xml","foo_pre.xml"]
    assert choose_presentation_source(items) == ("foo_pre.xml", "dedicated_presentation_linkbase")

def test_q220_prefixed_qname_matches_sec_presentation_fragment():
    gate = (ROOT / 'automation/q220_as_filed_xbrl_population_gate.py').read_text(encoding='utf-8')
    assert 'return f"{prefix}_{local}"' in gate
    assert 'qname_fragment(q)' in gate

def test_q220_mapping_completion_uses_qnames_after_qname_normalization():
    gate = (ROOT / "automation/q220_as_filed_xbrl_population_gate.py").read_text(encoding="utf-8")
    assert "len(hits)>=len(qnames)" in gate
    assert "len(hits)>=len(locals_)" not in gate

def test_q220_publish_step_avoids_windows_powershell_execution_policy():
    workflow = (ROOT / ".github/workflows/q220-as-filed-xbrl-population.yml").read_text(encoding="utf-8")
    publish = workflow.split("      - name: Publish population receipt", 1)[1].split("      - uses: actions/upload-artifact@v6", 1)[0]
    assert "shell: cmd" in publish
    assert "shell: powershell" not in publish
    assert "github_contents_publish.py" in publish


def test_q220_console_summary_exposes_per_issuer_gate_blockers():
    receipt = {
        "candidate_id": "Q220",
        "mode": "population",
        "status": "Q220_AS_FILED_XBRL_POPULATION_BLOCKED",
        "row_count": 55,
        "record_count": 55,
        "failure_count": 0,
        "receipt_fingerprint": "a" * 64,
        "issuer_summary": {
            "SPGI": {
                "original_10k_count": 5,
                "amendment_count": 1,
                "textblock_ready_originals": 4,
                "records_with_failures": 0,
            }
        },
        "failures": [],
        "records": [{"large": "payload must not be printed"}],
    }
    summary = console_summary(receipt)
    assert summary["per_issuer_minimum_originals_and_textblock_ready"] == 5
    assert summary["issuer_summary"]["SPGI"]["textblock_ready_originals"] == 4
    assert summary["failure_count"] == 0
    assert "records" not in summary
    assert summary["performance_authorized"] is False
    assert summary["promotion_allowed"] is False


def test_q220_blocked_receipt_is_published_before_positive_gate_fails():
    workflow = (ROOT / ".github/workflows/q220-as-filed-xbrl-population.yml").read_text(encoding="utf-8")
    publish = workflow.split("      - name: Publish population receipt", 1)[1].split(
        "      - name: Enforce positive population receipt", 1
    )[0]
    enforce = workflow.split("      - name: Enforce positive population receipt", 1)[1].split(
        "      - uses: actions/upload-artifact@v6", 1
    )[0]
    assert "if: always()" in publish
    assert "gh api " not in publish
    assert "--base-sha latest" in publish
    assert "github_contents_publish.py" in publish
    assert "if: always()" in enforce
    assert "Q220_POPULATION_POSITIVE=" in enforce
    assert "Q220_AS_FILED_XBRL_POPULATION_COMPLETED" in enforce

def test_q220_windows_receipt_publisher_is_cli_independent_and_preserves_gate():
    workflow = (ROOT / ".github/workflows/q220-as-filed-xbrl-population.yml").read_text(encoding="utf-8")
    publish = workflow.split("      - name: Publish population receipt", 1)[1].split(
        "      - name: Enforce positive population receipt", 1
    )[0]
    enforce = workflow.split("      - name: Enforce positive population receipt", 1)[1].split(
        "      - uses: actions/upload-artifact@v6", 1
    )[0]
    gate = (ROOT / "automation/q220_as_filed_xbrl_population_gate.py").read_text(encoding="utf-8")

    assert "shell: cmd" in publish
    assert "gh api " not in publish
    assert "--base-sha latest" in publish
    assert "github_contents_publish.py" in publish
    assert "int(r.get('failure_count',1))==0" in enforce
    assert 'original_10k_count"]>=(1 if mode=="route" else 5)' in gate
    assert 'textblock_ready_originals"]>=(1 if mode=="route" else 5)' in gate



def test_q220_historical_primary_document_uses_sec_form_typed_filing_index():
    index_html = b'''
    <table class="tableFile">
      <tr><th>Seq</th><th>Description</th><th>Document</th><th>Type</th><th>Size</th></tr>
      <tr><td>1</td><td>10-K</td><td><a href="/ix?doc=/Archives/edgar/data/820027/000082002719000010/amp12312018.htm">amp12312018.htm</a> iXBRL</td><td>10-K</td><td>10087676</td></tr>
      <tr><td>2</td><td>EXHIBIT 10.11</td><td><a href="/Archives/edgar/data/820027/000082002719000010/R1.htm">R1.htm</a></td><td>EX-10.11</td><td>34034</td></tr>
    </table>
    '''
    items = ["R1.htm", "amp12312018.htm"]
    assert primary_document_from_index(index_html, "10-K") == "amp12312018.htm"
    assert choose_primary(items, "amp12312018.htm") == "amp12312018.htm"
    # Missing mappings must never silently degrade to alphabetical R1.htm.
    assert choose_primary(items, None) is None


def test_q220_form_index_parser_fails_closed_without_matching_form_row():
    index_html = b'''<table><tr><td>1</td><td>EXHIBIT 10.11</td><td><a href="/Archives/edgar/data/1/2/R1.htm">R1.htm</a></td><td>EX-10.11</td><td>100</td></tr></table>'''
    assert primary_document_from_index(index_html, "10-K") is None
