import subprocess
import sys
from pathlib import Path

from config import settings


ROOT = Path(__file__).resolve().parent


def run(command):
    subprocess.run(command, cwd=ROOT, check=True)


def check_safety():
    if not settings.PAPER_ONLY:
        raise RuntimeError("Restore abgebrochen: PAPER_ONLY ist nicht aktiv.")

    if settings.LIVE_TRADING_ENABLED:
        raise RuntimeError(
            "Restore abgebrochen: LIVE_TRADING_ENABLED ist aktiv."
        )


def check_python():
    if sys.version_info < (3, 11):
        raise RuntimeError("Python 3.11 oder neuer erforderlich.")


def check_project():
    required = [
        "backtesting",
        "config",
        "data",
        "execution",
        "optimization",
        "risk",
        "strategies",
        "validation",
        "automation",
        "research",
        "tests",
    ]

    missing = [name for name in required if not (ROOT / name).exists()]

    if missing:
        raise RuntimeError(
            "Fehlende Projektbereiche: " + ", ".join(missing)
        )


def run_tests():
    tests = [
        "tests.test_backtest_engine",
        "tests.test_backtest_metrics",
        "tests.test_optimizer",
        "tests.test_walk_forward",
        "tests.test_rolling_walk_forward",
        "tests.test_trading_engine",
        "tests.test_backtest_runner",
        "tests.test_research_gates",
        "tests.test_research_writeback_policy",
        "tests.test_research_protocol",
        "tests.test_research_checkpoint",
    ]

    for test in tests:
        print(f"TEST {test}")
        run([sys.executable, "-m", test])


def restore_market_data():
    from data.market_updater import update_all

    datasets = [
        ("BTCUSDT", "1h", 10000),
        ("BTCUSDT", "15m", 10000),
        ("ETHUSDT", "1h", 10000),
        ("ETHUSDT", "15m", 10000),
    ]

    print("MARKTDATEN")
    update_all(datasets)


def main():
    print("TRADING-AGENT RESTORE")
    check_python()
    check_project()
    check_safety()

    print("SICHERHEIT OK")
    run_tests()
    restore_market_data()

    print("RESTORE OK")


if __name__ == "__main__":
    main()
