# Trading Agent — Research Engine

## Zweck

Die Research Engine vereinheitlicht den dauerhaften Forschungsablauf. Historische Trial-Workflows bleiben über Git-Historie und Evidence-Provenienz nachvollziehbar, sind aber nicht mehr die normale Ausführungsoberfläche.

## Ablauf

1. Aktuelle Marktdaten einlesen.
2. Datenqualität, Abdeckung und Point-in-Time-Eignung prüfen.
3. Explorative Beobachtungen erzeugen.
4. Beobachtungen als Hypothesen-Kandidaten markieren.
5. Nur vorab festgelegte Hypothesen in formale Trials überführen.
6. Preflight -> Research/OOS -> Rolling-WF -> Robustheit -> Kostenstress -> Holdout -> Gates.
7. Report, Fingerprints und Checkpoints archivieren.
8. Nur formal bestandene Evidenz darf in eine Kandidatenphase übergehen.

Die Discovery-Schicht ist keine profitable-Auswahlmaschine. Sie erzeugt Hypothesen. Eine aktuelle Beobachtung darf niemals rückwirkend in einen bestehenden Trial einfließen.

## Aktuelle Daten

Der Observer nutzt vorhandene öffentliche Datenquellen ohne Handels-API-Credentials. Daily-Yahoo-Daten werden als abgeschlossene Bars eingelesen. Zeitpunkt, Datenabdeckung und Fingerprint werden mit dem Beobachtungsbericht gespeichert.

## Discovery

Die erste Generation betrachtet feste Diagnostiken: aktueller Schlusskurs und letzter Return, 21-Session-Volatilität, 252-Session-Trendreturn, Paar-Korrelationen, feste Lead-Lag-Korrelationen für 1/5/21 Sessions und gemeinsamen Datenkalender. Es findet keine Parameter- oder Threshold-Suche statt.

## Promotion

Eine Discovery-Beobachtung darf erst nach neuer Präregistrierung als formaler Research-Trial ausgewertet werden. Der Holdout bleibt dabei vollständig blind.

## Sicherheit

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
Keine Handels-API-Credentials im Research-Runner. Keine automatische Echtgeldpromotion.

## Kosten

Die Research Engine verwendet keine bezahlte Agenten-API. Agentische Arbeit bleibt optional für Interpretation, Hypothesenbildung und Code-Review. Ein externer Agent darf nur genutzt werden, wenn außerhalb dieses Repositories ein tatsächlich kostenlos verfügbares Kontingent festgestellt wurde. Es gibt keinen Mechanismus zum Nachladen oder automatischen Bezahlen von Credits.

## Kontinuität

Der kanonische Maschinenzustand ist research/evidence/project_state.json. Laufende Ausführungen erzeugen zusätzlich Snapshots. PROJECT_STATUS.md bleibt die lesbare Übersicht.
