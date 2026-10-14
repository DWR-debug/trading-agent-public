"""Bounded header-only date-change capture for the six frozen Q104:I19 R3 rows.

The R3 source/archive receipt is immutable. This probe only re-reads official EDGAR
header routes to capture DATE-OF-FILING-DATE-CHANGE, which the R3 report did not
record. It downloads no filing body, archive, bulk file, or primary document.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SOURCE_RUN_ID = "38532233135"
SOURCE_ARTIFACT_NAME = "q104-i19-residual-lineage-r3-38532233135-1"
SOURCE_RECEIPT_FP = "f4c309fe9f5389fdd726fbdb9aa969a46e376d1bd212c3654cc7ec1a6682015a"
SOURCE_CENSUS_RUN_ID = "38168441086"
ARCHIVE_NAME = "2016q4_form13f.zip"
ARCHIVE_BYTES = 41801560
ARCHIVE_SHA256 = "40dea4a7e1e7d7ba118ffed32ab1941e365a2835d748e7ae682af8b1dc8f1be4"
MAX_RESPONSE_BYTES = 262_144
MAX_TOTAL_BYTES = 8_000_000
REQUEST_GAP_SECONDS = 1.0
TIMEOUT_SECONDS = 30
USER_AGENT = "DWR-debug/trading-agent-public Q104 R3 date-change header probe/1.0"

EXPECTED = {
    "0000950123-16-022491": {"cik":"0000896159","bulk_date":"2016-11-15","header_date":"2016-11-14","acceptance":"2016-11-14T17:49:15"},
    "0000950123-16-022512": {"cik":"0000732905","bulk_date":"2016-11-15","header_date":"2016-11-14","acceptance":"2016-11-14T18:06:11"},
    "0001138060-16-000026": {"cik":"0001138060","bulk_date":"2016-11-15","header_date":"2016-11-14","acceptance":"2016-11-14T17:51:19"},
    "0001144204-16-134468": {"cik":"0001317583","bulk_date":"2016-11-15","header_date":"2016-11-14","acceptance":"2016-11-14T18:36:53"},
    "0001144204-16-134474": {"cik":"0001502976","bulk_date":"2016-11-15","header_date":"2016-11-14","acceptance":"2016-11-14T18:40:51"},
    "0001352900-16-000030": {"cik":"0001352900","bulk_date":"2016-11-15","header_date":"2016-11-14","acceptance":"2016-11-14T17:52:59"},
}
ROUTES = ("index_headers","raw_sgml_header","complete_submission_header_prefix")


class ProbeError(ValueError):
    pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def fingerprint(value: dict[str, Any], field: str = "receipt_fingerprint") -> str:
    payload = dict(value)
    payload.pop(field, None)
    raw = json.dumps(payload, sort_keys=True, separators=(",",":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return sha256(raw)


def find_receipt(root: Path) -> Path:
    if root.is_file():
        return root
    found = sorted(root.rglob("receipt.json"))
    if len(found) != 1:
        raise ProbeError(f"R3_SOURCE_RECEIPT_COUNT_INVALID:{len(found)}")
    return found[0]


def validate_source(root: Path) -> dict[str, Any]:
    source_path = find_receipt(root)
    source = json.loads(source_path.read_text(encoding="utf-8"))
    if source.get("record_type") != "q104_i19_residual_source_lineage_diagnostic_r3":
        raise ProbeError("R3_SOURCE_RECORD_TYPE_MISMATCH")
    if source.get("status") != "LINEAGE_DIAGNOSTIC_COMPLETE":
        raise ProbeError("R3_SOURCE_STATUS_NOT_COMPLETE")
    if source.get("source_run_id") != SOURCE_CENSUS_RUN_ID:
        raise ProbeError("R3_SOURCE_CENSUS_RUN_MISMATCH")
    if source.get("receipt_fingerprint") != SOURCE_RECEIPT_FP or fingerprint(source) != SOURCE_RECEIPT_FP:
        raise ProbeError("R3_SOURCE_RECEIPT_FINGERPRINT_MISMATCH")
    archive = source.get("pinned_archives", {}).get(ARCHIVE_NAME, {})
    if not (
        archive.get("archive_verified") is True
        and archive.get("archive_sha256_match") is True
        and archive.get("archive_bytes_match") is True
        and archive.get("expected_bytes") == ARCHIVE_BYTES
        and archive.get("expected_sha256") == ARCHIVE_SHA256
    ):
        raise ProbeError("R3_FROZEN_ARCHIVE_PIN_MISMATCH")
    samples = source.get("samples", [])
    if len(samples) != len(EXPECTED) or {x.get("accession") for x in samples} != set(EXPECTED):
        raise ProbeError("R3_FROZEN_SAMPLE_SET_MISMATCH")
    for sample in samples:
        accession = sample["accession"]
        expected = EXPECTED[accession]
        row = sample.get("source_row") or {}
        if not (
            sample.get("status") == "OBSERVED"
            and sample.get("archive_name") == ARCHIVE_NAME
            and sample.get("archive_sha256_match") is True
            and sample.get("frozen_failure") == "FILING_DATE_MISMATCH"
            and row.get("accession") == accession
            and row.get("filer_cik") == expected["cik"]
            and row.get("filing_date_iso") == expected["bulk_date"]
            and row.get("form") == "13F-HR"
        ):
            raise ProbeError("R3_FROZEN_SAMPLE_ROW_MISMATCH:" + accession)
        prior = {p.get("route"):p.get("observed_identity") or {} for p in sample.get("probes", [])}
        if set(prior) != set(ROUTES):
            raise ProbeError("R3_PRIOR_ROUTE_SET_MISMATCH:" + accession)
        for route, observed in prior.items():
            if (
                observed.get("accession") != accession
                or str(observed.get("filer_cik","")).zfill(10) != expected["cik"]
                or observed.get("filing_date") != expected["header_date"]
                or observed.get("acceptance_datetime") != expected["acceptance"]
                or (observed.get("form") and observed.get("form") != "13F-HR")
            ):
                raise ProbeError(f"R3_PRIOR_HEADER_OBSERVATION_MISMATCH:{accession}:{route}")
    return source


def parse_header_fields(raw: bytes, route: str) -> dict[str, str | None]:
    text = raw.decode("utf-8", errors="replace")

    def first(patterns: tuple[str, ...]) -> str | None:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return None

    accession = first((
        r"<ACCESSION-NUMBER>\s*([0-9-]{18,25})",
        r"ACCESSION NUMBER:\s*([0-9-]{18,25})",
    ))
    filer = re.search(r"<FILER>.*?<CIK>\s*(\d{1,10})", text, re.IGNORECASE | re.DOTALL)
    cik = filer.group(1) if filer else first((r"CENTRAL INDEX KEY:\s*(\d{1,10})", r"<CIK>\s*(\d{1,10})"))
    form = first((r"<CONFORMED-SUBMISSION-TYPE>\s*([A-Z0-9/-]+)", r"CONFORMED SUBMISSION TYPE:\s*([A-Z0-9/-]+)"))
    filed = first((r"<FILING-DATE>\s*(\d{8})", r"FILED AS OF DATE:\s*(\d{8})", r"FILING DATE:\s*(\d{4}-\d{2}-\d{2})"))
    change = first((
        r"<DATE-OF-FILING-DATE-CHANGE>\s*(\d{8})",
        r"DATE OF FILING DATE CHANGE:\s*(\d{8})",
        r"DATE OF FILING DATE CHANGE:\s*(\d{4}-\d{2}-\d{2})",
    ))
    acceptance = first((r"<ACCEPTANCE-DATETIME>\s*(\d{14})",))
    if not acceptance:
        date_part = first((r"<ACCEPTANCE-DATE>\s*(\d{8})",))
        time_part = first((r"<ACCEPTANCE-TIME>\s*(\d{6})",))
        if date_part and time_part:
            acceptance = date_part + time_part
    def normal_date(value: str | None) -> str | None:
        if not value:
            return None
        value = value.strip()
        return f"{value[:4]}-{value[4:6]}-{value[6:8]}" if re.fullmatch(r"\d{8}", value) else value
    if acceptance and re.fullmatch(r"\d{14}", acceptance):
        acceptance = f"{acceptance[:4]}-{acceptance[4:6]}-{acceptance[6:8]}T{acceptance[8:10]}:{acceptance[10:12]}:{acceptance[12:14]}"
    return {
        "route": route,
        "accession": accession,
        "filer_cik": str(cik).zfill(10) if cik else None,
        "form": form.upper() if form else None,
        "filing_date": normal_date(filed),
        "date_of_filing_date_change": normal_date(change),
        "acceptance_datetime": acceptance,
    }


class Budget:
    def __init__(self) -> None:
        self.used = 0
        self.next_request_at = 0.0

    def wait(self) -> None:
        delay = self.next_request_at - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        self.next_request_at = time.monotonic() + REQUEST_GAP_SECONDS

    def add(self, count: int) -> None:
        if count < 0 or self.used + count > MAX_TOTAL_BYTES:
            raise ProbeError("TOTAL_HEADER_RESPONSE_BUDGET_EXCEEDED")
        self.used += count


def fetch_header(url: str, route: str, budget: Budget, marker: bytes | None = None) -> dict[str, Any]:
    budget.wait()
    request = urllib.request.Request(
        url,
        headers={"User-Agent":USER_AGENT,"Accept":"text/html,text/plain,*/*","Accept-Encoding":"identity","Connection":"close"},
        method="GET",
    )
    result: dict[str, Any] = {"route":route,"requested_url":url,"http_status":None,"status":"FAILED","response_bytes":0}
    body = bytearray()
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            result.update({"http_status":int(getattr(response,"status",200)),"content_type":str(response.headers.get("Content-Type","")),"last_modified":str(response.headers.get("Last-Modified","")),"etag":str(response.headers.get("ETag",""))})
            while len(body) <= MAX_RESPONSE_BYTES:
                count = min(8192, MAX_RESPONSE_BYTES + 1 - len(body))
                chunk = response.read(count)
                if not chunk:
                    break
                body.extend(chunk)
                if marker and marker in body:
                    break
            if len(body) > MAX_RESPONSE_BYTES:
                result["status"] = "RESPONSE_OVER_LIMIT"
                return result
            budget.add(len(body))
            raw = bytes(body)
            result.update({"response_bytes":len(raw),"response_sha256":sha256(raw),"observed_fields":parse_header_fields(raw,route)})
            result["status"] = "FETCHED_PREFIX" if marker and marker in raw else "FETCHED"
            if marker and marker not in raw:
                result["status"] = "PREFIX_MARKER_NOT_FOUND"
            return result
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            result["status"] = "HTTP_ERROR_BODY_OVER_LIMIT"
            return result
        budget.add(len(raw))
        result.update({"status":"HTTP_ERROR","http_status":int(exc.code),"response_bytes":len(raw),"response_sha256":sha256(raw)})
        return result
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        result.update({"status":"TRANSPORT_ERROR","error_type":type(exc).__name__})
        return result


def validate_sample_observations(accession: str, probes: list[dict[str, Any]]) -> tuple[bool, dict[str, Any]]:
    expected = EXPECTED[accession]
    by_route = {x.get("route"):x for x in probes}
    if set(by_route) != set(ROUTES):
        return False, {"reason":"ROUTE_SET_MISMATCH"}
    all_identity = True
    for route, probe in by_route.items():
        obs = probe.get("observed_fields") or {}
        if probe.get("http_status") != 200 or probe.get("status") not in {"FETCHED","FETCHED_PREFIX"}:
            all_identity = False
        if (
            obs.get("accession") != accession
            or obs.get("filer_cik") != expected["cik"]
            or obs.get("filing_date") != expected["header_date"]
            or obs.get("acceptance_datetime") != expected["acceptance"]
            or (obs.get("form") and obs.get("form") != "13F-HR")
        ):
            all_identity = False
    present_changes = [((x.get("observed_fields") or {}).get("date_of_filing_date_change")) for x in probes]
    present_changes = [x for x in present_changes if x]
    distinct = sorted(set(present_changes))
    return all_identity and len(distinct) <= 1, {
        "all_three_routes_identity_filed_date_acceptance_agree": all_identity,
        "date_change_route_values": present_changes,
        "date_change_distinct_value_count": len(distinct),
        "date_change_routes_agree_where_observed": len(distinct) <= 1,
        "date_change_observed": bool(present_changes),
        "date_change_equals_edgar_filing_date": (present_changes[0] == expected["header_date"]) if present_changes and len(distinct)==1 else None,
    }


def run(source_root: Path, output: Path) -> dict[str, Any]:
    source = validate_source(source_root)
    old_samples = {x["accession"]:x for x in source["samples"]}
    budget = Budget()
    samples = []
    complete = True
    for accession, expected in EXPECTED.items():
        base = f"https://www.sec.gov/Archives/edgar/data/{int(expected['cik'])}/{accession.replace('-','')}"
        routes = (
            ("index_headers",f"{base}/{accession}-index-headers.html",None),
            ("raw_sgml_header",f"{base}/{accession}.hdr.sgml",None),
            ("complete_submission_header_prefix",f"{base}/{accession}.txt",b"</SEC-HEADER>"),
        )
        probes = [fetch_header(url,route,budget,marker) for route,url,marker in routes]
        ok, checks = validate_sample_observations(accession,probes)
        complete = complete and ok
        samples.append({
            "accession":accession,"cik":expected["cik"],"bulk_filing_date":expected["bulk_date"],
            "pinned_edgar_filing_date":expected["header_date"],"pinned_acceptance_datetime":expected["acceptance"],
            "prior_r3_header_observations":[
                {"route":p.get("route"),"response_sha256":p.get("response_sha256"),"observed_identity":p.get("observed_identity")}
                for p in old_samples[accession].get("probes",[])
            ],
            "probes":probes,"checks":checks,
            "interpretation":"header-only observation; source precedence and PIT gates unchanged",
        })
    result = {
        "schema_version":1,
        "record_type":"q104_i19_r3_date_change_header_probe",
        "status":"R3_DATE_CHANGE_HEADER_PROBE_COMPLETE" if complete and len(samples)==6 and budget.used<=MAX_TOTAL_BYTES else "R3_DATE_CHANGE_HEADER_PROBE_INCOMPLETE",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "source_run_id":SOURCE_RUN_ID,"source_artifact_name":SOURCE_ARTIFACT_NAME,
        "source_receipt_fingerprint":SOURCE_RECEIPT_FP,"source_census_run_id":SOURCE_CENSUS_RUN_ID,
        "source_archive_name":ARCHIVE_NAME,"source_archive_bytes":ARCHIVE_BYTES,"source_archive_sha256":ARCHIVE_SHA256,
        "source_sample_count":len(samples),"probe_count_expected":18,
        "probe_count_captured":sum(len(x["probes"]) for x in samples),
        "response_bytes":budget.used,"response_budget_bytes":MAX_TOTAL_BYTES,
        "max_response_bytes":MAX_RESPONSE_BYTES,"request_gap_seconds":REQUEST_GAP_SECONDS,
        "archive_downloads":0,"primary_document_downloads":0,
        "samples":samples,"source_precedence_applied":False,"acceptance_time_gate_cleared":False,
        "historical_archive_gate_cleared":False,"performance_authorization":False,
        "holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False,
        "safety":{"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False},
        "next_gate":"Combine these six date-change observations with the pinned eight-row R1/R2 field probe. No date arithmetic or precedence application.",
    }
    result["analysis_fingerprint"] = fingerprint(result, "analysis_fingerprint")
    result["receipt_fingerprint"] = fingerprint(result)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"receipt_fingerprint":result["receipt_fingerprint"],"analysis_fingerprint":result["analysis_fingerprint"],"probe_count_captured":result["probe_count_captured"],"response_bytes":budget.used},sort_keys=True))
    if result["status"] != "R3_DATE_CHANGE_HEADER_PROBE_COMPLETE":
        raise ProbeError("R3_DATE_CHANGE_HEADER_PROBE_INCOMPLETE")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-artifact",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args = ap.parse_args()
    run(args.source_artifact,args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
