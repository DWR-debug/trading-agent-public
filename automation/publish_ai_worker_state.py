"""Race-tolerant publisher for bounded local AI worker state."""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path


def run(*args: str) -> None:
    subprocess.run(list(args), check=True)


def main() -> int:
    state = Path(os.environ["AI_WORKER_STATE_PATH"])
    output = Path(os.environ["AI_WORKER_OUTPUT_PATH"])
    state.parent.mkdir(parents=True, exist_ok=True)

    payload_source = output
    if not payload_source.is_file():
        state.write_text(
            '{"schema_version":1,"task_id":"'
            + os.environ["AI_WORKER_TASK_ID"]
            + '","provider":"'
            + os.environ["AI_WORKER_PROVIDER"]
            + '","status":"NO_OUTPUT","worker_output_is_scientific_evidence":false}\n',
            encoding="utf-8",
        )

    for attempt in range(1, 6):
        run("git", "fetch", "origin", "master")
        run("git", "checkout", "-B", "master", "origin/master")

        if output.is_file():
            shutil.copy2(output, state)
        state.touch(exist_ok=True)

        run("git", "config", "user.name", "github-actions[bot]")
        run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
        subprocess.run(["git", "add", str(state)], check=True)

        diff = subprocess.run(["git", "diff", "--cached", "--quiet"], check=False)
        if diff.returncode == 0:
            return 0

        commit = subprocess.run(
            ["git", "commit", "-m", "OPS: record local AI worker state"],
            check=False,
        )
        if commit.returncode != 0:
            if attempt == 5:
                return 1
            time.sleep(2)
            continue

        push = subprocess.run(["git", "push", "origin", "HEAD:master"], check=False)
        if push.returncode == 0:
            return 0
        time.sleep(2)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
