# Ergebnis: Trial T-2026-09-24-034 — Fixed ETF Relative-Value Pairs

## Status

**NO_SUPPORT / archived_rejected**

Der präregistrierte Relative-Value-Control wurde vollständig auf
`DWR-debug/trading-agent-public` ausgeführt. Es gab keine Pair-Suche,
Parameter-Suche, Threshold-Suche oder Holdout-Auswahl.

## Technischer Nachweis

- PR #147: gemerged
- Workflow-Run: `36045225948`
- Artifact-ID: `10827469931`
- Artifact-SHA256: `sha256:c90990863e1844977352a50cd6023c9ccca215e98de5dfa2225782f90bc468f3`
- Coverage-Preflight: Workflow `36044264502`, Artifact `10827702970`
- Coverage-Fingerprint: `b4102c8e01e442ca5657426b96f0dc97ec919783299408946975f49b05c445a4`
- 10/10 Symbole × 3.520 Candles im Coverage-Preflight
- 3.500 Candles je Symbol im Research-Run
- 3.498 gemeinsame Returnperioden
- 2.798 Research / 700 Holdout
- 679 Tests, Safety, Disjointness, Präregistrierung, Coverage und Kostenvertrag grün
- keine Orders

## Präregistrierte Regel

Fünf feste ökonomische ETF-Paare:

- VTWO / IJR
- QQEW / ONEQ
- EEMV / SCHE
- IGIB / SPIB
- SCHP / STIP

Je Paar:

- alle 21 Sessions ADF-Stationaritätsprüfung auf den letzten 200 Sessions;
- Zulassung bei ADF p < 0,05;
- täglicher Preisratio-Z-Score auf 200 Sessions;
- Entry bei |Z| > 1,65;
- Exit bei |Z| < 0,75;
- equal-capital long/short;
- gleiches Gross-Budget auf aktive Paare;
- maximales Gross-Exposure 1,0;
- Netto-Exposure 0,0;
- Close(t) -> nächstes Open -> folgende-Open-Periode;
- 10 bps Fee + 5 bps Slippage.

Borrow-Kosten und ETF-Dividenden wurden ausdrücklich nicht modelliert. Daher war
selbst ein eventueller Research-Pass noch nicht Paper-Ready gewesen.

## Ergebnis

| Kennzahl | Research | Holdout |
|---|---:|---:|
| Return | −18,92 % | −0,71 % |
| Max Drawdown | 19,01 % | 1,39 % |
| Profit Factor | 0,599 | 0,855 |
| abgeschlossene Trades | 85 | 6 |
| aktive Tage | 20,41 % | 9,00 % |
| profitable Rolling-Fenster | 0/5 | — |

Kostenstress im Holdout:

- 1,5x Kosten: −1,60 %
- 2,0x Kosten: −2,48 %

Das Research-Gesamtergebnis ist negativ; kein einziges der fünf Research-
Rolling-Fenster war profitabel.

## Paar-Diagnostik

| Pair | ADF-eligible Rebalance-Ratio | Entries |
|---|---:|---:|
| VTWO/IJR | 6,37 % | 12 |
| QQEW/ONEQ | 12,10 % | 14 |
| EEMV/SCHE | 5,73 % | 6 |
| IGIB/SPIB | 28,03 % | 50 |
| SCHP/STIP | 7,64 % | 9 |

Der einzige relativ häufig aktivierte Pair-Zweig war IGIB/SPIB; das änderte
den negativen Gesamtbefund nicht.

## Forschungsentscheidung

Die konkrete Relative-Value-Familie wird beendet.

- kein Threshold-Tuning;
- keine Lockerung des ADF-Gates;
- keine weitere Pair-Suche auf diesem Universum;
- kein VIX-/Regime-Overlay;
- keine Short-Borrow-Fantasiekosten nachträglich zurechtschätzen;
- keine Produktionsintegration;
- keine Echtgeldfreigabe;
- keine Orders.

Trial 034 liefert damit negative Evidenz gegen diese konkrete
cointegration-gated ETF-pairs Konstruktion unter dem getesteten Regelwerk.

## Nächster Fokus

Da Volatility-Parity, Common-Market-Gates, TSM-Ersatz, risk-adjusted CS Momentum
und diese Relative-Value-Regel keinen belastbaren Promotion-Kandidaten geliefert
haben, wird die Forschung nicht weiter in derselben Familie verfeinert.

Der nächste Schritt ist ein neuer, orthogonaler **Cross-Asset-Carry-/Trend-State-
Control**, aber nur nach derselben Reihenfolge:

1. aktuelle Literatur/Projektbestand prüfen;
2. neue, disjunkte Datenbasis;
3. Coverage-Preflight;
4. Präregistrierung einer einzigen festen Regel;
5. öffentliche ARM64-Ausführung;
6. bei Pass zuerst Borrow-/Execution-/Liquidity-Audit;
7. erst danach ein separater 30-Tage-Paper-Test.

## Sicherheitsstatus

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`orders_enabled=False`

Keine Live-Ausführung.
