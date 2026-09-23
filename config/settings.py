# Trading Agent - zentrale Sicherheitskonfiguration
# Echtgeldhandel ist in dieser Version NICHT implementiert.

INITIAL_CAPITAL_EUR = 500.00
RISK_PER_TRADE = 0.01
MAX_LEVERAGE = 3.0

# Zentrale Sicherheitsregel
PAPER_ONLY = True

# Live-Ausführung ist in V1 grundsätzlich deaktiviert.
LIVE_TRADING_ENABLED = False

# Sicherheitslimits
MAX_DAILY_LOSS_EUR = 15.00
MAX_DRAWDOWN_PERCENT = 10.0
MAX_OPEN_POSITIONS = 3
