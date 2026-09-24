# Trial 014 – Ergebnis: Long/Short und Leverage auf US-ETFs

## Laufidentität

- Trial-ID: T-2026-09-24-014
- Workflow-Run: 35986741350
- Artifact-ID: 10802099615
- Artifact-Digest: sha256:c9c6124ae5c1e54e6c864b158abadfbcd439858ef597d63c66b8ffaba79393ad
- Report-Fingerprint: 101d4ff7c6007020460b3912e0256cd5ecdce7f267e78cb88b8af7c6cc2c66f3
- Manifest-Fingerprint: 1cda83a64549c4f0e6c37b3643f43817449e0ce40e021b64f60a726e88f077d7

## Datenbasis

Neues, vollständig symbol-disjunktes US-ETF-Universum:

VOO, VT, VWO, VEU, IWD, IWF, IWN, IWO

- 3.500 gemeinsame Tages-Candles je Asset
- 3.498 gemeinsame Point-in-Time-Return-Perioden
- Research: 2.798 Returns
- Holdout: 700 Returns
- keine Optimierung
- keine Auswahl anhand des Holdouts
- Close(t) -> Open(t+1) -> Open(t+2)

## Präregistrierte Varianten

1. SMA 50/200 Long/Flat, 1x Margin-Leverage
2. SMA 50/200 Long/Short, 1x
3. SMA 50/200 Long/Short, 1,5x
4. SMA 50/200 Long/Short, 2x
5. SMA 50/200 Long/Short, 3x

Alle Varianten verwenden ein annualisiertes 10%-Volatilitätsziel, ein 63-Session-Volatilitätsfenster und 21-Session-Rebalancing.

## Basisfall

| Variante | Research Return | Research DD | Research PF | Rolling positiv | Holdout Return | Holdout DD | Holdout PF |
|---|---:|---:|---:|---:|---:|---:|---:|
| Long/Flat 1x | +30,65 % | 35,47 % | 1,0536 | 3/5 | +46,08 % | 20,93 % | 1,2019 |
| Long/Short 1x | -11,96 % | 50,85 % | 0,9969 | 3/5 | +16,56 % | 20,49 % | 1,0918 |
| Long/Short 1,5x | -23,66 % | 66,50 % | 0,9969 | 3/5 | +23,73 % | 29,41 % | 1,0918 |
| Long/Short 2x | -37,28 % | 77,65 % | 0,9969 | 2/5 | +29,87 % | 37,50 % | 1,0918 |
| Long/Short 3x | -64,16 % | 90,69 % | 0,9969 | 2/5 | +38,25 % | 51,43 % | 1,0918 |

Der Holdout war bei allen fünf Varianten positiv, aber die Long/Short-Varianten erreichten im Holdout jeweils nur einen Profit Factor von rund 1,092 gegenüber 1,202 bei der Long/Flat-Referenz. Der Research-Abschnitt zeigt bei allen Long/Short-Hebelstufen negative Gesamtrenditen und deutlich höhere Drawdowns.

## 500-EUR-Übersetzung

Zur Einordnung, ohne Entnahmen und ohne Anspruch auf zukünftige Ergebnisse:

| Variante | Research-Endequity aus 500 EUR | Holdout-Endequity aus 500 EUR |
|---|---:|---:|
| Long/Flat 1x | 653,24 EUR | 730,38 EUR |
| Long/Short 1x | 440,20 EUR | 582,79 EUR |
| Long/Short 1,5x | 381,69 EUR | 618,67 EUR |
| Long/Short 2x | 313,59 EUR | 649,36 EUR |
| Long/Short 3x | 179,19 EUR | 691,27 EUR |

Diese Beträge sind lediglich die historische Multiplikation der gemessenen Periodenrendite mit einem hypothetischen Startkapital von 500 EUR. Sie sind weder Prognosen noch auszahlbares Einkommen.

## Kosten- und Finanzierungssensitivität

Die Long/Short-Varianten werden unter erhöhten Trading-, Finanzierungs- und Borrow-Kosten nochmals deutlich schwächer.

Besonders deutlich bei 3x:

- Basis Research Return: -64,16 %
- Realistic Stress Research Return: -92,58 %
- Adverse Stress Research Return: -98,46 %
- Basis Research DD: 90,69 %
- Adverse Stress Research DD: 98,64 %
- Adverse Stress Holdout Return: -30,76 %
- Adverse Stress Holdout DD: 61,21 %

Die 2x-Variante fällt im Adverse Stress im Holdout bereits auf -10,13 % bei 45,02 % Drawdown. Die 1,5x-Variante erreicht dort noch +0,64 % Holdout-Return, aber bei 34,85 % Drawdown und PF 1,0191.

## Exposure

Die maximal simulierte Brutto- und Short-Exposition entspricht dem jeweiligen Hebel:

- 1x: 1,0x Gross / 1,0x Short
- 1,5x: 1,5x Gross / 1,5x Short
- 2x: 2,0x Gross / 2,0x Short
- 3x: 3,0x Gross / 3,0x Short

Der Simulator meldete in diesem historischen Lauf keinen vollständigen Kapitalverlust (ruined=False). Das bedeutet ausdrücklich nicht, dass der Risikopfad akzeptabel wäre; 98,64 % maximaler Drawdown im 3x-Adverse-Stress kommt einem nahezu vollständigen Kapitalverlust gleich.

## Forschungsentscheidung

**Die präregistrierte Hypothese erhält auf diesem Datensatz keine Unterstützung.**

Es gibt keinen Anlass, Long/Short oder 1,5x/2x/3x-Leverage aufgrund dieses Trials in den Produktionspfad zu übernehmen.

Insbesondere wird:

- kein Hebelwert auf diesem Datensatz optimiert,
- keine Long/Short-Variante nachträglich angepasst,
- kein Holdout-Ergebnis zur Auswahl verwendet,
- kein bestehendes Research-Gate abgeschwächt,
- keine Produktionsstrategie geändert.

Der Befund ist dennoch wichtig für das Ziel des Gesamtprojekts: Mehr Ertragskapazität durch Leverage ist nur dann sinnvoll, wenn sie nach Kosten und Stress gleichzeitig mit deutlich kontrollierbarem Risiko, stabiler Out-of-Sample-Performance und späterer Entnahmefähigkeit vereinbar ist.

## Konsequenz für die Agentenforschung

Leverage bleibt als Werkzeug im Forschungsraum.

Die Evidenz von Trial 014 spricht jedoch dafür, nicht einfach das Exposure zu erhöhen, um das Einkommensziel zu erreichen. Stattdessen müssen zunächst komplementäre, robustere Ertragsquellen gefunden werden.

Der Agent soll daher später drei Zustände unterscheiden können:

**validierte positive Exposition → reduzierte Exposition → kein Handeln/Cash**

und zusätzlich nur solche Hebel- oder Short-Komponenten einsetzen, deren eigener OOS-/Holdout-/Stress-Nachweis den Gesamtrisikopfad tatsächlich verbessert.

## Sicherheitsstatus

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine Produktionsfreigabe
- keine Live-Ausführung