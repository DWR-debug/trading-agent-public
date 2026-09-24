# Trial 015 — Ergebnis: Fixed Mean Reversion auf globalen ETFs

**Trial-ID:** T-2026-09-24-015  
**Status:** `archived_rejected`  
**Workflow Run:** 35989469745  
**Artifact:** 10803393326  
**Artifact SHA-256:** 528b8e82e6c0ff42ad223477718f7e94ba0a433faf1333ede839cabfae86b96d  
**Report-Fingerprint:** 37026149b73efe9bfd5b5f641c4d3838487542ec3c869c70ddd8c84b3ddc14ae  
**Manifest-Fingerprint:** fe66674879d494560cee43b3a55d635f421df0f2f916a1965604ce302b97b431  
**Code-Version des Runs:** dd5b7bec416474bb1c7bb4ef5369c62f9cb6fa2f

## Forschungsdesign

Vollständig präregistriert und ohne Ergebnis- oder Holdout-Auswahl:

- 8 neue ETFs: EWC, EWH, EWI, EWK, EWN, EWP, EWY, EWT
- 3.500 gemeinsame Tages-Candles
- 3.498 Return-Perioden
- 2.798 Research / 700 Holdout
- Mean Reversion: 5 Sessionen / 2 %-Band
- long-only, kein Shorting, kein Leverage
- fester SMA-50/200-Long/Flat-Control
- fester 50/50-Blend, vorab festgelegt
- Basis-Kosten 0,15 % pro Turnover-Einheit; Stress = 2×
- fünf feste Rolling-Research-Fenster decken alle 2.798 Research-Returns ab

Die Datenakquisition lieferte je Symbol 3.502 Roh-Candles; nach gemeinsamer
Kalenderausrichtung wurden die letzten 3.500 gemeinsamen Candles verwendet.
Die Daten lagen für alle acht Symbole im Zeitraum 17.10.2012 bis 21.09.2026 vor.

## Ergebnis

### Basis-Szenario

| Pfad | Research Return | Research Max DD | Research PF | Holdout Return | Holdout Max DD | Holdout PF |
|---|---:|---:|---:|---:|---:|---:|
| Mean Reversion | -37,75 % | 53,95 % | 0,971 | +38,75 % | 19,08 % | 1,148 |
| SMA 50/200 Control | -9,17 % | 45,40 % | 1,003 | +71,67 % | 19,79 % | 1,233 |
| 50/50 Blend | -23,44 % | 47,68 % | 0,984 | +54,85 % | 19,24 % | 1,195 |

### Realistic-Stress-Szenario (2× Kosten)

| Pfad | Research Return | Research Max DD | Research PF | Holdout Return | Holdout Max DD | Holdout PF |
|---|---:|---:|---:|---:|---:|---:|
| Mean Reversion | -61,17 % | 69,32 % | 0,927 | +19,30 % | 21,02 % | 1,086 |
| SMA 50/200 Control | -17,63 % | 46,62 % | 0,990 | +68,18 % | 20,52 % | 1,224 |
| 50/50 Blend | -42,41 % | 54,02 % | 0,952 | +42,13 % | 20,72 % | 1,158 |

Die Mean-Reversion-Komponente hatte im Basis-Research nur in zwei der fünf
Rolling-Fenster positive Periodenrenditen; drei Fenster waren negativ. Im
2×-Kosten-Stress waren alle fünf Rolling-Fenster negativ. Der feste 50/50-Blend
war im Basis-Research ebenfalls in drei von fünf Fenstern negativ und im
Kosten-Stress in allen fünf.

## Wissenschaftlicher Befund

Trial 015 liefert **keinen belastbaren Nachweis** für die präregistrierte
Mean-Reversion-Hypothese als zusätzliche robuste Ertragsquelle. Der zentrale
Grund ist die negative Gesamtperformance im Research zusammen mit hoher
Drawdown-Belastung und instabiler Rolling-Evidenz. Die positive Holdout-Phase wird
als Teil des Ergebnisses dokumentiert, wurde aber weder zur Auswahl noch zur
nachträglichen Anpassung verwendet und hebt den Research-/Rolling-Befund nicht
auf.

Der Trial wird deshalb als `archived_rejected` geführt. **Keine Änderung am
Produktionskandidaten, keine Änderung an Exposure-/Leverage-Grenzen und keine
Order-/Live-Funktion.**

## Sicherheitsnachweis

Der Workflow bestätigte:

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`orders_enabled=False`

Der vollständige CI-Testlauf auf der Trial-Spitze bestand mit **551 Tests**.
