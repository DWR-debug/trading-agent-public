"""Fail-closed consistency checks for durable project context and evidence metadata.

This checker is intentionally lightweight and read-only. It does not decide whether
a research hypothesis is scientifically correct; it detects repository-state
inconsistencies that can silently break project memory or trial accounting.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ACTIVE_WORKFLOWS = {
    "agent-dispatch.yml",
    "agent-request-queue.yml",
    "ai-worker-fabric.yml",
    "autonomous-control-plane.yml",
    "ci.yml",
    "c29-fresh-coverage-pit.yml",
    "c29-coverage-repair-discovery.yml",
    "c29r1-fresh-coverage-pit.yml",
    "c29r1-input-freeze.yml",
    "c29-performance-once.yml",
    "c29-performance-dispatch-repair.yml",
    "c29-performance-authorization-once.yml",
    "copilot-cli-ci-repair.yml",
    "copilot-cli-engineering-task.yml",
    "copilot-setup-steps.yml",
    "coverage-candidate-discovery.yml",
    "coverage-candidate-search.yml",
    "current-status-sync.yml",
    "evidence-graph-stage4-stage5-wave.yml",
    "q104-i19-13f-historical-identity-census.yml",
    "research-completion-monitor-a.yml",
    "research-completion-monitor-b.yml",
    "research-completion-relay.yml",
    "deep-frontier-source-feasibility.yml",
    "q171-material-receipt-sync.yml",
    "q133-q170-pit-readiness.yml",
    "q148-r1-wpsr-source-clock.yml",
    "q148-r1-persist-receipt.yml",
    "q169-noaa-swpc-pit-readiness.yml",
    "q169-noaa-swpc-pit-independent-reproduction.yml",
    "full-suite-verification.yml",
    "q129-options-source-feasibility.yml",
    "q129-independent-pit-reproduction.yml",
    "f1-profitability-feasibility.yml",
    "f2-quality-acceleration-cloud.yml",
    "f2-quality-acceleration-feasibility.yml",
    "f2-sec-cloud-source-probe.yml",
    "fixed-study-window-candidate-discovery.yml",
    "h06-mechanism-replication-run.yml",
    "h06-mechanism-replication.yml",
    "h06-mechanism.yml",
    "h06-master-coverage-repair.yml",
    "h06-pit-independent-reproduction.yml",
    "h06-p2-input-freeze.yml",
    "h06-p2-performance-authorization-once.yml",
    "h06-p2-performance.yml",
    "h06-p2-r1-performance-authorization-once.yml",
    "h06-p2-r1-performance.yml",
    "h06-p2-r2-performance-authorization-once.yml",
    "h06-p2-r2-performance.yml",
    "h06-p2-r3-performance-authorization-once.yml",
    "h06-p2-r3-performance.yml",
    "c29-fresh-coverage-pit-repair.yml",
    "hosted-research-failover.yml",
    "hosted-deterministic-frontier.yml",
    "intraday-directional-discovery.yml",
    "intraday-discovery.yml",
    "paper-2000-candidate.yml",
    "paper-30-day-experiment-harness.yml",
    "paper-500-candidate.yml",
    "paper-forward-persistent-mtm-2000.yml",
    "paper-forward-persistent-mtm.yml",
    "paper-forward-self-hosted-validation.yml",
    "permanent-pc-research-loop.yml",
    "public-frontier-feasibility.yml",
    "q014-resilient.yml",
    "q015-mechanism-discrimination.yml",
    "q017-coverage-first-standalone.yml",
    "q018-source-feasibility.yml",
    "q019-treasury-auction-contract.yml",
    "q020-treasury-auction-performance.yml",
    "q020-treasury-coverage-repair.yml",
    "q022-design-guard.yml",
    "q022-h1-directional-inversion-coverage.yml",
    "q022-h1-directional-inversion-performance.yml",
    "q023-treasury-release-timestamp-pit-feasibility.yml",
    "q024-treasury-auction-result-timestamp-pit-feasibility.yml",
    "q024-treasury-result-timestamp-pit.yml",
    "q025-treasury-auction-date-pit-feasibility.yml",
    "q031-q030-risk-stability-coverage.yml",
    "q032-q031-fixed-core-pit.yml",
    "q034-q033-mechanism-pit.yml",
    "q036-t056-risk-mechanism-diagnostic.yml",
    "q039-price-only-alpha-pit.yml",
    "q040-official-event-source-feasibility.yml",
    "q042-additional-price-alpha-pit.yml",
    "q043-fresh-disjoint-alpha-replication-coverage.yml",
    "q044-fresh-alpha-pit.yml",
    "q066-alpha-failure-diagnosis.yml",
    "q067-coverage-pit.yml",
    "q067-evidence-reconcile.yml",
    "q068-coverage-pit.yml",
    "q068-evidence-reconcile.yml",
    "q068-snapshot-recovery-audit.yml",
    "q070-coverage-pit.yml",
    "q070-evidence-reconcile.yml",
    "q071-source-feasibility.yml",
    "q072-candidate-bank.yml",
    "q074-extended-source-feasibility.yml",
    "q075-information-channel-contract.yml",
    "q077-fresh-e1-e2-discovery.yml",
    "q077r1-fresh-e1-e2-discovery.yml",
    "q077r1-pit.yml",
    "q077r1-authorization-once.yml",
    "q077r1-performance-once.yml",
    "q079-fresh-e1-e2-coverage-pit.yml",
    "q079-fresh-e1-e2-discovery.yml",
    "q079-persist-frozen-input-bundle.yml",
    "q081r1-preflight.yml",
    "q081r1-selfhosted-reproduction.yml",
    "q081r2-preflight.yml",
    "q081r3-authorization-once.yml",
    "q081r4-authorization-once.yml",
    "q081r4-performance-once.yml",
    "q081r3-performance-once.yml",
    "q081r2-authorization-once.yml",
    "q081r2-performance-once.yml",
    "q083-feasibility.yml",
    "q084-feasibility.yml",
    "q085-coverage-pit.yml",
    "q086-coverage-pit.yml",
    "q089-contract-audit.yml",
    "q089-performance-once.yml",
    "q089-coverage-cloud-crosscheck.yml",
    "q089-coverage-pit.yml",
    "q090-q089-failure-diagnosis.yml",
    "q091-portfolio-architecture-coverage.yml",
    "q091-contract-audit.yml",
    "q091-performance-once.yml",
    "q091-input-freeze.yml",
    "q091-persist-input-freeze-artifact.yml",
    "q091-persist-coverage.yml",
    "q092-q091-failure-diagnosis.yml",
    "q093-q091-cost-attribution-diagnosis.yml",
    "q094-coverage-pit-input-freeze.yml",
    "q094-performance-once.yml",
    "q095-coverage-pit-input-freeze.yml",
    "q095-contract-audit.yml",
    "q095-performance-once.yml",
    "q107-q104-equity-coverage.yml",
    "q108-q104-pit-integration.yml",
    "q110-q109-source-feasibility.yml",
    "q111-sec-security-identity.yml",
    "q112-sec-security-identity.yml",
    "q113-13f-q107-coverage.yml",
    "q114-13f-manager-transitions.yml",
    "q115-treasury-demand-state.yml",
    "q116-13f-transition-population.yml",
    "q117-treasury-demand-population.yml",
    "q118-composition-structural.yml",
    "q119-treasury-source-feasibility.yml",
    "q119-independent-reproduction.yml",
    "q120-independent-reproduction.yml",
    "q121-sec-beneficial-ownership-timing.yml",
    "q121r1-sec-reverse-issuer-coverage.yml",
    "q121r2-sec-daily-index-reconciliation.yml",
    "q121r3-sec-form-index.yml",
    "q121r4-sec-master-index.yml",
    "q121r6-sec-acceptance-time-compilation.yml",
    "q193-q196-source-feasibility.yml",
    "q199-q201-source-feasibility.yml",
    "q197-q198-source-feasibility.yml",
    "q198-pit-clock-census.yml",
    "q182-ferc-self-hosted-access-probe.yml",
    "q127r1-finra-regsho-historical-pit.yml",
    "q130r1-wikimedia-attention-source.yml",
    "q131r1-sec-disclosure-complexity.yml",
    "q095-authorization-once.yml",
    "rccsm-feasibility-cloud.yml",
    "rccsm-feasibility.yml",
    "rccsm-observational-feasibility-cloud.yml",
    "rccsm-observational-feasibility.yml",
    "rccsm-transition-diagnostic.yml",
    "research-governance-audit.yml",
    "research-orchestrator.yml",
    "self-hosted-capacity-autostart.yml",
    "self-hosted-continuous-qa.yml",
    "self-hosted-research-worker-v4.yml",
    "self-hosted-runner-probe.yml",
    "simulation-capital-focused-qa.yml",
    "t049-fixed-candidate-batch-coverage.yml",
    "t050-fixed-candidate-batch-02-coverage.yml",
    "t051-fixed-core-strategy-pit.yml",
    "t052-evidence-reconcile-once.yml",
    "t052-exact-master-ci-gate.yml",
    "t052-formal-once.yml",
    "ttaf-feasibility.yml",
    "wide-search.yml",
    "workflow-lint.yml",
    "evidence-critic-lab.yml",
    "evidence-critic-verdict.yml",
    "s10-runtime-probe.yml",
    "s10-phone-worker.yml",
    "s10-receipt-sync.yml",
    "s10-stale-run-recovery.yml",
    "s10-throughput-probe.yml",
    "q104-i22-filing-arrival.yml",
    "android-phone-fleet-worker.yml",
    "android-phone-fleet-receipt-sync.yml",
    "post-pass-independent-replication.yml",
    "q179-q184-source-feasibility.yml",
    "q179-q184-pit-readiness.yml",
    "q179-q184-pit-census-r2.yml",
    "q185-q186-source-feasibility.yml",
    "q185-q186-windows-reproduction.yml",
    "q187-q192-source-feasibility.yml",
    "ai-credit-availability-planner.yml",
    "groq-free-preflight.yml",
    "q187-q192-pit-readiness-r1.yml",
    "q188-q192-pit-census-r1.yml",
    "q188-q192-pit-census-r2.yml",
    "q121r6-windows-independent-reproduction.yml",
    "windows-local-ai-worker.yml",
    "resource-dashboard-update.yml",
    "top4-candidate-research-capacity.yml",
    "top4-candidate-slot-research.yml",
    "q220-as-filed-xbrl-population.yml",
    "groq-free-adversarial-worker.yml",
    "groq-api-key-smoke-test.yml",
    "github-pages-dashboard.yml",
    "current-status-drift-guard.yml",
    "orthogonal-candidate-development.yml",
    "orthogonal-pit-next-gate.yml",
    "q202-q204-information-timing-feasibility.yml",
    "q205-nlrb-source-feasibility.yml",
    "priority-research-wave-dispatch.yml",
    "windows-runner-c-long-research.yml",
    "runner-c-prepit-falsification.yml",
    "runner-c-long-duplicate-guard.yml",
    "litellm-compatibility.yml",
    "litellm-provider-smoke.yml",
    "litellm-groq-one-shot-smoke.yml",
    "litellm-q187-q192-one-shot.yml",
    "litellm-manual-groq-one-shot.yml",
    "capacity-saturation-rolling-waves.yml",
    "planned-capacity-fast-dispatch.yml",
    "continuous-useful-capacity-replenisher.yml",
    "literature-frontier-scout.yml",
    "q214-disclosure-risk-feasibility.yml",
    "q215-nhtsa-sec-bridge-feasibility.yml",
    "q215-observability-gap-feasibility.yml",
    "q216-data-revision-exposure-feasibility.yml",
    "q216-rt-vintage-pit-feasibility.yml",
    "q217-cognitive-processing-friction-feasibility.yml",
    "q217-q131-orthogonality-audit.yml",
    "q229-historical-release-census.yml",
    "q229-q230-source-feasibility.yml",
    "q230-windows-trace-connectivity.yml",
    "q224-edgar-modern-source-gate.yml",
    "q231-sec-foia-source-gate.yml",
    "windows-independent-capacity-pulse.yml",
    "knowledge-relation-plane.yml",
    "temporal-identity-state-spine-waves.yml",
    "spine-next-gate-autonomous-router.yml",
    "q228-sec-correspondence-source-gate.yml",
}

REQUIRED_FILES = (
    ROOT / "PROJECT_STATUS.md",
    ROOT / "docs" / "PROJECT_CONTEXT.md",
    ROOT / "docs" / "PROJECT_CONTEXT_INGESTION.md",
    ROOT / "docs" / "research_archaeology_2026_09_24.md",
    ROOT / "research" / "evidence" / "project_context.json",
    ROOT / "docs" / "CHAT_CONTEXT_2026_09_24.md",
    ROOT / "docs" / "PRE_CLEANUP_INVENTORY_2026_09_24.md",
    ROOT / "research" / "evidence" / "trial_ledger.json",
    ROOT / "research" / "governance" / "research_os_source_registry_2026_09_30.json",
    ROOT / "automation" / "research_os_evidence_bus.py",
    ROOT / "automation" / "research_os_scheduler.py",
    ROOT / "automation" / "research_os_source_probe.py",
    ROOT / "automation" / "s10_receipt_sync.py",
    ROOT / "automation" / "s10_utility_task.py",
    ROOT / "automation" / "android_phone_receipt_sync.py",
    ROOT / "tests" / "test_research_os_evidence_bus.py",
    ROOT / "tests" / "test_s10_receipt_sync.py",
    ROOT / "tests" / "test_s10_utility_task.py",
    ROOT / "tests" / "test_android_phone_receipt_sync.py",
    ROOT / "tests" / "test_s10_throughput_probe.py",
)


def fail(message: str) -> None:
    raise SystemExit(f"PROJECT INTEGRITY FAIL: {message}")




def _validate_q067_evidence_chain() -> None:
    """Reject impossible Q067 evidence/authorization states before publishing CI truth."""
    root = ROOT
    evidence = root / "research" / "evidence"
    authorizations = root / "research" / "authorizations"
    auth_path = authorizations / "q067_performance_2026_09_28.json"
    perf_result = evidence / "q067_performance_result.json"
    coverage_result = evidence / "q067_coverage_result.json"
    pit_result = evidence / "q067_pit_result.json"
    if not auth_path.exists():
        if perf_result.exists():
            fail("Q067 performance evidence exists without performance authorization")
        return

    try:
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Q067 performance authorization is unreadable: {exc}")
    for name, expected in (
        ("authorized", True),
        ("performance_execution_authorized", True),
        ("execution_scope", "Q067_FIXED_RULE_PERFORMANCE_ONLY"),
    ):
        if auth.get(name) != expected:
            fail(f"Q067 performance authorization contract invalid: {name}")
    if auth.get("safety") != {
        "PAPER_ONLY": True,
        "LIVE_TRADING_ENABLED": False,
        "ORDERS_ENABLED": False,
        "AUTOMATIC_PROMOTION": False,
    }:
        fail("Q067 performance authorization safety contract invalid")

    for path, trial_id, status in (
        (coverage_result, "T-2026-09-28-067-COVERAGE", "COVERAGE_PASSED"),
        (pit_result, "T-2026-09-28-067-PIT", "PIT_PASSED"),
    ):
        if not path.exists():
            fail(f"Q067 performance authorization exists without prerequisite: {path.relative_to(root)}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("trial_id") != trial_id or payload.get("status") != status:
            fail(f"Q067 prerequisite invalid: {path.relative_to(root)}")
        if payload.get("performance_trial_authorized") is not False:
            fail(f"Q067 prerequisite unexpectedly authorizes performance: {path.relative_to(root)}")
        if payload.get("selection_used") is not False:
            fail(f"Q067 prerequisite records selection: {path.relative_to(root)}")

    if perf_result.exists():
        payload = json.loads(perf_result.read_text(encoding="utf-8"))
        if payload.get("trial_id") != "T-2026-09-28-067-PERFORMANCE":
            fail("Q067 performance evidence trial identity mismatch")
        if payload.get("status") != "COMPLETED":
            fail("Q067 performance evidence is not completed")
        if payload.get("selection_used") is not False:
            fail("Q067 performance evidence records selection")
        if payload.get("holdout_used_for_selection") is not False:
            fail("Q067 performance evidence records holdout selection")


def _validate_research_os_registry() -> None:
    path = ROOT / "research" / "governance" / "research_os_source_registry_2026_09_30.json"
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Research OS registry is unreadable: {exc}")
    safety = registry.get("safety", {})
    if safety != {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
        "paid_resources_allowed": False,
    }:
        fail("Research OS registry safety contract invalid")
    sources = registry.get("source_lattice")
    agents = registry.get("agent_runtime_lattice")
    if not isinstance(sources, list) or not sources:
        fail("Research OS source lattice is missing")
    if not isinstance(agents, list) or not agents:
        fail("Research OS agent runtime lattice is missing")
    for item in sources:
        if not isinstance(item, dict):
            fail("Research OS source entry is not an object")
        if not isinstance(item.get("id"), str) or not item["id"]:
            fail("Research OS source entry lacks id")
        if not isinstance(item.get("source_url"), str) or not item["source_url"].startswith("https://"):
            fail(f"Research OS source has invalid source_url: {item.get('id')}")
        if "pit_fit" not in item:
            fail(f"Research OS source has no PIT classification: {item.get('id')}")
    for item in agents:
        if not isinstance(item, dict) or not item.get("adoption_mode"):
            fail("Research OS agent entry lacks adoption_mode")

    scheduler = registry.get("resource_scheduler", {})
    required_forbidden = {"holdout_return", "holdout_drawdown", "performance_rank", "future_information", "candidate_preference"}
    if not required_forbidden.issubset(set(scheduler.get("forbidden_axes", []))):
        fail("Research OS scheduler is missing forbidden anti-leakage axes")
    artifacts = scheduler.get("runtime_artifacts", [])
    expected_artifacts = {
        "research/runs/self_hosted/autonomous/**/research_os_resource_schedule.json",
        "research/runs/self_hosted/autonomous/**/research_os_source_probe.json",
    }
    if set(artifacts) != expected_artifacts:
        fail("Research OS runtime artifact contract drifted")

    probe = registry.get("source_probe_policy", {})
    if probe != {
        "rotation_bucket_count": 4,
        "max_sources_per_cycle": 4,
        "probe_is_reachability_only": True,
        "downloads_dataset_payloads": False,
        "uses_credentials": False,
        "scientific_evidence": False,
        "performance_authorization": False,
    }:
        fail("Research OS source-probe safety contract invalid")


def _validate_critical_research_controls() -> None:
    policy_path = ROOT / "research" / "governance" / "critical_research_quality_control.json"
    validator_path = ROOT / "automation" / "future_performance_quality_contract_check.py"
    candidate_gate_path = ROOT / "automation" / "candidate_robustness_gate.py"
    dispatcher_path = ROOT / "automation" / "independent_replication_dispatch.py"
    workflow_path = ROOT / ".github" / "workflows" / "post-pass-independent-replication.yml"
    for path in (policy_path, validator_path, candidate_gate_path, dispatcher_path, workflow_path):
        if not path.exists():
            fail(f"critical research control missing: {path.relative_to(ROOT)}")
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"critical research control policy is unreadable: {exc}")
    if policy.get("status") != "ACTIVE":
        fail("critical research quality policy is not active")
    try:
        from automation.future_performance_quality_contract_check import validate
        result = validate(ROOT)
    except Exception as exc:
        fail(f"future performance quality validator failed: {exc}")
    if result.get("status") != "PASS":
        fail("future performance quality validator returned non-PASS")
    candidate_gate = policy.get("candidate_robustness_gate", {})
    if candidate_gate.get("required_before_any_formal_phase") is not True:
        fail("universal candidate robustness gate is not enforced")
    if candidate_gate.get("gate_type") != "STRUCTURAL_NON_PERFORMANCE":
        fail("universal candidate robustness gate type is invalid")
    required_candidate_dimensions = set(candidate_gate.get("required_dimensions", []))
    if not required_candidate_dimensions.issubset({
        "construction_invariance",
        "input_order_invariance",
        "future_data_invariance",
        "missingness_fail_closed",
        "revision_amendment_invariance",
        "identity_mapping_fail_closed",
        "parameter_threshold_horizon_lock",
        "source_reproducibility",
    }):
        fail("universal candidate robustness dimensions are invalid")
    if policy.get("early_robustness", {}).get("required_before_future_performance_authorization") is not True:
        fail("early robustness prerequisite is not enforced")
    if policy.get("immediate_replication", {}).get("required_for_any_future_full_formal_pass") is not True:
        fail("immediate replication prerequisite is not enforced")
    required_dimensions = {
        "research_and_holdout_return",
        "research_and_holdout_drawdown",
        "profit_factor",
        "rolling_profit_factor",
        "rolling_profitable_window_ratio",
        "rolling_average_drawdown",
        "oos_to_is_return_ratio",
        "cost_stress_1_5x",
        "cost_stress_2x",
        "total_return_sensitivity",
        "turnover",
        "gross_exposure",
        "concentration_hhi",
        "market_correlation",
        "underwater_fraction",
        "regime_decomposition",
    }
    declared = set(policy.get("early_robustness", {}).get("required_dimensions", []))
    if not required_dimensions.issubset(declared):
        fail("critical research robustness dimensions are incomplete")
    forbidden = set(policy.get("orthogonal_search", {}).get("forbidden_scheduler_inputs", []))
    required_forbidden = {"holdout_return", "holdout_drawdown", "performance_rank", "future_information", "candidate_preference"}
    if not required_forbidden.issubset(forbidden):
        fail("critical research orthogonal scheduler remains vulnerable to forbidden inputs")


def _validate_i19_concept_freeze() -> None:
    path = ROOT / "research" / "preregistrations" / "q104_i19_xbrl_concept_freeze_2026_10_03.json"
    test_path = ROOT / "tests" / "test_q104_i19_xbrl_concept_freeze.py"
    if not path.exists() or not test_path.exists():
        fail("Q104 I19 exact XBRL concept freeze artifacts are missing")
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Q104 I19 exact concept freeze is unreadable: {exc}")
    if spec.get("candidate_id") != "Q104:I19":
        fail("Q104 I19 concept freeze identity mismatch")
    if spec.get("governance", {}).get("performance_authorized") is not False:
        fail("Q104 I19 concept freeze unexpectedly authorizes performance")
    if spec.get("fact_contract", {}).get("selection_rule") != "Choose the latest filing accepted no later than the decision cutoff that contains all three required concepts with a valid duration/instant alignment. No concept substitution is allowed.":
        fail("Q104 I19 concept-selection rule drifted")
    expected = {
        "net_income_loss": "us-gaap:NetIncomeLoss",
        "operating_cash_flow": "us-gaap:NetCashProvidedByUsedInOperatingActivities",
        "assets": "us-gaap:Assets",
    }
    if spec.get("xbrl_concepts") != expected:
        fail("Q104 I19 XBRL concept identifiers drifted")

def main() -> None:
    workflow_dir = ROOT / ".github" / "workflows"
    active_workflows = {path.name for path in workflow_dir.glob("*.yml")}
    unexpected = sorted(active_workflows - ACTIVE_WORKFLOWS)
    missing = sorted(ACTIVE_WORKFLOWS - active_workflows)
    if unexpected or missing:
        parts = []
        if unexpected:
            parts.append("unexpected active workflows: " + ", ".join(unexpected))
        if missing:
            parts.append("missing expected workflows: " + ", ".join(missing))
        fail("; ".join(parts))
    _validate_q067_evidence_chain()
    _validate_research_os_registry()
    _validate_critical_research_controls()
    _validate_i19_concept_freeze()

    for path in REQUIRED_FILES:
        if not path.exists():
            fail(f"missing required file: {path.relative_to(ROOT)}")

    status = (ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    for marker in (
        "docs/PROJECT_CONTEXT.md",
        "docs/PROJECT_CONTEXT_INGESTION.md",
        "docs/research_archaeology_2026_09_24.md",
        "research/evidence/project_context.json",
        "GitHub-",
        "technische Referenz",
    ):
        if marker not in status:
            fail(f"PROJECT_STATUS missing governance marker: {marker}")

    context = (ROOT / "research" / "evidence" / "project_context.json")
    index = json.loads(context.read_text(encoding="utf-8"))

    if index.get("repository") != "DWR-debug/trading-agent-public":
        fail("context index repository mismatch")

    safety = index.get("safety", {})
    if safety.get("paper_only") is not True:
        fail("paper_only invariant is not true in context index")
    if safety.get("live_trading_enabled") is not False:
        fail("live_trading_enabled invariant is not false in context index")
    if safety.get("orders_enabled") is not False:
        fail("orders_enabled invariant is not false in context index")

    documents = index.get("documents", {})
    for key, relpath in (
        ("project_context", "docs/PROJECT_CONTEXT.md"),
        ("chat_context_ingestion", "docs/PROJECT_CONTEXT_INGESTION.md"),
        ("research_archaeology", "docs/research_archaeology_2026_09_24.md"),
        ("chat_context", "docs/CHAT_CONTEXT_2026_09_24.md"),
        ("pre_cleanup_inventory", "docs/PRE_CLEANUP_INVENTORY_2026_09_24.md"),
    ):
        if documents.get(key) != relpath:
            fail(f"context index document mismatch: {key}")

    ledger = json.loads(
        (ROOT / "research" / "evidence" / "trial_ledger.json").read_text(
            encoding="utf-8"
        )
    )
    entries = ledger.get("trials", ledger.get("entries", ledger))
    if not isinstance(entries, list):
        fail("trial ledger is not a list")

    ids = [entry.get("trial_id") for entry in entries]
    if any(not trial_id for trial_id in ids):
        fail("ledger contains an entry without trial_id")
    if len(ids) != len(set(ids)):
        fail("duplicate trial_id in ledger")

    for entry in entries:
        status_value = entry.get("status")
        if status_value == "data_invalid":
            outcome = entry.get("outcome", {})
            if outcome.get("no_performance_claim") is False:
                fail(
                    f"{entry['trial_id']} is data_invalid but explicitly "
                    "declares a performance claim"
                )
            if outcome.get("validation_status") not in (None, "DATA_INVALID"):
                fail(
                    f"{entry['trial_id']} is data_invalid but has "
                    "non-DATA_INVALID validation status"
                )

    trial_docs = {
        path.name
        for path in (ROOT / "docs").glob("trial*.md")
    }
    for trial_id in ("T-2026-09-24-029", "T-2026-09-24-030",
                     "T-2026-09-24-031", "T-2026-09-24-032",
                     "T-2026-09-24-033"):
        suffix = trial_id.rsplit("-", 1)[-1]
        if not any(f"trial_{suffix}" in name for name in trial_docs):
            fail(f"recent formal trial has no discoverable trial doc: {trial_id}")

    print("PROJECT INTEGRITY OK")
    print(f"ledger_entries={len(entries)}")
    print("safety=paper_only")
    print("context_sources=technical/evidence/project-intent/work-state")


if __name__ == "__main__":
    main()
