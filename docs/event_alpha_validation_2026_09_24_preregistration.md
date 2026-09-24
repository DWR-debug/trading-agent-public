# Präregistrierung: Political/Event Relative-Value Alpha 2026-09-24

## Forschungsfrage

Kann ein strikt point-in-time definiertes internationales Konflikt-Ereignisfenster
eine kurzfristige relative Bewegung zwischen einem breiten US-Aktienproxy und einer
festen defensiven Zwei-Asset-Kombination erzeugen, die nach Basis-Kosten und
Kostenstress noch positiv ist?

## Einzige Hypothese

Trial-ID: EVENT-ALPHA-2026-09-24-001

Auf einem neuen, vollständig symbol-disjunkten Marktuniversum wird ausschließlich
folgende Regel geprüft:

- IWB: -50%
- GDX: +25%
- BIL: +25%

Die Bruttoexposition beträgt exakt 1,0x und die Nettoexposition 0,0x.

Die Position wird nur dann aktiviert, wenn im Fenster zwischen dem vorherigen
Markthandelstag und dem Zielhandelstag mindestens ein GDELT-Ereignistag mit
beiden bereits festgelegten Bedingungen vorliegt:

1. internationale Actor-Country-Codes sind vorhanden und verschieden;
2. mindestens ein hochvertrauenswürdiger internationaler Event ist zugleich
   ein materialer Konflikt.

Die Ereignisaggregation erfolgt ausschließlich aus bereits abgeschlossenen
GDELT-Daten. Das Eventfenster umfasst den vorherigen Markttag inklusive bis
zum Zielhandelstag exklusiv, damit Freitag-/Wochenendereignisse in den
Montagszustand eingehen können. Die Zielrendite ist weiterhin Previous-Close
-> Target-Close und wird niemals als Event-Feature verwendet.

## Daten

Marktuniverum:

IWB, GDX, BIL

Pro Asset: exakt 3.500 Tages-Candles.

Event-Research:
2025-04-01 bis 2025-06-30

Event-Holdout:
2025-07-01 bis 2025-09-30

Das Holdout wird ausschließlich als Bestätigung ausgewiesen und nicht zur
Auswahl oder Regeländerung verwendet.

## Kosten

Basis:
0,10% Gebühr + 0,05% Slippage.

Zusätzlich:
1,5x und 2,0x der Basis-Kosten ausschließlich als Stressszenarien.

Short-Borrow- und Finanzierungskosten werden in diesem ersten Control nicht
modelliert. Das ist eine bewusste Einschränkung; die realistische Execution-
und Finanzierungsschicht bleibt für die spätere Projektphase reserviert.

## Entscheidung

Der Lauf ist zunächst ein Forschungs-Control. Er verändert keine bestehenden
Produktionsparameter oder Gates.

Es gibt keine Parameter-, Schwellenwert-, Asset- oder Varianten-Suche.

Das Eventfenster ist damit exakt `previous_market_day <= event_date < target_market_day`.

Eine spätere Promotion erfordert einen separat definierten Evidence-Contract
und unabhängige Bestätigung. Ein positives Ergebnis dieses einzelnen Controls
allein reicht nicht für eine Produktionsintegration.

## Technische Datenakquisitions-Klarstellung

Am 2026-09-24 wurde nach einem technischen 404-Fehler des primären GDELT-Tagesarchivs
präzisierend festgehalten: Für dieselben historischen GDELT-2.0-Ereignistage darf
bei fehlender Primärdatei der öffentlich registrierte AWS-Spiegel
(s3://gdelt-open-data/events/) als reine Transport-/Bezugsalternative verwendet
werden. Die Forschungsregel, Ereignisfenster, Zeiträume, Asset-Gewichte, Kosten,
Selection-Regeln und Gates bleiben unverändert. Es werden keine fehlenden Tage
übersprungen, interpoliert oder durch andere Datensätze ersetzt. Die tatsächliche
Quelle jedes Tages wird im Rohdaten-Manifest dokumentiert.

Diese Klarstellung ist eine technische Reproduzierbarkeitsmaßnahme nach dem ersten
fehlgeschlagenen Lauf und keine Forschungsvariation.

## Sicherheit

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
Keine Orders.
