"""Research-only leverage and long/short return models.

Two distinct instrument abstractions are supported:
- margin_leverage: exposure is applied continuously to the underlying return
  and financing/borrow costs are charged separately;
- daily_reset_product: the stated leverage multiple is applied to each period
  independently, so path-dependent compounding is preserved.

This module never places orders and never enables live trading.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


class LeverageMode(StrEnum):
    MARGIN = "margin_leverage"
    DAILY_RESET_PRODUCT = "daily_reset_product"


class LeverageModelError(ValueError):
    """Raised when a leverage-model contract is violated."""


@dataclass(frozen=True)
class LeverageConfig:
    multiple: float = 1.0
    mode: LeverageMode = LeverageMode.MARGIN
    periods_per_year: int = 252
    financing_rate_annual: float = 0.0
    short_borrow_rate_annual: float = 0.0
    product_fee_annual: float = 0.0

    def __post_init__(self) -> None:
        if not isfinite(self.multiple) or self.multiple < 0.0:
            raise LeverageModelError("Leverage multiple must be finite and >= 0.")
        if self.periods_per_year < 1:
            raise LeverageModelError("periods_per_year must be >= 1.")
        for name, value in (
            ("financing_rate_annual", self.financing_rate_annual),
            ("short_borrow_rate_annual", self.short_borrow_rate_annual),
            ("product_fee_annual", self.product_fee_annual),
        ):
            if not isfinite(value) or value < 0.0:
                raise LeverageModelError(f"{name} must be finite and >= 0.")


@dataclass(frozen=True)
class LeveragedPathResult:
    final_equity: float
    total_return: float
    minimum_equity: float
    maximum_drawdown: float
    ruined: bool
    observations: tuple[float, ...]


def period_return(
    underlying_return: float,
    signed_exposure: float,
    config: LeverageConfig,
) -> float:
    """Calculate one-period portfolio return before liquidation handling.

    signed_exposure is normalized strategy exposure: +1 long, -1 short.
    Values between -1 and +1 represent partial exposure. The leverage
    multiple scales that signed exposure.
    """
    if not isfinite(underlying_return) or underlying_return <= -1.0:
        raise LeverageModelError(
            "underlying_return must be finite and greater than -100%."
        )
    if not isfinite(signed_exposure):
        raise LeverageModelError("signed_exposure must be finite.")

    notional = abs(signed_exposure) * config.multiple
    directional = signed_exposure * config.multiple * underlying_return

    if config.mode is LeverageMode.MARGIN:
        borrowed_notional = max(0.0, notional - abs(signed_exposure))
        financing = (
            borrowed_notional
            * config.financing_rate_annual
            / config.periods_per_year
        )
        borrow = (
            max(0.0, -signed_exposure)
            * config.multiple
            * config.short_borrow_rate_annual
            / config.periods_per_year
        )
        return directional - financing - borrow

    if config.mode is LeverageMode.DAILY_RESET_PRODUCT:
        product_fee = (
            abs(signed_exposure)
            * config.product_fee_annual
            / config.periods_per_year
        )
        return directional - product_fee

    raise LeverageModelError(f"Unsupported leverage mode: {config.mode}")


def simulate_leveraged_path(
    underlying_returns: tuple[float, ...],
    signed_exposures: tuple[float, ...],
    config: LeverageConfig | None = None,
) -> LeveragedPathResult:
    """Replay a signed strategy through the configured leverage instrument.

    Equity is floored at zero. Once zero is reached, the path remains closed.
    This is a research-safe abstraction rather than a broker-specific
    liquidation simulation.
    """
    if len(underlying_returns) != len(signed_exposures):
        raise LeverageModelError(
            "Return and exposure series must have equal length."
        )
    config = config or LeverageConfig()

    equity = 1.0
    peak = 1.0
    minimum = 1.0
    maximum_drawdown = 0.0
    ruined = False
    observations: list[float] = []

    for underlying_return, exposure in zip(underlying_returns, signed_exposures):
        if ruined:
            observations.append(0.0)
            continue

        net_return = period_return(
            underlying_return,
            exposure,
            config,
        )
        new_equity = equity * (1.0 + net_return)
        if new_equity <= 0.0:
            equity = 0.0
            ruined = True
            observations.append(-1.0)
            minimum = 0.0
            maximum_drawdown = 1.0
            continue

        equity = new_equity
        minimum = min(minimum, equity)
        peak = max(peak, equity)
        maximum_drawdown = max(
            maximum_drawdown,
            1.0 - equity / peak,
        )
        observations.append(net_return)

    return LeveragedPathResult(
        final_equity=equity,
        total_return=equity - 1.0,
        minimum_equity=minimum,
        maximum_drawdown=maximum_drawdown,
        ruined=ruined,
        observations=tuple(observations),
    )
