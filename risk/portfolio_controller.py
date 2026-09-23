"""
Trading Agent - Portfolio Risk Controller

Zentrale Sicherheitsinstanz vor jeder Paper-Order.

Kein Echtgeldhandel.
"""

from config import settings
from risk.risk_engine import RiskError


class PortfolioRiskController:
    def __init__(self, initial_capital: float):
        if initial_capital <= 0:
            raise RiskError("Initiales Kapital muss größer als 0 sein.")

        self.initial_capital = initial_capital
        self.equity = initial_capital
        self.peak_equity = initial_capital
        self.daily_start_equity = initial_capital

        self.open_positions = 0
        self.kill_switch = False

    def update_equity(self, equity: float) -> None:
        if equity < 0:
            raise RiskError("Equity darf nicht negativ sein.")

        self.equity = equity

        if equity > self.peak_equity:
            self.peak_equity = equity

        self._check_limits()

    def record_position_opened(self) -> None:
        self._check_limits()

        if self.open_positions >= settings.MAX_OPEN_POSITIONS:
            raise RiskError(
                f"Maximale Anzahl offener Positionen "
                f"({settings.MAX_OPEN_POSITIONS}) erreicht."
            )

        self.open_positions += 1

    def record_position_closed(self) -> None:
        if self.open_positions <= 0:
            raise RiskError("Keine offene Position zum Schließen.")

        self.open_positions -= 1

    def reset_daily_limit(self) -> None:
        self.daily_start_equity = self.equity

    def activate_kill_switch(self, reason: str) -> None:
        self.kill_switch = True
        raise RiskError(f"KILL-SWITCH AKTIV: {reason}")

    def check_trade_allowed(self) -> None:
        if self.kill_switch:
            raise RiskError(
                "KILL-SWITCH AKTIV: Keine weiteren Trades erlaubt."
            )

        self._check_limits()

    def _check_limits(self) -> None:
        daily_loss = self.daily_start_equity - self.equity

        if daily_loss >= settings.MAX_DAILY_LOSS_EUR:
            self.kill_switch = True
            raise RiskError(
                f"KILL-SWITCH: Tagesverlustlimit von "
                f"{settings.MAX_DAILY_LOSS_EUR:.2f} € erreicht."
            )

        if self.peak_equity > 0:
            drawdown_percent = (
                (self.peak_equity - self.equity)
                / self.peak_equity
                * 100
            )
        else:
            drawdown_percent = 0

        if drawdown_percent >= settings.MAX_DRAWDOWN_PERCENT:
            self.kill_switch = True
            raise RiskError(
                f"KILL-SWITCH: Maximaler Drawdown von "
                f"{settings.MAX_DRAWDOWN_PERCENT:.2f}% erreicht."
            )

    def status(self) -> dict:
        if self.peak_equity > 0:
            drawdown_percent = (
                (self.peak_equity - self.equity)
                / self.peak_equity
                * 100
            )
        else:
            drawdown_percent = 0

        return {
            "initial_capital": self.initial_capital,
            "equity": self.equity,
            "peak_equity": self.peak_equity,
            "daily_start_equity": self.daily_start_equity,
            "open_positions": self.open_positions,
            "drawdown_percent": drawdown_percent,
            "kill_switch": self.kill_switch,
        }
