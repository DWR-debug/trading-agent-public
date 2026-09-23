# Zeitphasen-/Asset-Typ-Diagnose — 2026-09-22

## Zweck

Reine Diagnose auf Basis der drei bereits abgeschlossenen, fingerprint-verifizierten Kontrollfamilien:

- \`small_cap_high_volatility\`
- \`benchmark\`
- \`liquid_high_volatility\`

Keine Research-Neuberechnung, keine Änderung an Gates, Schwellenwerten, Selection-Profilen oder Parameterraum.

## Evidenzumfang

- 12 archivierte Profil-Reports
- 52 Dataset/Profile-Auswertungen
- 260 Rolling-WF-Testfenster
- vier Selection-Profile je Dataset

Die Rolling-Zeitdimension wird ausschließlich über die relative Fensterposition 1–5 beschrieben. Aus den Reports werden keine Kalenderphasen konstruiert, weil pro Rolling-Fenster keine Candle-Timestamps gespeichert sind.

## Zeitphasen-Befund

| Universum | W1 | W2 | W3 | W4 | W5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| small_cap_high_volatility | 15 % | 40 % | 35 % | 55 % | 25 % |
| benchmark | 33,3 % | 25 % | 33,3 % | 41,7 % | 25 % |
| liquid_high_volatility | 55 % | 45 % | 30 % | 30 % | 30 % |

Angegeben ist jeweils der Anteil positiver Nettoprofit-Fenster.

Die Muster unterscheiden sich zwischen den Universen. Kein Universum zeigt über alle fünf relativen Fenster hinweg eine mehrheitlich positive Fensterquote. Über alle 260 Fenster zusammen sind 91 positiv (35,0 %).

## Asset-Heterogenität

Die Ergebnisse unterscheiden sich auch innerhalb derselben Universumsfamilie.

**small_cap_high_volatility**
- HIMS: W5 4/4 positive Fenster; W1 0/4.
- SOUN: W2 3/4; W1/W3/W5 jeweils 0/4.
- RKLB: W1 2/4 und W3 2/4; W2/W5 0/4.
- IONQ: W4 2/4; W5 0/4.
- ASTS: W3 3/4; W1 0/4.

**benchmark**
- IWM bleibt in allen fünf Fenstern bei 0–1 positiven Profilfenstern.
- QQQ zeigt 3/4 positive Fenster in W1, danach 0/4 in W3.
- SPY zeigt 3/4 in W3 und W4, aber 0/4 in W2 und W5.

**liquid_high_volatility**
- NVDA: W1 und W2 jeweils 4/4 positive Profilfenster; W3 und W4 jeweils 0/4.
- PLTR: W1 0/4, W3 und W4 jeweils 2/4.
- COIN: W4 3/4, W5 1/4.
- AMD: W1 3/4, danach überwiegend 1–2/4.
- TSLA: W1 3/4, W4 0/4, W5 2/4.

Diese Asset-Muster sind deskriptiv. Sie werden nicht als Asset-Rangfolge interpretiert.

## Kandidatenstruktur

Der bereits bekannte Gesamtwert für die Übereinstimmung zwischen Rolling- und festem WFO-Kandidaten bleibt bei 118/260 = 45,4 %.

Die Persistenz ist universums- und profilabhängig:
- small_cap_high_volatility: \`score_max\` 16 %, \`boundary_averse\` 52 %, \`risk_averse\` 16 %, \`trade_rich\` 64 %
- benchmark: 66,7 %, 73,3 %, 66,7 %, 60,0 %
- liquid_high_volatility: 40,0 %, 24,0 %, 32,0 %, 68,0 %

Damit ist ein Kandidatenwechsel selbst kein hinreichender Erklärungsbefund; er tritt in den Kontrollfamilien mit unterschiedlicher Häufigkeit auf.

## Fachliches Zwischenfazit

Die Failure-/Performance-Muster sind sowohl zeitabhängig als auch assetabhängig. Gleichzeitig gibt es kein einheitliches Zeitfenster und keine einheitliche Asset-Gruppe, die das beobachtete Generalisierungsproblem allein erklärt.

Für die nächste Stufe bleibt deshalb der Long-Horizon-Control-Lauf sinnvoll: Er sollte als getrennte Evidenzfamilie aufgebaut werden und dieselbe Research-Protokollierung, Fingerprints, Holdout-Trennung und Gates unverändert übernehmen.

Eine Änderung des Parameterraums oder der Strategie ist auf Basis dieser Diagnose noch nicht vorgesehen.

## Reproduzierbarkeit

Der Diagnose-Layer liegt in \`automation/time_asset_diagnostics.py\` und erzeugt einen deterministischen \`diagnostic_fingerprint\`. Vor der Aggregation werden die Quellreports über ihre bestehenden Ergebnis-Fingerprints verifiziert.
