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

prompt='Execute AGENT-HYPOTHESIS-ROUND-001. Use frozen T041/T042/T044/T045 and Q011 evidence. Generate multiple orthogonal hypotheses, competing explanations, mechanism synthesis, falsification criteria, required data, point-in-time rules, confounders, minimal deterministic preflights, expected null results, and conditions for preregistration. Do not modify files, execute shell commands, select on holdout data, change gates, alter existing trials, or trigger performance trials. Return a compact research memo for the primary research agent. Treat all output as ideas, not evidence. Explicitly report uncertainty and missing evidence.'

{
  printf '# AGENT-HYPOTHESIS-ROUND-001\n\n'
  printf '%s\n\n' "Timestamp (UTC): $stamp"
  printf 'Branch: %s\n\n' "$branch"
  printf '## Copilot output\n\n'
  copilot \
    --agent=information-hypothesis-researcher \
    --autopilot \
    --max-autopilot-continues=5 \
    --no-ask-user \
    --available-tools='read,search' \
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
