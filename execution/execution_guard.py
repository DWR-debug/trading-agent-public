"""
Trading Agent - Execution Guard

Sicherheitsbarriere:
Diese Version erlaubt ausschließlich Paper Trading.
Eine Live-Order-Ausführung ist ausdrücklich verboten.
"""

from config import settings


class SecurityError(Exception):
    """Wird bei einem nicht erlaubten Ausführungsversuch ausgelöst."""
    pass


def assert_paper_mode() -> None:
    """Bricht ab, wenn der Agent nicht eindeutig im Paper-Modus ist."""

    if settings.PAPER_ONLY is not True:
        raise SecurityError(
            "SICHERHEITSSTOPP: PAPER_ONLY muss True sein."
        )

    if settings.LIVE_TRADING_ENABLED is not False:
        raise SecurityError(
            "SICHERHEITSSTOPP: Live-Trading ist deaktiviert."
        )


def execute_order(order: dict) -> dict:
    """
    Führt ausschließlich simulierte Orders aus.

    Es existiert absichtlich keine Live-Order-Funktion.
    """

    assert_paper_mode()

    return {
        "status": "PAPER_ONLY",
        "order": order,
        "message": "Order wurde ausschließlich simuliert."
    }


def execute_live_order(order: dict) -> None:
    """
    Absichtlich gesperrt.
    Diese Funktion darf niemals eine echte Order senden.
    """

    raise SecurityError(
        "ECHTGELD-HANDEL BLOCKIERT: "
        "Live-Orders sind in dieser Version nicht implementiert."
    )
