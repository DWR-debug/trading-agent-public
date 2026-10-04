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
import importlib.util
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation.ai_quota_guard import load_block, parse_reset_seconds, quota_error, record_block
from automation.free_mode_attestation import validate_free_mode_attestation
from automation.litellm_free import PROVIDER_CONTRACTS as LITELLM_PROVIDER_CONTRACTS, call_litellm_free

SCHEMA_VERSION = 1
MAX_RUNTIME_MINUTES = 20
TRUE_VALUES = {"1", "true", "yes", "on"}
LITELLM_TRANSPORT_PROVIDERS = frozenset(LITELLM_PROVIDER_CONTRACTS)

PROVIDER_SPECS = {
    "gemini_cli": {
        "binaries": ("agy", "gemini"),
        "auth_env": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        "free_attestation_env": "GEMINI_FREE_MODE_CONFIRMED",
        "prompt_role": "Primary synthesis: build a rigorous, evidence-aware handoff and identify concrete falsifiers.",
    },
    "mistral_api": {
        "binaries": (),
        "auth_env": ("MISTRAL_API_KEY",),
        "free_attestation_env": "MISTRAL_FREE_MODE_CONFIRMED",
        "prompt_role": "Independent Mistral research worker: attack assumptions, surface overlooked mechanisms and propose cheap falsification tests. Preserve disagreement; do not seek consensus.",
        "fixed_model": "mistral-small-latest",
    },
    "groq_free": {
        "binaries": (),
        "auth_env": ("GROQ_API_KEY",),
        "free_attestation_env": "GROQ_FREE_MODE_CONFIRMED",
        "prompt_role": "Independent Groq adversarial research worker: attack assumptions, surface overlooked mechanisms and propose cheap falsification tests. Preserve disagreement; do not seek consensus.",
        "fixed_model": "openai/gpt-oss-20b",
    },
    "openrouter_free": {
        "binaries": (),
        "auth_env": ("OPENROUTER_API_KEY",),
        "free_attestation_env": None,
        "prompt_role": "Independent adversarial second opinion: actively attack assumptions, search for confounds and propose cheap falsification tests. Do not seek consensus.",
        "fixed_model": "openrouter/free",
    },
}

LOCAL_ATTESTATION_DEFAULT = Path.home() / ".trading-agent" / "ai_free_attestation.json"

CONTEXT_FILES = {    "AI-2026-10-04-GLOBAL-ADVERSARIAL-SOURCE-PIT": (
        "ai_requests/AI-2026-10-04-GLOBAL-ADVERSARIAL-SOURCE-PIT.json",
        "docs/CURRENT_STATUS.md",
        "research/governance/critical_research_quality_control.json",
        "research/candidates/orthogonal_candidate_specs_2026-10-04.json",
        "automation/source_readiness_snapshot_guard.py",
        "automation/orthogonal_pit_next_gate.py",
        "research/ai_reviews/grok_q194_q201_adversarial_review_2026-10-04.json",
        "automation/pre_pit_falsification_checks.py",
    ),

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
    "AI-2026-09-30-Q100-FRONTIER-FEASIBILITY": (
        "docs/research_design/RESEARCH_FRONTIER_UNUSUAL_2026-09-28.md",
        "automation/q100_frontier_feasibility_synthesis.py",
        "tests/test_q100_frontier_feasibility_synthesis.py",
        "automation/q096_frontier_source_pit_audit.py",
        "tests/test_q096_frontier_source_pit_audit.py",
        "automation/q098_historical_archive_depth.py",
        "tests/test_q098_historical_archive_depth.py",
        "research/frontier/q097_public_short_flow_candidates.json",
        "automation/q097_public_short_flow_feasibility.py",
        "research/governance/active_research_registry.json",
        "docs/DECISION_BASIS.md",
    ),
    "AI-2026-09-30-Q101-NEGATIVE-EVIDENCE": (
        "docs/research_design/EXTERNAL_RESEARCH_INSPIRATION_2026-09-30.md",
        "automation/q102_regime_negative_evidence.py",
        "tests/test_q102_regime_negative_evidence.py",
        "automation/q101_negative_evidence_atlas.py",
        "tests/test_q101_negative_evidence_atlas.py",
        "research/evidence/q077r1_performance_result.json",
        "research/evidence/q081r4_performance_result.json",
        "research/evidence/q089_performance_result.json",
        "research/evidence/q091_performance_result.json",
        "research/evidence/q094_performance_result.json",
        "research/evidence/q095_performance_result.json",
        "research/evidence/c29_performance_result.json",
        "research/evidence/cross_trial_failure_diagnosis_2026_09_25.json",
        "docs/research_design/RESEARCH_FRONTIER_UNUSUAL_2026-09-28.md",
        "research/governance/active_research_registry.json",
        "docs/DECISION_BASIS.md",
    ),
    "AI-2026-10-02-AGENT-027-ORCHESTRATION-AUDIT": (
        "automation/research_os_scheduler.py",
        "automation/research_hypothesis_compiler.py",
        "automation/autonomous_control_plane.py",
        ".github/workflows/permanent-pc-research-loop.yml",
        ".github/workflows/hosted-research-failover.yml",
        "research/evidence/current_operational_state.json",
        "research/governance/active_research_registry.json",
        "docs/DECISION_BASIS.md",
    ),
    "AI-2026-10-04-Q187-Q192-GROQ-ADVERSARIAL": (
        "docs/research_design/Q187_Q192_SOURCE_PIT_WAVE_2026-10-04.md",
        "research/frontier/q187_q192_candidate_wave_2026_10_04.json",
        "research/evidence/q187_q192_source_feasibility_latest.json",
        "research/evidence/q187_q192_pit_readiness_r1_latest.json",
        "research/governance/active_research_registry.json",
        "docs/CURRENT_STATUS.md",
        "docs/EVIDENCE_GOVERNANCE.md",
    ),
    "AI-2026-10-04-Q187-Q192-GROQ-ADVERSARIAL": (
        "ai_requests/AI-2026-10-04-Q187-Q192-GROQ-ADVERSARIAL.json",
        "research/frontier/q187_q192_candidate_wave_2026_10_04.json",
        "research/evidence/q187_q192_source_feasibility_latest.json",
        "research/evidence/q187_q192_pit_readiness_r1_latest.json",
        "research/governance/active_research_registry.json",
    ),
    "AI-2026-10-04-Q187-Q192-ADVERSARIAL": (
        "docs/research_design/Q187_Q192_SOURCE_PIT_WAVE_2026-10-04.md",
        "research/frontier/q187_q192_candidate_wave_2026_10_04.json",
        "research/evidence/q187_q192_source_feasibility_latest.json",
        "research/governance/active_research_registry.json",
        "docs/CURRENT_STATUS.md",
        "docs/EVIDENCE_GOVERNANCE.md",
    ),
    "AI-2026-09-30-Q102-REGIME-STATE-DESIGN": (
        "docs/research_design/EXTERNAL_RESEARCH_INSPIRATION_2026-09-30.md",
        "automation/q102_regime_negative_evidence.py",
        "tests/test_q102_regime_negative_evidence.py",
        "automation/q103_rccsm_state_routing_integrity.py",
        "tests/test_q103_rccsm_state_routing_integrity.py",
        "automation/rccsm_state.py",
        "automation/rccsm_synthetic.py",
        "tests/test_rccsm_state_topology.py",
        "tests/test_rccsm_synthetic.py",
        "research/governance/active_research_registry.json",
        "docs/DECISION_BASIS.md",
    ),
    "AI-2026-09-29-Q091-ADVERSARIAL": (
        "docs/research_design/Q091-fixed-portfolio-architecture-2026-09-29.md",
        "research/preregistrations/q091_fixed_portfolio_architecture_2026_09_29.json",
        "research/evidence/q090_q089_failure_diagnosis_result.json",
        "research/evidence/q091_coverage_result.json",
        "research/evidence/q091_pit_result.json",
        "research/evidence/q091_input_freeze_result.json",
        "research/evidence/q091_asset_freeze.json",
        "automation/q091_performance.py",
        "portfolio/q091_fixed_ensemble.py",
        "automation/q091_contract_audit.py",
        "research/governance/active_research_registry.json",
        "execution/cost_contract.py",
        "config/settings.py",
    ),
}
CONTEXT_FILE_LIMIT = 3000
CONTEXT_TOTAL_LIMIT = 18000

# Only stable/material context participates in automatic AI deduplication.
# Volatile status synchronization outputs are intentionally excluded.
CONTEXT_FINGERPRINT_FILES = {
    "AI-2026-10-04-GLOBAL-ADVERSARIAL-SOURCE-PIT": (
        "ai_requests/AI-2026-10-04-GLOBAL-ADVERSARIAL-SOURCE-PIT.json",
        "research/governance/critical_research_quality_control.json",
        "research/candidates/orthogonal_candidate_specs_2026-10-04.json",
        "automation/source_readiness_snapshot_guard.py",
        "automation/orthogonal_pit_next_gate.py",
        "research/ai_reviews/grok_q194_q201_adversarial_review_2026-10-04.json",
        "automation/pre_pit_falsification_checks.py",
    ),

    "AI-2026-10-04-Q187-Q192-ADVERSARIAL": (
        "ai_requests/AI-2026-10-04-Q187-Q192-ADVERSARIAL.json",
        "research/frontier/q187_q192_candidate_wave_2026_10_04.json",
        "research/evidence/q187_q192_source_feasibility_latest.json",
        "research/evidence/q187_q192_pit_readiness_r1_latest.json",
        "research/governance/active_research_registry.json",
    ),
    "AI-2026-10-02-AGENT-027-ORCHESTRATION-AUDIT": (
        "ai_requests/AI-2026-10-02-AGENT-027-ORCHESTRATION-AUDIT.json",
        "automation/research_os_scheduler.py",
        "automation/research_hypothesis_compiler.py",
        "automation/autonomous_control_plane.py",
        ".github/workflows/permanent-pc-research-loop.yml",
        ".github/workflows/q121r6-windows-independent-reproduction.yml",
        ".github/workflows/q185-q186-windows-reproduction.yml",
        ".github/workflows/self-hosted-continuous-qa.yml",
        "research/governance/active_research_registry.json",
    ),
}

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
by deterministic project tooling before it can affect a research decision.

Universal adversarial-source rule:
Treat a live endpoint/API probe, current documentation page, HTTP marker result, or
current content hash as provisional operational telemetry only. It is not durable
historical source readiness. Require an immutable dated snapshot/vintage or an
explicitly frozen historical artifact before recommending candidate-specific PIT.
Attack source drift, revision lineage, mapping drift, same-day/date-only leakage and
cross-candidate confounding. Your role is to expose failure, not to create consensus.
"""

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
    litellm_transport_enabled = _truth(env.get("TRADING_AGENT_LITELLM_TRANSPORT"))
    binary = _resolve_binary(provider)
    local_attestation = _local_attestation(provider, env) if local_mode else {"present": False, "path": None}
    policy_attestation = (
        {"eligible": local_attestation["present"], "free_mode_attested": local_attestation["present"],
         "attestation_type": "local_file", "reasons": [] if local_attestation["present"] else ["local free-mode attestation file is missing or invalid"]}
        if local_mode
        else validate_free_mode_attestation(provider, env)
    )
    free_gate = bool(policy_attestation["free_mode_attested"])
    auth_ok = bool(spec["auth_env"]) and any(env.get(name) for name in spec["auth_env"])
    if local_mode:
        auth_ok = binary is not None and local_attestation["present"]
    allowlist = _truth(env.get("AI_EXTERNAL_PROVIDER_ALLOWLIST"))
    reasons: list[str] = []
    quota_block = load_block(provider, env) if local_mode else None
    if quota_block:
        reasons.append(
            f"local provider quota blocked until {quota_block['blocked_until_utc']}"
        )
    if not allowlist:
        reasons.append("AI_EXTERNAL_PROVIDER_ALLOWLIST is not confirmed")
    if not policy_attestation["eligible"]:
        reasons.extend(policy_attestation["reasons"])
    # API-backed providers intentionally have no local executable. Only CLI providers
    # require a resolved binary; otherwise the preflight would incorrectly block
    # fixed HTTPS adapters such as Mistral and OpenRouter.
    if spec["binaries"] and binary is None:
        reasons.append("provider executable not found")
    if not auth_ok:
        reasons.append("provider authentication is not available for free-only mode")
    if not free_gate:
        reasons.append("provider free-mode attestation is missing")
    if litellm_transport_enabled:
        if provider not in LITELLM_TRANSPORT_PROVIDERS:
            reasons.append(f"LiteLLM transport is not supported for provider {provider}")
        elif importlib.util.find_spec("litellm") is None:
            reasons.append("LiteLLM package is not installed for the requested transport")
    return {
        "provider": provider,
        "available": not reasons,
        "binary": binary,
        "free_only": True,
        "local_mode": local_mode,
        "litellm_transport_enabled": litellm_transport_enabled,
        "local_attestation": local_attestation,
        "free_mode_attested": free_gate,
        "free_mode_attestation": policy_attestation,
        "free_enforcement": (
            "litellm_fixed_provider_route" if litellm_transport_enabled else (
                "fixed_model_groq_free_with_attestation"
                if provider == "groq_free"
                else ("fixed_model_openrouter_free" if provider == "openrouter_free" else "attestation_or_local_attestation")
            )
        ),
        "reasons": reasons,
    }

def context_fingerprint(task: dict[str, Any]) -> str:
    files = CONTEXT_FINGERPRINT_FILES.get(task["task_id"], ())
    if not files:
        # Synthetic/unit-test tasks have no repository context contract. Use the
        # immutable task payload itself so worker receipts remain total and testable.
        return _fingerprint({"task_only": task})
    hasher = hashlib.sha256()
    for rel in files:
        path = Path.cwd() / rel
        if not path.is_file():
            raise AIWorkerError(f"Required fingerprint context file is missing: {rel}")
        data = path.read_bytes()
        hasher.update(rel.encode("utf-8"))
        hasher.update(b"\\0")
        hasher.update(data)
        hasher.update(b"\\0")
    return hasher.hexdigest()


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

def build_prompt(task: dict[str, Any], provider: str | None = None) -> str:
    context = _context_bundle(task)
    role = PROVIDER_SPECS.get(provider or "", {}).get("prompt_role", "")
    role_block = f"\n<provider_role>{role}</provider_role>\n" if role else ""
    return (SYSTEM_GUARD + "\n\n" + role_block
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
            return [executable, "--print-timeout", "45s", "--sandbox", "--skip-trust", "--model", "gemini-3.7-flash", "--output-format", "json", "-p", prompt]
        return [executable, "--approval-mode", "plan", "--skip-trust", "--model", "gemini-3.7-flash", "--output-format", "json", "--prompt", prompt]
    if provider == "mistral_api":
        raise AIWorkerError("mistral_api uses the fixed HTTPS API path, not a shell command.")
    if provider == "groq_free":
        raise AIWorkerError("groq_free uses the fixed HTTPS API path, not a shell command.")
    if provider == "openrouter_free":
        raise AIWorkerError("openrouter_free uses the fixed HTTPS API path, not a shell command.")
    raise AIWorkerError(f"Unknown provider: {provider}.")

def run_task(task: dict[str, Any], provider: str, output: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    if provider not in task["providers"]:
        raise AIWorkerError(f"Provider {provider} is not enabled for this task.")
    runtime_env = dict(os.environ if env is None else env)
    local_mode = _truth(runtime_env.get("TRADING_AGENT_LOCAL_AI_MODE"))
    check = preflight(provider, runtime_env)
    base = {
        "schema_version": 1,
        "task_id": task["task_id"],
        "provider": provider,
        "free_only": True,
        "preflight": check,
        "litellm_transport_enabled": bool(check.get("litellm_transport_enabled")),
        "task_fingerprint": _fingerprint(task),
        "context_fingerprint": context_fingerprint(task),
        "observed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "worker_output_is_scientific_evidence": False,
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    if not check["available"]:
        result = {
            **base,
            "status": "SKIPPED",
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "quota_block": load_block(provider, runtime_env),
        }
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result

    started = time.monotonic()
    if check.get("litellm_transport_enabled"):
        contract = LITELLM_PROVIDER_CONTRACTS[provider]
        api_key_env = contract["api_key_env"]
        try:
            api_result = call_litellm_free(
                provider,
                build_prompt(task, provider),
                api_key=runtime_env.get(api_key_env, ""),
                timeout_seconds=min(60, task.get("max_runtime_minutes", 15) * 60),
            )
        except Exception as exc:
            result = {
                **base,
                "status": "FAILED_PROVIDER",
                "returncode": None,
                "duration_seconds": round(time.monotonic() - started, 3),
                "stdout": "",
                "stderr": f"{type(exc).__name__}: {exc}",
                "command_binary": "litellm",
                "api_model": contract["api_model"],
                "litellm_model": contract["litellm_model"],
            }
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return result
        result = {
            **base,
            "status": api_result["status"],
            "returncode": api_result.get("returncode"),
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout": api_result.get("content", ""),
            "stderr": api_result.get("error", ""),
            "command_binary": "litellm",
            "api_model": contract["api_model"],
            "litellm_model": contract["litellm_model"],
            "response_id": api_result.get("response_id"),
            "response_model": api_result.get("response_model"),
            "usage": api_result.get("usage"),
        }
        if api_result.get("status") == "RATE_LIMITED":
            reset_seconds = parse_reset_seconds(str(api_result.get("error", ""))) or 3600
            result["quota_block"] = record_block(
                provider, reset_seconds, raw_error=str(api_result.get("error", "")), env=runtime_env
            )
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result

    if provider == "mistral_api":
        from automation.mistral_free import call_mistral_free

        try:
            api_result = call_mistral_free(
                build_prompt(task, provider),
                api_key=runtime_env.get("MISTRAL_API_KEY", ""),
                timeout_seconds=min(60, task.get("max_runtime_minutes", 15) * 60),
            )
        except Exception as exc:
            result = {
                **base,
                "status": "FAILED_PROVIDER",
                "returncode": None,
                "duration_seconds": round(time.monotonic() - started, 3),
                "stdout": "",
                "stderr": f"{type(exc).__name__}: {exc}",
                "command_binary": "https-mistral",
                "api_model": "mistral-small-latest",
            }
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
            return result
        result = {
            **base,
            "status": api_result["status"],
            "returncode": api_result.get("returncode"),
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout": api_result.get("content", ""),
            "stderr": api_result.get("error", ""),
            "command_binary": "https-mistral",
            "api_model": "mistral-small-latest",
            "response_id": api_result.get("response_id"),
            "usage": api_result.get("usage"),
        }
        if api_result.get("status") == "RATE_LIMITED":
            reset_seconds = parse_reset_seconds(str(api_result.get("error", ""))) or 300
            result["quota_block"] = record_block(
                provider,
                reset_seconds,
                raw_error=str(api_result.get("error", "")),
                env=runtime_env,
            )
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
        return result
    if provider == "groq_free":
        from automation.groq_free import call_groq_free

        try:
            api_result = call_groq_free(
                build_prompt(task, provider),
                api_key=runtime_env.get("GROQ_API_KEY", ""),
                timeout_seconds=min(60, task.get("max_runtime_minutes", 15) * 60),
            )
        except Exception as exc:
            result = {
                **base,
                "status": "FAILED_PROVIDER",
                "returncode": None,
                "duration_seconds": round(time.monotonic() - started, 3),
                "stdout": "",
                "stderr": f"{type(exc).__name__}: {exc}",
                "command_binary": "https-groq",
                "api_model": "openai/gpt-oss-20b",
            }
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
            return result
        result = {
            **base,
            "status": api_result["status"],
            "returncode": api_result.get("returncode"),
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout": api_result.get("content", ""),
            "stderr": api_result.get("error", ""),
            "command_binary": "https-groq",
            "api_model": "openai/gpt-oss-20b",
            "response_id": api_result.get("response_id"),
            "usage": api_result.get("usage"),
        }
        if api_result.get("status") == "RATE_LIMITED":
            reset_seconds = parse_reset_seconds(str(api_result.get("error", ""))) or 3600
            result["quota_block"] = record_block(
                provider, reset_seconds, raw_error=str(api_result.get("error", "")), env=runtime_env
            )
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
        return result

    if provider == "openrouter_free":
        from automation.openrouter_free import call_openrouter_free

        try:
            api_result = call_openrouter_free(
                build_prompt(task, provider),
                api_key=runtime_env.get("OPENROUTER_API_KEY", ""),
                timeout_seconds=min(60, task.get("max_runtime_minutes", 15) * 60),
            )
        except Exception as exc:
            result = {
                **base,
                "status": "FAILED_PROVIDER",
                "returncode": None,
                "duration_seconds": round(time.monotonic() - started, 3),
                "stdout": "",
                "stderr": f"{type(exc).__name__}: {exc}",
                "command_binary": "https-openrouter",
                "api_model": "openrouter/free",
            }
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return result
        result = {
            **base,
            "status": api_result["status"],
            "returncode": api_result.get("returncode"),
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout": api_result.get("content", ""),
            "stderr": api_result.get("error", ""),
            "command_binary": "https-openrouter",
            "api_model": "openrouter/free",
            "response_id": api_result.get("response_id"),
            "usage": api_result.get("usage"),
        }
        if api_result.get("status") == "RATE_LIMITED":
            reset_seconds = parse_reset_seconds(str(api_result.get("error", ""))) or 3600
            result["quota_block"] = record_block(
                provider,
                reset_seconds,
                raw_error=str(api_result.get("error", "")),
                env=runtime_env,
            )
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result

    command = command_for(provider, build_prompt(task, provider), check.get("binary"))
    try:
        proc = subprocess.run(
            command,
            cwd=Path.cwd(),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=task.get("max_runtime_minutes", 15) * 60,
            check=False,
            env=runtime_env,
        )
    except OSError as exc:
        result = {
            **base,
            "status": "FAILED_PROCESS",
            "returncode": None,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
            "command_binary": command[0],
        }
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result

    stdout = (proc.stdout or "")[-20000:]
    stderr = (proc.stderr or "")[-12000:]
    if quota_error(proc.returncode, stdout, stderr):
        reset_seconds = parse_reset_seconds(f"{stdout}\n{stderr}") or 3600
        block = record_block(
            provider,
            reset_seconds,
            raw_error=f"{stdout}\n{stderr}",
            env=runtime_env,
        )
        result = {
            **base,
            "status": "QUOTA_BLOCKED",
            "returncode": proc.returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout": stdout,
            "stderr": stderr,
            "command_binary": command[0],
            "quota_block": block,
        }
    else:
        result = {
            **base,
            "status": "SUCCESS" if proc.returncode == 0 else "FAILED",
            "returncode": proc.returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout": stdout,
            "stderr": stderr,
            "command_binary": command[0],
        }
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", choices=sorted(PROVIDER_SPECS))
    parser.add_argument("--context-fingerprint", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--provider", choices=sorted(PROVIDER_SPECS))
    parser.add_argument("--task", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.preflight:
        result = preflight(args.preflight)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["available"] else 2
    if args.context_fingerprint:
        if not args.task:
            parser.error("--context-fingerprint requires --task")
        print(context_fingerprint(load_task(args.task)))
        return 0
    if args.run:
        if not args.provider or not args.task or not args.output:
            parser.error("--run requires --provider, --task and --output")
        result = run_task(load_task(args.task), args.provider, args.output)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] in {"SUCCESS", "SKIPPED", "QUOTA_BLOCKED", "RATE_LIMITED"} else 1
    parser.error("Choose --preflight or --run.")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
