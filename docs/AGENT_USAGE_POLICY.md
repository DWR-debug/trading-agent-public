# Agenten- und Credit-Nutzungsrichtlinie

## Grundsatz

Der Trading Agent darf nicht von bezahlter Agenten- oder API-Nutzung abhängig werden.

## Erlaubt

- bereits enthaltenes, nachweislich kostenloses Kontingent;
- kostenloses, ausdrücklich bereitgestelltes Kontingent;
- manuelle Agentenarbeit, sofern kein kostenpflichtiger Verbrauch erzwungen wird.

## Nicht erlaubt

- automatische API-Aufrufe zum Nachladen von Credits;
- automatische Nutzung eines kostenpflichtigen Restbudgets;
- API-Schlüssel in Research-Dateien;
- Research-Jobs, die ohne Agentencredits technisch nicht funktionieren;
- Promotion eines Kandidaten aufgrund eines Agentenurteils ohne formale Evidence.

## Technische Konsequenz

Die deterministische Research Engine funktioniert vollständig ohne Agentencredits. Agentische Arbeit wird auf Interpretation, Hypothesenbildung, Engineering-Review und die Auswahl der nächsten präregistrierbaren Forschungsfrage begrenzt.

Der Default ist kein bezahlter Agentenverbrauch.

PAPER_ONLY=True und LIVE_TRADING_ENABLED=False bleiben unabhängig davon unverändert.
