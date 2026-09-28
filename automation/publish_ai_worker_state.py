"""Race-tolerant publisher for bounded local AI worker state.

Uses the GitHub Git Data API instead of local git so self-hosted Windows
runners can operate in REST/ZIP checkout mode as well as full git checkouts.
"""
from __future__ import annotations

import base64
import os
import time
from pathlib import Path

from automation import github_contents_publish


MAX_ATTEMPTS = 5
RETRY_DELAY_SECONDS = 1.0


def main() -> int:
    state = Path(os.environ["AI_WORKER_STATE_PATH"])
    output = Path(os.environ["AI_WORKER_OUTPUT_PATH"])
    state.parent.mkdir(parents=True, exist_ok=True)

    if output.is_file():
        state.write_bytes(output.read_bytes())
    elif not state.is_file():
        state.write_text(
            '{"schema_version":1,"task_id":"'
            + os.environ["AI_WORKER_TASK_ID"]
            + '", "provider":"'
            + os.environ["AI_WORKER_PROVIDER"]
            + '", "status":"NO_OUTPUT","worker_output_is_scientific_evidence":false}\n'.replace(', ', ','),
            encoding="utf-8",
        )

    repository = os.environ["GITHUB_REPOSITORY"]
    state_path = state.as_posix()
    desired = state.read_text(encoding="utf-8")
    os.environ.setdefault("PUBLISH_MESSAGE", "OPS: record local AI worker state")

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            ref = github_contents_publish.api(
                "GET",
                f"https://api.github.com/repos/{repository}/git/ref/heads/master",
            )
            base_sha = ref["object"]["sha"]
            try:
                current = github_contents_publish.api(
                    "GET",
                    f"https://api.github.com/repos/{repository}/contents/{state_path}?ref=master",
                )
            except RuntimeError as exc:
                if ": 404:" not in str(exc):
                    raise
            else:
                current_content = base64.b64decode(current["content"]).decode("utf-8")
                if current_content == desired:
                    print("LOCAL_AI_STATE_UNCHANGED", flush=True)
                    return 0
            commit_sha = github_contents_publish.publish(
                repository,
                "master",
                base_sha,
                [(state_path, str(state))],
            )
            print(f"LOCAL_AI_STATE_PUBLISHED={commit_sha}", flush=True)
            return 0
        except (RuntimeError, KeyError, TypeError) as exc:
            if attempt == MAX_ATTEMPTS:
                print(f"LOCAL_AI_STATE_PUBLISH_FAILED={exc}", flush=True)
                return 1
            time.sleep(RETRY_DELAY_SECONDS * attempt)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
