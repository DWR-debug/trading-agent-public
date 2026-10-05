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
CHAT_HANDOFF = ROOT / "research" / "evidence" / "trading_agent_chat_handoff.json"


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


def _candidate_stage(receipt: dict[str, Any], candidate_id: str) -> str:
    for row in receipt.get("candidate_results", []):
        if isinstance(row, dict) and row.get("candidate_id") == candidate_id:
            return str(row.get("status", "NOT_RECORDED"))
    return "NOT_RECORDED"

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
    q148_r1_receipt = _load_json(ROOT / "research/evidence/q148_r1_wpsr_source_clock_latest.json", {})
    q137_q144_micro_receipt = _load_json(ROOT / "research/evidence/q137_q144_micro_pit_latest.json", {})
    q169_r4_receipt = _load_json(ROOT / "research/evidence/q169_noaa_swpc_archive_pit_r4_latest.json", {})
    q171_q177_pit_receipt = _load_json(ROOT / "research/evidence/q171_q177_pit_readiness_2026_10_03.json", {})
    q179_q184_source_receipt = _load_json(ROOT / "research/evidence/q179_q184_source_feasibility_latest.json", {})
    q179_q184_pit_receipt = _load_json(ROOT / "research/evidence/q179_q184_pit_readiness_r1_latest.json", {})
    q185_q186_source_receipt = _load_json(ROOT / "research/evidence/q185_q186_source_feasibility_latest.json", {})
    q185_q186_pit_receipt = _load_json(ROOT / "research/evidence/q185_q186_pit_readiness_r1_latest.json", {})
    q186_pit_r2_receipt = _load_json(ROOT / "research/evidence/q186_pit_readiness_r2_latest.json", {})
    q197_q198_source_receipt = _load_json(ROOT / "research/evidence/q197_q198_source_feasibility_latest.json", {})
    q199_q201_source_receipt = _load_json(ROOT / "research/evidence/q199_q201_source_feasibility_latest.json", {})
    q198_pit_clock_receipt = _load_json(ROOT / "research/evidence/q198_pit_clock_census_latest.json", {})
    q202_q204_source_receipt = _load_json(ROOT / "research/evidence/q202_q204_information_timing_feasibility_latest.json", {})
    source_pit_frontier_outcomes = _load_json(ROOT / "research/evidence/source_pit_frontier_outcomes_2026_10_03.json", {})
    q121_r5_receipt = _load_json(ROOT / "research/evidence/q121r5_dual_index_population_reconciliation_2026_10_03.json", {})
    q121_r6_attempts = _load_json(ROOT / "research/evidence/q121r6_execution_attempts_2026_10_03.json", {})

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
    rolling_capacity_lease = _load_json(
        ROOT / "research/run_requests/rolling_capacity_window_2026-10-05.json",
        {"status": "NOT_RECORDED"},
    )
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
    # The historical q126 branch was left as an empty elif. Keep the newer
    # correction/frontier overrides below independent of that legacy condition.
    # Explicitly surface newly active correction tracks so the human current-status document
    # cannot be dominated by an older frontier override. Scientific boundaries remain unchanged.
    if (
        (ROOT / "research/preregistrations/q121r1_sec_reverse_issuer_coverage_2026_10_03.json").is_file()
        or (ROOT / "research/preregistrations/q121r2_sec_daily_index_reconciliation_2026_10_03.json").is_file()
        or (ROOT / "research/preregistrations/q127r1_finra_regsho_historical_pit_2026_10_03.json").is_file()
        or (ROOT / "research/preregistrations/q131r1_sec_disclosure_complexity_2026_10_03.json").is_file()
    ):
        recorded_next_research_focus = (
            "Active correction tracks: Q121-R1 independently repairs SEC beneficial-ownership issuer "
            "coverage by separating subject-issuer and filer identity; Q121-R2 independently reconciles "
            "deterministic Q121-R1 filing anchors against SEC daily master indexes; Q131-R1 freezes a structural "
            "SEC disclosure-complexity vector; Q127-R1 tests fixed historical "
            "FINRA Reg-SHO source retrieval and preserves the unresolved publication/revision boundary; "
            "Q130-R1 tests Wikimedia Pageviews as a public historical attention proxy while preserving " 
            "the unresolved publication/revision boundary. These are source/PIT feasibility tracks only. " 
            "Q171-Q178 and Q126-Q132 remain active "
            "orthogonal frontier work; Q104/I22/Q119/Q120/Q125 remain formal-readiness work. "
            "No performance authorization, holdout selection, tuning, ranking, promotion or live "
            "execution is created by these tracks."
        )

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

    if source_pit_frontier_outcomes.get("generated_from_verified_workflow_runs") is True:
        recorded_next_research_focus = (
            "Verified 2026-10-03 Source/PIT outcomes: Q121-R1 issuer-oriented SEC browse route was "
            "falsified by its preregistered subject-issuer identity contract; Q121-R2 was therefore "
            "blocked without reconciliation; Q121-R3 completed the official SEC quarterly form-index "
            "route on the frozen window (7 quarters, 61,818 relevant form rows, 3 frozen controls); "
            "Q121-R4 independently completed the SEC quarterly master-index route on the same frozen "
            "window/control set (7 quarters, 61,818 relevant form rows, 3 frozen controls). The two "
            "routes establish source-route feasibility and controlled identity recovery only; same-day "
            "PIT safety, performance and full subject-issuer population reconstruction remain open. "
            "Q127-R1 historical FINRA Reg-SHO retrieval completed but revision lineage and same-day PIT "
            "safety remain unresolved; Q130-R1 historical Wikimedia attention retrieval completed but "
            "its publication/revision boundary remains unresolved; Q131-R1 produced no matching filings "
            "in its fixed preregistered window, so no complexity vector was inferred. Next work is "
            "dual-source Q121 reconciliation/PIT compilation before any performance consideration. No "
            "outcome above authorizes performance, holdout selection, tuning, ranking, promotion or "
            "live execution."
        )

    if q121_r5_receipt.get("research_status") == "Q121R5_DUAL_INDEX_POPULATION_RECONCILIATION_COMPLETED":
        recorded_next_research_focus = (
            "Q121-R5 has now completed the preregistered dual SEC-index population reconciliation: "
            "the official quarterly form.idx and master.idx routes are exactly equal as multisets on "
            "the frozen 2024-02-05 through 2025-09-24 window and four-form scope (61,818 rows; zero "
            "left-only/right-only canonical keys). This establishes source-population equivalence only. "
            "The next Q121 gate is candidate-specific acceptance-timestamp compilation, filing-date "
            "consistency, accession/revision lineage and synthetic boundary testing; same-day PIT safety "
            "and performance remain unproven. No performance, holdout selection, ranking, tuning, "
            "promotion or live execution is authorized."
        )

    if q121_r6_attempts.get("canonical_research") == "Q121-R6 SEC acceptance-time compilation":
        q121_r6_current = q121_r6_attempts.get("attempts", [])[-1] if q121_r6_attempts.get("attempts") else {}
        if q121_r6_current.get("classification") == "CURRENT":
            recorded_next_research_focus = (
                "Q121-R6 is the active formal PIT/source gate. The verified Q121-R5 dual-index "
                "population is fixed at 61,818 rows; current R6 execution is waiting for or using "
                "the two self-hosted Windows research slots. Earlier R6 failures are infrastructure "
                "only (portable tzdata, workspace handoff, artifact path) and have been corrected. "
                "No R6 scientific result is claimed until all 61,818 headers are fetched and "
                "validated and the immutable aggregate receipt passes. Revision lineage and first-public-"
                "availability timing remain separate gates. No performance, holdout selection, "
                "ranking, tuning, promotion or live execution is authorized."
            )

    if q179_q184_pit_receipt.get("status") == "PIT_READINESS_R1_COMPLETED_NO_PERFORMANCE":
        recorded_next_research_focus = (
            "Q179-Q184 is the active Lane-B frontier after source feasibility. Five of six public source probes "
            "pass (Q179/Q180/Q181/Q183/Q184); Q182 FERC eLibrary remains runner-access blocked by HTTP 403. "
            "PIT Readiness R1 is completed without performance: all six candidates have explicit clock/revision/"
            "mapping/archive contracts, but historical archive reconstruction, exact PIT timing where unresolved, "
            "fixed issuer mapping and independent reproduction remain open. No performance, holdout selection, "
            "tuning, ranking, promotion or live execution is authorized."
        )
    elif q179_q184_source_receipt.get("status") == "DISCOVERY_SOURCE_FEASIBILITY_COMPLETED":
        recorded_next_research_focus = (
            "Q179-Q184 source feasibility is active in Lane B. Current receipt is discovery-only; source/PIT "
            "contracts remain candidate-specific and no performance or promotion is authorized."
        )

    if q186_pit_r2_receipt.get("status") == "Q186_PIT_R2_CLOCK_ARCHIVE_COMPLETED_NO_PERFORMANCE":
        recorded_next_research_focus = (
            "Q186 has completed PIT-R2 clock/archive verification only: the official weekly grant clock "
            "and post-2023 eGrant public-access boundary are established on fixed controls, while "
            "citation-publication ordering, historical citation completeness, frozen assignee-to-issuer mapping, "
            "correction/withdrawal lineage and independent reproduction remain open. No performance, holdout "
            "selection, tuning, ranking, promotion or live execution is authorized."
        )

    if q186_pit_r2_receipt.get("status") == "Q186_PIT_R2_CLOCK_ARCHIVE_COMPLETED_NO_PERFORMANCE":
        recorded_next_research_focus = (
            "Q186 has completed PIT-R2 clock/archive verification only: the official weekly grant clock "
            "and post-2023 eGrant public-access boundary are established on fixed controls, while "
            "citation-publication ordering, historical citation completeness, frozen assignee-to-issuer mapping, "
            "correction/withdrawal lineage and independent reproduction remain open. No performance, holdout "
            "selection, tuning, ranking, promotion or live execution is authorized."
        )
    elif q185_q186_pit_receipt.get("status") == "PIT_READINESS_R1_COMPLETED_NO_PERFORMANCE":
        recorded_next_research_focus = (
            "A-priority frontier: Q186 upstream patent-grant shock through a literature-faithful directed "
            "five-year patent-citation dependency graph, and Q185 federal litigation as a deterministic legal-state "
            "machine. Both have completed only contract/source/PIT-readiness work; historical archive coverage, "
            "public dissemination timing, frozen issuer/entity mapping, revision lineage and independent reproduction "
            "remain mandatory. No performance, holdout selection, tuning, ranking, promotion or live execution is authorized."
        )
    elif q185_q186_source_receipt.get("status") == "DISCOVERY_SOURCE_FEASIBILITY_COMPLETED":
        recorded_next_research_focus = (
            "A-priority Q185-Q186 source feasibility is active. Q186 targets upstream patent-grant shocks through "
            "directed five-year citation dependencies; Q185 targets persistent federal litigation states. "
            "Both remain discovery/PIT-only with no performance or promotion authorization."
        )
    if any(str(item.get("code")) == "Q217" for item in active_registry.get("active_design_families", [])):
        recorded_next_research_focus = ("Priority frontier includes Q217 cognitive-processing-friction decomposition alongside Q214-Q216. "
                                         "Q217 remains discovery/PIT-only and must merge into Q131 if it is not empirically distinct.")
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
            "two_lane_research_contract": "research/governance/persistent_research_acceleration_contract.json",
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
            "literature_discovery": {
                "status": "ACTIVE_AND_PERSISTENT",
                "policy": "research/governance/literature_research_policy.json",
                "assistant_automations": ["daily Trading-Agent Literature Radar", "weekly Trading-Agent Deep Research"],
                "repository_scout_workflow": ".github/workflows/literature-frontier-scout.yml",
                "cadence": "daily assistant research + weekly deep research + every-6-hours public metadata scout",
                "principle": "Continuously seek genuinely orthogonal economic mechanisms and public information channels; verify primary sources; cheap-falsify; preserve negative evidence; never use literature discovery for performance selection, holdout tuning, ranking, promotion or live execution.",
                "shortlist_maximum": 4,
                "required_dimensions": [
                    "mechanism_novelty",
                    "orthogonality_to_existing_lineages",
                    "cheap_falsifiability",
                    "source_quality",
                    "historical_pit_feasibility",
                    "entity_mapping_feasibility",
                    "revision_lineage_feasibility",
                    "independent_reproducibility",
                    "expected_information_gain_per_compute"
                ],
                "scientific_authority": False,
                "performance_authorization": False
            },
            "rolling_capacity_waves": {
                "status": rolling_capacity_lease.get("status", "ACTIVE_AND_PERSISTENT"),
                "workflow": ".github/workflows/capacity-saturation-rolling-waves.yml",
                "lease": "research/run_requests/rolling_capacity_window_2026-10-05.json",
                "cadence": "*/10 * * * *",
                "objective": rolling_capacity_lease.get("principle", "maximize useful occupancy of genuinely available free capacity without duplicate or artificial work"),
                "current_window": {
                    "window_id": rolling_capacity_lease.get("window_id"),
                    "start_utc": rolling_capacity_lease.get("start_utc"),
                    "end_utc": rolling_capacity_lease.get("end_utc"),
                    "waves": [p.get("name") for p in rolling_capacity_lease.get("phases", [])]
                },
                "dispatch_rules": [
                    "skip active duplicate work",
                    "skip phase-successful work",
                    "allow only one bounded retry after failure/cancellation",
                    "prefer the smallest suitable free resource",
                    "retain downstream fail-closed scientific gates"
                ],
                "artificial_quota_consumption": False,
                "scientific_authority": False
            },
            "two_lane_research_mode": {
                "status": "ACTIVE",
                "lane_a": {
                    "name": "FORMAL_READINESS",
                    "runner_slot": "Windows self-hosted A",
                    "focus": ["Q104 I19/I20", "I22", "Q119/Q120/Q122", "Q125-F1"],
                    "performance_authorization_from_capacity": False,
                },
                "lane_b": {
                    "name": "FRONTIER_DISCOVERY",
                    "runner_slot": "Windows self-hosted B",
                    "focus": ["Q171-Q178", "Q126-Q132", "public-source/PIT frontier"],
                    "performance_authorization_from_capacity": False,
                },
                "separate_identity_and_outputs": True,
                "shared_mutable_research_state": False,
                "cross_lane_retroactive_mutation": False,
                "performance_capacity_rule": "Three physical slots never create performance authorization; each exact trial requires its own current formal authorization.",
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
                "self_hosted_parallel_slots": 3,
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
                "two_lane_research": {
                    "status": "ACTIVE",
                    "lane_a": "FORMAL_READINESS",
                    "lane_b": "FRONTIER_DISCOVERY",
                    "parallel_slots": 2,
                    "isolation_required": True,
                },
                "permanent_self_hosted_loop": {"cadence": "*/10 * * * *", "parallel_lanes": 2, "lane_roles": ["FORMAL_READINESS", "FRONTIER_DISCOVERY"], "concurrency_model": {"local_reproduction": "trading-agent-windows-research-capacity-v1", "data_qa": "trading-agent-windows-research-data-qa-v1"}, "local_ai_isolated": True},
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
                    "cadence": "event-driven",
                    "trigger_policy": "new_or_materially_changed_bounded_task_contract_only",
                    "authenticated_providers_only": True,
                    "deduplicate_unchanged_task_context": True,
                },
                "s10_phone": {
                    "cadence": "*/20 * * * *",
                    "mode": "adaptive_mechanical_research_qa",
                    "task_rotation": ["PROVENANCE_STATUS","FRONTIER_GOVERNANCE","PIT_CLOCK_AND_LINEAGE","CAPACITY_DISPATCH","NEGATIVE_EVIDENCE_DEDUP"],
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
        "q179_q184_source_feasibility": q179_q184_source_receipt,
        "q179_q184_pit_readiness_r1": q179_q184_pit_receipt,
        "q185_q186_source_feasibility": q185_q186_source_receipt,
        "q185_q186_pit_readiness_r1": q185_q186_pit_receipt,
        "q186_pit_readiness_r2": q186_pit_r2_receipt,
        "q197_q198_source_feasibility": q197_q198_source_receipt,
        "q199_q201_source_feasibility": q199_q201_source_receipt,
        "q198_pit_clock_census": q198_pit_clock_receipt,
        "q202_q204_information_timing_feasibility": q202_q204_source_receipt,
        "source_pit_frontier_outcomes": source_pit_frontier_outcomes,
        "q121_r5_dual_index_reconciliation": q121_r5_receipt,
        "q121_r6_execution_attempts": q121_r6_attempts,
        "scientific_state_recorded": {
            "latest_formal_trial": latest_formal.get("trial_id") or project_state.get("latest_formal_trial"),
            "latest_formal_status": latest_formal.get("status") or project_state.get("latest_trial_status"),
            "next_research_focus_recorded": recorded_next_research_focus,
            "frontier_q197_q201": {
                "Q198": {"stage": _candidate_stage(q197_q198_source_receipt, "Q198")},
                "Q197": {"stage": _candidate_stage(q197_q198_source_receipt, "Q197")},
                "Q199": {"stage": _candidate_stage(q199_q201_source_receipt, "Q199")},
                "Q201": {"stage": _candidate_stage(q199_q201_source_receipt, "Q201")},
                "performance_authorized": False,
            },
            "frontier_q202_q204": {
                "Q202": {"stage": _candidate_stage(q202_q204_source_receipt, "Q202")},
                "Q203": {"stage": _candidate_stage(q202_q204_source_receipt, "Q203")},
                "Q204": {"stage": _candidate_stage(q202_q204_source_receipt, "Q204")},
                "performance_authorized": False,
                "pit_validated": False,
            },
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
            "purpose": "Keep all configured self-hosted Windows research runners available for autonomous parallel work.",
            "windows_shells": 3,
            "instruction": "Open two PowerShell windows. Keep the existing Runner #1 window running. Use the second window for Runner #2 and, when a runner activation or reconfiguration is required, paste the resulting non-secret commands/output into the current trading-agent chat so the orchestration can verify the state.",
            "runner_1": "Keep the existing runner process alive in PowerShell window 1.",
            "runner_2": "Keep LHT-N133732-2 alive in PowerShell window 2.",
            "runner_3": "Keep LHT-N133732-3 alive in PowerShell window 3 for long deterministic runs/independent reproduction.",
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

    frontier_codes = [str(x.get("code")) for x in active_registry.get("active_design_families", []) if x.get("code")]
    current["chat_handoff"] = {"schema_version":"1.0","record_type":"trading_agent_chat_handoff","generated_at_utc":current["generated_at_utc"],"source_master_sha":source_master_sha,"active_frontier":frontier_codes,"next_research_focus":recorded_next_research_focus,"canonical_sources":current["canonical_sources"],"resume_rule":"Treat chat transcript as handoff context only; read this compact artifact, then verify current master, live Actions/runners and scientific evidence before acting.","response_rule":"Keep user-facing output bounded and delta-based; persist material state before reporting completion."}
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
- **Permanent two-lane research mode: ACTIVE.** Lane A = **Formal Readiness** (advanced Coverage/PIT/compiler/provenance/authorization readiness); Lane B = **Frontier Discovery** (orthogonal source/PIT feasibility and cheap falsification). The two Windows slots are isolated by candidate/trial identity, branches/workflows and output/provenance paths. Cross-lane findings cannot retroactively alter a frozen trial.
- Three physical research slots are capacity only: they **never** create performance authorization. A performance run remains individually fail-closed until an exact current formal authorization exists.
- Continuous QA is scheduled every 6 hours on GitHub-hosted Windows and uses only the bounded `repo_qa` lane; it consumes no self-hosted Windows research slot.
- The deterministic frontier loop runs every 10 minutes on free GitHub-hosted Ubuntu; its three 10-step packs cover all 30 frontier-worker steps.
- Windows Self-Hosted capacity is always routable for bounded local reproduction, data QA, local-AI and hardware-dependent work; three physical slots are intended to run in parallel, with Runner C reserved for long deterministic work and independent reproduction.
- Latest self-hosted capacity verification: two distinct Windows/X64 runner slots accepted concurrent jobs; see the timestamped capacity receipt.
- S10 phone capability receipt: **{s10_operational_status.get("status", "NOT_YET_SYNCHRONIZED")}**; routing availability is **ASSUMED_ALWAYS_AVAILABLE** and is independent of receipt freshness.
- S10 current physical online state is intentionally not treated as a routing blocker; the OS availability policy assumes the configured S10 resource is always routable.
- Fresh S10 receipts remain mandatory to substantiate successful execution and device-derived evidence. Receipt freshness does not remove the resource from the routing pool.
- Universal pre-formal candidate robustness gate: **ACTIVE**; structural candidate robustness must pass before PREREGISTRATION, SOURCE_FEASIBILITY, COVERAGE, PIT or PERFORMANCE formal phases.
- S10 output remains non-scientific and cannot authorize performance or promotion.
- **PERMANENT LITERATURE-RESEARCH RULE — ACTIVE:** The Trading Agent continuously searches for new, genuinely orthogonal economic mechanisms, information channels and cross-disciplinary relationships. Discovery is run on a recurring daily/weekly research cadence plus an independent public-metadata scout. Every promising finding is verified against primary sources, separated from existing candidate lineages, cheap-falsified where possible, and scored by novelty, PIT feasibility, reproducibility and information gain per compute. Negative/insufficient findings are retained to prevent cyclic rediscovery. Literature claims never become project evidence by themselves and can never authorize performance, holdout selection, ranking, tuning, promotion or live execution.

### Permanent Capacity Saturation & Rolling Research Waves

- **STATUS: ACTIVE_AND_PERSISTENT.** Useful free compute is continuously routed whenever a real bounded backlog exists.
- **Current two-hour activation:** `{rolling_capacity_lease.get("window_id", "NOT_RECORDED")}`, `{rolling_capacity_lease.get("start_utc", "UNKNOWN")}–{rolling_capacity_lease.get("end_utc", "UNKNOWN")}`.
- **Scheduler:** every 10 minutes; active duplicates are skipped, phase-successful work is not rerun, and only one bounded retry is permitted after failure/cancellation.
- **Wave order:** W1 source/PIT/clock closure -> W2 candidate/contracts and information timing -> W3 next-gate compilation and independent reproduction -> W4 literature discovery/consolidation.
- **Utilization rule:** maximize useful occupancy across Windows A/B/C, hosted Linux, bounded free-AI lanes and S10/mobile support when those resources are reachable and the work is independent and useful. Never manufacture work to consume quota.
- **Continuous background:** the permanent Windows/hosted 10-minute loops remain active; Runner C uses long deterministic research when useful and the bounded 20-minute capacity pulse otherwise.
- **Scientific boundary:** capacity allocation never creates performance authorization, holdout selection, ranking, tuning, promotion or live execution.

### Persistent Literature & Discovery Engine

- **Status: ACTIVE_AND_PERSISTENT.** Literature discovery is a permanent OS capability, not a one-off chat task.
- Recurring assistant research: **daily literature radar** plus **weekly deep research**.
- **Active literature frontier (registry):** {", ".join(frontier_codes)}.
- Repository metadata scout: **every 6 hours** on free GitHub-hosted compute.
- Search domains include information arrival/latency, disclosure breadth and networks, semantic novelty, disagreement, market microstructure, institutional behavior, data revisions/vintages, corporate event sequences, patent/innovation networks, unusual public-domain channels and forward-risk structure.
- Selection rule: maximize genuine mechanism novelty and orthogonality first; then cheap falsifiability, source/PIT feasibility, independent reproducibility and information gain per compute. Maximum shortlist = 4.
- The engine explicitly records **PRUNED / UNVERIFIED / DATA_INSUFFICIENT** paths to prevent rediscovering the same dead ends.
- Literature discovery is quarantined from scientific authority: no performance, holdout selection, ranking, parameter/asset/threshold/horizon search, promotion or live execution.

### Scientific status

- Latest recorded formal result: **{latest_formal.get("status", project_state.get("latest_trial_status", "UNKNOWN"))}** for `{latest_formal.get("trial_id", project_state.get("latest_formal_trial", "UNKNOWN"))}`.
- Q026 is recorded as **DATA_INVALID / NO_SCIENTIFIC_OUTCOME**; it did not produce performance evidence.
- Q023 is recorded as **COVERAGE_VALIDATED** and Q025 as **DATE_PIT_VALIDATED**; these are data-contract findings, not promotion evidence.
- No current candidate is authorized for promotion or live execution.
- Q091 fixed-portfolio performance is **AUTHORIZED** only when the active registry says so; the one-shot performance workflow remains fail-closed and consumes authorization only through immutable reconciliation.

### Active research registry

#### Permanent literature frontier

- **LITERATURE-DISCOVERY-PLANE:** ACTIVE_AND_PERSISTENT; daily/weekly assistant research plus a free 6-hour public-metadata scout. Discovery only.
- **Q211:** patent semantic information state — P1 source/PIT feasibility; distinct from patent publication/citation timing and price-only momentum.
- **Q212:** supply-chain disclosure sentiment propagation — P1 feasibility; network disclosure information only, with historical relationship/PIT requirements explicit.
- **Q213:** news-disagreement elasticity — P2 contingent; remains blocked until multi-year public intraday equity/news PIT feasibility is proven.
- **Q214:** disclosure-implied forward-beta/risk-structure state — P1-RISK; risk-state only, deliberately separated from Q088 peer-return/comomentum.
- All four are discovery-only. Literature claims are not project evidence; no performance, holdout selection, ranking, tuning, promotion or live execution may be derived from them.

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

### Verified Source/PIT Frontier Outcomes — 2026-10-03

- **Q121-R1:** `Q121R1_SOURCE_ROUTE_FALSIFIED`; the preregistered SEC browse route failed its subject-issuer identity contract. The verified workflow receipt records 93 discovered entries and 15 deterministic identity checks; receipt fingerprint `9c9a3a4fa05ccc5aa8e59d254c75577abb60b869dd53ff35505b335424cfbf8e`.
- **Q121-R2:** `Q121R2_BLOCKED_BY_Q121R1_FALSIFICATION`; no independent reconciliation was claimed. Receipt fingerprint `fd7b63d9f05e0cf9abf588c9c2d6c2ff02e2ea413927218de6f4e1c29f9fff97`.
- **Q121-R3:** `Q121R3_FORM_INDEX_ROUTE_FEASIBILITY_COMPLETED`; official SEC quarterly form-index route completed for 7 quarters with 61,818 relevant form rows and 3 frozen controls. Receipt fingerprint `a18abdffe2fde48dc4084d420f0a8d5c6ade92727baa23dcecaad481e9452dc1`.
- **Q121-R4:** `Q121R4_MASTER_INDEX_ROUTE_FEASIBILITY_COMPLETED`; independent SEC quarterly master-index route completed for the same 7-quarter window with 61,818 relevant form rows and 3 frozen controls. Receipt fingerprint `3f5616d6ddc18c0f39a10316fe3cbf69e98be2911741552f8a70d133ba94c076`.
- **Q121-R5:** `Q121R5_DUAL_INDEX_POPULATION_RECONCILIATION_COMPLETED`; the form-index and master-index populations are exactly equal as multisets on the frozen window/form scope: 61,818 rows, 61,818 unique canonical keys, zero left-only/right-only keys. Receipt fingerprint `897bc13c5f722d9a701ae7994b237fe7afd233f15cdc5e644061aa674b8f26c1`. This is source-population evidence only; acceptance timestamps, revision lineage and same-day PIT safety remain unproven.
- **Q127-R1:** `Q127R1_SOURCE_PIT_FEASIBILITY_COMPLETED`; four fixed historical dates were retrieved and parsed. Revision lineage and same-day PIT safety remain unresolved. Receipt fingerprint `60815a092421762ac1da2a96d003865b72f25eb640778287964a9648cdfc5b74`.
- **Q130-R1:** `Q130R1_SOURCE_FEASIBILITY_COMPLETED`; the frozen historical Wikimedia source probe passed, while publication/revision timing remains outside formal same-day PIT safety.
- **Q131-R1:** `Q131R1_FIXED_WINDOW_NO_MATCHING_FILINGS`; the fixed 2025-09-22 through 2025-09-24 issuer/form window yielded zero matching filings, so no complexity vector was inferred. Receipt fingerprint `e5d5077874d3eaa06b688c7294e83c42d3797da1c9cffdfdb98e067112d07a70`.
- These are discovery/source/PIT findings only. They do not authorize performance, holdout selection, tuning, ranking, promotion or live execution.

### Q171–Q178 Public Source Frontier

- Source-feasibility run: **COMPLETED** on master; Q171, Q172, Q174–Q177 and Q178 passed source probes; Q173 remains license-blocked.
- PIT-readiness: Q171 has a sample historical Common Crawl reconstruction receipt; Q174–Q177 have source-clock/version/revision semantics confirmed but are **not yet candidate-specific PIT-valid**.
- No member of this wave is performance-authorized; no holdout selection, tuning, ranking, promotion or live execution is permitted.

### Q179–Q184 Orthogonal Source/PIT Frontier

- Source-feasibility latest receipt: **{q179_q184_source_receipt.get("status", "NOT_RECORDED")}**.
- Q179 ClinicalTrials.gov, Q180 NHTSA, Q181 OSHA/DOL, Q183 NTSB and Q184 FCC currently pass the bounded source probe; Q182 FERC eLibrary remains **runner-access blocked** where the GitHub-hosted probe receives HTTP 403.
- PIT Readiness R1 latest receipt: **{q179_q184_pit_receipt.get("status", "NOT_RECORDED")}**.
- Latest Q179–Q184 PIT receipt fingerprint: `{q179_q184_pit_receipt.get("receipt_fingerprint", "UNKNOWN")}`.
- Candidate-level PIT status remains non-authorizing; all six current statuses are surfaced directly in `research/evidence/q179_q184_pit_readiness_r1_latest.json`.
- Remaining gates are historical archive reconstruction, exact public-clock proof where not yet established, fixed entity mapping, revision/amendment lineage and independent reproduction. No performance, holdout selection, tuning, ranking, promotion or live execution is authorized.
### Q197–Q201 Orthogonal Information Frontier

- Q198 Federal Register: **{_candidate_stage(q197_q198_source_receipt, "Q198")}**; source receipt `{q197_q198_source_receipt.get("receipt_fingerprint", "UNKNOWN")}`. Next gate: fixed historical Public Inspection filing clock, correction/withdrawal lineage, immutable reconstruction and independent PIT reproduction.
- Q197 USAspending: **{_candidate_stage(q197_q198_source_receipt, "Q197")}**; source receipt `{q197_q198_source_receipt.get("receipt_fingerprint", "UNKNOWN")}`. Next gate: historical award-state revision/public-observation boundary, frozen pre-event relationship network and independent event-time reproduction.
- Q199 USPTO: **{_candidate_stage(q199_q201_source_receipt, "Q199")}**; source receipt `{q199_q201_source_receipt.get("receipt_fingerprint", "UNKNOWN")}`. Next gate: historical publication-state archive, frozen assignee/technology exposure and independent PIT reproduction.
- Q201 ClinicalTrials.gov: **{_candidate_stage(q199_q201_source_receipt, "Q201")}**; source receipt `{q199_q201_source_receipt.get("receipt_fingerprint", "UNKNOWN")}`. Next gate: historical results-state revision lineage, explicit posted-time semantics, frozen sponsor/exposure mapping and independent PIT reproduction.
- Q198 historical PIT clock census: **{q198_pit_clock_receipt.get("status", "NOT_RECORDED")}**; pages parsed **{q198_pit_clock_receipt.get("aggregate", {}).get("pages_parsed", 0)}** / **{q198_pit_clock_receipt.get("aggregate", {}).get("pages_requested", 0)}**, with fixed dates **{", ".join(q198_pit_clock_receipt.get("frozen_dates", []))}**.
- All four frontier candidates remain non-authorizing: performance/holdout selection/ranking/tuning/promotion/live execution are closed. Source readiness is not PIT validation.
### Q202–Q204 Information-Timing Frontier

- Q202 ClinicalTrials.gov: **{_candidate_stage(q202_q204_source_receipt, "Q202")}**; source receipt `{q202_q204_source_receipt.get("receipt_fingerprint", "UNKNOWN")}`. Next gate: immutable historical record-version snapshots at the applicable reporting boundary, applicability/certification/extension lineage, frozen sponsor-to-issuer mapping and independent PIT reproduction.
- Q203 Federal procurement × ex-ante financing constraint: **{_candidate_stage(q202_q204_source_receipt, "Q203")}**; source receipt `{q202_q204_source_receipt.get("receipt_fingerprint", "UNKNOWN")}`. Next gate: immutable historical award-state/public-observation boundary, frozen pre-event financing vintage and entity mapping, correction/amendment lineage and independent PIT reproduction.
- Q204 Public-information release latency: **{_candidate_stage(q202_q204_source_receipt, "Q204")}**; source receipt `{q202_q204_source_receipt.get("receipt_fingerprint", "UNKNOWN")}`. Next gate: immutable public-observation/process-stage timestamps, fixed event-class semantics, pre-event-only latency calibration and correction/withdrawal lineage.
- Q202–Q204 remain source/PIT discovery tracks only: performance, holdout selection, ranking, tuning, promotion and live execution remain closed. Source feasibility is not PIT validation.

### Q148-R1 EIA WPSR Source/Clock Gate

- Receipt status: **{q148_r1_receipt.get("status", "NOT_RECORDED")}**.
- Persistent receipt fingerprint: `{q148_r1_receipt.get("receipt_fingerprint", "UNKNOWN")}`.
- Frozen controls: **{len(q148_r1_receipt.get("controls", []))}**; exact first-public-availability timestamp proven = **{q148_r1_receipt.get("pit_boundary", {}).get("exact_first_public_availability_timestamp_proven", False)}**.
- Candidate-specific revision lineage proven = **{q148_r1_receipt.get("pit_boundary", {}).get("candidate_specific_revision_lineage_proven", False)}**; same-day PIT safe = **{q148_r1_receipt.get("pit_boundary", {}).get("same_day_pit_safe", False)}**.
- This gate is source/clock evidence only; performance, ranking, holdout selection, tuning, promotion and live execution remain closed.

### Q137/Q144 Historical Micro-PIT

- Micro-PIT receipt status: **{q137_q144_micro_receipt.get("status", "NOT_RECORDED")}**.
- Q137 SEC all-symbols reconstructable = **{q137_q144_micro_receipt.get("q137_sec_submission_sample", {}).get("all_symbols_reconstructable", False)}**.
- Q144 Wikimedia all-symbols reconstructable = **{q137_q144_micro_receipt.get("q144_wikimedia_pageview_sample", {}).get("all_symbols_reconstructable", False)}**.
- This bounded sample produced feasibility evidence only; unresolved archive/entity coverage stays fail-closed.

### Q169 R4 Independent NOAA Reproduction

- Independent reproduction status: **{q169_r4_receipt.get("status", "NOT_RECORDED")}**.
- Persistent receipt fingerprint: `{q169_r4_receipt.get("receipt_fingerprint", "UNKNOWN")}`.
- All fixed R3 archive samples reproduced = **{q169_r4_receipt.get("reproduction_boundary", {}).get("all_fixed_samples_reproduced", False)}**.
- Candidate-specific exposure map frozen = **{q169_r4_receipt.get("reproduction_boundary", {}).get("candidate_specific_exposure_map_frozen", False)}**; revision lineage reconstructed = **{q169_r4_receipt.get("reproduction_boundary", {}).get("candidate_specific_revision_lineage_reconstructed", False)}**.
- This strengthens NOAA source/archive provenance only; candidate PIT validation and performance remain closed.

### Q133–Q170 Public Source Frontier

- Hosted discovery/source-feasibility run: **COMPLETED**; 25 source probes passed across Q133–Q170.
- Newly source-feasible candidates include Q137, Q144, Q147–Q151, Q153–Q155, Q157–Q158, Q161–Q169; remaining candidates stay blocked or design-only pending further source/PIT work.
- **PIT-readiness R1 is now ACTIVE** for the 21 source-feasible candidates; it audits candidate-specific clock, revision/version, entity-mapping and historical-archive requirements without evaluating returns or ranking candidates.
- Source-feasibility and PIT-readiness are not performance evidence and do not authorize performance, holdout selection, ranking, tuning, promotion or live execution.

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
- Permanent research continuity uses the two self-hosted Windows lanes every 30 minutes, event-driven free-AI review only when a new high-value task contract or material research-state change warrants it, always-routable S10/Android adaptive mechanical research-QA capacity, and bounded agent dispatch every 2 hours. Hosted research failover is manual-only.

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
    CHAT_HANDOFF.parent.mkdir(parents=True, exist_ok=True)
    CHAT_HANDOFF.write_text(json.dumps(current["chat_handoff"], ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(current, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if current["safety"]["status"] == "SAFE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
