### 2p. Turn-of-Month Calendar Alpha — 2026-09-24

Die präregistrierte Turn-of-Month-Kalenderhypothese wurde auf einem vollständig
symbol-disjunkten globalen Country-ETF-Universum technisch vollständig und
methodisch reproduzierbar ausgeführt.

- Workflow-Run: 36006749490
- Artifact-ID: 10810214406
- Artifact-Digest: sha256:1d7ebd14a4da359908ec2d10011598e6689b47f9d81605ae2a62aec53d33835b
- Code-Commit: 546fd8aad0008923bb63f70936b57882f579ef9f
- Report-Fingerprint: 27df7c6ba36083d599d39c65fdd5fd089ec9216bd03211a42b8530c75ee3e85a
- Market-Manifest-Fingerprint: 561c0d76fe6bbb4435f7399179f4e9f0542138c8d8a1586e3012f49465f9e031
- 8 Assets, 3.500 Candles je Asset, 3.498 Returns
- Research/Holdout: 2.798 / 700
- vollständige Testsuite: 615 bestanden
- Paper-only, Universums-Disjointness, Präregistrierung und Ergebnisintegrität: bestanden
- keine Auswahl, keine Parameter-/Threshold-Suche, keine Orders

Die Implementierung wurde vor der eigentlichen Forschungsrechnung auf die bereits
präregistrierte Regel ausgerichtet: letzter Handelstag des Monats plus erste drei
Handelstage des Folgemonats. Die Präregistrierung selbst wurde nicht nachträglich
geändert.

### Fachlicher Befund

Basis-Szenario:

- Research: -11,67% Return, 24,40% Drawdown, PF 0,963
- Holdout: -1,92% Return, 9,29% Drawdown, PF 0,977
- Research-Rolling: 3/5 Fenster positiv
- OOS/Research-Ratio: 0,00
- TOM-Mittelrendite minus Nicht-TOM im Research: +0,0789 Prozentpunkte pro Tag
- TOM-Mittelrendite minus Nicht-TOM im Holdout: +0,0187 Prozentpunkte pro Tag
- Turnover: 267 Research / 68 Holdout

Kostenstress verschlechtert den Befund weiter:

- 1,5x Kosten: Holdout -6,81%, PF 0,891
- 2x Kosten: Holdout -11,45%, PF 0,817

Von den elf festen Entscheidungschecks bestehen nur vier:
die TOM-gegen-Nicht-TOM-Mittelrendite in Research und Holdout, die
Research-Rolling-Quote von 3/5 und das Holdout-Drawdown-Gate.

Verfehlt werden insbesondere Research-Return/Drawdown/PF, OOS/Research,
Holdout-Return/PF sowie beide Kostenstress-Checks.

### Entscheidung

NO_SUPPORT / archived_rejected.

Der Control liefert damit trotz positiver deskriptiver TOM-Mittelrendite keinen
robusten kostenbereinigten Portfolio-Nachweis. Es gibt keine Produktionsintegration,
keine Gewichtsanpassung, keine TOM-Varianten-Suche und keine nachträgliche
Gateänderung.

Dauerhafte Evidenzablage:

- docs/turn_of_month_validation_2026_09_24_result.md
- research/checkpoints/turn_of_month_2026_09_24_result.json
- research/evidence/trial_ledger.json

Der nächste Research-Schritt bleibt außerhalb dieser Kalenderregel; es erfolgt
kein weiteres TOM-Tuning auf Basis dieses Resultats.

