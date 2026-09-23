"""
Trading Agent - Risk Engine

Berechnet Positionsgrößen ausschließlich auf Basis
des erlaubten Risikos.
"""

from config import settings


class RiskError(Exception):
    """Sicherheitsfehler der Risk Engine."""
    pass


def calculate_position(
    capital_eur: float,
    entry_price: float,
    stop_price: float,
    leverage: float = 1.0,
) -> dict:
    """
    Berechnet die maximale Positionsgröße.

    Das maximale Risiko beträgt standardmäßig 1 % des Kapitals.
    Hebel verändert die Margin-Anforderung, nicht das erlaubte Risiko.
    """

    if capital_eur <= 0:
        raise RiskError("Kapital muss größer als 0 sein.")

    if entry_price <= 0 or stop_price <= 0:
        raise RiskError("Preise müssen größer als 0 sein.")

    if leverage < 1:
        raise RiskError("Hebel muss mindestens 1x betragen.")

    if leverage > settings.MAX_LEVERAGE:
        raise RiskError(
            f"Hebel {leverage}x überschreitet das erlaubte Maximum "
            f"von {settings.MAX_LEVERAGE}x."
        )

    stop_distance = abs(entry_price - stop_price)

    if stop_distance == 0:
        raise RiskError("Entry und Stop dürfen nicht identisch sein.")

    max_risk_eur = capital_eur * settings.RISK_PER_TRADE

    quantity = max_risk_eur / stop_distance
    position_value = quantity * entry_price
    margin_required = position_value / leverage

    return {
        "capital_eur": capital_eur,
        "risk_eur": max_risk_eur,
        "entry_price": entry_price,
        "stop_price": stop_price,
        "stop_distance": stop_distance,
        "quantity": quantity,
        "position_value": position_value,
        "leverage": leverage,
        "margin_required": margin_required,
    }
