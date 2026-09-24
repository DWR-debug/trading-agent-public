### 2v. Portfolio Risk-Parity — Trial 022 Ergebnis — 2026-09-24

Trial T-2026-09-24-022 wurde vollständig und reproduzierbar auf zwei neuen,
symbol-disjunkten U.S.-Aktienuniversen ausgeführt. Die zugrunde liegenden
Trend-/Cross-Sectional-Signale blieben unverändert; ausschließlich die
Portfolioaggregation wurde als präregistrierter Control verändert.

- Workflow-Run: 36012719190
- Artifact-ID: 10813113637
- Artifact-Digest: sha256:a2419c933b4f0d84adf4cd7e187deb1bfa4261691bffa12f1dddf829bbeb1ed7
- Trend-Manifest: e102276bb387ca7174271c663402d17f445d77fcd3cde23d0e54854b807ab657
- CS-Manifest: 2a4dd8c6d67041c388fb41518faf6d16d68e8d785356b322e8380de5f69d72ab
- Report-Fingerprint: feeb659b4c0ac59082e333200327e1b44407902c6f69e5fd72f75dd9c16c4313
- Code-Commit: 757da1ba764db79c9c602f6f5cd71f035cbbecf2
- 13 Assets, 3.500 Candles/Asset, 3.498 Returns, Research/Holdout 2.798/700
- vollständige Testsuite: 628 bestanden
- Paper-only, Universums-Disjointness, Präregistrierung und Ergebnisintegrität: bestanden
- keine Auswahl, keine Parameter-/Gewichtssuche, keine Orders

### Fachlicher Befund

Dynamische 63-Sessionen-Inverse-Volatilität:

- Research: +103,90%, DD 42,93%, PF 1,090
- Holdout: +100,52%, DD 23,83%, PF 1,273
- Rolling Research: 4/5 profitable Fenster
- OOS/Research-Ratio: 0,967
- Holdout-Turnover: 17,18; davon Allokations-Turnover 4,97

Unveränderte 50/50-Referenz:

- Research: +121,73%, DD 41,29%, PF 1,093
- Holdout: +114,92%, DD 24,87%, PF 1,289

Damit verbessert die dynamische Allokation zwar den Holdout-Drawdown geringfügig
und erfüllt Return-, Rolling-, OOS/IS-, Holdout-PF- und Kostenstress-Bedingungen.
Sie verfehlt jedoch die harten Drawdown-Grenzen von 10% in Research und Holdout,
liegt beim Research-PF knapp unter 1,10 und verschlechtert gegenüber 50/50 sowohl
Research- als auch Holdout-Return und PF.

### Entscheidung

NO_SUPPORT / archived_rejected.

Keine Produktionsintegration, keine Gewichtsanpassung und keine erneute Suche über
Lookback, Caps oder Allokationsregeln aus diesem Holdout-Befund.

Der nächste methodische Schritt ist eine Failure-Diagnose der Portfolioaggregation:
insbesondere die Trennung von Allokations-Turnover/Kosten, Sleeve-Risiko und der
Frage, ob die dynamische Gewichtsänderung tatsächlich die Drawdown-Failures adressiert.
