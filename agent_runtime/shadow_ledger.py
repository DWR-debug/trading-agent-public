"""Append-only ledger for paper-shadow intents.

The ledger records already-frozen intents without executing orders or evaluating
outcomes. It enforces safety, uniqueness, monotone decision time and a durable
chain fingerprint so later paper-forward consumers can verify provenance.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from agent_runtime.decision_adapter import intent_fingerprint
from agent_runtime.paper_intent import PaperIntent, PaperIntentError


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PaperIntentError(f"invalid intent timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise PaperIntentError("intent timestamp must include a timezone")
    return parsed


@dataclass(frozen=True)
class ShadowLedgerReceipt:
    count: int
    last_decision_time_utc: str | None
    chain_fingerprint: str


class PaperShadowIntentLedger:
    """Append-only in-memory ledger; persistence is explicit via persist()."""

    def __init__(self) -> None:
        self._intents: list[PaperIntent] = []
        self._fingerprints: set[str] = set()

    @property
    def intents(self) -> tuple[PaperIntent, ...]:
        return tuple(self._intents)

    def append(self, intent: PaperIntent) -> ShadowLedgerReceipt:
        intent.validate()
        fp = intent_fingerprint(intent)
        if fp in self._fingerprints:
            raise PaperIntentError(f"duplicate paper-shadow intent: {fp}")

        current_time = _timestamp(intent.decision_time_utc)
        if self._intents:
            previous_time = _timestamp(self._intents[-1].decision_time_utc)
            if current_time < previous_time:
                raise PaperIntentError("paper-shadow intent decision time moved backwards")

        self._intents.append(intent)
        self._fingerprints.add(fp)
        return self.receipt()

    def receipt(self) -> ShadowLedgerReceipt:
        fps = [intent_fingerprint(item) for item in self._intents]
        chain = hashlib.sha256("|".join(fps).encode("utf-8")).hexdigest()
        return ShadowLedgerReceipt(
            count=len(self._intents),
            last_decision_time_utc=self._intents[-1].decision_time_utc if self._intents else None,
            chain_fingerprint=chain,
        )

    def persist(self, path: str | Path) -> dict[str, object]:
        receipt = self.receipt()
        envelope = {
            "schema_version": 1,
            "record_type": "paper_shadow_intent_ledger",
            "intents": [
                {
                    "candidate_id": item.candidate_id,
                    "symbol": item.symbol,
                    "decision_time_utc": item.decision_time_utc,
                    "input_fingerprint": item.input_fingerprint,
                    "decision_fingerprint": item.decision_fingerprint,
                    "target_exposure": item.target_exposure,
                    "execution_route": item.execution_route,
                    "broker_order_supported": item.broker_order_supported,
                    "intent_fingerprint": intent_fingerprint(item),
                }
                for item in self._intents
            ],
            "scientific_evidence": False,
            "performance_authorization": False,
            "promotion": False,
            "live_execution": False,
            "count": receipt.count,
            "last_decision_time_utc": receipt.last_decision_time_utc,
            "chain_fingerprint": receipt.chain_fingerprint,
        }
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(envelope, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        return envelope
