"""
Trading Agent - Backtesting Metrics

Berechnet Performance- und Risikokennzahlen
aus abgeschlossenen virtuellen Trades.

Keine Orderausführung.
Keine Netzwerkverbindung.
"""

from math import sqrt

from backtesting.models import BacktestTrade


def calculate_net_profit(trades: tuple[BacktestTrade, ...]) -> float:
    return sum(trade.pnl_eur for trade in trades)


def calculate_return_percent(
    initial_capital: float,
    trades: tuple[BacktestTrade, ...],
) -> float:
    if initial_capital <= 0:
        raise ValueError(
            "Initiales Kapital muss größer als 0 sein."
        )

    net_profit = calculate_net_profit(trades)

    return (net_profit / initial_capital) * 100.0


def calculate_win_rate(
    trades: tuple[BacktestTrade, ...],
) -> float:
    if not trades:
        return 0.0

    winning_trades = sum(
        1 for trade in trades if trade.pnl_eur > 0
    )

    return winning_trades / len(trades) * 100.0


def calculate_profit_factor(
    trades: tuple[BacktestTrade, ...],
) -> float:
    gross_profit = sum(
        trade.pnl_eur
        for trade in trades
        if trade.pnl_eur > 0
    )

    gross_loss = sum(
        -trade.pnl_eur
        for trade in trades
        if trade.pnl_eur < 0
    )

    if gross_loss == 0:
        if gross_profit > 0:
            return float("inf")

        return 0.0

    return gross_profit / gross_loss


def calculate_max_drawdown_percent(
    initial_capital: float,
    trades: tuple[BacktestTrade, ...],
) -> float:
    if initial_capital <= 0:
        raise ValueError(
            "Initiales Kapital muss größer als 0 sein."
        )

    equity = initial_capital
    peak = initial_capital
    max_drawdown = 0.0

    for trade in trades:
        equity += trade.pnl_eur

        if equity > peak:
            peak = equity

        if peak > 0:
            drawdown = (
                (peak - equity) / peak
            ) * 100.0

            max_drawdown = max(
                max_drawdown,
                drawdown,
            )

    return max_drawdown


def calculate_sharpe_ratio(
    initial_capital: float,
    trades: tuple[BacktestTrade, ...],
) -> float:
    """
    Vereinfachte Sharpe Ratio auf Trade-Basis.

    Noch keine zeitbasierte Annualisierung.
    Diese kommt später mit einer echten Equity Curve.
    """

    if initial_capital <= 0:
        raise ValueError(
            "Initiales Kapital muss größer als 0 sein."
        )

    if len(trades) < 2:
        return 0.0

    returns = [
        trade.pnl_eur / initial_capital
        for trade in trades
    ]

    mean_return = sum(returns) / len(returns)

    variance = sum(
        (value - mean_return) ** 2
        for value in returns
    ) / (len(returns) - 1)

    standard_deviation = sqrt(variance)

    if standard_deviation == 0:
        return 0.0

    return (
        mean_return / standard_deviation
    ) * sqrt(len(returns))


def calculate_average_trade(
    trades: tuple[BacktestTrade, ...],
) -> float:
    if not trades:
        return 0.0

    return calculate_net_profit(trades) / len(trades)


def calculate_metrics(
    initial_capital: float,
    trades: tuple[BacktestTrade, ...],
) -> dict:
    """
    Liefert alle zentralen Backtest-Kennzahlen.
    """

    return {
        "net_profit_eur": calculate_net_profit(trades),
        "return_percent": calculate_return_percent(
            initial_capital,
            trades,
        ),
        "win_rate_percent": calculate_win_rate(trades),
        "profit_factor": calculate_profit_factor(trades),
        "max_drawdown_percent": calculate_max_drawdown_percent(
            initial_capital,
            trades,
        ),
        "sharpe_ratio": calculate_sharpe_ratio(
            initial_capital,
            trades,
        ),
        "trade_count": len(trades),
        "average_trade_eur": calculate_average_trade(
            trades,
        ),
    }
