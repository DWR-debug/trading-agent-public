"""Fixed turn-of-month calendar-alpha research policy."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


class TurnOfMonthAlphaError(ValueError):
    """Raised for malformed turn-of-month policy configuration."""


@dataclass(frozen=True)
class TurnOfMonthPolicy:
    """Long-only equal-weight exposure during the fixed four-day TOM window."""

    symbols: tuple[str, ...] = (
        "EWS",
        "EWM",
        "EZA",
        "ECH",
        "EPU",
        "EIDO",
        "THD",
        "EPHE",
    )

    def __post_init__(self) -> None:
        if len(self.symbols) != 8 or len(set(self.symbols)) != 8:
            raise TurnOfMonthAlphaError("Exactly eight distinct symbols are required.")

    @property
    def weight(self) -> float:
        return 1.0 / len(self.symbols)

    def is_active(self, day: date, trading_days: tuple[date, ...]) -> bool:
        if day not in trading_days:
            raise TurnOfMonthAlphaError(
                "Target day must exist on the supplied trading calendar."
            )
        month_days = tuple(
            value
            for value in trading_days
            if value.year == day.year and value.month == day.month
        )
        day_index = month_days.index(day)
        return day_index < 3 or day_index == len(month_days) - 1

    def weights_for_day(
        self,
        day: date,
        trading_days: tuple[date, ...],
    ) -> dict[str, float]:
        return (
            {symbol: self.weight for symbol in self.symbols}
            if self.is_active(day, trading_days)
            else {}
        )
