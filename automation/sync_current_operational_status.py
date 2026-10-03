"""Generate the canonical, machine-readable current operational project status."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from automation.q067_pipeline_state import summarize as summarize_q067_pipeline
from automation.q068_pipeline_state import summarize as summarize_q068_pipeline
from automation.q070_pipeline_state import summarize as summarize_q070_pipeline

ROOT = Path(__file__).resolve().parents[1]
STATUS_DOC = ROOT / "docs" / "CURRENT_STATUS.md"
STATUS_JSON = ROOT / "research" / "evidence" / "current_operational_state.json"


def _load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def _recent_commits(limit: int = 8) -> list[dict[str, str]]:
    last_error: subprocess.CalledProcessError | None = None
    for ref in ("master", "origin/master", "HEAD"):
        try:
            output = _git(
                "log",
                f"-{limit}",
                "--format=%H%x09%aI%x09%s",
                ref,
            )
        except subprocess.CalledProcessError as exc:
            last_error = exc
            continue
        rows = []
        for line in output.splitlines():
            sha, timestamp, message = line.split("\t", 2)
            rows.append(
                {"sha": sha, "timestamp": timestamp, "message": message}
            )
        return rows
    assert last_error is not None
    raise last_error


def _read_queue_files() -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    root = ROOT / "agent_requests"
    for lane in ("lane0", "lane1"):
        lane_root = root / lane
        if not lane_root.exists():
            continue
        for path in sorted(lane_root.glob("*.request")):
            payload = _load_json(path, {})
            if isinstance(payload, dict):
                results.append(
                    {
                        "lane": lane,
                        "request_file": str(path.relative_to(ROOT)).replace("\\", "/"),
                        "task_id": str(payload.get("task_id", "")),
                        "issue_number": str(payload.get("issue_number", "")),
                    }
                )
    return results


def _safety_state() -> dict[str, bool]:
    from config import settings
    return {
        "PAPER_ONLY": settings.PAPER_ONLY is True,
        "LIVE_TRADING_ENABLED": settings.LIVE_TRADING_ENABLED is True,
        "ORDERS_ENABLED": settings.ORDERS_ENABLED is True,
        "AUTOMATIC_PROMOTION": settings.AUTOMATIC_PROMOTION is True,
    }


def generate(
    *,
    source_master_sha: str,
    workflow_run_id: str | None,
    github_state_path: Path | None,
) -> tuple[dict[str, Any], str]:
    project_state = _load_json(ROOT / "research/evidence/project_state.json", {})
    checkpoint = _load_json(
        ROOT / "research/evidence/current_project_checkpoint.json", {}
    )
    decision_basis = _load_json(
        ROOT / "research/evidence/decision_basis_latest.json", {}
    )
    trial_ledger = _load_json(ROOT / "research/evidence/trial_ledger.json", {})
    ledger_entries = trial_ledger.get("trials", trial_ledger.get("entries", []))
    formal_entries = [
        entry for entry in ledger_entries
        if isinstance(entry, dict)
        and str(entry.get("status", "")).startswith("performance_completed")
    ]
    latest_formal = formal_entries[-1] if formal_entries else {}
    q092_diagnosis = _load_json(ROOT / "research/evidence/q092_q091_failure_mechanism_diagnosis_result.json", {})
    q093_diagnosis = _load_json(ROOT / "research/evidence/q093_q091_cost_attribution_diagnosis_result.json", {})
    github_state = _load_json(github_state_path, {}) if github_state_path else {}
    h06_pit = _load_json(ROOT / "research/evidence/h06_pit_independent_reproduction_2026_10_01.json", {})
    q129_receipt = _load_json(ROOT / "research/evidence/q129_independent_pit_2026_10_03.json", {})
    q133_q170_receipt = _load_json(ROOT / "research/evidence/q133_q170_source_feasibility_2026_10_03.json", {})
    q171_q177_pit_receipt = _load_json(ROOT / "research/evidence/q171_q177_pit_readiness_2026_10_03.json", {})

    safety = _safety_state()
    from config import settings
    queue = _read_queue_files()
    open_prs = github_state.get("open_prs", [])
    agent_ready_issues = github_state.get("agent_ready_issues", [])
    runner_capacity_receipt = _load_json(ROOT / "research/evidence/self_hosted_runner_capacity_2026-09-28.json", {})
    s10_operational_status = _load_json(ROOT / "ops/s10_runtime_status.json", {
        "status": "NOT_YET_SYNCHRONIZED",
        "eligible": False,
        "scientific_evidence": False,
        "performance_authorization": False,
    })
    # S10/Android availability is an orchestration assumption. Receipt freshness remains an evidence/diagnostic signal only.
    # Load the synchronized receipt before evaluating its freshness.
    s10_presence_fresh = False
    s10_presence_observed = (
        s10_operational_status.get("generated_at_utc")
        or s10_operational_status.get("workflow_run_updated_at")
    )
    try:
        observed = datetime.fromisoformat(str(s10_presence_observed).replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        s10_presence_fresh = (
            s10_operational_status.get("status") == "S10_UTILITY_ACCEPTED"
            and s10_operational_status.get("eligible") is True
            and now - observed <= timedelta(hours=6)
            and observed <= now + timedelta(minutes=5)
        )
    except (TypeError, ValueError):
        s10_presence_fresh = False
    active_registry = _load_json(ROOT / "research/governance/active_research_registry.json", {})
    active_trials = {
        str(entry.get("code")): entry
        for entry in active_registry.get("active_trials", [])
        if isinstance(entry, dict)
    }
    q067_pipeline = {
        "family": "Q067",
        "state": "RETIRED",
        "blocking_reasons": ["obsolete execution path retired; historical evidence preserved"],
        "coverage_receipt": {"present": False, "status": None, "trial_id": None},
        "pit_receipt": {"present": False, "status": None, "trial_id": None},
        "performance_authorization": {"present": False, "authorized": False, "execution_scope": None},
        "performance_result": {"present": False, "status": None, "trial_id": None},
        "performance_preregistration": {"present": True, "status": "RETIRED", "trial_id": "historical"},
        "ledger_reconciled": False,
        "no_selection_or_promotion": True,
        "paper_only": True,
    }
    q068_pipeline = {
        "family": "Q068",
        "state": "RETIRED",
        "blocking_reasons": ["obsolete execution path retired; historical evidence preserved"],
        "coverage_receipt": {"present": False, "status": None, "trial_id": None},
        "pit_receipt": {"present": False, "status": None, "trial_id": None},
        "performance_authorization": {"present": False, "authorized": False, "execution_scope": None},
        "performance_result": {"present": False, "status": None, "trial_id": None},
        "performance_preregistration": {"present": True, "status": "PERMANENTLY_BLOCKED", "trial_id": "T-2026-09-28-068-PERFORMANCE"},
        "ledger_reconciled": False,
        "no_selection_or_promotion": True,
        "paper_only": True,
    }
    q091_registry = active_trials.get("091", {})
    q091_state = str(q091_registry.get("state", "UNKNOWN"))
    q091_authorized = q091_registry.get("performance_authorization_allowed") is True

    q070_pipeline = {
        "family": "Q070",
        "state": "PERMANENTLY_BLOCKED",
        "blocking_reasons": ["frozen snapshot unrecoverable; execution workflows retired"],
        "coverage_receipt": {"present": True, "status": "COVERAGE_PASSED", "trial_id": "T-2026-09-28-070-COVERAGE"},
        "pit_receipt": {"present": True, "status": "PIT_PASSED", "trial_id": "T-2026-09-28-070-PIT"},
        "performance_authorization": {"present": False, "authorized": False, "execution_scope": None},
        "performance_result": {"present": False, "status": None, "trial_id": None},
        "performance_preregistration": {"present": True, "status": "PERMANENTLY_BLOCKED", "trial_id": "T-2026-09-28-070-PERFORMANCE"},
        "ledger_reconciled": False,
        "no_selection_or_promotion": True,
        "paper_only": True,
    }
    recorded_qa = project_state.get("quality_assurance", {}).get(
        "last_verified_self_hosted_qa", {}
    )

    recorded_next_research_focus = project_state.get("next_research_focus")
    # Keep operational status aligned with the actual ledger/active-design frontier.
    # project_state.json contains historical planning context and can lag behind
    # newly completed formal trials; this override changes documentation only.
    if (
        latest_formal.get("status", "").startswith("performance_completed")
        and (ROOT / "automation/q100_frontier_feasibility_synthesis.py").is_file()
    ):
        recorded_next_research_focus = (
            "Q099 diagnostic-only is complete and must not be used to retune Q081R4. "
            "Next gate is Q100 frontier feasibility synthesis, followed by the predeclared "
            "frontier source/PIT gates for C29/C30/C31/M4/M5 and Q097/C32/C33. "
            "No step in this sequence creates performance authorization; only an exact, "
            "fresh, ex-ante preregistered contract may do so."
        )
    if (
        latest_formal.get("trial_id") == "T-2026-09-30-081R4-PERFORMANCE"
        and latest_formal.get("status") == "performance_completed_no_arm_passed_all_13_gates"
    ):
        recorded_next_research_focus = (
            "Q099 diagnostic-only completed on the immutable Q081-R4 result; no retune or repeat "
            "of Q081-R4 is authorized. Next gate is Q100 frontier feasibility synthesis, followed "
            "by the predeclared frontier data/PIT gates (C29 fresh input contract; M4 PIT industry "
            "mapping; C30/C31/M5/Q097 source/archive contracts). No performance authorization is "
            "created by these feasibility steps."
        )
    if (ROOT / "research/preregistrations/q105_q104_historical_pit_2026_10_01.json").is_file():
        recorded_next_research_focus = (
            "Q104 source-feasibility completed for 5 data-backed candidates; Q105 historical "
            "archive/PIT feasibility, Q106 shared PIT join integrity, Q107 fresh disjoint coverage "
            "and Q108 real SEC/XBRL/13F/Treasury PIT integration are completed. The active gates "
            "are now candidate-specific: I19/I20 require full 13F security coverage and manager/"
            "issuer mapping; I22 has issuer-filing PIT verified and requires a frozen signal compiler; "
            "M6 has Treasury PIT verified and can reuse the existing Q023/Q024/Q025 event contract; "
            "I21 remains historically window-limited; R9 remains synthetic-only. No performance "
            "authorization, holdout selection, parameter search, promotion or live execution is "
            "permitted by Q104-Q108."
        )
    if (ROOT / "research/preregistrations/q113_13f_q107_coverage_2026_10_01.json").is_file():
        recorded_next_research_focus = (
            "Q112 live SEC identity feasibility completed dual-architecture with 3/3 source "
            "families verifiable and zero schema mismatches. Q113 is now the active feasibility "
            "gate: one fixed official 13F quarter is scanned against the eight-symbol Q107 "
            "fresh universe with deterministic Q111 identity resolution and manager/accession "
            "lineage. If Q113 passes, the next candidate-specific compiler gates are I22 "
            "(frozen filing-arrival state), M6 (fixed Treasury event contract), and the remaining "
            "I19/I20 historical breadth requirements. No performance authorization, holdout "
            "selection, parameter search, promotion or live execution is permitted."
        )
    if (ROOT / "research/evidence/q116_13f_transition_population_result.json").is_file():
        q116_receipt = _load_json(ROOT / "research/evidence/q116_13f_transition_population_result.json", {})
        if q116_receipt.get("status") == "13F_TWO_QUARTER_TRANSITION_FEASIBILITY_ONLY":
            recorded_next_research_focus = (
                "Q112/Q113/Q114/Q115 are complete and Q116 now has an immutable two-quarter 13F "
                "transition-population receipt. Q116 remains feasibility-only: the frozen 2026-03-to-08 "
                "SEC datasets produced a deterministic manager/security transition population with PIT "
                "cutoff invariants, but no performance evaluation or candidate selection occurred. Next "
                "candidate-specific frontier work is I22 filing-arrival compilation plus a separate, "
                "deterministic XBRL concept/coverage gate for I19/I20. No performance authorization, "
                "holdout selection, parameter search, promotion or live execution is permitted."
            )

    if (ROOT / "research/preregistrations/q117_treasury_demand_population_2026_10_01.json").is_file():
        recorded_next_research_focus = (
            "Q112 and Q113 are complete: live SEC identity is verified on 13F/N-PORT/Form 4 "
            "and the fixed 2026-06-to-08 13F universe scan found all 8 Q107 symbols with manager "
            "and CUSIP coverage. Q114/Q115 deterministic compilers are contract-complete; Q117 "
            "verified 89 historical 10-Year Treasury auction events and compiled demand states. "
            "Q116 is the active two-quarter 13F transition population gate and must remain "
            "fail-closed until its immutable receipt validates. Next candidate-specific frontier "
            "work is I22 filing-arrival compilation plus I19/I20 institutional-demand joins. "
            "No performance authorization, holdout selection, parameter search, promotion or "
            "live execution is permitted."
        )

    if (ROOT / "research/evidence/q116_13f_transition_population_result.json").is_file():
        q116_receipt = _load_json(ROOT / "research/evidence/q116_13f_transition_population_result.json", {})
        if q116_receipt.get("status") == "13F_TWO_QUARTER_TRANSITION_FEASIBILITY_ONLY":
            recorded_next_research_focus = (
                "Q112/Q113/Q114/Q115 are complete and Q116 now has an immutable two-quarter 13F "
                "transition-population receipt. Q116 remains feasibility-only: the frozen 2026-03-to-08 "
                "SEC datasets produced a deterministic manager/security transition population with PIT "
                "cutoff invariants, but no performance evaluation or candidate selection occurred. Next "
                "candidate-specific frontier work is I22 filing-arrival compilation plus a separate, "
                "deterministic XBRL concept/coverage gate for I19/I20. No performance authorization, "
                "holdout selection, parameter search, promotion or live execution is permitted."
            )
    if (ROOT / "research/evidence/q171_q177_pit_readiness_2026_10_03.json").is_file():
        recorded_next_research_focus = (
            "Priority frontier is Q171-Q178 public-domain orthogonal information research plus Q126-Q132. "
            "Q171 has sample-level Common Crawl historical capture reconstruction; Q174-Q177 have source-clock "
            "or version semantics confirmed but require candidate-specific PIT compilers; Q173 remains license-blocked. "
            "Q172/Q178 now have separate GitHub Advisory endpoint and OSV-format source contracts. All remain "
            "discovery/PIT-only with no performance, holdout selection, tuning, ranking, promotion or live execution."
        )
    elif (ROOT / "automation/q126_q132_frontier_feasibility.py").is_file():
        recorded_next_research_focus = (
            "Priority frontier is now the orthogonal SEC/13F/XBRL/Treasury/CFTC channel block plus "
            "Q121 and Q126-Q132. Q121 has a fixed SEC acceptance-time discovery/PIT compiler. "
            "Q126 reuses frozen SEC filing-arrival components; Q127 uses FINRA Reg-SHO daily short "
            "volume with revision-aware publication timing; Q128/Q129 remain blocked until a free, "
            "reproducible historical options source is established; Q130 remains blocked until a "
            "timestamped reproducible public attention history is established; Q131 has source access "
            "but its disclosure-complexity definition is not yet frozen; Q132 has a deterministic "
            "fixed-decomposition synthetic contract. Q119/Q120/Q122 remain active Treasury/CFTC "
            "source/PIT work. None of these states authorizes performance, holdout selection, tuning, "
            "promotion or live execution."
        )

    current = {
        "schema_version": "1.0",
        "status_type": "current_operational_project_state",
        "repository": "DWR-debug/trading-agent-public",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_master_sha": source_master_sha,
        "status_commit_is_documentation_only": True,
        "canonical_sources": {
            "human_current_status": "docs/CURRENT_STATUS.md",
            "machine_current_status": "research/evidence/current_operational_state.json",
            "project_context": "docs/PROJECT_CONTEXT.md",
            "historical_status": "PROJECT_STATUS.md",
            "research_state": "research/evidence/project_state.json",
            "research_checkpoint": "research/evidence/current_project_checkpoint.json",
            "research_decision_basis": "research/evidence/decision_basis_latest.json",
            "trial_ledger": "research/evidence/trial_ledger.json",
            "active_research_registry": "research/governance/active_research_registry.json",
            "research_os_source_registry": "research/governance/research_os_source_registry_2026_09_30.json",
            "resource_availability_policy": "research/governance/resource_availability_policy_2026_10_03.json",
        },
        "active_research_registry": active_registry,
        "repository_state": {
            "default_branch": "master",
            "recent_commits": _recent_commits(),
            "open_pull_requests": open_prs,
            "open_agent_ready_issues": agent_ready_issues,
            "agent_queue_requests": queue,
        },
        "engineering_state": {
            "paper_forward": {
                "status": "MERGED",
                "merge_commit": "a1536a2531ff8341b2ab25a8cdd0012a22e3e3ba",
                "pr": 352,
                "components": [
                    "closed-candle Binance market feed",
                    "persistent autonomous update loop",
                    "schema-v2 per-candle MTM ledger",
                    "paper-only safety guard",
                    "persistent fingerprint integrity checks",
                ],
            },
            "canonical_data_layer": {
                "status": "MERGED",
                "merge_commit": "d81c4399260145e21156064ab76fad77a9969222",
                "pr": 232,
            },
            "agent_orchestration": {
                "bounded_two_lane_queue": True,
                "control_plane": "automation/autonomous_control_plane.py",
                "copilot_cli_queue": ".github/workflows/agent-request-queue.yml",
                "copilot_protected_reserve": {
                    "starts_utc": "2026-10-01T00:00:00Z",
                    "max_sessions_per_month": 4,
                    "max_ai_credits_per_session": 30,
                    "max_parallel_sessions": 1,
                    "paid_fallback_allowed": False,
                    "overages_allowed": False,
                    "entitlement_is_live_verified_at_dispatch": True,
                },
                "self_hosted_parallel_slots": 2,
                "local_ai_smoke_after_research_lanes": True,
                "current_pending_requests": queue,
            },
            "resource_availability_policy": {
                "self_hosted_windows": "ASSUMED_ALWAYS_AVAILABLE",
                "s10": "ASSUMED_ALWAYS_AVAILABLE",
                "android_fleet": "ASSUMED_ALWAYS_AVAILABLE",
                "routing_may_use_assumed_capacity": True,
                "receipts_remain_diagnostic_and_evidentiary": True,
                "assumption_does_not_authorize_scientific_evidence": True,
            },
            "research_os": {
                "version": "ROS-0.1",
                "source_registry": "research/governance/research_os_source_registry_2026_09_30.json",
                "layers": ["source_fabric", "evidence_bus", "research_compiler", "agent_mesh", "sandbox_execution_boundary", "decision_state"],
                "performance_authorization_from_os": False,
                "agent_output_is_scientific_evidence": False,
            },
            "s10_phone": {
                "status": s10_operational_status.get("status"),
                "eligible": s10_operational_status.get("eligible") is True,
                "receipt_eligible": s10_operational_status.get("receipt_eligible", s10_operational_status.get("eligible") is True),
                "orchestration_available": True,
                "availability_policy": "ASSUMED_ALWAYS_AVAILABLE",
                "current_online": s10_operational_status.get("current_online"),
                "current_online_verification": s10_operational_status.get("current_online_verification", "NOT_PERFORMED"),
                "presence_signal": "fresh_successful_s10_run" if s10_presence_fresh else "stale_or_unverified_receipt",
                "routing_uses_presence_receipt": False,
                "presence_signal_fresh": s10_presence_fresh,
                "eligibility_basis": "fresh_successful_utility_receipt" if s10_presence_fresh else s10_operational_status.get("eligibility_basis", "completed_workflow_acceptance_receipt"),
                "receipt_status": s10_operational_status.get("receipt_status"),
                "workflow_run_id": s10_operational_status.get("workflow_run_id"),
                "source_commit": s10_operational_status.get("source_commit"),
                "artifact_id": s10_operational_status.get("artifact_id"),
                "acceptance_receipt_sha256": s10_operational_status.get("acceptance_receipt_sha256"),
                "scientific_evidence": False,
                "performance_authorization": False,
                "candidate_selection": False,
                "candidate_ranking": False,
                "promotion": False,
            },
            "continuous_qa": {
                "cadence": "15 */6 * * *",
                "runner": "GitHub-hosted windows-latest",
                "matrix_lanes": ["repo_qa"],
                "self_hosted_slots_consumed": 0,
                "architecture": "single bounded hosted QA lane",
                "runner_capacity_last_verified": runner_capacity_receipt,
                "last_recorded_verified_baseline": recorded_qa,
            },
            "research_continuity": {
                "permanent_self_hosted_loop": {"cadence": "*/30 * * * *", "parallel_lanes": 2},
                "hosted_research_failover": {
                    "cadence": "manual",
                    "mode": "manual_only_under_assumed_always_available_self_hosted_pool",
                },
                "continuous_qa": {
                    "cadence": "15 */6 * * *",
                    "runner": "GitHub-hosted windows-latest",
                    "self_hosted_slots_consumed": 0,
                },
                "free_ai_worker_fabric": {
                    "cadence": "0 */6 * * *",
                    "authenticated_providers_only": True,
                },
                "s10_phone": {
                    "cadence": "0 */6 * * *",
                    "event_driven": True,
                    "orchestration_available": True,
                    "availability_policy": "ASSUMED_ALWAYS_AVAILABLE",
                    "receipt_gated_for_routing": False,
                    "receipt_required_for_evidence": True,
                    "formal_evidence_allowed": False,
                },
                "android_fleet": {
                    "orchestration_available": True,
                    "availability_policy": "ASSUMED_ALWAYS_AVAILABLE",
                    "receipt_required_for_evidence": True,
                    "formal_evidence_allowed": False,
                },
                "bounded_agent_queue": {
                    "cadence": "15 */2 * * *",
                    "paid_fallback_allowed": False,
                },
                "principle": (
                    "idle runners are capacity, not a defect; the scheduler should keep meaningful "
                    "work flowing without duplicate or artificial jobs"
                ),
            },
            "deep_frontier_source_feasibility": {
                "workflow": ".github/workflows/deep-frontier-source-feasibility.yml",
                "cadence": "17 */12 * * *",
                "runner": "ubuntu-24.04",
                "formal_evidence_allowed": False,
                "purpose": "public/free source and PIT feasibility only",
            },
            "hosted_deterministic_frontier": {
                "workflow": ".github/workflows/hosted-deterministic-frontier.yml",
                "cadence": "*/10 * * * *",
                "runner": "ubuntu-24.04",
                "purpose": "deterministic frontier QA/research workpack rotation without consuming scarce Windows capacity",
                "workpack_rotation": "three equal 10-step packs cover all 30 autonomous_frontier_qa steps",
                "formal_evidence_allowed": False,
            },
            "scientific_compute": {
                "canonical_path": "GitHub-hosted deterministic workflows",
                "self_hosted_output_formal_evidence": False,
            },
        },
        "q067_execution_pipeline": q067_pipeline,
        "q068_execution_pipeline": q068_pipeline,
        "q070_execution_pipeline": q070_pipeline,
        "h06_independent_pit": h06_pit,
        "q129_options": q129_receipt,
        "q133_q170_source_feasibility": q133_q170_receipt,
        "q171_q177_pit_readiness": q171_q177_pit_receipt,
        "scientific_state_recorded": {
            "latest_formal_trial": latest_formal.get("trial_id") or project_state.get("latest_formal_trial"),
            "latest_formal_status": latest_formal.get("status") or project_state.get("latest_trial_status"),
            "next_research_focus_recorded": recorded_next_research_focus,
            "decision_basis_stage": decision_basis.get("current_stage"),
            "q026_recorded": checkpoint.get("q026"),
            "q025_recorded": checkpoint.get("q025"),
            "q023_recorded": checkpoint.get("q023"),
            "note": "Latest recorded research state; not re-evaluated by this synchronizer.",
        },
        "resource_policy": {
            "paid_agent_budget_usd": 0,
            "paid_api_budget_usd": 0,
            "free_resources_only": True,
            "actual_capital_available": False,
            "hypothetical_reference_capital_eur": float(settings.HYPOTHETICAL_STARTING_CAPITAL_EUR),
            "legacy_operational_canary_capital_eur": 500.0,
            "copilot_protected_reserve": {
                "starts_utc": "2026-10-01T00:00:00Z",
                "max_sessions_per_month": 4,
                "max_ai_credits_per_session": 30,
                "max_parallel_sessions": 1,
                "paid_fallback_allowed": False,
                "overages_allowed": False,
            },
        },
        "operator_action_required": {
            "purpose": "Keep both self-hosted Windows research runners available for autonomous parallel work.",
            "windows_shells": 2,
            "instruction": "Open two PowerShell windows. Keep the existing Runner #1 window running. Use the second window for Runner #2 and, when a runner activation or reconfiguration is required, paste the resulting non-secret commands/output into the current trading-agent chat so the orchestration can verify the state.",
            "runner_1": "Keep the existing runner process alive in PowerShell window 1.",
            "runner_2": "Keep LHT-N133732-2 alive in PowerShell window 2.",
            "secret_rule": "Never paste GitHub registration tokens, API keys, OAuth tokens, passwords, or other credentials into chat; redact them before sharing output.",
            "service_note": "Windows service installation is a separate maintenance step and requires administrator privileges; do not migrate a runner to service mode until its local AI identity has been verified because Antigravity CLI authentication uses the local user's system keyring or Google Sign-In context.",
        },
        "safety": safety,
        "workflow": {
            "name": "Current Operational Status Synchronizer",
            "run_id": workflow_run_id,
            "purpose": "Keep current operational status synchronized with master without mutating scientific evidence.",
        },
    }

    if (
        not safety["PAPER_ONLY"]
        or safety["LIVE_TRADING_ENABLED"]
        or safety["ORDERS_ENABLED"]
        or safety["AUTOMATIC_PROMOTION"]
    ):
        current["safety"]["status"] = "VIOLATION"
    else:
        current["safety"]["status"] = "SAFE"

    current_json = json.dumps(current, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    doc = f"""# Trading Agent — Current Operational Status

**Current operational snapshot:** `{source_master_sha}`

**Generated (UTC):** `{current['generated_at_utc']}`

**Repository:** `DWR-debug/trading-agent-public`

> This file is the canonical current operational status. `PROJECT_STATUS.md` is historical reconstruction and must not override it for current operational facts. Scientific evidence remains governed by the trial ledger, immutable evidence/checkpoints and workflow artifacts.

## Current state

### Engineering

- Paper/Shadow/Forward infrastructure: **MERGED** via PR #352, merge commit `a1536a2531ff8341b2ab25a8cdd0012a22e3e3ba`.
- The Forward path contains closed-candle market-data ingestion, a persistent update loop and a schema-v2 per-candle MTM ledger.
- Canonical data-layer infrastructure is merged.
- Bounded agent routing uses two queue lanes with fail-closed task contracts.
- Continuous QA is scheduled every 6 hours on GitHub-hosted Windows and uses only the bounded `repo_qa` lane; it consumes no self-hosted Windows research slot.
- The deterministic frontier loop runs every 10 minutes on free GitHub-hosted Ubuntu; its three 10-step packs cover all 30 frontier-worker steps.
- Windows Self-Hosted capacity is always routable for bounded local reproduction, data QA, local-AI and hardware-dependent work; two physical slots are intended to run in parallel.
- Latest self-hosted capacity verification: two distinct Windows/X64 runner slots accepted concurrent jobs; see the timestamped capacity receipt.
- S10 phone capability receipt: **{s10_operational_status.get("status", "NOT_YET_SYNCHRONIZED")}**; routing availability is **ASSUMED_ALWAYS_AVAILABLE** and is independent of receipt freshness.
- S10 current physical online state is intentionally not treated as a routing blocker; the OS availability policy assumes the configured S10 resource is always routable.
- Fresh S10 receipts remain mandatory to substantiate successful execution and device-derived evidence. Receipt freshness does not remove the resource from the routing pool.
- Universal pre-formal candidate robustness gate: **ACTIVE**; structural candidate robustness must pass before PREREGISTRATION, SOURCE_FEASIBILITY, COVERAGE, PIT or PERFORMANCE formal phases.
- S10 output remains non-scientific and cannot authorize performance or promotion.

### Scientific status

- Latest recorded formal result: **{latest_formal.get("status", project_state.get("latest_trial_status", "UNKNOWN"))}** for `{latest_formal.get("trial_id", project_state.get("latest_formal_trial", "UNKNOWN"))}`.
- Q026 is recorded as **DATA_INVALID / NO_SCIENTIFIC_OUTCOME**; it did not produce performance evidence.
- Q023 is recorded as **COVERAGE_VALIDATED** and Q025 as **DATE_PIT_VALIDATED**; these are data-contract findings, not promotion evidence.
- No current candidate is authorized for promotion or live execution.
- Q091 fixed-portfolio performance is **AUTHORIZED** only when the active registry says so; the one-shot performance workflow remains fail-closed and consumes authorization only through immutable reconciliation.

### Active research registry

- Q081-R2: **{active_trials.get("081R2", {}).get("state", "PREREGISTERED_WAITING_PREFLIGHT")}**; infrastructure-rebased corrective reproduction; no performance authorization.
- Q089: **{active_trials.get("089", {}).get("state", "UNKNOWN")}**; fresh symbol-disjoint successor to quarantined Q086; separate performance authorization remains required.
- Q077-R1: **{active_trials.get("077R1", {}).get("state", "PREREGISTERED_WAITING_PREFLIGHT")}**; coverage-only repair after the original Q077 pool left insufficient unused symbols; no performance authorization.
- Q091: **{q091_state}**; fixed portfolio architecture on the fresh symbol-disjoint universe; performance authorization flag = **{q091_authorized}**.
- Q092: **{q092_diagnosis.get("status", "DIAGNOSTIC_COMPLETED_ONLY")}**; post-performance Q091 failure-mechanism diagnosis; no performance authorization.
- Q093: **{q093_diagnosis.get("status", "DIAGNOSTIC_COMPLETED_ONLY")}**; Q091 turnover/cost attribution diagnosis; no performance authorization.
- Q094: **{active_trials.get("094", {}).get("state", "UNKNOWN")}**; fixed monthly-rebalance successor to the Q091 low-turnover diagnosis; performance authorization flag = **{active_trials.get("094", {}).get("performance_authorization_allowed", False)}**.
- Q084, Q088 and Q082 remain **design/feasibility tracks** for unusual market-state, textual-network, rebalance-demand and SEC information channels.
- The unusual-strategy frontier is maintained in `docs/research_design/RESEARCH_FRONTIER_UNUSUAL_2026-09-28.md` and is design-only until feasibility and provenance are established.
- Research OS capability lattice: `research/governance/research_os_source_registry_2026_09_30.json`; it is metadata only and cannot authorize performance.
- Q104 orthogonal candidate wave: **SOURCE_FEASIBILITY_COMPLETED_DUAL_ARCH**; 5/6 data-backed candidates are source-feasible and Q104:R9 is synthetic-only. The archived receipt is `research/evidence/q104_source_feasibility_2026_10_01.json`.
- Q105 historical archive/PIT feasibility: **COMPLETED**, with I21 remaining historically window-limited.
- Q106 shared SEC/Treasury PIT join integrity: **COMPLETED_DUAL_ARCH**.
- Q107 fresh Q104 equity coverage: **COMPLETED**; 8/8 symbols and 3,704 common sessions.
- Q108 real SEC/XBRL/13F/Treasury PIT integration: **COMPLETED_DUAL_ARCH**; 8/8 issuer filings and 8/8 XBRL lineage verified, 13F sample and Treasury chain verified.
- Candidate-specific next gates: I19/I20 = full 13F security coverage; I22 = frozen event-state compiler; M6 = fixed Treasury state reuse; I21 = explicit bounded historical horizon; R9 = synthetic-only.

### Q129 Options Source / PIT

- Q129 historical options source-feasibility: **COMPLETED** on hosted Linux with pinned release hashes verified.
- Independent Q129 PIT/structural reproduction: **REPRODUCED**; workflow run `37123847841`, receipt fingerprint `41d723734f030d1a212f5eb4b3e6467223a5cfcdeb97c77ffa9713f8889c7587`.
- The fixed downstream view preserves raw rows and quarantines quote/calendar anomalies deterministically; same-day use remains **False**.
- This receipt does **not** authorize performance, holdout selection, ranking, tuning, promotion or live execution.

### Q171–Q178 Public Source Frontier

- Source-feasibility run: **COMPLETED** on master; Q171, Q172, Q174–Q177 and Q178 passed source probes; Q173 remains license-blocked.
- PIT-readiness: Q171 has a sample historical Common Crawl reconstruction receipt; Q174–Q177 have source-clock/version/revision semantics confirmed but are **not yet candidate-specific PIT-valid**.
- No member of this wave is performance-authorized; no holdout selection, tuning, ranking, promotion or live execution is permitted.

### Q133–Q170 Public Source Frontier

- Hosted discovery/source-feasibility run: **COMPLETED**; 25 source probes passed across Q133–Q170.
- Newly source-feasible candidates include Q137, Q144, Q147–Q151, Q153–Q155, Q157–Q158, Q161–Q169; remaining candidates stay blocked or design-only pending further source/PIT work.
- Source-feasibility is not performance evidence and does not authorize performance, holdout selection, ranking, tuning, promotion or live execution.

### H06 independent PIT

- Status: **{h06_pit.get("status", "NOT_RECORDED")}**.
- Independent reproduction workflow: `{h06_pit.get("independent_reproduction_run_id", "UNKNOWN")}`.
- Canonical coverage workflow: `{h06_pit.get("upstream_coverage_run_id", "UNKNOWN")}`.
- Checked PIT decision points: **{h06_pit.get("data_contract", {}).get("checked_decision_points", "UNKNOWN")}**.
- Semantic check fingerprint: `{h06_pit.get("reconciliation", {}).get("check_fingerprint", "UNKNOWN")}`.
- This is PIT/data-contract evidence only; it does not authorize performance or promotion.

### Q067 execution pipeline

- Operational state: **{q067_pipeline["state"]}**.
- Coverage receipt: **{q067_pipeline["coverage_receipt"]["status"] or "MISSING"}**.
- PIT receipt: **{q067_pipeline["pit_receipt"]["status"] or "MISSING"}**.
- Performance authorization: **{q067_pipeline["performance_authorization"]["authorized"]}**.
- Performance evidence: **{q067_pipeline["performance_result"]["status"] or "MISSING"}**.
- Ledger reconciled: **{q067_pipeline["ledger_reconciled"]}**.
- Blocking reasons: **{"; ".join(q067_pipeline["blocking_reasons"]) or "none"}**.

This is an operational pipeline summary only; it does not create scientific evidence or select a candidate.

### Q068 execution pipeline

- Operational state: **{q068_pipeline["state"]}**.
- Coverage receipt: **{q068_pipeline["coverage_receipt"]["status"] or "MISSING"}**.
- PIT receipt: **{q068_pipeline["pit_receipt"]["status"] or "MISSING"}**.
- Performance authorization: **{q068_pipeline["performance_authorization"]["authorized"]}**.
- Performance evidence: **{q068_pipeline["performance_result"]["status"] or "MISSING"}**.
- Ledger reconciled: **{q068_pipeline["ledger_reconciled"]}**.
- Blocking reasons: **{"; ".join(q068_pipeline["blocking_reasons"]) or "none"}**.

Q068 is a fresh symbol-disjoint validation of the unchanged Q067 E1/E2 mechanisms. This operational summary does not create scientific evidence or select an arm.

### Q070 execution pipeline

- Operational state: **{q070_pipeline["state"]}**.
- Coverage receipt: **{q070_pipeline["coverage_receipt"]["status"] or "MISSING"}**.
- PIT receipt: **{q070_pipeline["pit_receipt"]["status"] or "MISSING"}**.
- Performance preregistration: **{q070_pipeline["performance_preregistration"]["status"] or "MISSING"}**.
- Performance authorization: **{q070_pipeline["performance_authorization"]["authorized"]}**.
- Performance evidence: **{q070_pipeline["performance_result"]["status"] or "MISSING"}**.
- Ledger reconciled: **{q070_pipeline["ledger_reconciled"]}**.
- Blocking reasons: **{"; ".join(q070_pipeline["blocking_reasons"]) or "none"}**.

Q070 is the fresh symbol-disjoint validation pipeline for the fixed Q069 OHLCV candidate bank. This operational summary does not create scientific evidence or rank candidates.

### Operator action when runner capacity is being (re)activated

- Open **two PowerShell windows** on the Windows research PC.
- Keep the existing Runner #1 process running in window 1.
- Use window 2 for Runner #2 (LHT-N133732-2).
- When activation/reconfiguration is needed, paste the resulting **non-secret** commands/output into the current "trading agent" chat so the orchestration can verify the live state.
- **Never paste registration tokens, API keys, OAuth tokens or passwords into chat.**
- Do not switch a runner to Windows service mode until local AI authentication has been verified; Windows service mode requires administrative privileges and can change the user/keyring context available to local AI CLIs.

### Resource policy

- Paid agent/API budget: **0 USD**.
- Actual available capital: **0 EUR**.
- Hypothetical reference capital: **{int(settings.HYPOTHETICAL_STARTING_CAPITAL_EUR)} EUR**, simulation/planning only.
- Legacy 500-EUR operational canary remains separate.
- Deterministic research stays on reproducible runner paths.
- Agent output is never scientific evidence by itself.
- Protected Copilot reserve starts **2026-10-01T00:00:00Z**: at most 4 sessions/month, 30 AI credits/session, 1 concurrent session; actual entitlement is verified at dispatch and no paid fallback/overage is permitted.
- Permanent research continuity uses the two self-hosted Windows lanes every 30 minutes, free-AI rotation every 6 hours when authenticated, always-routable S10/Android utility capacity, and bounded agent dispatch every 2 hours. Hosted research failover is manual-only.

## Safety

`PAPER_ONLY=True`

`LIVE_TRADING_ENABLED=False`

`ORDERS_ENABLED=False`

`AUTOMATIC_PROMOTION=False`

## Canonical source order

1. Current operational facts: `docs/CURRENT_STATUS.md` and `research/evidence/current_operational_state.json`
2. Technical truth: current `master`
3. Scientific evidence: trial ledger, immutable evidence/checkpoints and workflow artifacts
4. Project intent: `docs/PROJECT_CONTEXT.md`
5. Historical reconstruction: `PROJECT_STATUS.md`

## Continuity protocol

Every relevant `master` push triggers the status synchronizer. It records the exact source commit being synchronized and updates these two operational-status files in a documentation-only commit. Those files are excluded from the synchronizer trigger, preventing recursive commits.

A future `trading agent` chat must read this file first, then verify live GitHub state before acting.
"""
    return current, doc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-master-sha", required=True)
    parser.add_argument("--workflow-run-id")
    parser.add_argument("--github-state")
    parser.add_argument("--output-doc", default=str(STATUS_DOC))
    parser.add_argument("--output-json", default=str(STATUS_JSON))
    args = parser.parse_args()

    current, doc = generate(
        source_master_sha=args.source_master_sha,
        workflow_run_id=args.workflow_run_id,
        github_state_path=Path(args.github_state) if args.github_state else None,
    )
    doc_path = Path(args.output_doc)
    json_path = Path(args.output_json)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(doc, encoding="utf-8")
    json_path.write_text(
        json.dumps(current, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if current["safety"]["status"] == "SAFE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
