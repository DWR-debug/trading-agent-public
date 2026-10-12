from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "automation" / "gh_api_retry.sh"
REQUEST_WORKFLOW = ROOT / ".github/workflows/q104-i19-targeted-acceptance-repair-request.yml"
REPAIR_WORKFLOW = ROOT / ".github/workflows/q104-i19-targeted-acceptance-repair.yml"


def _fake_gh(tmp_path: Path) -> tuple[Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    count_file = tmp_path / "gh-count.txt"
    gh = bin_dir / "gh"
    gh.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
[[ "${1:-}" == "api" ]] || exit 88
count=0
[[ -f "$FAKE_GH_COUNT_FILE" ]] && count="$(cat "$FAKE_GH_COUNT_FILE")"
count=$((count+1))
printf '%s' "$count" > "$FAKE_GH_COUNT_FILE"
case "$FAKE_GH_MODE" in
  retry_502)
    if (( count == 1 )); then
      echo 'gh: Server Error (HTTP 502)' >&2
      exit 1
    fi
    ;;
  always_502)
    echo 'gh: Server Error (HTTP 502)' >&2
    exit 1
    ;;
  permanent_404)
    echo 'gh: Not Found (HTTP 404)' >&2
    exit 1
    ;;
esac
printf '{"ok":true,"count":%s}\\n' "$count"
""",
        encoding="utf-8",
    )
    gh.chmod(0o755)
    return bin_dir, count_file


def _run_helper(tmp_path: Path, mode: str, max_attempts: int = 5):
    bin_dir, count_file = _fake_gh(tmp_path)
    env = os.environ.copy()
    env.update({
        "PATH": str(bin_dir) + os.pathsep + env.get("PATH", ""),
        "RUNNER_TEMP": str(tmp_path),
        "FAKE_GH_COUNT_FILE": str(count_file),
        "FAKE_GH_MODE": mode,
        "GITHUB_API_MAX_ATTEMPTS": str(max_attempts),
        "GITHUB_RUN_ID": "unit-test",
    })
    command = (
        f"source {json.dumps(str(HELPER))}; "
        "sleep() { :; }; "
        "gh_api_retry /repos/example/actions/runs/123"
    )
    result = subprocess.run(
        ["bash", "-e", "-c", command],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    count = int(count_file.read_text(encoding="utf-8"))
    return result, count


def test_gh_api_retry_recovers_from_transient_server_error(tmp_path):
    result, count = _run_helper(tmp_path, "retry_502")

    assert result.returncode == 0
    assert json.loads(result.stdout) == {"ok": True, "count": 2}
    assert count == 2
    assert "GITHUB_API_RETRY endpoint=/repos/example/actions/runs/123" in result.stderr


def test_gh_api_retry_does_not_retry_permanent_404(tmp_path):
    result, count = _run_helper(tmp_path, "permanent_404")

    assert result.returncode != 0
    assert count == 1
    assert "HTTP 404" in result.stderr
    assert "GITHUB_API_RETRY_EXHAUSTED" not in result.stderr


def test_gh_api_retry_exhaustion_is_bounded_and_visible(tmp_path):
    result, count = _run_helper(tmp_path, "always_502", max_attempts=2)

    assert result.returncode != 0
    assert count == 2
    assert "GITHUB_API_RETRY_EXHAUSTED" in result.stderr
    assert "attempts=2" in result.stderr


def test_q104_recovery_workflows_use_shared_read_only_api_retry():
    request = REQUEST_WORKFLOW.read_text(encoding="utf-8")
    repair = REPAIR_WORKFLOW.read_text(encoding="utf-8")

    assert "source automation/gh_api_retry.sh" in request
    assert "source automation/gh_api_retry.sh" in repair
    assert 'gh_api_retry "/repos/$GITHUB_REPOSITORY/actions/runs/$source_run_id"' in request
    assert 'gh_api_retry "/repos/$GITHUB_REPOSITORY/actions/runs/$SOURCE_RUN_ID"' in repair
    assert "gh api \"/repos/$GITHUB_REPOSITORY/" not in request
    assert "gh api \"/repos/$GITHUB_REPOSITORY/" not in repair
    assert "POST" not in HELPER.read_text(encoding="utf-8").upper()
