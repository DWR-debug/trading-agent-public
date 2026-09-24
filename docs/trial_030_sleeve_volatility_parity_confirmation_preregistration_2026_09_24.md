# Präregistrierung: Trial T-2026-09-24-030 — Sleeve Volatility Parity Confirmation

## Forschungsfrage

Kann die im Trial-028-Diagnosepfad entwickelte und in Trial 028 technisch
unterstützte Risikologik auf einem vollständig neuen, disjunkten Datensatz
reproduziert werden, wenn die Kapitalallokation zwischen den unveränderten
Trend- und Cross-Sectional-Sleeves monatlich nach inverser 63-Tage-Volatilität
bestimmt wird?

## Warum dieser Trial zulässig ist

Trial 029 wurde vor jeder Performanceauswertung als DATA_INVALID beendet, weil
sein Universum nur 3.496 gemeinsame Candles statt der vorgeschriebenen 3.500
lieferte. Es wurde keine Performanceentscheidung getroffen und kein Symbol
nachträglich ersetzt.

Vor Trial 030 wurde deshalb ein separater Coverage-Preflight ausschließlich auf
Datenverfügbarkeit durchgeführt:

- Workflow: 36040186007
- Artifact: 10825967102
- Artifact-SHA256: sha256:66c283525399dc9a185dcf3db7432e5d0f06fb7853ba77b497eedb7d1e9b8f52
- 13/13 Kandidaten: 3.520 Candles
- gemeinsamer Kalender: 3.520 Candles
- keine Performancewerte im Auswahlkriterium

Die Auswahl des Trial-030-Universums basiert damit ausschließlich auf
Datenabdeckung und technischer Verfügbarkeit.

## Externe Motivation

Inverse-Volatilitäts-/Risk-Parity-Allokation ist als einfache risk-based
Referenz in aktueller Forschung etabliert; komplexere Tail-Risk-Erweiterungen
sind nicht zuverlässig überlegen. Die Literatur wird nur als Motivation
verwendet, nicht als Eigenevidenz. citeturn768597search0turn768597search4

## Einzige Intervention

Unverändert:

- 50 % Trend-Sleeve mit SMA 50/200 und inverser Volatilitätsgewichtung;
- 50 % 12-1 Cross-Sectional Momentum Top-2;
- bestehender aggregierter 63-Sessionen-/10%-Volatilitätsmechanismus;
- Point-in-Time-Ausführung;
- gleiche Gebühren und Slippage.

Einzige Änderung:

- zu Beginn jedes neuen Monats wird die Kapitalgewichtung der beiden Sleeves
  anhand ihrer vorherigen 63 vollständig abgeschlossenen täglichen
  Sleeve-Renditen invers zur Volatilität bestimmt;
- Gewicht = inverse Volatilität / Summe beider inverser Volatilitäten;
- Warm-up: fest 50/50, bis 63 historische gemeinsame Sleeve-Returns verfügbar sind;
- Gewichtungen sind vollständig investiert, 0..100 % pro Sleeve;
- Allokationsänderungen werden als zusätzlicher Turnover kostenwirksam;
- das bestehende aggregierte 63-Sessionen-/10%-Volatilitätsbudget bleibt
  nach der Sleeve-Allokation unverändert;
- keine Signaländerung;
- keine Parameter-, Threshold- oder Varianten-Suche;
- kein Shorting;
- kein Leverage;
- keine Orders.

Die Allokationsentscheidung für eine Periode darf ausschließlich Informationen
aus früheren Perioden verwenden.

## Neue Validierungsbasis

Trend-Sleeve:

VV, VHT, VFH, VIS, VAW, VDE, VPU, VGT

Cross-Sectional-Sleeve:

SPDW, SPMB, SPEM, SPTL, SPIP

Alle 13 Symbole sind vollständig symbol-disjunkt zu sämtlichen im Projekt
registrierten Universen und zum verworfenen Trial-029-Universum.

Preflight:

- 3.520 Candles je Symbol
- 3.520 gemeinsame Candles
- Zielvertrag: 3.500 / 3.498
- 2.798 Research / 700 Holdout im Researchlauf

## Präregistrierter Entscheidungsvertrag

Der Challenger muss alle absoluten Kriterien erfüllen:

- Research-Return > 0;
- Research-Drawdown <= 10 %;
- Research-PF >= 1,10;
- Rolling-PF >= 1,10;
- profitable Rolling-Fensterquote >= 50 %;
- durchschnittlicher Rolling-Drawdown <= 10 %;
- OOS/IS >= 0,25;
- positiver Holdout;
- Holdout-PF >= 1,10;
- Holdout-Drawdown <= 10 %;
- 1,5x-Kostenstress-Holdout nicht negativ;
- 2x-Kostenstress-Holdout nicht negativ;
- positive Total-Return-Sensitivität.

Zusätzlich darf der Challenger gegenüber dem unveränderten 50/50-Kandidaten
auf demselben Validierungsset nicht schlechter sein bei:

- Research-Return;
- Research-Drawdown;
- Research-PF;
- Rolling-PF;
- profitable Rolling-Fensterquote;
- durchschnittlichem Rolling-Drawdown;
- OOS/IS;
- Holdout-Return;
- Holdout-PF;
- Holdout-Drawdown.

Ein Bestehen ist ausschließlich ein Research-Befund VALIDATED_PASS. Es ist keine
Produktions-, Echtgeld- oder Live-Freigabe.

## Sicherheitsvertrag

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False

Keine Live-Orders und keine automatische Promotion.
