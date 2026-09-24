"""Fixed overnight-gap / same-day intraday reversal research policy."""
from __future__ import annotations

from dataclasses import dataclass


class OpenCloseGapReversalError(ValueError):
    """Raised for malformed gap-reversal policy configuration."""


@dataclass(frozen=True)
class OpenCloseGapReversalPolicy:
    """Equal-weight, parameter-free reversal of each asset's overnight gap."""

    symbols: tuple[str, ...] = (
        "SPYG",
        "IJR",
        "IEFA",
        "IEMG",
        "IVE",
        "IVW",
        "VOE",
        "VOT",
    )

    def __post_init__(self) -> None:
        if len(self.symbols) != 8 or len(set(self.symbols)) != 8:
            raise OpenCloseGapReversalError(
                "Exactly eight distinct symbols are required."
            )

    @property
    def weight(self) -> float:
        return 1.0 / len(self.symbols)

    def signal(self, overnight_gap: float) -> int:
        """Long after a negative gap, short after a positive gap, flat at zero."""
        if overnight_gap > 0.0:
            return -1
        if overnight_gap < 0.0:
            return 1
        return 0

    def target_weight(self, overnight_gap: float, symbol: str) -> float:
        if symbol not in self.symbols:
            raise OpenCloseGapReversalError(f"Unknown symbol: {symbol}")
        return self.weight * self.signal(overnight_gap)
