"""
Trading Agent - Strategy Parameters

Veränderbare Parameter für Strategien und spätere Optimierung.

WICHTIG:
Diese Datei enthält keine Möglichkeit, Sicherheitslimits
aus config.settings.py zu überschreiben.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MomentumParameters:
    lookback: int = 5

    def __post_init__(self):
        if self.lookback < 1:
            raise ValueError(
                "Momentum-Lookback muss mindestens 1 sein."
            )


@dataclass(frozen=True)
class MeanReversionParameters:
    window: int = 5
    threshold: float = 0.02

    def __post_init__(self):
        if self.window < 2:
            raise ValueError(
                "Mean-Reversion-Window muss mindestens 2 sein."
            )

        if self.threshold <= 0:
            raise ValueError(
                "Mean-Reversion-Threshold muss größer als 0 sein."
            )


@dataclass(frozen=True)
class StrategyParameters:
    momentum: MomentumParameters = MomentumParameters()
    mean_reversion: MeanReversionParameters = (
        MeanReversionParameters()
    )
