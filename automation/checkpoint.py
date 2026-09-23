"""Atomic checkpoints for resumable local research."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def checkpoint_fingerprint(state: dict[str, Any]) -> str:
    payload = dict(state)
    payload.pop("checkpoint_fingerprint", None)
    payload.pop("updated_at", None)
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


class ResearchCheckpointStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(self, state: dict[str, Any]) -> None:
        payload = dict(state)
        payload.pop("checkpoint_fingerprint", None)
        payload["checkpoint_fingerprint"] = checkpoint_fingerprint(payload)
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            ),
            encoding="utf-8",
        )
        os.replace(temp, self.path)

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        data = json.loads(
            self.path.read_text(encoding="utf-8")
        )
        if not isinstance(data, dict):
            raise ValueError(
                "Checkpoint muss ein JSON-Objekt enthalten."
            )
        stored = data.get("checkpoint_fingerprint")
        if stored is not None and stored != checkpoint_fingerprint(data):
            raise ValueError(
                "Research-Checkpoint besitzt keinen gültigen Fingerprint."
            )
        return data


def checkpoint_key(symbol: str, interval: str) -> str:
    return f"{symbol.upper()}::{interval}"
