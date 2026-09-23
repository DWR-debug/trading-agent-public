"""Reproduzierbares Forschungsprotokoll.

Der finale Holdout-Abschnitt wird bis zur Auswahl des Kandidaten nicht
verwendet. Ausführungskosten und Randomisierungs-Seed sind explizit
festgelegt und werden im Research-Report gespeichert.

Keine Orderausführung.
Kein Echtgeldhandel.
"""

from dataclasses import dataclass
from hashlib import sha256
import json
import random

from backtesting.models import Candle


@dataclass(frozen=True)
class ResearchProtocol:
    holdout_ratio: float = 0.10
    fee_rate: float = 0.001
    slippage_rate: float = 0.0005
    permutation_trials: int = 1000
    permutation_seed: int = 20260921

    def __post_init__(self):
        if not 0.0 < self.holdout_ratio < 0.5:
            raise ValueError(
                "holdout_ratio muss zwischen 0 und kleiner 0.5 liegen."
            )
        if self.fee_rate < 0.0:
            raise ValueError("fee_rate darf nicht negativ sein.")
        if self.slippage_rate < 0.0:
            raise ValueError("slippage_rate darf nicht negativ sein.")
        if self.permutation_trials < 100:
            raise ValueError(
                "permutation_trials muss mindestens 100 sein."
            )


def split_holdout(
    candles: tuple[Candle, ...],
    protocol: ResearchProtocol,
) -> tuple[tuple[Candle, ...], tuple[Candle, ...]]:
    if len(candles) < 2:
        raise ValueError(
            "Für einen Holdout-Split werden mindestens 2 Candles benötigt."
        )

    holdout_count = max(
        1,
        int(len(candles) * protocol.holdout_ratio),
    )
    research_count = len(candles) - holdout_count

    if research_count < 2:
        raise ValueError(
            "Der Forschungsabschnitt wäre nach Holdout-Split zu klein."
        )

    return candles[:research_count], candles[research_count:]


def dataset_fingerprint(candles: tuple[Candle, ...]) -> str:
    payload = [
        {
            "timestamp": candle.timestamp.isoformat(),
            "open": candle.open,
            "high": candle.high,
            "low": candle.low,
            "close": candle.close,
            "volume": candle.volume,
        }
        for candle in candles
    ]
    raw = json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(raw).hexdigest()


def permutation_positive_tail_probability(
    pnls: tuple[float, ...],
    *,
    trials: int,
    seed: int,
) -> float | None:
    """Diagnostik: deterministische Sign-Permutation der Holdout-PnLs.

    Das ist bewusst nur ein Diagnosewert und kein separates Profitabilitäts-
    Gate, da die Nullannahme von der Trade-Verteilung abhängt.
    """

    if len(pnls) < 10:
        return None

    observed = sum(pnls)
    if observed <= 0.0:
        return 1.0

    rng = random.Random(seed)
    absolute = [abs(value) for value in pnls]
    extreme = 0

    for _ in range(trials):
        randomized_total = sum(
            value if rng.getrandbits(1) else -value
            for value in absolute
        )
        if randomized_total >= observed:
            extreme += 1

    return (extreme + 1) / (trials + 1)
