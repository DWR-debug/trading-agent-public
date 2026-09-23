"""
Trading Agent - Backtest Engine

Offline-Simulation historischer Trades.

Keine Netzwerkverbindung.
Keine Live-Orders.
Kein Echtgeldhandel.
"""

from dataclasses import dataclass

from backtesting.metrics import calculate_metrics
from backtesting.models import Candle, BacktestTrade
from config import settings
from config.parameters import StrategyParameters
from risk.risk_engine import calculate_position
from strategies.signals import SignalType, TradingSignal
from strategies.strategy_engine import StrategyEngine


@dataclass(frozen=True)
class BacktestResult:
    initial_capital: float
    final_capital: float
    realized_pnl: float
    trades: tuple[BacktestTrade, ...]

    @property
    def total_return_percent(self) -> float:
        if self.initial_capital <= 0:
            return 0.0

        return (
            (self.final_capital - self.initial_capital)
            / self.initial_capital
        ) * 100.0

    @property
    def metrics(self) -> dict:
        return calculate_metrics(
            self.initial_capital,
            self.trades,
        )


class BacktestEngine:
    def __init__(
        self,
        initial_capital: float = settings.INITIAL_CAPITAL_EUR,
        risk_per_trade: float = settings.RISK_PER_TRADE,
        leverage: float = 1.0,
        fee_rate: float = 0.001,
        slippage_rate: float = 0.0005,
        parameters: StrategyParameters | None = None,
    ):
        if initial_capital <= 0:
            raise ValueError(
                "Initiales Kapital muss größer als 0 sein."
            )

        if not 0 < risk_per_trade <= settings.RISK_PER_TRADE:
            raise ValueError(
                "Risiko überschreitet das zentrale Sicherheitslimit."
            )

        if not 1.0 <= leverage <= settings.MAX_LEVERAGE:
            raise ValueError(
                "Hebel überschreitet das zentrale Sicherheitslimit."
            )

        if fee_rate < 0:
            raise ValueError(
                "Fee-Rate darf nicht negativ sein."
            )

        if slippage_rate < 0:
            raise ValueError(
                "Slippage-Rate darf nicht negativ sein."
            )

        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.leverage = leverage
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        self.strategy_engine = StrategyEngine(
            parameters=parameters
        )

    def _calculate_exit(
        self,
        side: str,
        entry_price: float,
        exit_price: float,
        quantity: float,
    ) -> tuple[float, float, float, float]:
        """
        Berechnet Entry-/Exit-Ausführungspreise,
        Brutto-PnL und Gebühren.
        """

        if side == "BUY":
            execution_entry = (
                entry_price
                * (1.0 + self.slippage_rate)
            )

            execution_exit = (
                exit_price
                * (1.0 - self.slippage_rate)
            )

            gross_pnl = (
                execution_exit - execution_entry
            ) * quantity

        else:
            execution_entry = (
                entry_price
                * (1.0 - self.slippage_rate)
            )

            execution_exit = (
                exit_price
                * (1.0 + self.slippage_rate)
            )

            gross_pnl = (
                execution_entry - execution_exit
            ) * quantity

        entry_value = execution_entry * quantity
        exit_value = execution_exit * quantity

        fees = (
            entry_value + exit_value
        ) * self.fee_rate

        net_pnl = gross_pnl - fees

        return execution_entry, execution_exit, net_pnl, fees

    def run(
        self,
        symbol: str,
        candles: list[Candle],
        signals: list[TradingSignal | None] | tuple[TradingSignal | None, ...] | None = None,
    ) -> BacktestResult:

        if not symbol:
            raise ValueError(
                "Symbol darf nicht leer sein."
            )

        if not candles:
            raise ValueError(
                "Candles dürfen nicht leer sein."
            )

        if signals is not None and len(signals) != len(candles):
            raise ValueError(
                "Anzahl der Signale muss der Anzahl der Candles entsprechen."
            )

        prices = []
        trades = []
        capital = self.initial_capital
        open_position = None

        for index, candle in enumerate(candles):
            prices.append(candle.close)

            if signals is None:
                try:
                    signal = self.strategy_engine.generate_signal(
                        symbol,
                        prices,
                    )
                except ValueError:
                    continue
            else:
                signal = signals[index]

                if signal is None:
                    continue

            if open_position is None:
                if signal.signal != SignalType.HOLD:
                    entry_price = candle.close
                    stop_distance = entry_price * 0.02

                    if signal.signal == SignalType.BUY:
                        stop_price = (
                            entry_price - stop_distance
                        )
                    else:
                        stop_price = (
                            entry_price + stop_distance
                        )

                    position = calculate_position(
                        capital_eur=capital,
                        entry_price=entry_price,
                        stop_price=stop_price,
                        leverage=self.leverage,
                    )

                    risk_scale = (
                        self.risk_per_trade
                        / settings.RISK_PER_TRADE
                    )

                    quantity = (
                        position["quantity"] * risk_scale
                    )

                    open_position = {
                        "side": signal.signal.value,
                        "entry_price": entry_price,
                        "stop_price": stop_price,
                        "quantity": quantity,
                        "entry_timestamp": candle.timestamp,
                    }

                continue

            side = open_position["side"]
            entry_price = open_position["entry_price"]
            quantity = open_position["quantity"]
            stop_price = open_position["stop_price"]

            exit_price = None

            # Stop-Loss hat Vorrang vor einem Signal-Exit.
            if side == "BUY":
                if candle.low <= stop_price:
                    exit_price = stop_price
                elif signal.signal == SignalType.SELL:
                    exit_price = candle.close

            elif side == "SELL":
                if candle.high >= stop_price:
                    exit_price = stop_price
                elif signal.signal == SignalType.BUY:
                    exit_price = candle.close

            if exit_price is None:
                continue

            (
                execution_entry,
                execution_exit,
                net_pnl,
                fees,
            ) = self._calculate_exit(
                side,
                entry_price,
                exit_price,
                quantity,
            )

            capital += net_pnl

            trades.append(
                BacktestTrade(
                    symbol=symbol,
                    side=side,
                    entry_price=execution_entry,
                    exit_price=execution_exit,
                    quantity=quantity,
                    entry_timestamp=open_position[
                        "entry_timestamp"
                    ],
                    exit_timestamp=candle.timestamp,
                    pnl_eur=net_pnl,
                    fees_eur=fees,
                )
            )

            open_position = None

        # Falls am Ende noch eine Position offen ist,
        # wird sie zum letzten verfügbaren Schlusskurs geschlossen.
        if open_position is not None:
            last_candle = candles[-1]

            side = open_position["side"]
            entry_price = open_position["entry_price"]
            quantity = open_position["quantity"]

            (
                execution_entry,
                execution_exit,
                net_pnl,
                fees,
            ) = self._calculate_exit(
                side,
                entry_price,
                last_candle.close,
                quantity,
            )

            capital += net_pnl

            trades.append(
                BacktestTrade(
                    symbol=symbol,
                    side=side,
                    entry_price=execution_entry,
                    exit_price=execution_exit,
                    quantity=quantity,
                    entry_timestamp=open_position[
                        "entry_timestamp"
                    ],
                    exit_timestamp=last_candle.timestamp,
                    pnl_eur=net_pnl,
                    fees_eur=fees,
                )
            )

        return BacktestResult(
            initial_capital=self.initial_capital,
            final_capital=capital,
            realized_pnl=capital - self.initial_capital,
            trades=tuple(trades),
        )
