# Trial 016 — Präregistrierung: Cross-Asset Cross-Sectional Momentum

## Forschungsfrage

Prüft Trial 016, ob die bereits fest definierte 12-1-Cross-Sectional-Momentum-
Mechanik eine zusätzliche Ertragsquelle außerhalb der bisherigen Equity-/Sector-
Universen liefern kann.

Die Hypothese wird vor Datenakquisition festgelegt:
Ein monatlich rebalancierter Top-2-Long-only-CS-Momentumkorb auf einem
Nicht-Aktien-ETF-Universum liefert nach Kosten nicht nur Holdout-, sondern auch
positive und ausreichend stabile Research-Evidenz.

## Feste Datenbasis

Universum:

- DBA — Agriculture
- DBB — Base Metals
- FXA — Australian Dollar
- FXY — Japanese Yen
- MUB — U.S. Municipal Bonds
- SHV — U.S. Treasury 0–1 Year
- EMB — USD Emerging Markets Bonds
- BWX — International Treasury Bonds

Die Instrumente sind vollständig symbol-disjunkt zu den auf `master` registrierten
Research-Universen. Die öffentlich dokumentierten Inception-Daten liegen für den
gesamten Satz im Jahr 2007 bzw. früher, sodass ein ausreichender historischer
Zeitraum grundsätzlich plausibel ist; die CI-Datenakquisition bleibt dennoch
fail-closed und akzeptiert nur tatsächlich verfügbare 3.500 gemeinsame Candles.

- 3.500 gemeinsame Tages-Candles
- 3.498 Return-Perioden
- 2.798 Research / 700 Holdout
- gemeinsame Timestamp-Intersection
- keine Asset-Auswahl nach Ergebnis

## Feste Strategie

- Formation: 252 Sessions
- Skip: 21 Sessions
- Rebalance: 21 Sessions
- Top 2
- 100 % Long, equal-weight
- Entscheidung am Close(t)
- Ausführung Open(t+1) bis Open(t+2)
- Basis-Kosten: 0,10 % Fee + 0,05 % Slippage je Turnover-Einheit
- Stress: doppelte Gesamtkosten

Deskriptive Fixed Controls:

1. Cross-sectional 12-1 Top-2 Long-only
2. SMA 50/200 Long/Flat über denselben Assetkorb
3. Equal-weight Buy-and-Hold
4. fester 50/50-Blend aus CS-Momentum und SMA-Control

Der Blend ist vorab fest und kein Auswahlmechanismus.

## Gating

Dokumentiert werden:

- Research-/Holdout-Return
- Maximum Drawdown
- Profit Factor
- positive Return Ratio
- fünf Research-Rolling-Fenster, die zusammen alle 2.798 Research-Returns abdecken
- 2x-Kosten-Stress
- Holdout vollständig blind gegenüber Auswahl
- Disjunktheit gegenüber dem gesamten registrierten Universum

Es gibt keine Parameteroptimierung, kein Threshold Search und keine nachträgliche
Holdout-Selektion.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine Änderung an Produktionsstrategie oder Research-Gates
- Trial 016 ist ausschließlich Evidenzgewinn.

## Forschungsentscheidung

Positive Holdout-Zahlen allein reichen nicht für Übernahme. Ein Kandidat müsste
auch Research-, Rolling-, Drawdown- und Kostenrobustheit erfüllen. Bei fehlender
Unterstützung wird der Trial als `archived_rejected` dokumentiert.

Methodeninspiration: Cross-sectional Momentum wurde in der empirischen Forschung
über Aktien und andere Asset-Kontexte untersucht; hier wird ausschließlich die
Methodik als vorab definierter Test verwendet, nicht ein externer Erfolgsnachweis.
