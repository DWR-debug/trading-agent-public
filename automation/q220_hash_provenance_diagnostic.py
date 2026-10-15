"""Offline, receipt-pinned Q220 primary-body hash lineage diagnostic.

It reads committed summaries and two small immutable historical receipts. It does
not fetch SEC data, download primary documents/Feeds, alter expected hashes, or
recompute any candidate/PIT/performance gate.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CANDIDATE="Q220"
SOURCE_RECEIPT_FP="c7fc53c9ef2daaef9caee29c0ba1084602c0bf4b24c6d2a13cb812b7b592c075"
POPULATION_FP="158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543"
# Exact current canonical compiler receipt captured 2026-10-15T04:41:43Z. The target accession changed body hash/length while URL and Last-Modified remained unchanged; the prior probe is independently pinned below.
COMPILER_FP="1ca885190d7b277c809ac8a6c3386a637e7750df6bb51755260c9bd7351f868d"
SENSITIVITY_RUN_ID="38590133217"
SENSITIVITY_ARTIFACT_ID=11907246485
SENSITIVITY_ARTIFACT_NAME="q220-http-representation-sensitivity-38590133217-1"
SENSITIVITY_FP="870aa4fdae7eda932bb8f50ebb9eab1a7781ee503fb5120dea5b0f099e4fd65c"
SENSITIVITY_REQUEST_FP="211b2afacf8eddf0b8b56aaf9ee7896e14d5788ba88e9ada0d98be101158f0e2"
SENSITIVITY_BODY_SHA="fc7dfedd605cdbc9e497bb0c0bc306c74e3f90493a68fb6025d762540ef600f3"
SENSITIVITY_BODY_BYTES=4774457
SENSITIVITY_RESPONSE_COUNT=5
FORENSICS_RUN_ID="38254139755"
FORENSICS_ARTIFACT_ID=11749259509
FORENSICS_ARTIFACT_NAME="q220-primary-source-vintage-forensics-38254139755-1"
FORENSICS_FP="840f280cbcb1fdbe4b2fbaa88f8d7f02edf447799e13fe0171d37fcd57f3221b"
HEADER_RUN_ID="38258251764"
HEADER_ARTIFACT_ID=11751436149
HEADER_ARTIFACT_NAME="q220-bounded-header-evidence-38258251764-1"
HEADER_FP="39bf95fa15bf149094d5b56c90e58622c2339d452fd138c6deb0a463668f85b4"
SINGLE_FEED_RUN_ID=38446029194
SINGLE_FEED_ARTIFACT_ID=11838034399
RECORD_KEY="0000064040|0000064040-19-000059|10-K|2019-02-13"
EXPECTED_SHA="27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83"
EXPECTED_BYTES=4774458
LAST_MODIFIED="Wed, 13 Feb 2019 11:02:53 GMT"
PRIMARY_URL="https://www.sec.gov/Archives/edgar/data/64040/000006404019000059/spgi-20181231x10k.htm"

class DiagnosticError(ValueError): pass

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def fp(value: dict[str, Any], field: str="receipt_fingerprint") -> str:
    payload=dict(value); payload.pop(field,None)
    return sha(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8"))

def read_json(path: Path) -> dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def find_receipt(root: Path) -> Path:
    if root.is_file(): return root
    paths=sorted(root.rglob("receipt.json"))
    if len(paths)!=1: raise DiagnosticError(f"PINNED_ARTIFACT_RECEIPT_COUNT_INVALID:{len(paths)}")
    return paths[0]

def classify_primary_hashes(expected_sha: str, observations: list[dict[str,Any]]) -> dict[str,Any]:
    whole=[x for x in observations if x.get("scope")=="whole_primary_document" and x.get("sha256")]
    distinct=sorted({x["sha256"] for x in whole})
    by_identity: dict[tuple[str,str],set[str]]={}
    for row in whole:
        by_identity.setdefault((str(row.get("url") or ""),str(row.get("last_modified") or "")),set()).add(str(row["sha256"]))
    same_url_same_modified=any(url and modified and len(hashes)>1 for (url,modified),hashes in by_identity.items())
    return {
        "whole_primary_observation_count":len(whole),
        "distinct_whole_primary_sha256_count":len(distinct),
        "distinct_whole_primary_sha256":distinct,
        "frozen_expected_hash_reproduced":any(x["sha256"]==expected_sha for x in whole),
        "same_url_same_last_modified_multiple_hashes":same_url_same_modified,
        "body_variants_are_separately_scoped":all(x.get("scope")!="whole_primary_document" for x in observations if x.get("scope") in {"raw_textblock_body","complete_submission_member","feed_archive"}),
    }

def validate_sensitivity_observations(sensitivity: dict[str,Any]) -> dict[str,Any]:
    """Validate the immutable five-response receipt without repeating any HTTP request."""
    if sensitivity.get("record_type")!="q220_http_representation_sensitivity":
        raise DiagnosticError("PINNED_SENSITIVITY_RECORD_TYPE_MISMATCH")
    if sensitivity.get("status")!="HTTP_REPRESENTATION_INVARIANT_AT_PROBE_TIME":
        raise DiagnosticError("PINNED_SENSITIVITY_STATUS_MISMATCH")
    if sensitivity.get("request_validation_passed") is not True or sensitivity.get("source_validation_passed") is not True:
        raise DiagnosticError("PINNED_SENSITIVITY_SOURCE_VALIDATION_FAILED")
    if sensitivity.get("requested_profile_count")!=SENSITIVITY_RESPONSE_COUNT or sensitivity.get("completed_request_count")!=SENSITIVITY_RESPONSE_COUNT:
        raise DiagnosticError("PINNED_SENSITIVITY_RESPONSE_COUNT_MISMATCH")
    if sensitivity.get("source_download_bytes")!=SENSITIVITY_BODY_BYTES*SENSITIVITY_RESPONSE_COUNT:
        raise DiagnosticError("PINNED_SENSITIVITY_DOWNLOAD_BYTES_MISMATCH")
    if sensitivity.get("source_receipt_fingerprint")!=SOURCE_RECEIPT_FP or sensitivity.get("source_population_receipt_fingerprint")!=POPULATION_FP:
        raise DiagnosticError("PINNED_SENSITIVITY_UPSTREAM_MISMATCH")
    if sensitivity.get("request_fingerprint")!=SENSITIVITY_REQUEST_FP:
        raise DiagnosticError("PINNED_SENSITIVITY_REQUEST_FINGERPRINT_MISMATCH")
    comparison=sensitivity.get("comparison",{})
    if (
        comparison.get("baseline_repeat_stable") is not True
        or comparison.get("profile_body_differences_observed")!=0
        or comparison.get("all_responses_complete_http_200") is not True
        or comparison.get("source_responses_share_same_requested_url") is not True
        or comparison.get("no_source_bodies_persisted") is not True
        or comparison.get("prior_expected_hash_match_count")!=0
    ):
        raise DiagnosticError("PINNED_SENSITIVITY_COMPARISON_CONTRACT_MISMATCH")
    profiles=sensitivity.get("response_profiles")
    expected_names={
        "population_baseline_first",
        "pit_user_agent_only",
        "pit_accept_only",
        "forensic_combined_profile",
        "population_baseline_repeat",
    }
    if not isinstance(profiles,list) or len(profiles)!=SENSITIVITY_RESPONSE_COUNT:
        raise DiagnosticError("PINNED_SENSITIVITY_PROFILE_LIST_INVALID")
    if {str(row.get("profile_name")) for row in profiles}!=expected_names:
        raise DiagnosticError("PINNED_SENSITIVITY_PROFILE_SET_MISMATCH")
    for row in profiles:
        if (
            row.get("status")!="FETCHED"
            or row.get("http_status")!=200
            or row.get("complete_http_200_response") is not True
            or row.get("response_sha256")!=SENSITIVITY_BODY_SHA
            or row.get("response_bytes")!=SENSITIVITY_BODY_BYTES
            or row.get("requested_url")!=PRIMARY_URL
            or row.get("final_url")!=PRIMARY_URL
            or row.get("last_modified")!=LAST_MODIFIED
            or "body" in row
        ):
            raise DiagnosticError("PINNED_SENSITIVITY_PROFILE_OBSERVATION_MISMATCH")
    return {
        "source":"http_sensitivity_probe_five_identical_responses",
        "scope":"whole_primary_document",
        "sha256":SENSITIVITY_BODY_SHA,
        "bytes":SENSITIVITY_BODY_BYTES,
        "url":PRIMARY_URL,
        "last_modified":LAST_MODIFIED,
        "replicate_count":SENSITIVITY_RESPONSE_COUNT,
        "probe_receipt_fingerprint":SENSITIVITY_FP,
    }


def build_analysis(compiler: dict[str,Any], forensics: dict[str,Any], header: dict[str,Any], sensitivity: dict[str,Any], single: dict[str,Any]) -> dict[str,Any]:
    if compiler.get("candidate_id")!="Q220" or compiler.get("status")!="Q220_HISTORICAL_REPRESENTATION_PIT_BLOCKED":
        raise DiagnosticError("CURRENT_COMPILER_NOT_BLOCKED_SOURCE")
    if compiler.get("receipt_fingerprint")!=COMPILER_FP or fp(compiler)!=COMPILER_FP:
        raise DiagnosticError("CURRENT_COMPILER_FINGERPRINT_MISMATCH")
    if compiler.get("source_population_receipt_fingerprint")!=POPULATION_FP or compiler.get("source_hash_failure_count")!=55 or compiler.get("verified_primary_document_count")!=0:
        raise DiagnosticError("COMPILER_SOURCE_POPULATION_CONTRACT_MISMATCH")
    if forensics.get("record_type")!="q220_original_sec_feed_primary_hash_forensics" or forensics.get("status")!="FORENSIC_COMPARISON_INCOMPLETE":
        raise DiagnosticError("PINNED_FORENSICS_RECEIPT_STATUS_MISMATCH")
    if forensics.get("receipt_fingerprint")!=FORENSICS_FP or fp(forensics)!=FORENSICS_FP:
        raise DiagnosticError("PINNED_FORENSICS_RECEIPT_FINGERPRINT_MISMATCH")
    if forensics.get("source_receipt_fingerprint")!=SOURCE_RECEIPT_FP or forensics.get("source_population_receipt_fingerprint")!=POPULATION_FP:
        raise DiagnosticError("PINNED_FORENSICS_UPSTREAM_MISMATCH")
    if header.get("record_type")!="q220_bounded_header_evidence" or header.get("status")!="HEADER_EVIDENCE_COMPLETE":
        raise DiagnosticError("PINNED_HEADER_RECEIPT_STATUS_MISMATCH")
    if header.get("receipt_fingerprint")!=HEADER_FP or fp(header)!=HEADER_FP:
        raise DiagnosticError("PINNED_HEADER_RECEIPT_FINGERPRINT_MISMATCH")
    if header.get("source_receipt_fingerprint")!=FORENSICS_FP or header.get("source_population_receipt_fingerprint")!=POPULATION_FP:
        raise DiagnosticError("PINNED_HEADER_UPSTREAM_MISMATCH")
    if header.get("no_feed_downloads") is not True or header.get("no_primary_document_downloads") is not True:
        raise DiagnosticError("HEADER_ONLY_SCOPE_NOT_PRESERVED")
    if sensitivity.get("receipt_fingerprint")!=SENSITIVITY_FP or fp(sensitivity)!=SENSITIVITY_FP:
        raise DiagnosticError("PINNED_SENSITIVITY_RECEIPT_FINGERPRINT_MISMATCH")
    sensitivity_observation=validate_sensitivity_observations(sensitivity)
    if single.get("candidate_id")!="Q220" or single.get("workflow_run_id")!=SINGLE_FEED_RUN_ID:
        raise DiagnosticError("SINGLE_FEED_SOURCE_IDENTITY_MISMATCH")
    fs=single.get("frozen_source",{})
    if fs.get("source_receipt_fingerprint")!=SOURCE_RECEIPT_FP or fs.get("population_receipt_fingerprint")!=POPULATION_FP or fs.get("record_key")!=RECORD_KEY:
        raise DiagnosticError("SINGLE_FEED_FROZEN_SAMPLE_MISMATCH")
    if fs.get("expected_sha256")!=EXPECTED_SHA or fs.get("expected_bytes")!=EXPECTED_BYTES:
        raise DiagnosticError("SINGLE_FEED_EXPECTED_HASH_MISMATCH")
    ff=next((x for x in forensics.get("samples",[]) if x.get("record_key")==RECORD_KEY),None)
    if not ff: raise DiagnosticError("FORENSICS_FROZEN_SAMPLE_MISSING")
    comp=next((x for x in compiler.get("source_hash_failures",[]) if x.get("record_key")==RECORD_KEY),None)
    if not comp: raise DiagnosticError("CURRENT_COMPILER_FROZEN_SAMPLE_MISSING")
    err=str(comp.get("error") or "")
    match=re.search(r"expected=([0-9a-f]{64}).*actual=([0-9a-f]{64}).*expected_bytes=(\d+):actual_bytes=(\d+)",err)
    if not match or match.group(1)!=EXPECTED_SHA or int(match.group(3))!=EXPECTED_BYTES:
        raise DiagnosticError("CURRENT_COMPILER_HASH_DIAGNOSTIC_SHAPE_MISMATCH")
    if ("last_modified=Wed, 13 Feb 2019 11_02_53 GMT" not in err
        or "primary=spgi-20181231x10k.htm" not in err
        or "final_url=https_//www.sec.gov/Archives/edgar/data/64040/000006404019000059/spgi-20181231x10k.htm" not in err):
        raise DiagnosticError("CURRENT_COMPILER_HTTP_METADATA_MISMATCH")
    original=ff.get("current_primary",{})
    feed=ff.get("daily_feed",{})
    primary=feed.get("primary",{})
    current=single.get("bounded_run",{})
    if (
        original.get("response_sha256")!="08039132d6d6d1692d1f7552193c70a04cad4c1dcadad1cfa3ca2b8b4efe3fdb"
        or original.get("response_bytes")!=EXPECTED_BYTES
        or current.get("current_primary_sha256")!="2693819652172f0c218394ef036eb3f4af95c2a7077f624f6efcd990df370172"
        or current.get("current_primary_response_bytes")!=4774465
        or current.get("current_primary_last_modified")!=LAST_MODIFIED
        or original.get("last_modified")!=LAST_MODIFIED
        or original.get("final_url")!=PRIMARY_URL
        or current.get("current_primary_http_status")!=200
    ):
        raise DiagnosticError("OBSERVED_PRIMARY_BODY_LINEAGE_CHANGED")
    observations=[
        {"source":"frozen_expected_primary_document","scope":"frozen_expected_value","sha256":EXPECTED_SHA,"bytes":EXPECTED_BYTES,"url":PRIMARY_URL,"last_modified":LAST_MODIFIED},
        {"source":"original_forensics_current_primary","scope":"whole_primary_document","sha256":original["response_sha256"],"bytes":original["response_bytes"],"url":original["final_url"],"last_modified":original["last_modified"]},
        sensitivity_observation,
        {"source":"current_compiler_observation","scope":"whole_primary_document","sha256":match.group(2),"bytes":int(match.group(4)),"url":PRIMARY_URL,"last_modified":LAST_MODIFIED},
        {"source":"single_feed_boundary_later_primary_response","scope":"whole_primary_document","sha256":current["current_primary_sha256"],"bytes":current["current_primary_response_bytes"],"url":PRIMARY_URL,"last_modified":current["current_primary_last_modified"]},
        {"source":"original_daily_feed_submission_member","scope":"complete_submission_member","sha256":feed.get("original_member_sha256"),"bytes":feed.get("original_member_bytes"),"url":feed.get("final_url"),"last_modified":feed.get("last_modified")},
        {"source":"raw_textblock_extraction","scope":"raw_textblock_body","sha256":primary.get("raw_text_block_sha256"),"bytes":primary.get("raw_text_block_bytes"),"url":None,"last_modified":None},
        {"source":"raw_textblock_variant_drop_leading_linebreak","scope":"raw_textblock_body","sha256":primary.get("body_hash_variants",{}).get("drop_one_leading_linebreak",{}).get("sha256"),"bytes":primary.get("body_hash_variants",{}).get("drop_one_leading_linebreak",{}).get("bytes"),"url":None,"last_modified":None},
        {"source":"raw_textblock_variant_drop_outer_linebreaks","scope":"raw_textblock_body","sha256":primary.get("body_hash_variants",{}).get("drop_outer_linebreaks",{}).get("sha256"),"bytes":primary.get("body_hash_variants",{}).get("drop_outer_linebreaks",{}).get("bytes"),"url":None,"last_modified":None},
    ]
    if observations[5]["sha256"]!="e73d211f2bb02f099d9a8559735fb627678d7db0e3b11ae491eb80ae2b45fa54":
        raise DiagnosticError("COMPLETE_SUBMISSION_MEMBER_HASH_CHANGED")
    if observations[6]["sha256"]!="aa1f89efdf13029de9dd8f7eb020502dd518d4350513d4ef041ba67d902ef368":
        raise DiagnosticError("TEXTBLOCK_VARIANT_HASH_CHANGED")
    classification=classify_primary_hashes(EXPECTED_SHA,observations)
    if classification["frozen_expected_hash_reproduced"] is not False or classification["distinct_whole_primary_sha256_count"]!=4 or classification["same_url_same_last_modified_multiple_hashes"] is not True:
        raise DiagnosticError("PRIMARY_HASH_CLASSIFICATION_CONTRACT_MISMATCH")
    core={
        "schema_version":1,"record_type":"q220_offline_source_hash_lineage_diagnostic",
        "candidate_id":"Q220","status":"Q220_SOURCE_HASH_LINEAGE_UNRESOLVED_MULTIPLE_OBSERVED_HASHES",
        "source_receipts":{
            "compiler_receipt_fingerprint":COMPILER_FP,"compiler_source_population_fingerprint":POPULATION_FP,
            "frozen_fixture_receipt_fingerprint":SOURCE_RECEIPT_FP,
            "forensics_run_id":FORENSICS_RUN_ID,"forensics_artifact_id":FORENSICS_ARTIFACT_ID,
            "forensics_artifact_name":FORENSICS_ARTIFACT_NAME,"forensics_receipt_fingerprint":FORENSICS_FP,
            "header_run_id":HEADER_RUN_ID,"header_artifact_id":HEADER_ARTIFACT_ID,
            "header_artifact_name":HEADER_ARTIFACT_NAME,"header_receipt_fingerprint":HEADER_FP,
            "sensitivity_run_id":SENSITIVITY_RUN_ID,"sensitivity_artifact_id":SENSITIVITY_ARTIFACT_ID,
            "sensitivity_artifact_name":SENSITIVITY_ARTIFACT_NAME,"sensitivity_receipt_fingerprint":SENSITIVITY_FP,
            "sensitivity_request_fingerprint":SENSITIVITY_REQUEST_FP,
            "single_feed_run_id":SINGLE_FEED_RUN_ID,"single_feed_artifact_id":SINGLE_FEED_ARTIFACT_ID,
            "single_feed_summary_upstream_fingerprint":single.get("upstream_receipt_fingerprint"),
        },
        "record_key":RECORD_KEY,"observations":observations,"classification":classification,
        "header_context":{
            "header_receipt_source_download_bytes":header.get("source_download_bytes"),
            "header_receipt_no_feed_downloads":header.get("no_feed_downloads"),
            "header_receipt_no_primary_document_downloads":header.get("no_primary_document_downloads"),
            "acceptance_clock_proves_body_vintage":False,
        },
        "interpretation_scope":{
            "diagnostic_only":True,"source_vintage_proven":False,"frozen_hash_reproduced":False,
            "expected_hash_changed":False,"feed_archive_downloaded_by_this_diagnostic":False,
            "primary_document_downloaded_by_this_diagnostic":False,"source_receipts_modified":False,
            "gate_positive":False,"scientific_evidence":False,"performance_authorization":False,
            "holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False,
        },
        "next_gate":"Identify an authoritative pinned source-vintage record or preserve the blocked state. Do not fetch another Feed/primary document, rewrite expected hashes, or re-run the census to force a match.",
        "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},
    }
    core["analysis_fingerprint"]=sha(json.dumps(core,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8"))
    return core

def run(repo_root: Path, forensics_dir: Path, header_dir: Path, sensitivity_dir: Path, output: Path, expected_analysis_fingerprint: str|None=None) -> dict[str,Any]:
    compiler=read_json(repo_root/"research/evidence/q220_historical_representation_pit_latest.json")
    single=read_json(repo_root/"research/evidence/q220_single_feed_boundary_validation_2026_10_13_summary.json")
    forensics=read_json(find_receipt(forensics_dir))
    header=read_json(find_receipt(header_dir))
    sensitivity=read_json(find_receipt(sensitivity_dir))
    core=build_analysis(compiler,forensics,header,sensitivity,single)
    if expected_analysis_fingerprint and core["analysis_fingerprint"]!=expected_analysis_fingerprint:
        raise DiagnosticError("CROSS_ARCH_ANALYSIS_FINGERPRINT_MISMATCH")
    result={**core,"generated_at_utc":datetime.now(timezone.utc).isoformat()}
    result["receipt_fingerprint"]=fp(result)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"analysis_fingerprint":result["analysis_fingerprint"],"receipt_fingerprint":result["receipt_fingerprint"],"classification":result["classification"]},sort_keys=True))
    return result

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,default=Path.cwd())
    ap.add_argument("--forensics-artifact",type=Path,required=True)
    ap.add_argument("--header-artifact",type=Path,required=True)
    ap.add_argument("--sensitivity-artifact",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--expected-analysis-fingerprint",default=None)
    a=ap.parse_args()
    run(a.repo_root,a.forensics_artifact,a.header_artifact,a.sensitivity_artifact,a.output,a.expected_analysis_fingerprint)
    return 0
if __name__=="__main__": raise SystemExit(main())
