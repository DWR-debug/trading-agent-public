import io,zipfile
from datetime import date
from automation.q104_i19_13f_historical_identity_census import SHARDS,discover_archives,scan_archive,synthetic_contract

def test_archive_discovery_and_partition():
    page=b'''<a href="/files/structureddata/data/form-13f-data-sets/2013q3_form13f.zip">2013 Q3</a>
    <a href="/files/structureddata/data/form-13f-data-sets/2017q4_form13f.zip">2017 Q4</a>
    <a href="/files/structureddata/data/form-13f-data-sets/2018q1_form13f.zip">2018 Q1</a>
    <a href="/files/data/form-13f-data-sets/01jun2025-31aug2025_form13f.zip">2025 Jun-Aug</a>'''
    a=discover_archives(page)
    assert [x["period_start"] for x in a]==["2013-07-01","2017-10-01","2018-01-01","2025-06-01"]
    assert len([x for x in a if SHARDS["2013-2017"][0]<=date.fromisoformat(x["period_start"])<SHARDS["2013-2017"][1]])==2
    assert len([x for x in a if SHARDS["2022-2025-09"][0]<=date.fromisoformat(x["period_start"])<SHARDS["2022-2025-09"][1]])==1

def test_future_filing_is_excluded():
    sub="ACCESSION_NUMBER\tFILING_DATE\tPERIODOFREPORT\nA1\t01-JUL-2017\t30-JUN-2017\nA2\t01-NOV-2025\t30-SEP-2025\n"
    info="ACCESSION_NUMBER	NAMEOFISSUER	TITLEOFCLASS	CUSIP
A1	Old Name Corp	Common Stock	78409V104
A2	Future Name Corp	Common Stock	78409V104
"
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:z.writestr("SUBMISSION.tsv",sub);z.writestr("INFOTABLE.tsv",info)
    r=scan_archive(b.getvalue(),{"url":"synthetic://q104","label":"2017 Q3","period_start":"2017-07-01"},{"SPGI":{"78409V104"}})
    assert r["target_hits"]["SPGI"]["row_count"]==1
    assert r["target_hits"]["SPGI"]["issuer_names"]==["Old Name Corp"]

def test_synthetic_contract():
    assert all(synthetic_contract().values())
