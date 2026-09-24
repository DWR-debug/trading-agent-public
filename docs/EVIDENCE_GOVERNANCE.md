# Evidence Governance

Die Forschungsplattform unterscheidet ausdrücklich zwischen einem Backtest-Ergebnis
und Evidenz, die überhaupt für eine spätere Promotions-/Allokationsentscheidung
eligible sein darf.

## Gemeinsamer Evidence-Contract

Ein promotionsrelevanter Snapshot bindet:

- unveränderliche Trial-ID;
- Artifact-ID und SHA-256-Digest;
- Report- und Datenmanifest-Fingerprint;
- den exakten Research-Code-Commit;
- explizite Research-/Holdout-Anzahlen;
- die ausdrückliche Erklärung, dass Holdout nicht zur Auswahl verwendet wurde;
- benannte Gate-Ergebnisse;
- den bestehenden Paper-only-Sicherheitsvertrag.

Fehlende oder inkonsistente Angaben führen fail-closed zu BLOCKED bzw.
NOT_ELIGIBLE.

## Entscheidungssemantik

Für eine Evidence-Eligible-Einstufung müssen gleichzeitig der Trialstatus
VALIDATED_PASS vorliegen, alle deklarierten Gates bestanden sein und der
Holdout darf nicht zur Selektion verwendet worden sein.

Dieser Contract ersetzt keine bestehenden Research-, Rolling-, Holdout- oder
Kostenstress-Gates und lockert kein Gate. Er verbindet deren Ergebnis lediglich
mit einer reproduzierbaren Provenienz.

## Versionsvergleich

Eine Änderung an Strategie-ID, Artifact, Artifact-Digest, Report-Fingerprint,
Manifest-Fingerprint, Code-Commit, Research-/Holdout-Umfang oder Holdout-
Selektionskennzeichen wird explizit sichtbar gemacht.

## Sicherheit

Der Contract ist selbst paper-only und besitzt keinen Aufrufpfad zu Broker oder
Orderausführung.