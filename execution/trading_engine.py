"""
Trading Agent - sichere Trading Engine

Signal -> Risk Engine -> Portfolio Risk Controller
       -> Execution Guard -> Paper Broker

Ausschließlich Paper Trading.
"""

from config import settings
from execution.execution_guard import execute_order
from execution.paper_broker import PaperBroker
from risk.risk_engine import calculate_position
from risk.portfolio_controller import PortfolioRiskController


class TradingEngine:
    def __init__(self):
        if settings.PAPER_ONLY is not True:
            raise RuntimeError(
                "SICHERHEITSSTOPP: PAPER_ONLY muss True sein."
            )

        if settings.LIVE_TRADING_ENABLED is not False:
            raise RuntimeError(
                "SICHERHEITSSTOPP: Live Trading ist aktiviert."
            )

        self.broker = PaperBroker(
            initial_capital=settings.INITIAL_CAPITAL_EUR
        )

        self.portfolio_risk = PortfolioRiskController(
            initial_capital=settings.INITIAL_CAPITAL_EUR
        )

    def update_market_equity(self, market_prices: dict) -> dict:
        """
        Aktualisiert die Portfolio-Equity anhand der aktuellen
        simulierten Marktpreise.

        Prüft automatisch alle offenen Stop-Loss-Positionen.

        Keine Netzwerkverbindung und kein Live-Trading.
        """

        stop_losses = []

        # Kopie der Symbolliste, weil ausgelöste Positionen
        # während der Schleife entfernt werden.
        for symbol in list(self.broker.positions):
            if symbol not in market_prices:
                continue

            if self.broker.check_stop_loss(
                symbol,
                market_prices[symbol],
            ):
                closed = self.broker.execute_stop_loss(
                    symbol=symbol,
                    current_price=market_prices[symbol],
                )

                self.portfolio_risk.record_position_closed()
                stop_losses.append(closed)

        # Equity nach eventuellen Stop-Loss-Schließungen neu berechnen.
        equity = self.broker.equity(market_prices)

        self.portfolio_risk.update_equity(equity)

        return {
            "equity": equity,
            "stop_losses": stop_losses,
            "portfolio_risk": self.portfolio_risk.status(),
            "account": self.broker.account_status(market_prices),
        }

    def close_paper_position(
        self,
        symbol: str,
        price: float,
    ) -> dict:
        """
        Schließt ausschließlich eine simulierte Paper-Position
        und synchronisiert den Portfolio-Risikostatus.
        """

        result = self.broker.close_position(
            symbol=symbol,
            price=price,
        )

        self.portfolio_risk.record_position_closed()

        equity = self.broker.equity()

        self.portfolio_risk.update_equity(equity)

        result["portfolio_risk"] = self.portfolio_risk.status()
        result["account"] = self.broker.account_status()

        return result

    def create_paper_trade(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        stop_price: float,
        leverage: float = 1.0,
    ) -> dict:

        # 1. Portfolio-Sicherheitsprüfung
        self.portfolio_risk.check_trade_allowed()

        # 2. Risk Engine berechnet erlaubte Positionsgröße
        risk = calculate_position(
            capital_eur=self.broker.cash,
            entry_price=entry_price,
            stop_price=stop_price,
            leverage=leverage,
        )

        # 3. Sicherheitsprüfung des Einzelrisikos
        if risk["risk_eur"] > (
            self.broker.initial_capital * settings.RISK_PER_TRADE
        ):
            raise RuntimeError(
                "SICHERHEITSSTOPP: Trade-Risiko überschreitet das erlaubte Limit."
            )

        # 4. Prüfung der maximalen Positionsanzahl
        self.portfolio_risk.record_position_opened()

        try:
            # 5. Execution Guard
            guard_result = execute_order(
                {
                    "symbol": symbol,
                    "side": side,
                    "quantity": risk["quantity"],
                    "entry_price": entry_price,
                    "stop_price": stop_price,
                    "leverage": leverage,
                }
            )

            if guard_result["status"] != "PAPER_ONLY":
                raise RuntimeError(
                    "SICHERHEITSSTOPP: Paper-Modus nicht bestätigt."
                )

            # 6. Ausschließlich lokaler Paper Broker
            result = self.broker.execute_order(
                symbol=symbol,
                side=side,
                quantity=risk["quantity"],
                price=entry_price,
                leverage=leverage,
                stop_price=stop_price,
            )

        except Exception:
            # Position wurde nicht erfolgreich eröffnet.
            self.portfolio_risk.record_position_closed()
            raise

        return {
            "security": guard_result,
            "risk": risk,
            "execution": result,
            "portfolio_risk": self.portfolio_risk.status(),
        }
