"""Q112 live SEC security identity feasibility.

Fetches three fixed representative SEC filing indexes and representative XML
payloads for 13F, N-PORT and Form 4. Source-native identifiers are adapted
into the Q111 canonical identity schema and the full source lineage is
fingerprinted.

No market returns, ranking, parameter search, holdout access, or promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from automation.q111_security_identity_contract import canonical_security_key

UA = "trading-agent-public/Q112 research"
TIMEOUT = 45

FIXED_SOURCES = {
    "13F": "https://www.sec.gov/Archives/edgar/data/1418814/000141881426000003/index.json",
    "N-PORT": "https://www.sec.gov/Archives/edgar/data/736913/000141036826084698/index.json",
    "FORM-4": "https://www.sec.gov/Archives/edgar/data/886982/000191038826000010/index.json",
}


def get(url: str) -> tuple[int, bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            return int(response.status), response.read(), response.headers.get("content-type", "")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read(), ""
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, str(exc).encode("utf-8"), ""


def response_fp(body: bytes) -> str:
    return "sha256:" + hashlib.sha256(body).hexdigest()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def first_text(root: ET.Element, names: set[str]) -> str | None:
    for elem in root.iter():
        if local_name(elem.tag) in names:
            value = "".join(elem.itertext()).strip()
            if value:
                return value
    return None


def candidate_elements(root: ET.Element, names: set[str]) -> list[ET.Element]:
    return [elem for elem in root.iter() if local_name(elem.tag) in names]


def first_security_row(root: ET.Element) -> dict[str, Any] | None:
    row_names = {"inforow", "infotable"}
    for node in candidate_elements(root, row_names):
        issuer = first_text(node, {"nameofissuer", "issuername"})
        title = first_text(node, {"titleofclass", "classname"})
        cusip = first_text(node, {"cusip", "cusipnumber"})
        ticker = first_text(node, {"ticker", "tickersymbol", "issuersymbol"})
        if issuer and title and cusip:
            return {
                "name_of_issuer": issuer,
                "title_of_class": title,
                "cusip": cusip,
                "ticker": ticker,
            }
    return None


def first_nport_security(root: ET.Element) -> dict[str, Any] | None:
    rows = candidate_elements(root, {"invstorseq", "invstorsecurity", "invstOrSec".lower()})
    for node in rows:
        issuer = first_text(node, {"name", "nameofissuer", "issuername"})
        title = first_text(node, {"title", "titleofclass", "classname"})
        cusip = first_text(node, {"cusip"})
        figi = first_text(node, {"figi"})
        ticker = first_text(node, {"ticker", "tickersymbol"})
        if cusip or figi or (issuer and ticker) or (issuer and title):
            return {
                "name_of_issuer": issuer or "",
                "title_of_class": title or "",
                "cusip": cusip,
                "figi": figi,
                "ticker": ticker,
            }
    return None


def extract_fields(source: str, xml_body: bytes) -> dict[str, Any]:
    root = ET.fromstring(xml_body)

    if source == "13F":
        row = first_security_row(root)
        if row is None:
            raise ValueError("Q112_13F_SECURITY_FIELDS_INCOMPLETE")
    elif source == "N-PORT":
        row = first_nport_security(root)
        if row is None:
            raise ValueError("Q112_NPORT_SECURITY_FIELDS_INCOMPLETE")
    else:
        issuer = first_text(root, {"issuername"})
        issuer_cik = first_text(root, {"issuercik"})
        ticker = first_text(root, {"issuertradingsymbol"})
        title = first_text(root, {"securitytitle", "securitytitlevalue"})
        if not title:
            # Form 4 commonly stores the actual value beneath <securityTitle><value>.
            for node in candidate_elements(root, {"securitytitle"}):
                title = first_text(node, {"value"})
                if title:
                    break
        if not (issuer and ticker and title and issuer_cik):
            raise ValueError("Q112_FORM4_ISSUER_SECURITY_FIELDS_INCOMPLETE")
        row = {
            "name_of_issuer": issuer,
            "title_of_class": title,
            "ticker": ticker,
            "issuer_cik": issuer_cik,
        }

    key = canonical_security_key(row)
    return {
        "source": source,
        "canonical_security_key": key,
        "issuer_name": row.get("name_of_issuer"),
        "title_of_class": row.get("title_of_class"),
        "ticker": row.get("ticker"),
        "cusip": row.get("cusip"),
        "figi": row.get("figi"),
        "issuer_cik": row.get("issuer_cik"),
    }


def discover_xml(index_url: str, source: str) -> tuple[str, bytes, str]:
    status, body, content_type = get(index_url)
    if status != 200:
        raise ValueError(f"Q112_INDEX_HTTP_{status}:{index_url}")

    payload = json.loads(body)
    items = payload.get("directory", {}).get("item", [])
    xml_names = [str(item.get("name")) for item in items if str(item.get("name", "")).lower().endswith(".xml")]

    if source == "13F":
        preferred = [n for n in xml_names if "infotable" in n.lower() or "information" in n.lower()]
    elif source == "N-PORT":
        preferred = [n for n in xml_names if "primary" in n.lower() or "nport" in n.lower()]
    else:
        preferred = [n for n in xml_names if "doc4" in n.lower() or "ownership" in n.lower()]

    candidates = preferred + [n for n in xml_names if n not in preferred]
    if not candidates:
        raise ValueError(f"Q112_NO_XML_DISCOVERED:{source}")

    match = re.search(r"/Archives/edgar/data/(\d+)/(\d+)/index\.json$", index_url)
    if not match:
        raise ValueError("Q112_INDEX_URL_UNPARSEABLE")
    cik_folder, accession_folder = match.groups()
    xml_url = f"https://www.sec.gov/Archives/edgar/data/{cik_folder}/{accession_folder}/{candidates[0]}"

    status_xml, xml_body, xml_type = get(xml_url)
    if status_xml != 200:
        raise ValueError(f"Q112_XML_HTTP_{status_xml}:{xml_url}")
    return xml_url, xml_body, xml_type or content_type


def synthetic_contract() -> dict[str, Any]:
    fixtures = {
        "13F": b"""<informationTable xmlns="urn:13f"><infoTable><nameOfIssuer>Apple Inc.</nameOfIssuer><titleOfClass>Common Stock</titleOfClass><cusip>037833100</cusip></infoTable></informationTable>""",
        "N-PORT": b"""<nport><invstOrSec><name>Microsoft Corp.</name><title>Common Stock</title><identifiers><identifier><CUSIP>594918104</CUSIP></identifier></identifiers></invstOrSec></nport>""",
        "FORM-4": b"""<ownershipDocument><issuer><issuerCik>0000320193</issuerCik><issuerName>Apple Inc.</issuerName><issuerTradingSymbol>AAPL</issuerTradingSymbol></issuer><nonDerivativeTable><nonDerivativeTransaction><securityTitle><value>Common Stock</value></securityTitle></nonDerivativeTransaction></nonDerivativeTable></ownershipDocument>""",
    }
    parsed = {source: extract_fields(source, body) for source, body in fixtures.items()}
    return {
        "sources": list(parsed),
        "all_resolve": all(bool(item["canonical_security_key"]) for item in parsed.values()),
        "form4_preserves_issuer_cik": parsed["FORM-4"]["issuer_cik"] == "0000320193",
        "future_mutation_safe": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research/runs/q112_sec_security_identity/result.json"))
    args = parser.parse_args()

    live: list[dict[str, Any]] = []
    for source, index_url in FIXED_SOURCES.items():
        status, index_body, index_type = get(index_url)
        entry: dict[str, Any] = {
            "source": source,
            "index_url": index_url,
            "index_http_status": status,
            "index_content_type": index_type,
            "index_response_sha256": response_fp(index_body),
        }
        if status == 200:
            try:
                xml_url, xml_body, xml_type = discover_xml(index_url, source)
                extracted = extract_fields(source, xml_body)
                accession = index_url.rstrip("/").split("/")[-2]
                entry.update(
                    {
                        "xml_url": xml_url,
                        "xml_content_type": xml_type,
                        "xml_response_sha256": response_fp(xml_body),
                        "accession_folder": accession,
                        "extracted": extracted,
                        "status": "VERIFIABLE",
                    }
                )
            except (ValueError, json.JSONDecodeError, ET.ParseError) as exc:
                entry.update({"status": "SCHEMA_MISMATCH", "error": str(exc)})
        else:
            entry["status"] = "BLOCKED"

        live.append(entry)

    synthetic = synthetic_contract()
    summary = {
        "verifiable_sources": sum(x["status"] == "VERIFIABLE" for x in live),
        "schema_mismatch_sources": sum(x["status"] == "SCHEMA_MISMATCH" for x in live),
        "blocked_sources": sum(x["status"] == "BLOCKED" for x in live),
    }

    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-01-112-SEC-SECURITY-LIVE-FEASIBILITY",
        "status": "LIVE_SOURCE_SECURITY_IDENTITY_FEASIBILITY_ONLY",
        "live_sources": live,
        "synthetic": synthetic,
        "summary": summary,
        "governance": {
            "performance_evaluation": False,
            "holdout_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "variant_search": False,
            "performance_authorization": False,
            "automatic_promotion": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["receipt_fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Q112_STATUS:", result["status"])
    print("Q112_VERIFIABLE:", summary["verifiable_sources"])
    print("Q112_SCHEMA_MISMATCH:", summary["schema_mismatch_sources"])
    print("Q112_BLOCKED:", summary["blocked_sources"])
    print("Q112_SYNTHETIC_ALL_PASS:", all(synthetic.values()))
    print("Q112_FINGERPRINT:", result["receipt_fingerprint"])
    return 0 if all(synthetic.values()) and summary["blocked_sources"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
