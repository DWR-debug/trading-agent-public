"""Bounded, source-first pilot for pre-event Q221 recipient/entity links.

The pilot captures six official SEC pages and one official Northrop Grumman
release for three already-frozen Q221 transaction keys. It does not map issuers,
change the 348-row universe, or prove first-public timestamps or legal continuity
through the event date. All scientific/performance/live-execution gates stay shut.
"""
from __future__ import annotations

import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUEST_PATH = "research/run_requests/q221_pre_event_identity_bridge_pilot.trigger"
PREREG_PATH = "research/preregistrations/q221_pre_event_identity_bridge_pilot_2026_10_15.json"
MANIFEST_PATH = "research/evidence/q221_historical_public_boundary_latest.json"
MANIFEST_BLOB_SHA1 = "b78cf6f7b48af3f914ee7c6d06a38f6485b0438f"
MANIFEST_FP = "9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4"
PARENT_MAP_RUN_ID = 38305074104
PARENT_MAP_HEAD_SHA = "179aab94f12bf15aff05a4fea7010872d8fa8317"
PARENT_MAP_ARTIFACT_ID = 11772786096
PARENT_MAP_ARTIFACT_NAME = "q221-current-parent-identity-map-38305074104-1"
PARENT_MAP_RAW_SHA256 = "5f62867c8153fc03dec7d2d983f9017d9014e829e5cfcdf1729579539db4c0f0"
PARENT_MAP_FP = "ae3a3263d5e7d2545dbdaed7ba7ff1cfe3d4cd00e0403352096dcce4d4797602"
SUMMARY_PATH = "research/evidence/q221_current_parent_identity_map_summary_2026_10_12.json"
SUMMARY_FP = "444179ed66cb0560ca792d2b831144c89165f46f19095a15456e21db7b18623a"

MAX_BYTES_PER_SOURCE = 300_000
MAX_TOTAL_BYTES = 900_000
TIMEOUT_SECONDS = 30
REQUEST_GAP_SECONDS = 1.0
USER_AGENT = "DWR-debug/trading-agent-public Q221 pre-event identity bridge pilot/1.0"

TRANSACTIONS = {
    "CACI_2019": {
        "transaction_key": "FA875018C0180|P00003|2019-01-03|28eee911-76af-7147-f760-4ec5f90bec2d-C|N3PBJAVNKF61",
        "action_date": "2019-01-03",
        "recipient_name": "CACI, INC. - FEDERAL",
        "recipient_id": "28eee911-76af-7147-f760-4ec5f90bec2d-C",
        "recipient_uei": "N3PBJAVNKF61",
        "current_parent_name": "CACI INTERNATIONAL INC",
        "current_parent_uei": "QSRTXLFKV857",
    },
    "AURORA_2024": {
        "transaction_key": "HR001123C0013|P00006|2024-01-02|23c9b680-370f-e3eb-79d0-f1afc23e13fc-C|K1L1BZLNPWC4",
        "action_date": "2024-01-02",
        "recipient_name": "AURORA FLIGHT SCIENCES CORPORATION",
        "recipient_id": "23c9b680-370f-e3eb-79d0-f1afc23e13fc-C",
        "recipient_uei": "K1L1BZLNPWC4",
        "current_parent_name": "THE BOEING COMPANY",
        "current_parent_uei": "ZE95AC36GJ76",
    },
    "ATK_2019": {
        "transaction_key": "FA930018FD001|P00004|2019-01-03|1a27c4e3-c0a0-5d50-3277-128bfbd90200-C|GRJJTMCRKJD1",
        "action_date": "2019-01-03",
        "recipient_name": "ATK LAUNCH SYSTEMS LLC",
        "recipient_id": "1a27c4e3-c0a0-5d50-3277-128bfbd90200-C",
        "recipient_uei": "GRJJTMCRKJD1",
        "current_parent_name": "NORTHROP GRUMMAN INNOVATION SYSTEMS LLC",
        "current_parent_uei": "GJVCPEBZV574",
    },
}

SOURCES = (
    {
        "id": "caci_index",
        "url": "https://www.sec.gov/Archives/edgar/data/16058/000156459018022021/0001564590-18-022021-index.htm",
        "allowed_host": "www.sec.gov",
        "required_tokens": [
            "0001564590-18-022021",
            "2018-08-20",
            "2018-08-20 15:13:34",
            "caci-ex211_14.htm",
            "caci international inc",
        ],
    },
    {
        "id": "caci_ex21",
        "url": "https://www.sec.gov/Archives/edgar/data/16058/000156459018022021/caci-ex211_14.htm",
        "allowed_host": "www.sec.gov",
        "required_tokens": [
            "significant subsidiaries of the registrant",
            "caci, inc. - federal",
            "a delaware corporation",
        ],
    },
    {
        "id": "aurora_index",
        "url": "https://www.sec.gov/Archives/edgar/data/1706946/000170694622000124/0001706946-22-000124-index.htm",
        "allowed_host": "www.sec.gov",
        "required_tokens": [
            "0001706946-22-000124",
            "2022-08-04",
            "2022-08-04 16:10:40",
            "a101auroramasteragreement.htm",
        ],
    },
    {
        "id": "aurora_agreement",
        "url": "https://www.sec.gov/Archives/edgar/data/1706946/000170694622000124/a101auroramasteragreement.htm",
        "allowed_host": "www.sec.gov",
        "required_tokens": [
            "made as of july 4, 2022",
            "aurora flight sciences corporation",
            "wholly owned subsidiary of the boeing company",
        ],
    },
    {
        "id": "orbital_index",
        "url": "https://www.sec.gov/Archives/edgar/data/866121/000086612117000027/0000866121-17-000027-index.htm",
        "allowed_host": "www.sec.gov",
        "required_tokens": [
            "0000866121-17-000027",
            "2017-04-28",
            "oa-ex21x20161231.htm",
        ],
    },
    {
        "id": "orbital_ex21",
        "url": "https://www.sec.gov/Archives/edgar/data/866121/000086612117000027/oa-ex21x20161231.htm",
        "allowed_host": "www.sec.gov",
        "required_tokens": [
            "subsidiaries of orbital atk, inc.",
            "all subsidiaries listed below are 100% owned except joint ventures",
            "atk launch systems inc.",
        ],
    },
    {
        "id": "northrop_release",
        "url": "https://investor.northropgrumman.com/news-releases/news-release-details/northrop-grumman-completes-orbital-atk-acquisition-blake-larson",
        "allowed_host": "investor.northropgrumman.com",
        "required_tokens": [
            "june 6, 2018",
            "has closed the acquisition of orbital atk inc.",
            "orbital atk is now northrop grumman innovation systems",
        ],
    },
)
SOURCE_BY_ID = {x["id"]: x for x in SOURCES}

# Only the specified source endpoints may be fetched. This is enforced before
# any request is issued; tests exercise the fixed allowlist.
ALLOWED_URLS = {x["url"] for x in SOURCES}


class PilotError(ValueError):
    """A frozen input, source response, byte bound, or reproduction is invalid."""


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._hidden_depth:
            self._hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._hidden_depth:
            self.parts.append(data)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def canonical_fingerprint(value: dict[str, Any], field: str = "receipt_fingerprint") -> str:
    payload = dict(value)
    payload.pop(field, None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return sha256(encoded)


def normalize_text(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace")
    parser = VisibleTextParser()
    parser.feed(text)
    visible = html.unescape(" ".join(parser.parts))
    visible = visible.replace("\u00a0", " ")
    for dash in ("\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"):
        visible = visible.replace(dash, "-")
    return " ".join(visible.lower().split())


def find_receipt(directory: Path, exact_name: str) -> Path:
    if directory.is_file():
        return directory
    if not directory.is_dir():
        raise PilotError(f"INPUT_DIRECTORY_MISSING:{directory}")
    matches = sorted(directory.rglob(exact_name))
    if len(matches) != 1:
        raise PilotError(f"INPUT_RECEIPT_COUNT_INVALID:{exact_name}:{len(matches)}")
    return matches[0]


def read_pinned_manifest(repo_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = repo_root / MANIFEST_PATH
    raw = path.read_bytes()
    if git_blob_sha1(raw) != MANIFEST_BLOB_SHA1:
        raise PilotError("Q221_FROZEN_MANIFEST_GIT_BLOB_SHA_MISMATCH")
    manifest = json.loads(raw.decode("utf-8"))
    if canonical_fingerprint(manifest) != MANIFEST_FP:
        raise PilotError("Q221_FROZEN_MANIFEST_FINGERPRINT_MISMATCH")
    if (
        manifest.get("candidate_id") != "Q221"
        or manifest.get("status") != "Q221_HISTORICAL_AWARD_SAMPLE_CAPTURED_PUBLIC_BOUNDARY_UNPROVEN"
        or manifest.get("receipt_fingerprint") != MANIFEST_FP
        or manifest.get("sampled_transaction_count") != 348
        or manifest.get("gate_positive") is not False
        or manifest.get("historical_first_public_observation_proven") is not False
        or manifest.get("recipient_to_issuer_mapping_frozen") is not False
    ):
        raise PilotError("Q221_FROZEN_MANIFEST_STATE_OR_GATE_MISMATCH")
    rows = manifest.get("transactions")
    if not isinstance(rows, list) or len(rows) != 348:
        raise PilotError("Q221_FROZEN_MANIFEST_ROW_COUNT_MISMATCH")
    by_key = {str(row.get("transaction_key") or ""): row for row in rows}
    if len(by_key) != 348:
        raise PilotError("Q221_FROZEN_MANIFEST_DUPLICATE_TRANSACTION_KEY")
    for row_id, expected in TRANSACTIONS.items():
        row = by_key.get(expected["transaction_key"])
        if not isinstance(row, dict):
            raise PilotError(f"Q221_FROZEN_TARGET_KEY_MISSING:{row_id}")
        for field in ("action_date", "recipient_name", "recipient_id", "recipient_uei"):
            if str(row.get(field) or "") != expected[field]:
                raise PilotError(f"Q221_FROZEN_TARGET_FIELD_MISMATCH:{row_id}:{field}")
        if row.get("issuer_symbol") is not None:
            raise PilotError(f"Q221_FROZEN_TARGET_ALREADY_MAPPED:{row_id}")
        if row.get("recipient_to_issuer_status") != "UNMAPPED_NO_FROZEN_PRE_EVENT_IDENTITY_RECEIPT":
            raise PilotError(f"Q221_FROZEN_TARGET_MAPPING_STATE_CHANGED:{row_id}")
    return manifest, [by_key[x["transaction_key"]] for x in TRANSACTIONS.values()]


def read_pinned_parent_map(directory: Path, manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    path = find_receipt(directory, "q221-current-parent-identity-map-receipt.json")
    raw = path.read_bytes()
    if sha256(raw) != PARENT_MAP_RAW_SHA256:
        raise PilotError("Q221_PARENT_MAP_RAW_SHA256_MISMATCH")
    payload = json.loads(raw.decode("utf-8"))
    if canonical_fingerprint(payload) != PARENT_MAP_FP:
        raise PilotError("Q221_PARENT_MAP_RECEIPT_FINGERPRINT_MISMATCH")
    if (
        payload.get("candidate_id") != "Q221"
        or payload.get("record_type") != "q221_current_parent_identity_lead_map"
        or payload.get("status") != "CURRENT_PARENT_MAP_COMPLETE_HISTORY_UNPROVEN"
        or payload.get("receipt_fingerprint") != PARENT_MAP_FP
        or payload.get("source_receipt_git_blob_sha") != MANIFEST_BLOB_SHA1
        or payload.get("source_receipt_fingerprint") != MANIFEST_FP
        or payload.get("recipient_count_expected") != 247
        or payload.get("recipient_count_captured") != 247
        or payload.get("query_count_expected") != 247
        or payload.get("query_count_captured") != 247
        or payload.get("verified_profile_count") != 247
        or payload.get("current_parent_classification_counts") != {
            "CURRENT_PARENT_ENTITY_LEAD": 71,
            "CURRENT_PROFILE_SELF_OR_NO_SEPARATE_PARENT": 176,
        }
        or payload.get("historical_parent_lineage_proven") is not False
        or payload.get("historical_first_public_observation_proven") is not False
        or payload.get("recipient_to_issuer_mapping_frozen") is not False
    ):
        raise PilotError("Q221_PARENT_MAP_UPSTREAM_OR_GATE_MISMATCH")
    recipients = payload.get("recipients")
    if not isinstance(recipients, list) or len(recipients) != 247:
        raise PilotError("Q221_PARENT_MAP_RECIPIENT_COUNT_MISMATCH")
    by_id = {str(row.get("recipient_id") or ""): row for row in recipients}
    if len(by_id) != 247:
        raise PilotError("Q221_PARENT_MAP_DUPLICATE_RECIPIENT_ID")
    selected: dict[str, dict[str, Any]] = {}
    for row_id, expected in TRANSACTIONS.items():
        row = by_id.get(expected["recipient_id"])
        profile = (row or {}).get("current_profile_observation", {}).get("profile", {})
        if (
            not isinstance(row, dict)
            or row.get("recipient_name_from_frozen_sample") != expected["recipient_name"]
            or row.get("recipient_uei") != expected["recipient_uei"]
            or row.get("current_parent_classification") != "CURRENT_PARENT_ENTITY_LEAD"
            or row.get("historical_parent_lineage_proven") is not False
            or row.get("recipient_to_issuer_mapping_frozen") is not False
            or profile.get("recipient_id") != expected["recipient_id"]
            or profile.get("uei") != expected["recipient_uei"]
            or profile.get("parent_name") != expected["current_parent_name"]
            or profile.get("parent_uei") != expected["current_parent_uei"]
        ):
            raise PilotError(f"Q221_PARENT_MAP_SELECTED_LEAD_MISMATCH:{row_id}")
        selected[row_id] = row
    return payload, selected


def fetch_source(spec: dict[str, Any], max_bytes: int = MAX_BYTES_PER_SOURCE) -> tuple[dict[str, Any], bytes]:
    url = str(spec["url"])
    if url not in ALLOWED_URLS:
        raise PilotError("SOURCE_URL_OUTSIDE_FROZEN_ALLOWLIST")
    if max_bytes < 1 or max_bytes > MAX_BYTES_PER_SOURCE:
        raise PilotError("SOURCE_BUDGET_BOUND_INVALID")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise PilotError(f"SOURCE_RESPONSE_OVER_LIMIT:{spec['id']}")
            status = int(getattr(response, "status", 200))
            content_type = str(response.headers.get("Content-Type", ""))
            final_url = str(response.geturl())
            last_modified = str(response.headers.get("Last-Modified", ""))
    except urllib.error.HTTPError as exc:
        raise PilotError(f"SOURCE_HTTP_ERROR:{spec['id']}:{exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise PilotError(f"SOURCE_TRANSPORT_ERROR:{spec['id']}:{type(exc).__name__}") from exc
    final = urllib.parse.urlparse(final_url)
    if status != 200:
        raise PilotError(f"SOURCE_HTTP_STATUS_INVALID:{spec['id']}:{status}")
    if final.scheme != "https" or final.hostname != spec["allowed_host"]:
        raise PilotError(f"SOURCE_FINAL_HOST_INVALID:{spec['id']}:{final.hostname}")
    if not content_type.lower().startswith("text/html"):
        raise PilotError(f"SOURCE_CONTENT_TYPE_INVALID:{spec['id']}:{content_type[:100]}")
    observation = {
        "source_id": spec["id"],
        "requested_url": url,
        "final_url": final_url,
        "http_status": status,
        "content_type": content_type,
        "last_modified": last_modified,
        "response_bytes": len(raw),
        "response_sha256": sha256(raw),
    }
    return observation, raw


def evaluate_source_tokens(source_id: str, raw: bytes) -> dict[str, bool]:
    if source_id not in SOURCE_BY_ID:
        raise PilotError(f"UNKNOWN_SOURCE_ID:{source_id}")
    normalized = normalize_text(raw)
    return {
        token: token in normalized
        for token in SOURCE_BY_ID[source_id]["required_tokens"]
    }


def make_analysis(
    manifest: dict[str, Any],
    parent_map: dict[str, Any],
    selected_map_rows: dict[str, dict[str, Any]],
    observations: list[dict[str, Any]],
    bodies: dict[str, bytes],
) -> dict[str, Any]:
    if len(observations) != len(SOURCES) or set(bodies) != set(SOURCE_BY_ID):
        raise PilotError("Q221_PILOT_SOURCE_SET_INCOMPLETE")
    observations_by_id = {str(row.get("source_id") or ""): row for row in observations}
    if set(observations_by_id) != set(SOURCE_BY_ID):
        raise PilotError("Q221_PILOT_SOURCE_METADATA_SET_MISMATCH")
    source_rows = []
    source_ok: dict[str, bool] = {}
    for spec in SOURCES:
        source_id = spec["id"]
        obs = observations_by_id[source_id]
        raw = bodies[source_id]
        if (
            obs.get("requested_url") != spec["url"]
            or obs.get("http_status") != 200
            or obs.get("response_bytes") != len(raw)
            or obs.get("response_sha256") != sha256(raw)
            or len(raw) > MAX_BYTES_PER_SOURCE
        ):
            raise PilotError(f"Q221_PILOT_SOURCE_BODY_OR_PIN_MISMATCH:{source_id}")
        final_host = urllib.parse.urlparse(str(obs.get("final_url") or "")).hostname
        hits = evaluate_source_tokens(source_id, raw)
        valid = (
            final_host == spec["allowed_host"]
            and str(obs.get("content_type") or "").lower().startswith("text/html")
            and all(hits.values())
        )
        source_ok[source_id] = valid
        source_rows.append({
            "source_id": source_id,
            "requested_url": spec["url"],
            "final_url": obs["final_url"],
            "http_status": obs["http_status"],
            "content_type": obs["content_type"],
            "response_bytes": len(raw),
            "response_sha256": sha256(raw),
            "required_token_checks": hits,
            "required_token_checks_passed": all(hits.values()),
        })

    # Event-link claims are deliberately narrower than ownership/name matches.
    # Pre-event public documents support a lead; continuity through the action
    # date and the transaction's first-public timestamp are separate questions.
    all_sources_ok = all(source_ok.values())
    decisions = {
        "CACI_2019": (
            "PRE_EVENT_SUBSIDIARY_EVIDENCE_FOUND_PERSISTENCE_TO_ACTION_DATE_UNPROVEN"
            if source_ok["caci_index"] and source_ok["caci_ex21"]
            else "SOURCE_EVIDENCE_INCOMPLETE"
        ),
        "AURORA_2024": (
            "PRE_EVENT_PARENT_RELATION_EVIDENCE_FOUND_PERSISTENCE_TO_ACTION_DATE_UNPROVEN"
            if source_ok["aurora_index"] and source_ok["aurora_agreement"]
            else "SOURCE_EVIDENCE_INCOMPLETE"
        ),
        "ATK_2019": (
            "BLOCKED_LEGAL_ENTITY_FORM_MISMATCH"
            if source_ok["orbital_index"] and source_ok["orbital_ex21"] and source_ok["northrop_release"]
            else "SOURCE_EVIDENCE_INCOMPLETE"
        ),
    }
    rows = []
    for row_id, target in TRANSACTIONS.items():
        parent_row = selected_map_rows[row_id]
        profile = parent_row["current_parent_identity_leads_only"] if "current_parent_identity_leads_only" in parent_row else parent_row["current_profile_observation"]["profile"]
        source_refs = {
            "CACI_2019": ["caci_index", "caci_ex21"],
            "AURORA_2024": ["aurora_index", "aurora_agreement"],
            "ATK_2019": ["orbital_index", "orbital_ex21", "northrop_release"],
        }[row_id]
        rows.append({
            "row_id": row_id,
            "transaction_key": target["transaction_key"],
            "action_date": target["action_date"],
            "recipient_name_from_frozen_transaction": target["recipient_name"],
            "recipient_id": target["recipient_id"],
            "recipient_uei": target["recipient_uei"],
            "current_parent_name_from_prior_profile_only": profile["parent_name"],
            "current_parent_uei_from_prior_profile_only": profile["parent_uei"],
            "current_parent_is_not_historical_proof": True,
            "pre_event_sources": source_refs,
            "pre_event_evidence_classification": decisions[row_id],
            "issuer_symbol": None,
            "historical_parent_lineage_proven": False,
            "persistence_to_action_date_proven": False,
            "historical_first_public_observation_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
        })
    source_byte_total = sum(int(row["response_bytes"]) for row in source_rows)
    if source_byte_total > MAX_TOTAL_BYTES:
        raise PilotError("Q221_PILOT_TOTAL_SOURCE_BUDGET_EXCEEDED")
    return {
        "schema_version": 1,
        "record_type": "q221_pre_event_identity_bridge_analysis",
        "candidate_id": "Q221",
        "status": (
            "Q221_PRE_EVENT_IDENTITY_BRIDGE_PILOT_COMPLETE_MAPPING_UNRESOLVED"
            if all_sources_ok
            else "Q221_PRE_EVENT_IDENTITY_BRIDGE_PILOT_SOURCE_EVIDENCE_INCOMPLETE"
        ),
        "method": "One bounded capture of seven fixed pre-event corporate/SEC documents; exact token validation; no issuer map or historical publication-clock inference.",
        "frozen_upstream": {
            "manifest_path": MANIFEST_PATH,
            "manifest_receipt_fingerprint": manifest["receipt_fingerprint"],
            "manifest_git_blob_sha1": MANIFEST_BLOB_SHA1,
            "parent_map_run_id": PARENT_MAP_RUN_ID,
            "parent_map_artifact_id": PARENT_MAP_ARTIFACT_ID,
            "parent_map_receipt_fingerprint": parent_map["receipt_fingerprint"],
            "parent_map_raw_json_sha256": PARENT_MAP_RAW_SHA256,
        },
        "source_capture_count": len(source_rows),
        "source_capture_bytes": source_byte_total,
        "max_bytes_per_source": MAX_BYTES_PER_SOURCE,
        "max_total_bytes": MAX_TOTAL_BYTES,
        "source_observations": source_rows,
        "transaction_assessments": rows,
        "authority": {
            "historical_parent_lineage_proven": False,
            "persistence_to_action_date_proven": False,
            "historical_first_public_observation_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "scientific_evidence": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }


def read_captured_sources(capture_dir: Path, observations: list[dict[str, Any]]) -> dict[str, bytes]:
    bodies: dict[str, bytes] = {}
    sources_dir = capture_dir / "sources"
    for spec in SOURCES:
        path = sources_dir / f"{spec['id']}.html"
        if not path.is_file():
            raise PilotError(f"Q221_CAPTURED_SOURCE_MISSING:{spec['id']}")
        raw = path.read_bytes()
        if len(raw) > MAX_BYTES_PER_SOURCE:
            raise PilotError(f"Q221_CAPTURED_SOURCE_OVER_LIMIT:{spec['id']}")
        bodies[spec["id"]] = raw
    if sum(map(len, bodies.values())) > MAX_TOTAL_BYTES:
        raise PilotError("Q221_CAPTURED_TOTAL_SOURCE_BUDGET_EXCEEDED")
    return bodies


def read_capture_receipt(capture_dir: Path) -> dict[str, Any]:
    path = capture_dir / "receipt.json"
    if not path.is_file():
        raise PilotError("Q221_CAPTURE_RECEIPT_MISSING")
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if (
        receipt.get("record_type") != "q221_pre_event_identity_bridge_capture"
        or receipt.get("status") != "Q221_PRE_EVENT_IDENTITY_BRIDGE_CAPTURE_COMPLETE"
        or receipt.get("receipt_fingerprint") != canonical_fingerprint(receipt)
    ):
        raise PilotError("Q221_CAPTURE_RECEIPT_INVALID_OR_INCOMPLETE")
    return receipt


def run_capture(repo_root: Path, parent_map_dir: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "sources").mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    observations: list[dict[str, Any]] = []
    bodies: dict[str, bytes] = {}
    failure: str | None = None
    try:
        request_path = repo_root / REQUEST_PATH
        prereg_path = repo_root / PREREG_PATH
        request = parse_key_value_request(request_path)
        prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
        validate_request_and_prereg(request, prereg)
        manifest, _ = read_pinned_manifest(repo_root)
        parent_map, selected_map_rows = read_pinned_parent_map(parent_map_dir, manifest)
        for index, spec in enumerate(SOURCES):
            try:
                remaining = MAX_TOTAL_BYTES - sum(len(value) for value in bodies.values())
                if remaining < 1:
                    raise PilotError("Q221_PILOT_TOTAL_SOURCE_BUDGET_EXHAUSTED")
                if index:
                    time.sleep(REQUEST_GAP_SECONDS)
                observation, raw = fetch_source(spec, min(MAX_BYTES_PER_SOURCE, remaining))
                bodies[spec["id"]] = raw
                observations.append(observation)
                (output_dir / "sources" / f"{spec['id']}.html").write_bytes(raw)
            except Exception as exc:
                observations.append({
                    "source_id": spec["id"],
                    "requested_url": spec["url"],
                    "http_status": None,
                    "source_error": f"{type(exc).__name__}:{str(exc)}"[:500],
                })
                failure = f"SOURCE_CAPTURE_FAILED:{spec['id']}:{type(exc).__name__}"
                break
        if failure is None and len(bodies) == len(SOURCES):
            analysis = make_analysis(manifest, parent_map, selected_map_rows, observations, bodies)
            if analysis["status"] != "Q221_PRE_EVENT_IDENTITY_BRIDGE_PILOT_COMPLETE_MAPPING_UNRESOLVED":
                failure = "Q221_PILOT_SOURCE_CONTRACT_INCOMPLETE"
        else:
            analysis = None
            if failure is None:
                failure = "Q221_PILOT_CAPTURE_SET_INCOMPLETE"
    except Exception as exc:
        analysis = None
        failure = f"{type(exc).__name__}:{str(exc)}"[:700]

    receipt: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q221_pre_event_identity_bridge_capture",
        "status": (
            "Q221_PRE_EVENT_IDENTITY_BRIDGE_CAPTURE_COMPLETE"
            if failure is None and analysis is not None
            else "Q221_PRE_EVENT_IDENTITY_BRIDGE_CAPTURE_INCOMPLETE"
        ),
        "generated_at_utc": started,
        "workflow_run_id": os.getenv("GITHUB_RUN_ID"),
        "request_sequence": "2026-10-15T12:58:00Z",
        "request_path": REQUEST_PATH,
        "preregistration_path": PREREG_PATH,
        "source_observations": observations,
        "analysis": analysis,
        "analysis_fingerprint": canonical_fingerprint(analysis) if analysis is not None else None,
        "error": failure,
        "network_request_limit": len(SOURCES),
        "network_requests_attempted": len(observations),
        "network_response_bytes": sum(int(x.get("response_bytes") or 0) for x in observations),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
    }
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    (output_dir / "receipt.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return receipt


def run_verify(
    repo_root: Path,
    parent_map_dir: Path,
    capture_dir: Path,
    output_dir: Path,
    expected_analysis_fingerprint: str,
) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    manifest, _ = read_pinned_manifest(repo_root)
    parent_map, selected_map_rows = read_pinned_parent_map(parent_map_dir, manifest)
    capture = read_capture_receipt(capture_dir)
    observations = capture.get("source_observations")
    if not isinstance(observations, list) or len(observations) != len(SOURCES):
        raise PilotError("Q221_CAPTURE_SOURCE_OBSERVATION_COUNT_MISMATCH")
    bodies = read_captured_sources(capture_dir, observations)
    analysis = make_analysis(manifest, parent_map, selected_map_rows, observations, bodies)
    fingerprint = canonical_fingerprint(analysis)
    if (
        capture.get("analysis") != analysis
        or capture.get("analysis_fingerprint") != fingerprint
        or expected_analysis_fingerprint != fingerprint
    ):
        raise PilotError("Q221_OFFLINE_ANALYSIS_FINGERPRINT_MISMATCH")
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "q221_pre_event_identity_bridge_offline_verification",
        "status": "Q221_PRE_EVENT_IDENTITY_BRIDGE_REPRODUCED_OFFLINE",
        "generated_at_utc": started,
        "network_requests_made": 0,
        "analysis_fingerprint": fingerprint,
        "capture_receipt_fingerprint": capture["receipt_fingerprint"],
        "parent_map_receipt_fingerprint": parent_map["receipt_fingerprint"],
        "source_receipt_fingerprint": manifest["receipt_fingerprint"],
        "reproduced_status": analysis["status"],
        "all_required_source_tokens_validated": True,
        "authority": analysis["authority"],
        "safety": analysis["safety"],
    }
    receipt["receipt_fingerprint"] = canonical_fingerprint(receipt)
    (output_dir / "receipt.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return receipt


def run_publish(
    repo_root: Path,
    parent_map_dir: Path,
    capture_dir: Path,
    verification_path: Path,
    output: Path,
) -> dict[str, Any]:
    manifest, _ = read_pinned_manifest(repo_root)
    parent_map, selected_map_rows = read_pinned_parent_map(parent_map_dir, manifest)
    capture = read_capture_receipt(capture_dir)
    observations = capture.get("source_observations")
    if not isinstance(observations, list) or len(observations) != len(SOURCES):
        raise PilotError("Q221_CAPTURE_SOURCE_OBSERVATION_COUNT_MISMATCH")
    bodies = read_captured_sources(capture_dir, observations)
    analysis = make_analysis(manifest, parent_map, selected_map_rows, observations, bodies)
    analysis_fp = canonical_fingerprint(analysis)
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    if (
        capture.get("analysis") != analysis
        or capture.get("analysis_fingerprint") != analysis_fp
        or verification.get("record_type") != "q221_pre_event_identity_bridge_offline_verification"
        or verification.get("status") != "Q221_PRE_EVENT_IDENTITY_BRIDGE_REPRODUCED_OFFLINE"
        or verification.get("network_requests_made") != 0
        or verification.get("analysis_fingerprint") != analysis_fp
        or verification.get("capture_receipt_fingerprint") != capture.get("receipt_fingerprint")
        or verification.get("receipt_fingerprint") != canonical_fingerprint(verification)
        or analysis["status"] != "Q221_PRE_EVENT_IDENTITY_BRIDGE_PILOT_COMPLETE_MAPPING_UNRESOLVED"
    ):
        raise PilotError("Q221_PUBLISH_REQUIRES_MATCHED_COMPLETE_OFFLINE_REPRODUCTION")
    result: dict[str, Any] = {
        **analysis,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "record_type": "q221_pre_event_identity_bridge_pilot",
        "cross_arch_reproduction": {
            "status": "DETERMINISTIC_ANALYSIS_MATCHED",
            "same_analysis_fingerprint": True,
            "analysis_fingerprint": analysis_fp,
            "capture_receipt_fingerprint": capture["receipt_fingerprint"],
            "verification_receipt_fingerprint": verification["receipt_fingerprint"],
            "capture_platform": "ubuntu-24.04",
            "verification_platform": "ubuntu-24.04-arm",
            "network_requests_made_during_verification": 0,
        },
        "decision_boundary": {
            "interpretation": "Pre-event identity-source pilot only. Source links can support a historical lead, but do not prove legal continuity through the action date or transaction-level first-public observation.",
            "historical_parent_lineage_proven": False,
            "persistence_to_action_date_proven": False,
            "historical_first_public_observation_proven": False,
            "recipient_to_issuer_mapping_frozen": False,
            "scientific_evidence": False,
            "performance_authorization": False,
            "holdout_selection": False,
            "ranking": False,
            "tuning": False,
            "promotion": False,
            "live_execution": False,
        },
        "run_provenance": {
            "capture_workflow_run_id": capture.get("workflow_run_id"),
            "capture_receipt_fingerprint": capture["receipt_fingerprint"],
            "verification_receipt_fingerprint": verification["receipt_fingerprint"],
        },
    }
    result["receipt_fingerprint"] = canonical_fingerprint(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def parse_key_value_request(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise PilotError(f"REQUEST_LINE_INVALID:{line_number}")
        key, value = line.split("=", 1)
        if key in values or not key or not value:
            raise PilotError(f"REQUEST_KEY_VALUE_INVALID:{line_number}")
        values[key] = value
    return values


def validate_request_and_prereg(request: dict[str, str], prereg: dict[str, Any]) -> None:
    expected = {
        "RUN_Q221_PRE_EVENT_IDENTITY_BRIDGE_PILOT": "true",
        "SOURCE_OF_TRUTH": "DWR-debug/trading-agent-public",
        "SOURCE_MANIFEST_PATH": MANIFEST_PATH,
        "SOURCE_MANIFEST_GIT_BLOB_SHA": MANIFEST_BLOB_SHA1,
        "SOURCE_MANIFEST_RECEIPT_FINGERPRINT": MANIFEST_FP,
        "PARENT_MAP_RUN_ID": str(PARENT_MAP_RUN_ID),
        "PARENT_MAP_ARTIFACT_ID": str(PARENT_MAP_ARTIFACT_ID),
        "PARENT_MAP_RAW_SHA256": PARENT_MAP_RAW_SHA256,
        "PARENT_MAP_RECEIPT_FINGERPRINT": PARENT_MAP_FP,
        "SOURCE_REQUEST_COUNT": str(len(SOURCES)),
        "MAX_BYTES_PER_SOURCE": str(MAX_BYTES_PER_SOURCE),
        "MAX_TOTAL_BYTES": str(MAX_TOTAL_BYTES),
        "NO_USASPENDING_API_REQUESTS": "true",
        "NO_ARCHIVE_PAYLOAD_DOWNLOADS": "true",
        "NO_FULL_348_ROW_REQUERY": "true",
        "NO_ISSUER_MAPPING": "true",
        "HISTORICAL_FIRST_PUBLIC_OBSERVATION_PROVEN": "false",
        "PERFORMANCE": "false",
        "HOLDOUT_SELECTION": "false",
        "RANKING": "false",
        "TUNING": "false",
        "PROMOTION": "false",
        "LIVE_EXECUTION": "false",
        "PAPER_ONLY": "true",
        "LIVE_TRADING_ENABLED": "false",
        "ORDERS_ENABLED": "false",
        "AUTOMATIC_PROMOTION": "false",
        "REQUEST_SEQUENCE": "2026-10-15T12:58:00Z",
    }
    for key, value in expected.items():
        if request.get(key) != value:
            raise PilotError(f"REQUEST_VALUE_MISMATCH:{key}")
    if set(request) != set(expected):
        raise PilotError("REQUEST_KEY_SET_MISMATCH")
    if (
        prereg.get("record_type") != "q221_pre_event_identity_bridge_pilot_preregistration"
        or prereg.get("candidate_id") != "Q221"
        or prereg.get("source_manifest_receipt_fingerprint") != MANIFEST_FP
        or prereg.get("parent_map_receipt_fingerprint") != PARENT_MAP_FP
        or prereg.get("transaction_keys") != {k: v["transaction_key"] for k, v in TRANSACTIONS.items()}
        or prereg.get("source_urls") != [x["url"] for x in SOURCES]
        or prereg.get("limits", {}).get("maximum_requests") != len(SOURCES)
        or prereg.get("limits", {}).get("maximum_bytes_per_source") != MAX_BYTES_PER_SOURCE
        or prereg.get("limits", {}).get("maximum_total_bytes") != MAX_TOTAL_BYTES
        or prereg.get("prohibitions", {}).get("issuer_mapping") is not True
        or prereg.get("prohibitions", {}).get("publication_clock_inference") is not True
        or prereg.get("safety", {}).get("paper_only") is not True
        or prereg.get("safety", {}).get("live_trading_enabled") is not False
        or prereg.get("safety", {}).get("orders_enabled") is not False
        or prereg.get("safety", {}).get("automatic_promotion") is not False
    ):
        raise PilotError("PREREGISTRATION_CONTRACT_MISMATCH")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("capture", "verify", "publish"), required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--parent-map-artifact", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--capture-dir", type=Path)
    parser.add_argument("--verification-receipt", type=Path)
    parser.add_argument("--expected-analysis-fingerprint", default="")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "capture":
            if args.output_dir is None:
                raise PilotError("--output-dir-required-for-capture")
            result = run_capture(args.repo_root, args.parent_map_artifact, args.output_dir)
            print(json.dumps({
                "status": result["status"],
                "analysis_fingerprint": result.get("analysis_fingerprint"),
                "receipt_fingerprint": result["receipt_fingerprint"],
                "error": result.get("error"),
            }, sort_keys=True))
            return 0 if result["status"] == "Q221_PRE_EVENT_IDENTITY_BRIDGE_CAPTURE_COMPLETE" else 2
        if args.mode == "verify":
            if args.output_dir is None or args.capture_dir is None or not args.expected_analysis_fingerprint:
                raise PilotError("--output-dir-capture-dir-and-expected-fingerprint-required-for-verify")
            result = run_verify(
                args.repo_root, args.parent_map_artifact, args.capture_dir,
                args.output_dir, args.expected_analysis_fingerprint,
            )
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.mode == "publish":
            if args.capture_dir is None or args.verification_receipt is None or args.output is None:
                raise PilotError("--capture-dir-verification-receipt-and-output-required-for-publish")
            result = run_publish(
                args.repo_root, args.parent_map_artifact, args.capture_dir,
                args.verification_receipt, args.output,
            )
            print(json.dumps({
                "status": result["status"],
                "analysis_fingerprint": result["cross_arch_reproduction"]["analysis_fingerprint"],
                "receipt_fingerprint": result["receipt_fingerprint"],
                "historical_first_public_observation_proven": result["decision_boundary"]["historical_first_public_observation_proven"],
                "recipient_to_issuer_mapping_frozen": result["decision_boundary"]["recipient_to_issuer_mapping_frozen"],
            }, sort_keys=True))
            return 0
        raise PilotError("MODE_UNREACHABLE")
    except Exception as exc:
        print(json.dumps({"status": "Q221_PRE_EVENT_IDENTITY_BRIDGE_FAIL_CLOSED", "error": f"{type(exc).__name__}:{str(exc)}"[:800]}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
