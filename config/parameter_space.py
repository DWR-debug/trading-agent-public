"""
Trading Agent - Parameter Space

Definiert erlaubte Kandidaten für die spätere Optimierung.

Sicherheitslimits aus config.settings werden niemals überschrieben.
"""

from dataclasses import dataclass
from config import settings
from config.parameters import (
    MomentumParameters,
    MeanReversionParameters,
    StrategyParameters,
)


@dataclass(frozen=True)
class ParameterCandidate:
    strategy: StrategyParameters
    risk_per_trade: float
    leverage: float

    def __post_init__(self):
        if not 0 < self.risk_per_trade <= settings.RISK_PER_TRADE:
            raise ValueError(
                "Risk-per-Trade überschreitet das zentrale Sicherheitslimit."
            )

        if not 1.0 <= self.leverage <= settings.MAX_LEVERAGE:
            raise ValueError(
                "Hebel überschreitet das zentrale Sicherheitslimit."
            )


class ParameterSpace:
    """
    Erzeugt gültige Parameterkombinationen.

    Der Raum kann später vom Optimizer durchsucht werden.
    """

    def __init__(
        self,
        momentum_lookbacks: list[int] | None = None,
        mean_reversion_windows: list[int] | None = None,
        mean_reversion_thresholds: list[float] | None = None,
        risk_per_trade_values: list[float] | None = None,
        leverage_values: list[float] | None = None,
    ):
        self.momentum_lookbacks = momentum_lookbacks or [3, 5, 8, 13, 21]
        self.mean_reversion_windows = (
            mean_reversion_windows or [5, 10, 20, 30]
        )
        self.mean_reversion_thresholds = (
            mean_reversion_thresholds or [0.01, 0.02, 0.03, 0.05]
        )

        self.risk_per_trade_values = (
            risk_per_trade_values
            or [
                0.0025,
                0.005,
                0.0075,
                0.01,
            ]
        )

        self.leverage_values = (
            leverage_values
            or [1.0, 1.5, 2.0, 3.0]
        )

        self._validate_space()

    def _validate_space(self):
        if not self.momentum_lookbacks:
            raise ValueError("Momentum-Parameterraum darf nicht leer sein.")

        if not self.mean_reversion_windows:
            raise ValueError(
                "Mean-Reversion-Parameterraum darf nicht leer sein."
            )

        if not self.mean_reversion_thresholds:
            raise ValueError(
                "Mean-Reversion-Threshold-Raum darf nicht leer sein."
            )

        if not self.risk_per_trade_values:
            raise ValueError(
                "Risk-Parameterraum darf nicht leer sein."
            )

        if not self.leverage_values:
            raise ValueError(
                "Hebel-Parameterraum darf nicht leer sein."
            )

        for risk in self.risk_per_trade_values:
            if not 0 < risk <= settings.RISK_PER_TRADE:
                raise ValueError(
                    f"Ungültiges Risiko: {risk:.4f}. "
                    f"Maximum: {settings.RISK_PER_TRADE:.4f}"
                )

        for leverage in self.leverage_values:
            if not 1.0 <= leverage <= settings.MAX_LEVERAGE:
                raise ValueError(
                    f"Ungültiger Hebel: {leverage}. "
                    f"Maximum: {settings.MAX_LEVERAGE}"
                )

    def candidates(self):
        """
        Liefert alle gültigen Parameterkombinationen.
        """

        for lookback in self.momentum_lookbacks:
            for window in self.mean_reversion_windows:
                for threshold in self.mean_reversion_thresholds:
                    for risk in self.risk_per_trade_values:
                        for leverage in self.leverage_values:

                            strategy = StrategyParameters(
                                momentum=MomentumParameters(
                                    lookback=lookback
                                ),
                                mean_reversion=MeanReversionParameters(
                                    window=window,
                                    threshold=threshold,
                                ),
                            )

                            yield ParameterCandidate(
                                strategy=strategy,
                                risk_per_trade=risk,
                                leverage=leverage,
                            )

    def size(self) -> int:
        """
        Anzahl aller zu testenden Kombinationen.
        """

        return (
            len(self.momentum_lookbacks)
            * len(self.mean_reversion_windows)
            * len(self.mean_reversion_thresholds)
            * len(self.risk_per_trade_values)
            * len(self.leverage_values)
        )
