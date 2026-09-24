# Event Alpha 2026-09-24 — technischer Abschluss

## Trial

- Trial-ID: `EVENT-ALPHA-2026-09-24-001`
- Status: `ARCHIVED_TECHNICAL_FAILURE`
- Forschungsregel: IWB -50%, GDX +25%, BIL +25%
- Zieluniversum: IWB / GDX / BIL
- Research: 2025-04-01 bis 2025-06-30
- Holdout: 2025-07-01 bis 2025-09-30
- Paper-only: ja

## Ergebnis der technischen Prüfung

Der Control wurde zweimal auf aktuellem Master-Stand gestartet. Beide Läufe bestanden
die vorgelagerten Methodik- und Sicherheitsprüfungen; die eigentliche Event-Auswertung
konnte wegen fehlender historischer GDELT-Tagesdateien nicht vollständig ausgeführt
werden.

### Lauf 1

- Workflow: 36001720932
- Artifact: 10808552519
- Artifact-SHA256: `341a35797dad6192445a243ab9253b729d8a950b6f977665ac8ed893f8a5897b`
- Tests: bestanden
- Paper-only: bestanden
- Universums-Disjointness: bestanden
- Präregistrierung: bestanden
- Fehler: HTTP 404 beim Abruf eines benötigten GDELT-Tagesexports

Die Rohdaten-Ablage enthielt bis einschließlich 2025-06-13 insgesamt 81 Tagesdateien.

### Lauf 2

Nach einer technischen Fallback-Implementierung wurde derselbe Control erneut
ausgeführt:

- Workflow: 36003014680
- Artifact: 10809202708
- Artifact-SHA256: `692b1bd7160d9544e86b438ee26d014e113cc99247d22f937ad35797b9db16d5`
- Tests: bestanden
- Paper-only: bestanden
- Universums-Disjointness: bestanden
- Präregistrierung: bestanden
- Ergebnisintegrität: nicht erreicht
- Fehler: HTTP 404 sowohl beim Primärarchiv als auch beim getesteten AWS-Fallback
- Letzte erfolgreich akquirierte Eventdatei: 2025-06-13

Der getestete AWS-Pfad war damit nicht als kompatibler täglicher GDELT-Eventexport
verifiziert. Er wird nicht als Datensatzersatz verwendet.

## Methodische Konsequenz

Dies ist **kein negatives oder positives Alpha-Ergebnis**. Es existiert kein
vollständiger Research-/Holdout-Report und damit keine Aussage über die Hypothese.

Insbesondere wurden:

- keine fehlenden Tage übersprungen,
- keine Eventdaten interpoliert,
- keine alternativen Nachrichtenquellen substituiert,
- keine Parameter verändert,
- keine Assets geändert,
- keine Gewichte verändert,
- kein Holdout zur Entscheidungsfindung verwendet.

Der Control wird daher technisch geschlossen und nicht in den Master übernommen.
Eine spätere erneute Validierung wäre ein neuer, separat dokumentierter Lauf und
erfordert einen vorab verifizierten, vollständigen historischen GDELT-Datenbezug.

## Sicherheitsstatus

`PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, keine Orders.
