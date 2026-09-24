# Trial 015 — Präregistrierung: Short-Horizon Mean Reversion auf globalen ETFs

## Forschungsfrage

Prüft Trial 015, ob die bereits im Repository vorhandene Mean-Reversion-Mechanik
als **zusätzliche, nicht gehebelte long-only Ertragsquelle** auf einem neuen
globalen ETF-Universum robuste historische Evidenz zeigt.

Die Hypothese ist vor Datenakquisition festgelegt:
Ein 5-Tage-Mittelwert und eine Abweichungsschwelle von 2 % erzeugen ein
zustandsbehaftetes Long/Flat-Signal, das nach Kosten mindestens in einem neuen
Datensatz positive und nicht ausschließlich von der bestehenden Trendfamilie
getragene Ergebnisse liefern kann.

## Fixe Datenbasis

Universum:
EWC, EWH, EWI, EWK, EWN, EWP, EWY, EWT

- 3.500 gemeinsame Tages-Candles je Asset
- 3.498 gemeinsame Point-in-Time-Return-Perioden
- Research: 2.798 Returns
- Holdout: 700 Returns
- neues Symbolset disjunkt zu allen auf `master` registrierten Universen
- zusätzlich disjunkt zu den im geschlossenen PR #79 registrierten Symbolen
- keine Daten- oder Asset-Auswahl nach Ergebnisbeobachtung

## Feste Signalregel

- Mean-Reversion-Fenster: 5 Schlusskurse
- Schwelle: 2 %
- Kurs <= Mittelwert * 0,98 → Long
- Kurs >= Mittelwert * 1,02 → Flat
- dazwischen → vorherigen Zustand beibehalten
- kein Short
- gleiche Gewichtung über aktive Assets
- Ausführung: Close(t) Entscheidung → Open(t+1) → Open(t+2)

Zum Vergleich werden ausschließlich deskriptiv drei feste Pfade berechnet:

1. Mean-Reversion Long/Flat
2. SMA 50/200 Long/Flat als mechanische Referenz
3. fester 50/50-Blend beider Pfade

Der Blend ist vorab fixiert; er wird nicht nach Ergebnissen optimiert.

## Kosten

- Basisszenario: 0,10 % Fee + 0,05 % Slippage je Turnover-Einheit
- Realistic Stress: doppelte Gesamtkosten

Keine Finanzierungskosten, kein Leverage und kein Short-Borrow.

## Auswertung

Dokumentiert werden je Pfad:

- Research- und Holdout-Return
- Maximum Drawdown
- Profit Factor
- positive Return-Quote
- fünf feste Research-Rolling-Fenster
- Basis-/Stress-Sensitivität
- Differenz des 50/50-Blends gegenüber den beiden Einzelpfaden

Es findet kein Holdout-Selection- oder Parameter-Search-Schritt statt.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine Produktionsänderung
- Trial 015 kann den bestehenden Produktionskandidaten nicht freigeben.

## Forschungsentscheidung

Ein positives Ergebnis ist nur historische Evidenz für die konkret präregistrierte
Mechanik und nicht automatisch eine Produktionsfreigabe. Ein negatives Ergebnis
wird als Forschungsevidenz gegen diese konkrete, nicht optimierte Ausprägung
archiviert.

Externe Methodeninspiration:
Poterba/Summers dokumentierten historische Evidenz zu Mean Reversion, während
andere Arbeiten die Empfindlichkeit solcher Strategien gegenüber Liquidität und
Transaktionskosten hervorheben. Diese Literatur wird nicht als Ergebnisnachweis
für den Trading Agent verwendet.
