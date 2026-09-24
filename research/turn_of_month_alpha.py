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

        months: dict[tuple[int, int], list[date]] = {}
        for value in trading_days:
            months.setdefault((value.year, value.month), []).append(value)

        month_keys = tuple(months)
        active_days: set[date] = set()
        for index, key in enumerate(month_keys):
            active_days.add(months[key][-1])
            if index + 1 < len(month_keys):
                active_days.update(months[month_keys[index + 1]][:3])

        return day in active_days

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
