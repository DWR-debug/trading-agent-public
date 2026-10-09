"""Publish one current Q218 focus-gate receipt into the canonical index."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "research/evidence/q218_focus_gate_receipt_index_latest.json"


def blob_sha(path: str | Path) -> str:
    """Compute the Git blob SHA-1 from checked-out bytes without requiring git on PATH."""
    target = Path(path)
    if not target.is_absolute():
        target = ROOT / target
    content = target.read_bytes()
    header = b"blob " + str(len(content)).encode("ascii") + b"\0"
    return hashlib.sha1(header + content).hexdigest()


def performance_boundary_is_closed(receipt: dict) -> bool:
    """Fail closed while supporting both canonical Q218 receipt schema versions."""
    declared = []
    scientific_boundary = receipt.get("scientific_boundary")
    if isinstance(scientific_boundary, dict) and "performance_authorized" in scientific_boundary:
        declared.append(scientific_boundary["performance_authorized"])
    for key in ("performance_authorization", "performance_authorized"):
        if key in receipt:
            declared.append(receipt[key])
    return bool(declared) and all(value is False for value in declared)


def paper_only_boundary_is_closed(receipt: dict) -> bool:
    """Fail closed across canonical Q218 paper-only receipt schema variants."""
    declared = []
    if "paper_only" in receipt:
        declared.append(receipt["paper_only"])
    safety = receipt.get("safety")
    if isinstance(safety, dict):
        for key in ("paper_only", "PAPER_ONLY"):
            if key in safety:
                declared.append(safety[key])
    # If multiple schema variants declare this boundary, every declaration
    # must be the literal boolean True; absence and string values fail closed.
    return bool(declared) and all(value is True for value in declared)


def select_run_artifact(payload: dict) -> tuple[int, str] | None:
    """Select a published, unexpired artifact with an immutable digest."""
    artifacts = payload.get("artifacts", [])
    if not isinstance(artifacts, list):
        return None
    for artifact in artifacts:
        if not isinstance(artifact, dict) or artifact.get("expired") is not False:
            continue
        artifact_id = artifact.get("id")
        digest = artifact.get("digest")
        if isinstance(artifact_id, int) and isinstance(digest, str) and digest:
            return artifact_id, digest
    return None


def fetch_run_artifact(run_id: int) -> tuple[int, str]:
    """Look up the current run's artifact via the authenticated GitHub REST API."""
    repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
    token = os.environ.get("GH_TOKEN", "").strip()
    if not repository or repository.count("/") != 1 or not token:
        raise SystemExit("Q218_GATE_GITHUB_API_CONTEXT_MISSING")

    url = (
        "https://api.github.com/repos/"
        + urllib.parse.quote(repository, safe="/")
        + f"/actions/runs/{run_id}/artifacts?per_page=100"
    )
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "TradingAgent-Q218-Receipt-Publisher",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Q218_GATE_ARTIFACT_LOOKUP_FAILED:{type(exc).__name__}") from exc

    selected = select_run_artifact(payload)
    if selected is None:
        raise SystemExit("Q218_GATE_ARTIFACT_NOT_FOUND")
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", choices=("source", "event_pair"), required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--run-id", type=int, required=True)
    args = parser.parse_args()

    if not args.receipt.exists():
        raise SystemExit("Q218_GATE_RECEIPT_MISSING")
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    if receipt.get("candidate_id") != "Q218":
        raise SystemExit("Q218_GATE_RECEIPT_CANDIDATE_MISMATCH")
    if not performance_boundary_is_closed(receipt):
        raise SystemExit("Q218_GATE_PERFORMANCE_BOUNDARY_FAILED")
    if not paper_only_boundary_is_closed(receipt):
        raise SystemExit("Q218_GATE_SAFETY_BOUNDARY_FAILED")

    data = (
        json.loads(INDEX.read_text(encoding="utf-8"))
        if INDEX.exists()
        else {
            "schema_version": "1.0",
            "record_type": "q218_focus_gate_receipt_index",
            "candidate_id": "Q218",
        }
    )
    code_path = (
        "automation/q218_sec_multichannel_source_gate.py"
        if args.gate == "source"
        else "automation/q218_sec_event_pair_lineage_gate.py"
    )
    key = "source_gate" if args.gate == "source" else "event_pair_gate"
    artifact_id, artifact_digest = fetch_run_artifact(args.run_id)
    data[key] = {
        "run_id": args.run_id,
        "artifact_id": artifact_id,
        "artifact_digest": artifact_digest,
        "receipt_fingerprint": receipt.get("receipt_fingerprint"),
        "verified_positive_complete": True,
        "gate_code_blob_sha": blob_sha(code_path),
    }
    current_source = (
        bool(data.get("source_gate", {}).get("verified_positive_complete"))
        and data.get("source_gate", {}).get("gate_code_blob_sha")
        == blob_sha("automation/q218_sec_multichannel_source_gate.py")
    )
    current_event = (
        bool(data.get("event_pair_gate", {}).get("verified_positive_complete"))
        and data.get("event_pair_gate", {}).get("gate_code_blob_sha")
        == blob_sha("automation/q218_sec_event_pair_lineage_gate.py")
    )
    data["status"] = (
        "Q218_SOURCE_AND_EVENT_PAIR_GATES_COMPLETE"
        if current_source and current_event
        else "Q218_FOCUS_GATE_PARTIAL_CURRENT_CONTEXT"
    )
    data["verified_at_utc"] = receipt.get("generated_at_utc")
    data["next_gate"] = (
        "INDEPENDENT_ARCHITECTURE_PIT_REPRODUCTION"
        if current_source and current_event
        else ("event-pair gate" if current_source else "source gate")
    )
    INDEX.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": data["status"],
                "gate": args.gate,
                "run_id": args.run_id,
                "receipt_fingerprint": receipt.get("receipt_fingerprint"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
