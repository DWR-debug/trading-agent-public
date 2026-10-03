from automation.q131r1_sec_disclosure_complexity import (
    accession_from_filename,
    daily_index_url,
    parse_filing_detail,
)

def test_daily_index_url():
    assert daily_index_url("2025-09-22").endswith("/2025/QTR3/master.20250922.idx")

def test_accession_from_filename():
    assert accession_from_filename("edgar/data/104169/000010416925000153/wmt-20250922.htm") == "0000104169-25-000153"

def test_parse_filing_detail_contract():
    html="""<html>
    <div>Documents <span>13</span></div>
    <div>Document Format Files</div>
    <table><tr><th>Seq</th><th>Description</th><th>Document</th><th>Type</th><th>Size</th></tr>
    <tr><td>1</td><td>PRIMARY DOCUMENT</td><td>wmt-20250922.htm iXBRL</td><td>8-K</td><td>35936</td></tr>
    </table>
    <div>Data Files</div>
    <table><tr><th>Seq</th><th>Description</th><th>Document</th><th>Type</th><th>Size</th></tr>
    <tr><td>2</td><td>XBRL TAXONOMY EXTENSION SCHEMA DOCUMENT</td><td>x.xsd</td><td>EX-101.SCH</td><td>4560</td></tr>
    <tr><td>15</td><td>EXTRACTED XBRL INSTANCE DOCUMENT</td><td>x.xml</td><td>XML</td><td>9814</td></tr>
    </table>
    <div>Mailing Address</div></html>"""
    out=parse_filing_detail(html)
    assert out["documents_count"]==13
    assert out["primary_document_size_bytes"]==35936
    assert out["data_files_count"]==2
    assert out["primary_document_ixbrl"] is True

def test_whitespace_mutation_invariance():
    html="<div>Documents 13</div><table><tr><td>1</td><td>PRIMARY DOCUMENT</td><td>x.htm iXBRL</td><td>8-K</td><td>10000</td></tr></table><div>Data Files</div><table><tr><td>2</td><td>XBRL</td><td>x.xml</td><td>XML</td><td>2000</td></tr></table><div>Mailing Address</div>"
    a=parse_filing_detail(html)
    b=parse_filing_detail(html.replace("  ","\n    "))
    assert a==b
