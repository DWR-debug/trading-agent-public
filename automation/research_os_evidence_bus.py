"""Bounded provenance primitives for the Research OS Evidence Bus.

Schema v1 remains readable. Schema v2 adds explicit public-availability semantics
without retroactively changing frozen v1 receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "research/governance/research_os_source_registry_2026_09_30.json"

REQUIRED = (
    "schema_version",
    "receipt_type",
    "source_id",
    "source_url",
    "retrieved_at",
    "available_at",
    "release_id",
    "parser_version",
    "raw_fingerprint",
    "normalized_fingerprint",
    "pit_status",
    "access_status",
    "scientific_evidence",
    "performance_authorization",
    "holdout_used",
)
REQUIRED_V2 = REQUIRED + (
    "availability_basis",
    "availability_evidence_url",
    "vintage_id",
    "revision_parent_fingerprint",
)
AVAILABILITY_BASES = frozenset(
    {
        "SOURCE_TIMESTAMP",
        "OFFICIAL_RELEASE_TIMESTAMP",
        "VERSIONED_SNAPSHOT_FIRST_OBSERVED",
        "CONSERVATIVE_NEXT_SESSION",
        "UNKNOWN",
    }
)


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value.lower())
    )


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("research_os_version") != "ROS-0.1":
        raise ValueError("Unsupported Research OS registry.")
    return payload


def source_index(registry: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in registry.get("source_lattice", []):
        if (
            not isinstance(item, dict)
            or not item.get("id")
            or not str(item.get("source_url", "")).startswith("https://")
        ):
            raise ValueError("Invalid Research OS source entry.")
        if item["id"] in out:
            raise ValueError(f"Duplicate source_id: {item['id']}")
        out[item["id"]] = item
    if not out:
        raise ValueError("Empty Research OS source lattice.")
    return out


def _ts(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include timezone.")
    return parsed.astimezone(timezone.utc)


def build_receipt(
    *,
    source_id: str,
    raw_payload: Any,
    normalized_payload: Any | None = None,
    retrieved_at: str | None = None,
    available_at: str | None = None,
    release_id: str | None = None,
    parser_version: str = "unparsed",
    pit_status: str = "DISCOVERY_ONLY",
    access_status: str = "SUCCESS",
    receipt_type: str = "source_fetch",
    schema_version: int = 1,
    availability_basis: str | None = None,
    availability_evidence_url: str | None = None,
    vintage_id: str | None = None,
    revision_parent_fingerprint: str | None = None,
    registry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a registry-bound operational receipt, never scientific evidence.

    V1 callers retain the prior receipt shape. V2 callers must provide explicit
    evidence for any claimed public-availability timestamp.
    """
    if isinstance(schema_version, bool) or schema_version not in (1, 2):
        raise ValueError(f"Unsupported receipt schema_version: {schema_version}")
    if schema_version == 1 and any(
        value is not None
        for value in (
            availability_basis,
            availability_evidence_url,
            vintage_id,
            revision_parent_fingerprint,
        )
    ):
        raise ValueError("V2_FIELDS_REQUIRE_SCHEMA_VERSION_2")

    registry = registry or load_registry()
    source = source_index(registry).get(source_id)
    if source is None:
        raise ValueError(f"Unregistered source_id: {source_id}")

    retrieved_at = retrieved_at or utc_now()
    normalized_payload = raw_payload if normalized_payload is None else normalized_payload
    receipt: dict[str, Any] = {
        "schema_version": schema_version,
        "receipt_type": receipt_type,
        "source_id": source_id,
        "source_url": source["source_url"],
        "retrieved_at": retrieved_at,
        "available_at": available_at,
        "release_id": release_id,
        "parser_version": parser_version,
        "raw_fingerprint": fingerprint(raw_payload),
        "normalized_fingerprint": fingerprint(normalized_payload),
        "pit_status": pit_status,
        "access_status": access_status,
        "scientific_evidence": False,
        "performance_authorization": False,
        "holdout_used": False,
        "registry_research_os_version": registry["research_os_version"],
        "registry_source_pit_fit": source.get("pit_fit"),
    }
    if schema_version == 2:
        receipt.update(
            {
                "availability_basis": availability_basis or "UNKNOWN",
                "availability_evidence_url": availability_evidence_url,
                "vintage_id": vintage_id,
                "revision_parent_fingerprint": revision_parent_fingerprint,
            }
        )
    receipt["receipt_fingerprint"] = fingerprint(receipt)
    validate_receipt(receipt, registry=registry)
    return receipt


def validate_receipt(
    receipt: Mapping[str, Any],
    *,
    registry: Mapping[str, Any] | None = None,
) -> None:
    registry = registry or load_registry()
    version = receipt.get("schema_version")
    if isinstance(version, bool) or version not in (1, 2):
        raise ValueError(f"Unsupported receipt schema_version: {version}")
    required = REQUIRED if version == 1 else REQUIRED_V2
    missing = [key for key in required if key not in receipt]
    if missing:
        raise ValueError("Missing receipt fields: " + ",".join(missing))

    source = source_index(registry).get(receipt["source_id"])
    if source is None:
        raise ValueError("Receipt uses unregistered source.")
    if receipt["source_url"] != source["source_url"]:
        raise ValueError(f"Source URL drift for {receipt['source_id']}.")

    retrieved = _ts(receipt["retrieved_at"])
    available = _ts(receipt["available_at"])
    if available and retrieved and available > retrieved:
        raise ValueError("available_at cannot be later than retrieved_at.")

    if version == 2:
        basis = receipt.get("availability_basis")
        evidence_url = receipt.get("availability_evidence_url")
        if basis not in AVAILABILITY_BASES:
            raise ValueError(f"Unsupported availability_basis: {basis}")
        if available is None:
            if basis != "UNKNOWN":
                raise ValueError("availability_basis must be UNKNOWN when available_at is null.")
            if evidence_url is not None:
                raise ValueError("availability_evidence_url must be null when available_at is null.")
        else:
            if basis == "UNKNOWN":
                raise ValueError("availability_basis cannot be UNKNOWN when available_at is set.")
            if not isinstance(evidence_url, str) or not evidence_url.startswith("https://"):
                raise ValueError("availability_evidence_url must be HTTPS when available_at is set.")
        vintage_id = receipt.get("vintage_id")
        if vintage_id is not None and (not isinstance(vintage_id, str) or not vintage_id.strip()):
            raise ValueError("vintage_id must be a non-empty string or null.")
        parent = receipt.get("revision_parent_fingerprint")
        if parent is not None and not is_sha256(parent):
            raise ValueError("revision_parent_fingerprint must be SHA-256 or null.")

    if (
        receipt["scientific_evidence"] is not False
        or receipt["performance_authorization"] is not False
        or receipt["holdout_used"] is not False
    ):
        raise ValueError("Operational receipt cannot become scientific evidence, authorization, or holdout input.")

    for key in ("raw_fingerprint", "normalized_fingerprint", "receipt_fingerprint"):
        if not is_sha256(receipt.get(key)):
            raise ValueError(f"{key} must be SHA-256.")

    # Check the digest over the full payload, excluding only the digest field itself.
    # This catches valid-looking hashes copied onto mutated or stale receipt contents.
    digest_payload = dict(receipt)
    stored_digest = digest_payload.pop("receipt_fingerprint", None)
    if stored_digest != fingerprint(digest_payload):
        raise ValueError("Receipt fingerprint mismatch.")


def write_receipt(receipt: Mapping[str, Any], output: str | Path) -> Path:
    validate_receipt(receipt)
    path = Path(output)
    path = path if path.is_absolute() else ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", type=Path)
    args = parser.parse_args()
    if not args.validate:
        parser.error("pass --validate RECEIPT.json")
    validate_receipt(json.loads(args.validate.read_text(encoding="utf-8")))
    print("RESEARCH OS EVIDENCE RECEIPT OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
