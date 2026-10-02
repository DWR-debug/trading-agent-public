"""Optional isolated S10 Evidence-Critic benchmark runner.

Unavailable or unstable S10 is an operational skip, never a scientific failure.
A bounded endpoint preflight prevents spending a full benchmark budget when the
local model cannot answer even one fixed smoke request.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path

from automation.evidence_critic_benchmark import main as benchmark_main
from automation.s10_runtime import resolve

SMOKE_TIMEOUT_SECONDS = 180
SMOKE_CLAIM = "The local S10 endpoint answered this bounded smoke request."
SMOKE_EVIDENCE = "The endpoint returned a valid typed verdict object for this request."


def _smoke_payload() -> dict:
    return {
        "mode": "smoke",
        "state": {
            "claim": SMOKE_CLAIM,
            "evidence": SMOKE_EVIDENCE,
            "domain": "bounded operational smoke test",
        },
        "questions": {
            "verdict": {
                "criteria": {
                    "SUPPORTED": "The supplied evidence establishes the claim.",
                    "REFUTED": "The supplied evidence contradicts the claim.",
                    "INSUFFICIENT": "The supplied evidence is not enough to decide the claim.",
                }
            }
        },
    }


def _endpoint_request(descriptor: dict[str, object]) -> tuple[str, str | None, dict[str, object] | None, str, str | None]:
    url = str(descriptor["base_url"]).rstrip("/") + str(descriptor["protocol_path"])
    body = json.dumps(_smoke_payload(), ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=SMOKE_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8")
        payload = json.loads(raw)
        verdict = ((payload.get("answers") or {}).get("verdict") or {})
        choice = verdict.get("choice")
        probabilities = verdict.get("probabilities")
        valid = (
            choice in {"SUPPORTED", "REFUTED", "INSUFFICIENT"}
            and isinstance(probabilities, dict)
            and set(probabilities) == {"SUPPORTED", "REFUTED", "INSUFFICIENT"}
        )
        return ("PASS" if valid else "FAIL_INVALID_RESPONSE", choice if isinstance(choice, str) else None, probabilities if isinstance(probabilities, dict) else None, url, None)
    except Exception as exc:
        return ("FAIL_ENDPOINT_UNAVAILABLE", None, None, url, f"{type(exc).__name__}: {exc}")


def _endpoint_smoke(descriptor: dict[str, object]) -> dict[str, object]:
    status, choice, probabilities, url, error = _endpoint_request(descriptor)
    return {
        "status": status,
        "url": url,
        "choice_present": choice in {"SUPPORTED", "REFUTED", "INSUFFICIENT"},
        "probabilities_contract_valid": status == "PASS",
        **({"error": error} if error else {}),
    }


def _endpoint_repeatability(descriptor: dict[str, object]) -> dict[str, object]:
    a_status, a_choice, a_probs, url, a_error = _endpoint_request(descriptor)
    b_status, b_choice, b_probs, _, b_error = _endpoint_request(descriptor)
    ok = (
        a_status == "PASS"
        and b_status == "PASS"
        and a_choice == b_choice
        and a_probs == b_probs
    )
    return {
        "status": "PASS" if ok else "FAIL_NONDETERMINISTIC",
        "attempts": 2,
        "url": url,
        "choice_equal": a_choice == b_choice,
        "probabilities_equal": a_probs == b_probs,
        "attempt_1_status": a_status,
        "attempt_2_status": b_status,
        **({"attempt_1_error": a_error} if a_error else {}),
        **({"attempt_2_error": b_error} if b_error else {}),
    }


def _write_operational_skip(args: argparse.Namespace, descriptor: dict[str, object], smoke: dict[str, object]) -> int:
    result = {
        "schema_version": 1,
        "task_id": "ECL-2026-10-01-001-S10",
        "status": smoke.get("status"),
        "model": descriptor.get("model"),
        "endpoint": descriptor.get("base_url"),
        "protocol_path": descriptor.get("protocol_path"),
        "descriptor_path": descriptor.get("path"),
        "runner_name": os.environ.get("RUNNER_NAME"),
        "source_commit": os.environ.get("GITHUB_SHA"),
        "preflight": smoke,
        "worker_output_is_scientific_evidence": False,
        "governance": {
            "performance_evaluation": False,
            "holdout_selection": False,
            "candidate_selection": False,
            "candidate_ranking": False,
            "promotion": False,
            "live_execution": False,
        },
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "model": descriptor.get("model"), "preflight": smoke}))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--corpus", type=Path, default=Path("research/benchmarks/evidence_critic_pilot_2026_10_01.jsonl"))
    ap.add_argument("--option-order-checks", type=int, default=6)
    args = ap.parse_args()

    descriptor = resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    if not descriptor.get("available"):
        return _write_operational_skip(
            args,
            descriptor,
            {"status": str(descriptor.get("status", "S10_UNAVAILABLE")), "endpoint": descriptor.get("base_url")},
        )

    smoke = _endpoint_smoke(descriptor)
    if smoke.get("status") != "PASS":
        return _write_operational_skip(args, descriptor, smoke)

    repeatability = _endpoint_repeatability(descriptor)
    if repeatability.get("status") != "PASS":
        return _write_operational_skip(args, descriptor, {
            "status": repeatability["status"],
            "endpoint": repeatability["url"],
            "repeatability": repeatability,
        })

    # The benchmark CLI reads its arguments from sys.argv, so invoke it through
    # the module-level parser with a controlled temporary argv.
    import sys

    old = sys.argv[:]
    try:
        sys.argv = [
            "evidence_critic_benchmark",
            "--endpoint", str(descriptor["base_url"]),
            "--protocol-path", str(descriptor["protocol_path"]),
            "--model", str(descriptor["model"]),
            "--corpus", str(args.corpus),
            "--output", str(args.output),
            "--option-order-checks", str(args.option_order_checks),
        ]
        code = benchmark_main()
        if code == 0 and args.output.is_file():
            result = json.loads(args.output.read_text(encoding="utf-8"))
            result["s10_repeatability_preflight"] = repeatability
            result["s10_runtime"] = {
                "seed": int(os.environ.get("S10_SEED", "271828")),
                "threads": 1,
                "temperature": 0,
                "top_k": 1,
                "deterministic_cpu_mode": True,
            }
            args.output.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            from automation.s10_acceptance import build_receipt

            receipt = build_receipt(args.output)
            acceptance_path = args.output.with_name("s10_acceptance_receipt.json")
            acceptance_path.write_text(
                json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(json.dumps({
                "s10_utility_status": receipt["status"],
                "s10_acceptance_receipt": str(acceptance_path),
            }, ensure_ascii=False))
        return code
    finally:
        sys.argv = old


if __name__ == "__main__":
    raise SystemExit(main())
