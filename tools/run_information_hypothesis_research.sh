#!/usr/bin/env bash
set -euo pipefail

EXPECTED_URLS=(
  "https://github.com/DWR-debug/trading-agent-public"
  "https://github.com/DWR-debug/trading-agent-public.git"
  "git@github.com:DWR-debug/trading-agent-public.git"
)

remote="$(git remote get-url origin 2>/dev/null || true)"
ok_remote=false
for expected in "${EXPECTED_URLS[@]}"; do
  [[ "$remote" == "$expected" ]] && ok_remote=true
done
if [[ "$ok_remote" != true ]]; then
  echo "ABORT: origin is not DWR-debug/trading-agent-public: $remote" >&2
  exit 2
fi

branch="$(git branch --show-current)"
case "$branch" in
  master|research/copilot-hypothesis-subagent) ;;
  *)
    echo "ABORT: unsupported branch: $branch" >&2
    exit 2
    ;;
esac

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ABORT: worktree is not clean; commit or stash unrelated changes first." >&2
  exit 2
fi

python - <<'PY'
from pathlib import Path
import re

settings = Path("config/settings.py").read_text(encoding="utf-8")
checks = {
    "PAPER_ONLY=True": r"^PAPER_ONLY\s*=\s*True\b",
    "LIVE_TRADING_ENABLED=False": r"^LIVE_TRADING_ENABLED\s*=\s*False\b",
}
for label, pattern in checks.items():
    if not re.search(pattern, settings, re.MULTILINE):
        raise SystemExit(f"ABORT: safety check failed: {label}")
print("Safety preflight: PAPER_ONLY=True, LIVE_TRADING_ENABLED=False")
PY

command -v copilot >/dev/null 2>&1 || {
  echo "ABORT: copilot CLI is not installed." >&2
  exit 2
}

mkdir -p research/agent_outputs
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
out="research/agent_outputs/AGENT-HYPOTHESIS-ROUND-001-${stamp}.md"

prompt='Execute AGENT-HYPOTHESIS-ROUND-001 as an evidence-grounded Q012 research-design memo. First use only the read-only repository tools to inspect these exact sources: research/research_queue.json (Q012 definition), research/evidence/project_state.json (current state and safety), research/evidence/q011_discovery_result_2026_09_25.json (Q011 discovery observations), research/evidence/cross_trial_failure_diagnosis_2026_09_25.json and research/evidence/cross_trial_failure_diagnosis_2026_09_24.json (failure signatures), research/evidence/t041_formal_result_2026_09_24.json, research/evidence/t044_failure_diagnosis_2026_09_25.json, research/evidence/t045_failure_diagnosis_2026_09_25.json, plus research/evidence/trial_ledger.json for family/provenance checks. Also inspect docs/PROJECT_CONTEXT.md and PROJECT_STATUS.md for governance and current research focus. Do not use holdout outcomes to select or rank hypotheses. Focus on Q012: longer-window temporal stability of the same GDELT information source before any feature-based performance study. Produce multiple competing, orthogonal hypotheses specifically about temporal stability, decay, regime dependence, and mechanism discrimination, tied explicitly to what Q011 actually observed and what is missing. For each hypothesis provide: ID, mechanism, measurable prediction, required point-in-time data, exact falsification criterion, confounders, orthogonality to prior trial families, minimal deterministic preflight, expected null, and prerequisites for a later preregistration. Explicitly identify any evidence you could not read or any claim you cannot support. Do not modify files, execute shell commands, select on holdout data, change gates, alter existing trials, or trigger performance trials. Return only a compact research memo; treat all output as IDEAS_ONLY / NOT_EVIDENCE.'

{
  printf '# AGENT-HYPOTHESIS-ROUND-001\n\n'
  printf '%s\n\n' "Timestamp (UTC): $stamp"
  printf 'Branch: %s\n\n' "$branch"
  printf '## Copilot output\n\n'
  copilot \
    --agent=information-hypothesis-researcher \
    --autopilot \
    --max-autopilot-continues=1 \
    --no-ask-user \
    --available-tools='view,grep,glob' \
    --prompt "$prompt" 2>&1
} | tee "$out"

status=${PIPESTATUS[0]}
if [[ "$status" -ne 0 ]]; then
  echo "Copilot exited with status $status. Output retained at $out" >&2
  exit "$status"
fi

echo
echo "Saved research memo: $out"
echo "Scientific status: IDEAS_ONLY / NOT_EVIDENCE"