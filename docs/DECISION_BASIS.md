# Decision Basis — Trading Agent

Stand: 2026-09-25

Diese Datei ist die laufende, chatübergreifende Entscheidungsgrundlage. Nach jedem
abgeschlossenen Research- oder Engineering-Schritt wird sie mit dem verifizierten
neuen Stand aktualisiert. Deskriptive Evidenz, Aussagegrenzen und nächste Aktion
bleiben strikt getrennt.

## Aktueller Stand

### Was wissen wir?

- Die technische Referenz bleibt ausschließlich `DWR-debug/trading-agent-public`.
  Der aktuell verifizierte Master-Head ist `39c21708bc44fac1a750fcdde63665bdc12abf43`.
- Der Forschungsmodus ist operativ `wide search -> aggressive pruning -> narrow formal validation`.
- Round 001 hat vier günstige Yahoo-Signalprobes auf dem Research-Split verworfen:
  H03, H07, H09 und H10. Kein Holdout wurde zur Auswahl benutzt.
- Q017-G3 bleibt ein reiner Daten-/PIT-Befund mit `DATA_INSUFFICIENT`; daraus ist kein
  Performance-Trial autorisiert.
- Round 002 / H08 wurde vollständig ausgeführt: Workflow `36188766298`,
  Artifact `10887128923`, Digest
  `sha256:9ce4f10f10998d55e144b5dd01b991f4d48815a0a335ba4b96457a8bef307433`,
  Result-Fingerprint
  `de1af470352d4bc7666b9b11b67829c1252cf46fa11615c675f176a4fb5f5760`.
- H08 verwendet ausschließlich einen vorab fixierten Research-Test:
  20-Tage-/60-Tage-Volatilitätsverhältnis >= 1,5; anschließend 5-Tage-realized-volatility
  relativ zur Ereignis-Basisvolatilität.
- Es gab 316 Expansionsevents. Der Gesamtmittelwert des Forward-/Baseline-Volatilitäts-
  verhältnisses beträgt 1,325. Beide Research-Hälften überschreiten die präregistrierte
  Support-Grenze von 1,10: 1,516 bzw. 1,135.
- Der robuste Gegenbefund ist wichtig: Der gepoolte Median liegt nur bei 0,978.
  Außerdem ist der Mittelwerteffekt über Symbole ungleich verteilt; besonders hoch sind
  IYF (1,592), IYH (1,576), IDU (2,182) und OIH (1,221), während mehrere andere Symbole
  nahe 1,0 liegen oder darunter.
- Round 002 ist deshalb als `EXPLORATION_SUPPORT_WITH_ROBUSTNESS_CONCERN` archiviert:
  ein explorativer Risikoregime-Hinweis, aber noch kein formaler Validierungskandidat.
- Governance blieb vollständig research-only: 2.798 Research-Candles, 702 Holdout-Candles
  ungenutzt, keine Performanceauswertung, keine Holdout-Auswahl, keine Trial-Autorisierung,
  keine automatische Promotion.

### Was wissen wir nicht?

- Ob H08 robust über einen größeren Anteil der acht Symbole wirkt.
- Ob die Beobachtung nach median-/outlier-robuster Betrachtung bestehen bleibt.
- Ob ein H08-basiertes Risikoverlay gegenüber bestehenden Kontroll-/Baseline-Sleeves
  tatsächlich die historischen Risikogates verbessert.
- Ob ein späterer formaler H08-Versuch die unveränderten OOS-/Holdout-/Drawdown-/
  Nichtverschlechterungs-Gates bestehen würde.
- ALFRED und CFTC bleiben wegen offener PIT-/Datenvertragsprobleme nicht für formale
  Auswahl freigegeben.

### Was ändert sich?

- Round 002 liefert erstmals in der neuen Wide-Search-Lane einen positiven,
  risikoorientierten Explorationshinweis.
- Wir überspringen wegen dieses Hinweises nicht den nächsten Filter. Im Gegenteil:
  der Median-vs.-Mean-Konflikt macht robuste Symbolabdeckung zum nächsten Engpass.
- Round 003 wird daher keine neue Schwelle suchen, sondern dieselbe H08-Regel
  auf Symbolbreite und robuste Aggregation prüfen.
- Erst wenn dieser Filter belastbar ist, kommt eine separate Preregistration für einen
  möglichen formalen Risikoverlay in Betracht.

## Nächste Aktion

`WIDE-SEARCH-ROUND-003`: feste H08-Regel erneut auf dem identischen Research-Universum
prüfen, diesmal mit zwei vorab festgelegten Robustheitsfragen:

1. Wie viele Symbole zeigen einen nicht-trivialen H08-Effekt?
2. Bleibt der gepoolte Effekt unter einer median-/trimmed-robusten Zusammenfassung erhalten?

Diese Runde bleibt vollständig auf dem Research-Split. Ein positives Round-003-Ergebnis
würde noch keine Live- oder formale Freigabe erteilen; es würde nur die Kandidatenklasse
für den nächsten engen Validierungsschritt verbessern.

### Welche Schutzgrenzen bleiben unverändert?

- `PAPER_ONLY=True`
- `LIVE_TRADING_ENABLED=False`
- `ORDERS_ENABLED=False`
- `automatic_promotion=False`
- Kein Holdout wird zur Exploration oder Auswahl verwendet.
- Keine nachträgliche Parameter-, Asset-, Feature-, Horizon- oder Threshold-Optimierung.
- Zeit-/Erfolgsdruck erhöht nur Priorisierung und Parallelisierung, niemals Evidenzstandard
  oder finanzielles Risiko.

## Update-Regel

Nach jedem neuen signifikanten Ergebnis werden mindestens diese Felder ersetzt:
**Was wissen wir? — Was wissen wir nicht? — Was ändert sich? — Nächste Aktion —
Welche Schutzgrenzen bleiben unverändert?**
