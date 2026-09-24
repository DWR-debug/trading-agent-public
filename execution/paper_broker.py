"""
Trading Agent - Paper Broker

Lokale Börsensimulation.
Keine Netzwerkverbindung.
Keine echten Orders.

Unterstützt:
- Position eröffnen
- Position schließen
- P&L berechnen
- Gebühren
- Slippage
- Equity-Berechnung
"""

from dataclasses import dataclass

from execution.cost_contract import ResearchExecutionCostContract


@dataclass
class Position:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    stop_price: float
    leverage: float
    margin: float


class PaperBroker:
    def __init__(
        self,
        initial_capital: float = 500.0,
        fee_rate: float = 0.0005,
        slippage_rate: float = 0.0005,
        *,
        cost_contract: ResearchExecutionCostContract | None = None,
    ):
        if initial_capital <= 0:
            raise ValueError("Startkapital muss größer als 0 sein.")

        if cost_contract is not None:
            cost_contract.validate()
            fee_rate = cost_contract.fee_bps / 10_000.0
            slippage_rate = cost_contract.slippage_bps / 10_000.0

        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        self.positions = {}

        # Realisiertes P&L
        self.realized_pnl = 0.0

        # Bereits bezahlte Gebühren
        self.total_fees = 0.0

    def execute_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        leverage: float = 1.0,
        stop_price: float | None = None,
    ) -> dict:

        side = side.upper()

        if side not in {"BUY", "SELL"}:
            raise ValueError("Side muss BUY oder SELL sein.")

        if quantity <= 0:
            raise ValueError("Quantity muss größer als 0 sein.")

        if price <= 0:
            raise ValueError("Preis muss größer als 0 sein.")

        if leverage < 1:
            raise ValueError("Hebel muss mindestens 1x betragen.")

        if stop_price is not None and stop_price <= 0:
            raise ValueError("Stop-Preis muss größer als 0 sein.")

        if stop_price is not None:
            if side == "BUY" and stop_price >= price:
                raise ValueError(
                    "Bei BUY muss der Stop unter dem Entry liegen."
                )

            if side == "SELL" and stop_price <= price:
                raise ValueError(
                    "Bei SELL muss der Stop über dem Entry liegen."
                )

        if symbol in self.positions:
            raise ValueError(
                f"Für {symbol} existiert bereits eine offene Position."
            )

        # Slippage simulieren
        if side == "BUY":
            execution_price = price * (1 + self.slippage_rate)
        else:
            execution_price = price * (1 - self.slippage_rate)

        position_value = quantity * execution_price
        margin = position_value / leverage
        fee = position_value * self.fee_rate

        total_required = margin + fee

        if total_required > self.cash:
            raise ValueError(
                f"Nicht genügend virtuelles Kapital. "
                f"Benötigt: {total_required:.2f} €, "
                f"verfügbar: {self.cash:.2f} €"
            )

        self.cash -= total_required
        self.total_fees += fee

        self.positions[symbol] = Position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=execution_price,
            stop_price=stop_price,
            leverage=leverage,
            margin=margin,
        )

        return {
            "status": "PAPER_FILLED",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "requested_price": price,
            "execution_price": execution_price,
            "position_value": position_value,
            "margin": margin,
            "fee": fee,
            "remaining_cash": self.cash,
        }

    def check_stop_loss(
        self,
        symbol: str,
        current_price: float,
    ) -> bool:
        """
        Prüft, ob der Stop-Loss erreicht wurde.

        BUY: Stop wird ausgelöst, wenn der Marktpreis <= Stop ist.
        SELL: Stop wird ausgelöst, wenn der Marktpreis >= Stop ist.

        Gibt True zurück, wenn der Stop ausgelöst wurde.
        """

        if symbol not in self.positions:
            return False

        if current_price <= 0:
            raise ValueError("Preis muss größer als 0 sein.")

        position = self.positions[symbol]

        if position.stop_price is None:
            return False

        if position.side == "BUY":
            return current_price <= position.stop_price

        return current_price >= position.stop_price

    def execute_stop_loss(
        self,
        symbol: str,
        current_price: float,
    ) -> dict:
        """
        Schließt eine Position ausschließlich dann,
        wenn ihr Stop-Loss erreicht wurde.
        """

        if not self.check_stop_loss(symbol, current_price):
            raise ValueError(
                f"Stop-Loss für {symbol} wurde nicht erreicht."
            )

        result = self.close_position(
            symbol=symbol,
            price=current_price,
        )

        result["reason"] = "STOP_LOSS"

        return result

    def close_position(
        self,
        symbol: str,
        price: float,
    ) -> dict:

        if symbol not in self.positions:
            raise ValueError(
                f"Keine offene Position für {symbol}."
            )

        if price <= 0:
            raise ValueError("Preis muss größer als 0 sein.")

        position = self.positions[symbol]

        # Slippage beim Schließen
        if position.side == "BUY":
            exit_price = price * (1 - self.slippage_rate)
        else:
            exit_price = price * (1 + self.slippage_rate)

        entry_value = position.quantity * position.entry_price
        exit_value = position.quantity * exit_price

        if position.side == "BUY":
            gross_pnl = exit_value - entry_value
        else:
            gross_pnl = entry_value - exit_value

        exit_fee = exit_value * self.fee_rate
        net_pnl = gross_pnl - exit_fee

        # Margin wird beim Schließen freigegeben.
        self.cash += position.margin + net_pnl

        self.realized_pnl += net_pnl
        self.total_fees += exit_fee

        del self.positions[symbol]

        return {
            "status": "PAPER_CLOSED",
            "symbol": symbol,
            "side": position.side,
            "quantity": position.quantity,
            "entry_price": position.entry_price,
            "exit_price": exit_price,
            "gross_pnl": gross_pnl,
            "exit_fee": exit_fee,
            "net_pnl": net_pnl,
            "released_margin": position.margin,
            "cash": self.cash,
            "realized_pnl": self.realized_pnl,
        }

    def unrealized_pnl(
        self,
        symbol: str,
        current_price: float,
    ) -> float:

        if symbol not in self.positions:
            raise ValueError(
                f"Keine offene Position für {symbol}."
            )

        if current_price <= 0:
            raise ValueError("Preis muss größer als 0 sein.")

        position = self.positions[symbol]

        if position.side == "BUY":
            return (
                current_price - position.entry_price
            ) * position.quantity

        return (
            position.entry_price - current_price
        ) * position.quantity

    def equity(
        self,
        market_prices: dict | None = None,
    ) -> float:

        total = self.cash

        if market_prices:
            for symbol, position in self.positions.items():
                if symbol not in market_prices:
                    continue

                total += position.margin
                total += self.unrealized_pnl(
                    symbol,
                    market_prices[symbol],
                )

        return total

    def account_status(
        self,
        market_prices: dict | None = None,
    ) -> dict:

        current_equity = self.equity(market_prices)

        unrealized = current_equity - self.cash

        return {
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "equity": current_equity,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": unrealized,
            "total_fees": self.total_fees,
            "open_positions": len(self.positions),
        }
