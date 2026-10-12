#!/usr/bin/env bash
# Source this helper from Bash steps that perform idempotent, read-only gh api GETs.
# Do not use it for workflow dispatches, artifact mutations, or other write requests.
gh_api_retry() {
  if [[ "${#}" != "1" || -z "${1:-}" ]]; then
    echo "GITHUB_API_RETRY_ARGUMENT_ERROR" >&2
    return 64
  fi

  local endpoint="$1"
  local max_attempts="${GITHUB_API_MAX_ATTEMPTS:-5}"
  if [[ ! "$max_attempts" =~ ^[1-5]$ ]]; then
    max_attempts=5
  fi
  local temp_root="${RUNNER_TEMP:-${TMPDIR:-/tmp}}"
  mkdir -p "$temp_root"
  local prefix="$temp_root/gh-api-retry-${GITHUB_RUN_ID:-local}-${BASHPID}"
  local response_file="${prefix}.json"
  local error_file="${prefix}.err"
  local attempt=1
  local rc=1

  while (( attempt <= max_attempts )); do
    if gh api "$endpoint" >"$response_file" 2>"$error_file"; then
      cat "$response_file"
      rc=$?
      rm -f "$response_file" "$error_file"
      return "$rc"
    else
      rc=$?
    fi

    if ! grep -Eiq       'HTTP (408|425|429|500|502|503|504)|API rate limit exceeded|secondary rate limit|connection reset|timed out|timeout|unexpected EOF|TLS handshake timeout'       "$error_file"; then
      cat "$error_file" >&2
      rm -f "$response_file" "$error_file"
      return "$rc"
    fi

    if (( attempt >= max_attempts )); then
      echo "GITHUB_API_RETRY_EXHAUSTED endpoint=$endpoint attempts=$attempt" >&2
      cat "$error_file" >&2
      rm -f "$response_file" "$error_file"
      return "$rc"
    fi

    echo "GITHUB_API_RETRY endpoint=$endpoint attempt=$attempt/$max_attempts delay_seconds=$attempt" >&2
    sleep "$attempt"
    attempt=$((attempt + 1))
  done

  rm -f "$response_file" "$error_file"
  return "$rc"
}
