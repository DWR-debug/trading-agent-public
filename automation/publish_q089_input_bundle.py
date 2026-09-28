"""Persist the already-frozen Q089 adjusted-close input bundle to master."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path


def current_master_sha(repository: str) -> str:
    url = f"https://api.github.com/repos/{repository}/git/ref/heads/master"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)["object"]["sha"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-root", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    args = parser.parse_args()

    bundle_root = Path(args.bundle_root)
    manifest = json.loads(
        (bundle_root / "input_bundle_manifest.json").read_text(encoding="utf-8")
    )

    files = [
        args.result,
        (bundle_root / "input_bundle_manifest.json").as_posix(),
    ]
    files.extend(
        (bundle_root / item["path"]).as_posix()
        for item in manifest["datasets"]
    )

    command = [
        sys.executable,
        "automation/github_contents_publish.py",
        "--repository",
        args.repository,
        "--branch",
        "master",
        "--base-sha",
        current_master_sha(args.repository),
    ]
    for path in files:
        command.extend(["--file", f"{path}={path}"])
    subprocess.check_call(command)
    print("Q089_INPUT_BUNDLE_PERSISTED", manifest["bundle_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
