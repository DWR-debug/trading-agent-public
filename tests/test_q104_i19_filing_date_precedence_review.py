from pathlib import Path
from automation import q104_i19_filing_date_precedence_review as review


def test_request_cannot_apply_precedence(tmp_path):
    values=dict(review.FROZEN); values["REQUEST_SEQUENCE"]="2026-10-12T20:40:00Z"
    p=tmp_path/"request.trigger"; p.write_text("".join(f"{k}={v}\n" for k,v in values.items()),encoding="utf-8")
    assert review.read_request(p)["APPLY_FIELD_PRECEDENCE"]=="false"
    values["APPLY_FIELD_PRECEDENCE"]="true"; p.write_text("".join(f"{k}={v}\n" for k,v in values.items()),encoding="utf-8")
    try: review.read_request(p)
    except review.ReviewError as e: assert "VALUE_MISMATCH:APPLY_FIELD_PRECEDENCE" in str(e)
    else: raise AssertionError("review must not apply field precedence")


def test_analysis_keeps_date_change_separate_from_filed_date():
    samples=[]
    for i in range(8):
        date=f"202{i//2}-02-14"; change=date if i in {2,3} else f"202{i//2}-02-20"
        accept=f"202{i//2}-02-14T18:00:00"
        common={"accession":f"0000950123-{15+i:02d}-003104","filer_cik":"0001226779","form":"13F-HR","filing_date":date,"date_of_filing_date_change":change,"acceptance_datetime":accept}
        samples.append({"accession":common["accession"],"bulk_filing_date":f"202{i//2}-02-15","probes":[
          {"route":"index_headers","observed_fields":dict(common)},{"route":"raw_sgml_header","observed_fields":dict(common)},
          {"route":"complete_submission_header_prefix","observed_fields":{**common,"date_of_filing_date_change":None}}]})
    out=review.analyze({"samples":samples})
    assert out["status"]=="FIELD_PRECEDENCE_REVIEW_PROPOSAL_READY_NOT_APPLIED"
    assert out["counts"]["bulk_date_differs"]==8
    assert out["counts"]["acceptance_routes_agree"]==8
    assert out["counts"]["date_change_equals_filing_date"]==2
    assert out["counts"]["date_change_differs_from_filing_date"]==6
