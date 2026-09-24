# Präregistrierung: Trial T-2026-09-24-035 — Trend Family Walk-Forward

## Forschungsfrage

Überträgt eine kleine Auswahl bereits unabhängig geprüfter Trendfamilien out-of-sample auf einen neuen, vollständig symbol-disjunkten Multi-Asset-Satz, wenn die Familienauswahl ausschließlich auf einem vorgelagerten Trainingsteil getroffen und für das anschließende OOS-Fenster eingefroren wird?

## Fest definierte Familien

Nur diese drei bereits zuvor untersuchten Familien dürfen gewählt werden:
1. monatliches Time-Series Momentum;
2. SMA 50/200 Long/Flat mit inverser Volatilitätsgewichtung;
3. fixer 50/50-Blend aus TSM und SMA.

Die Familien werden nicht parametriert oder verändert.

## Neue Validierungsbasis

SPTM, IWR, RWR, SCHZ, VGSH, VGLT, DJP, MOO, GCC, REM

Alle zehn Symbole sind im Projekt vorab noch nicht verwendet und wurden im Coverage-Preflight vollständig historisch bestätigt.

Coverage-Preflight:
- Workflow 36046054250
- Artifact 10829105161
- 3.520 Candles je Symbol
- gemeinsamer Kalender: >= 3.500
- keine Performanceauswahl

Research:
- 2.798 Research-Returns nach dem 2-Candle-PIT-Warm-up
- fünf WFO-Fenster
- 700 blinder Holdout

## Präregistrierte WFO-Geometrie

Research = 2.798 Returns.

Je Fenster:
- Training: 1.398 Returns
- OOS-Test: 280 Tage
- Schrittweite: 280 Tage

Fenster:
- 1: Training 0–1.398, OOS 1.398–1.678
- 2: Training 280–1.678, OOS 1.678–1.958
- 3: Training 560–1.958, OOS 1.958–2.238
- 4: Training 840–2.238, OOS 2.238–2.518
- 5: Training 1.120–2.518, OOS 2.518–2.798

Die Familienauswahl erfolgt pro Fenster ausschließlich auf dem Trainingsteil:
1. höchste Training-Profit-Factor;
2. bei Gleichstand höhere Training-Rendite;
3. bei erneutem Gleichstand niedrigerer Training-Drawdown;
4. lexikographischer Familienname als deterministischer Tiebreak.

Die gewählte Familie wird für das gesamte anschließende OOS-Fenster eingefroren.

Für den 700-Tage-Holdout wird ausschließlich die Familie verwendet, die im fünften und letzten Research-Fenster gewählt wurde. Der Holdout beeinflusst die Auswahl nicht.

## Kosten und Ausführung

- 10 bps Fee je Richtung;
- 5 bps Slippage je Richtung;
- Basisszenario und 2x-Kostenstress;
- Close(t) Entscheidung -> nächstes Open -> folgende Open-Returnperiode;
- kein Parameter-Tuning;
- kein Selection-Profile;
- keine Änderung der Produktions-Gates.

## Präregistrierter Research-Vertrag

Für einen PASSED_CONTROL müssen gleichzeitig gelten:

### OOS

- aggregierte OOS-Rendite > 0;
- aggregierter OOS-Profit-Factor >= 1,10;
- mindestens 3 von 5 OOS-Fenstern positiv;
- 2x-Kostenstress aggregierte OOS-Rendite >= 0.

### Holdout

- Holdout-Rendite > 0;
- Holdout-Profit-Factor >= 1,10;
- Holdout-Max-Drawdown <= 10 %;
- Holdout unter 2x-Kostenstress >= 0.

Bei einem einzigen fehlenden Kriterium lautet der Status BLOCKED / NO_SUPPORT.

## Auswahl- und Überfit-Schutz

- exakt drei vorab bekannte Familien;
- keine Parameteroptimierung;
- keine Suche über Lookbacks;
- keine Auswahl anhand des Holdouts;
- keine freie Auswahl einer Familie außerhalb der Trainingregel;
- alle Research-OOS-Fenster werden vollständig dokumentiert;
- der finale Holdout wird erst nach Abschluss aller fünf Research-Fenster ausgewertet.

Ein positiver WFO-Befund ist nur ein Research-Nachweis für Übertragbarkeit einer kleinen vorab definierten Familienmenge. Er ist keine Produktions- oder Echtgeldfreigabe.

## Sicherheitsvertrag

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False

Keine Live-Orders und keine automatische Promotion.
