"""Non-invasive preflight for optional SAM.gov API credential configuration.

Reports only whether the named protected environment secret is non-empty.
It never makes a network request, prints or persists the value, or treats
credential presence as scientific evidence.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

SECRET_ENV_NAME = "SAM_GOV_API_KEY"


def build_receipt(secret_value: str | None) -> dict[str, Any]:
    configured = bool(secret_value and secret_value.strip())
    return {
        "schema_version": 1,
        "record_type": "q221_sam_api_credential_preflight",
        "candidate_id": "Q221",
        "status": (
            "SAM_GOV_API_KEY_CONFIGURED_NO_REQUESTS"
            if configured
            else "SAM_GOV_API_KEY_NOT_CONFIGURED_NO_REQUESTS"
        ),
        "credential_secret_name": SECRET_ENV_NAME,
        "credential_configured": configured,
        "credential_value_logged": False,
        "credential_value_persisted": False,
        "credential_value_hashed": False,
        "network_requests_made": 0,
        "sam_api_requests_made": 0,
        "source_requests_made": 0,
        "historical_snapshots_retrieved": 0,
        "historical_public_clock_gate_cleared": False,
        "scientific_evidence": False,
        "paper_only": True,
        "performance_authorization": False,
        "holdout_selection": False,
        "ranking": False,
        "tuning": False,
        "promotion": False,
        "live_execution": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    receipt = build_receipt(os.environ.get(SECRET_ENV_NAME))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\\n",
        encoding="utf-8",
    )
    # Report only the boolean/status; never expose or hash the secret value.
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "credential_secret_name": SECRET_ENV_NAME,
                "credential_configured": receipt["credential_configured"],
                "source_requests_made": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
