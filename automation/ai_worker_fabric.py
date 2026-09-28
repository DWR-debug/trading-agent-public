"""Provider-neutral, free-only AI worker fabric for bounded research support.

This module routes non-deterministic research/design/review tasks to optional
external CLIs. It never performs scientific computation, selection, gate
changes, promotion, or live execution. Provider calls are fail-closed unless
the local environment explicitly attests that the provider is operating in a
free-only mode.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
MAX_RUNTIME_MINUTES = 20
TRUE_VALUES = {"1", "true", "yes", "on"}

PROVIDER_SPECS = {
    "gemini_cli": {
        "binaries": ("agy", "gemini"),
        "auth_env": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        "free_attestation_env": "GEMINI_FREE_MODE_CONFIRMED",
    },
    "claude_cli": {
        "binaries": ("claude",),
        "auth_env": (),
        "free_attestation_env": "CLAUDE_FREE_MODE_CONFIRMED",
    },
}

LOCAL_ATTESTATION_DEFAULT = Path.home() / ".trading-agent" / "ai_free_attestation.json"

CONTEXT_FILES = {
    "AI-2026-09-28-Q089-ADVERSARIAL": (
        "docs/research_design/Q089-clean-fresh-q069-validation-2026-09-28.md",
        "docs/research_design/Q089_CROSS_RUN_REPRO_AUDIT_2026-09-28.md",
        "research/evidence/q089_coverage_result.json",
        "research/evidence/q089_input_freeze_result.json",
        "research/evidence/q089_pit_result.json",
        "research/evidence/q089_asset_freeze.json",
        "automation/q089_coverage_pit.py",
        "automation/q089_input_freeze.py",
        "docs/DECISION_BASIS.md",
        "docs/EVIDENCE_GOVERNANCE.md",
        "research/governance/active_research_registry.json",
    ),
    "AI-2026-09-28-UNUSUAL-FRONTIER": (
        "docs/research_design/RESEARCH_FRONTIER_UNUSUAL_2026-09-28.md",
        "docs/DECISION_BASIS.md",
        "research/evidence/current_operational_state.json",
        "research/governance/active_research_registry.json",
    ),
}
CONTEXT_FILE_LIMIT = 8000
CONTEXT_TOTAL_LIMIT = 50000

FORBIDDEN_TASK_FLAGS = (
    "deterministic_compute", "holdout_selection", "parameter_selection",
    "asset_selection", "threshold_selection", "horizon_selection",
    "research_gate_changes", "promotion_decision", "live_execution",
    "paid_usage", "research_decision",
)

SYSTEM_GUARD = """You are a bounded worker inside the trading-agent-public research system.
This is paper-only research.

Hard invariants:
PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False

You may produce hypotheses, research designs, adversarial reviews, architecture
review observations, documentation suggestions, and other bounded support material.

You must not perform or claim deterministic backtests/statistical evidence, select
holdouts/assets/parameters/thresholds/horizons/candidates by observed performance,
alter or weaken research gates, authorize promotion/live trading, or treat your
own output as scientific evidence.

Your output is worker material only and must be independently checked or reproduced
by deterministic project tooling before it can affect a research decision."""

class AIWorkerError(ValueError):
    """Raised for invalid AI-worker contracts."""

def _truth(value: object) -> bool:
    return isinstance(value, str) and value.strip().lower() in TRUE_VALUES

def _fingerprint(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def load_task(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AIWorkerError("Task must be a JSON object.")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise AIWorkerError("Unsupported AI worker task schema.")
    task_id = data.get("task_id")
    if not isinstance(task_id, str) or not task_id.startswith("AI-"):
        raise AIWorkerError("task_id must use the AI-* namespace.")
    providers = data.get("providers")
    if not isinstance(providers, list) or not providers or any(p not in PROVIDER_SPECS for p in providers):
        raise AIWorkerError("providers must list known providers.")
    prompt = data.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise AIWorkerError("prompt is required.")
    max_runtime = data.get("max_runtime_minutes", 15)
    if not isinstance(max_runtime, int) or not 1 <= max_runtime <= MAX_RUNTIME_MINUTES:
        raise AIWorkerError(f"max_runtime_minutes must be 1..{MAX_RUNTIME_MINUTES}.")
    for flag in FORBIDDEN_TASK_FLAGS:
        if data.get(flag, False) is not False:
            raise AIWorkerError(f"{flag} must be false.")
    if data.get("allow_workspace_writes", False) is not False:
        raise AIWorkerError("allow_workspace_writes must be false.")
    return data

def _local_attestation(provider: str, env: dict[str, str]) -> dict[str, Any]:
    path = Path(env.get("TRADING_AGENT_AI_ATTESTATION", str(LOCAL_ATTESTATION_DEFAULT))).expanduser()
    try:
        # Windows PowerShell 5.1 writes UTF-8 text files with a BOM. Accept
        # both BOM-prefixed and BOM-free JSON so a locally generated
        # free-only attestation is not falsely rejected.
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {"present": False, "path": str(path)}
    providers = data.get("providers", [])
    ok = (
        data.get("schema_version") == 1
        and data.get("free_only") is True
        and data.get("paid_fallback_allowed") is False
        and data.get("personal_credit_fallback_allowed") is False
        and provider in providers
    )
    return {"present": ok, "path": str(path)}

def _resolve_binary(provider: str) -> str | None:
    for candidate in PROVIDER_SPECS[provider]["binaries"]:
        found = shutil.which(candidate)
        if found:
            return found
    return None

def preflight(provider: str, env: dict[str, str] | None = None) -> dict[str, Any]:
    if provider not in PROVIDER_SPECS:
        raise AIWorkerError(f"Unknown provider: {provider}.")
    env = dict(os.environ if env is None else env)
    spec = PROVIDER_SPECS[provider]
    local_mode = _truth(env.get("TRADING_AGENT_LOCAL_AI_MODE"))
    binary = _resolve_binary(provider)
    explicit_free = _truth(env.get(spec["free_attestation_env"]))
    local_attestation = _local_attestation(provider, env) if local_mode else {"present": False, "path": None}
    free_gate = explicit_free or local_attestation["present"]
    auth_ok = bool(spec["auth_env"]) and any(env.get(name) for name in spec["auth_env"])
    if local_mode:
        auth_ok = binary is not None and local_attestation["present"]
    elif provider == "claude_cli":
        auth_ok = free_gate
    allowlist = _truth(env.get("AI_EXTERNAL_PROVIDER_ALLOWLIST"))
    reasons: list[str] = []
    if not allowlist:
        reasons.append("AI_EXTERNAL_PROVIDER_ALLOWLIST is not confirmed")
    if binary is None:
        reasons.append("provider executable not found")
    if not auth_ok:
        reasons.append("provider authentication is not available for free-only mode")
    if not free_gate:
        reasons.append("provider free-mode attestation is missing")
    return {
        "provider": provider,
        "available": not reasons,
        "binary": binary,
        "free_only": True,
        "local_mode": local_mode,
        "local_attestation": local_attestation,
        "free_mode_attested": free_gate,
        "reasons": reasons,
    }

def _context_bundle(task: dict[str, Any]) -> str:
    files = CONTEXT_FILES.get(task["task_id"], ())
    if not files:
        return "No repository context bundle is configured for this task. Do not use terminal tools."
    sections: list[str] = []
    total = 0
    for rel in files:
        path = Path.cwd() / rel
        if not path.is_file():
            raise AIWorkerError(f"Required context file is missing: {rel}")
        file_text = path.read_text(encoding="utf-8")
        remaining = CONTEXT_TOTAL_LIMIT - total
        if remaining <= 0:
            break
        file_text = file_text[: min(CONTEXT_FILE_LIMIT, remaining)]
        sections.append(f"=== FILE {rel} ===\n{file_text}")
        total += len(file_text)
    return "\n\n".join(sections)

def build_prompt(task: dict[str, Any]) -> str:
    context = _context_bundle(task)
    return (SYSTEM_GUARD + "\n\n"
            + f"<task_id>{task["task_id"]}</task_id>\n"
            + f"<scope>{task.get("scope", "bounded research support")}</scope>\n"
            + "<repository_context>\n" + context + "\n</repository_context>\n\n"
            + "<execution_guard>All required repository context is included above. Do not call terminal, command, shell, file, browser, git, or other tools. Do not modify the workspace. Analyze only the supplied context and task request.</execution_guard>\n\n"
            + f"<request>\n{task["prompt"].strip()}\n</request>\n\n"
            + "Return a concise structured worker handoff with findings, counterarguments, concrete next actions, and uncertainty. Do not claim validation or promotion.")

def command_for(provider: str, prompt: str, binary: str | None = None) -> list[str]:
    if provider == "gemini_cli":
        executable = binary or "gemini"
        if Path(executable).name.lower().startswith("agy"):
            return [executable, "--print-timeout", "45s", "--sandbox", "--output-format", "json", "-p", prompt]
        return [executable, "--approval-mode", "plan", "--output-format", "json", "--prompt", prompt]
    if provider == "claude_cli":
        return [binary or "claude", "-p", prompt]
    raise AIWorkerError(f"Unknown provider: {provider}.")

def run_task(task: dict[str, Any], provider: str, output: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    if provider not in task["providers"]:
        raise AIWorkerError(f"Provider {provider} is not enabled for this task.")
    check = preflight(provider, env)
    base = {
        "schema_version": 1, "task_id": task["task_id"], "provider": provider,
        "free_only": True, "preflight": check, "task_fingerprint": _fingerprint(task),
        "worker_output_is_scientific_evidence": False,
        "safety": {"paper_only": True, "live_trading_enabled": False, "orders_enabled": False, "automatic_promotion": False},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    if not check["available"]:
        result = {**base, "status": "SKIPPED", "returncode": None, "stdout": "", "stderr": ""}
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result
    command = command_for(provider, build_prompt(task), check.get("binary"))
    started = time.monotonic()
    proc = subprocess.run(command, cwd=Path.cwd(), text=True, capture_output=True,
                          timeout=task.get("max_runtime_minutes", 15) * 60, check=False,
                          env=env or os.environ.copy())
    result = {**base, "status": "SUCCESS" if proc.returncode == 0 else "FAILED",
              "returncode": proc.returncode, "duration_seconds": round(time.monotonic() - started, 3),
              "stdout": proc.stdout[-20000:], "stderr": proc.stderr[-12000:], "command_binary": command[0]}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", choices=sorted(PROVIDER_SPECS))
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--provider", choices=sorted(PROVIDER_SPECS))
    parser.add_argument("--task", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.preflight:
        result = preflight(args.preflight)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["available"] else 2
    if args.run:
        if not args.provider or not args.task or not args.output:
            parser.error("--run requires --provider, --task and --output")
        result = run_task(load_task(args.task), args.provider, args.output)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] in {"SUCCESS", "SKIPPED"} else 1
    parser.error("Choose --preflight or --run.")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
