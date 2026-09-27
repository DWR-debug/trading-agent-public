# T052 — Fixed-Core Sleeve Performance

## Zweck

T052 prüft die unveränderten Fixed-Core-Mechanismen auf zwei neuen, vollständig
symbol-disjunkten Universen. Die Studie ist ex ante festgelegt und verwendet
keine Parameter-, Asset-, Threshold-, Horizon- oder Varianten-Suche.

## Universen

T049:
TAP, CLX, HSY, KR, SYY, STT, USB, TROW, BEN, NTRS, PNC, MET

T050:
PRU, ALL, TRV, AFL, AIZ, CB, HIG, CINF, GL, MKC, ED, PEG

Beide Universen haben die Coverage-Anforderung von mindestens 3.500 gemeinsamen
Candles bereits erfüllt. T051 hat die beiden festen Signalpfade zusätzlich
point-in-time validiert.

## Fixed-Core-Regeln

### Trend-Sleeve

SMA 50/200 long/flat, monatliche Rebalancierung und die bereits bestehende
Inverse-Volatilitätsgewichtung mit 25-Prozent-Asset-Cap.

### Cross-Sectional-Sleeve

252 Sessions Formation, 21 Sessions Skip, 21 Sessions Rebalance, Top-2
long-only, gleichgewichtet.

Beide Regeln verwenden ausschließlich Informationen bis zum Entscheidungszeitpunkt.

## Daten- und Kostenvertrag

3500 gemeinsame Candles werden als eingefrorener Snapshot verwendet.
2798 Perioden bilden Research und 700 Perioden den blinden Holdout.

Ausführung:
Close(t)-Entscheidung -> nächstes Open -> folgendes Open.

Kosten:
10 bps Fee und 5 bps Slippage. Zusätzlich werden 1,5x- und 2x-Kostenstress
gerechnet.

Total-return sensitivity ist ausschließlich eine vorab definierte Diagnose.

## Governance

Alle vier Kombinationen aus Universum und Sleeve werden vollständig berichtet.
Es findet keine Auswahl oder Rangbildung zwischen den Zellen statt.

Der Holdout darf nicht zur Auswahl verwendet werden. Ein positives Gate-Ergebnis
führt nicht automatisch zu einer Promotion.

Vor Performance muss:
1. der aktuelle Master exakt durch einen erfolgreichen vollständigen CI-Lauf
   validiert sein;
2. die aktuelle Coverage erneut erfolgreich sein;
3. die aktuelle Strategie-PIT erneut erfolgreich sein.

Bei einem Coverage-, PIT- oder CI-Fehler endet der Lauf ohne Performance-Evaluation.

## Sicherheit

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False

Die Studie erzeugt ausschließlich Forschungsevidence und niemals Broker- oder
Exchange-Orders.
