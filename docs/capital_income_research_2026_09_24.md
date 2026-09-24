# Capital / Income Research Model — 2026-09-24

## Zweck

Der Research-Pfad trennt drei wirtschaftlich unterschiedliche Vorgänge:
Auszahlung von netto-realisiertem Gewinn, dauerhafte Kapitalisierung eines
Gewinnanteils in die geschützte Kapitaleinlage und Belassen des Restes als
Working Capital.

Die bestehende `CapitalAccount` bleibt die Buchführungsquelle. Positive und
negative realisierte Ergebnisse werden kumuliert. Ein späterer Verlust reduziert
damit automatisch den künftig verfügbaren Ausschüttungsbetrag.

## Modellvertrag

`CapitalIncomePolicy` macht die Annahmen explizit: geschütztes Kapital,
Reserve, Auszahlungsanteil, Kapitalisierungsanteil, Intervall und optionales
maximales Auszahlungslimit. Auszahlung plus Kapitalisierung dürfen zusammen
höchstens 100 % des verfügbaren Überschusses beanspruchen; der Rest bleibt im
Working Capital.

Der Simulator verwendet bewusst einen Research-Realization-Proxy: Jede
Periodenrendite wird auf das zu Periodenbeginn vorhandene Eigenkapital
angewendet und als realisiertes P&L verbucht. Das ist reproduzierbar für
Portfolio-Return-Serien, aber kein Broker-Modell für die Abrechnung einzelner
Trades.

## Sequence-Risk-Diagnose

`sequence_sensitivity()` vergleicht die chronologische und umgekehrte
Reihenfolge derselben Renditeserie. Das ist eine deterministische Diagnose der
Entnahme-/Kapitalpfad-Sensitivität, kein probabilistischer Forecast.

Die Methodik wird durch aktuelle Retirement-Income-Forschung motiviert, in der
Sequence-of-Returns-Risk und flexible Ausgabenansätze explizit berücksichtigt
werden. Die dort publizierten Entnahmesätze werden nicht als Trading-Agent-
Defaults übernommen.

Für die Suche nach Ertragsquellen bleibt die Literatur getrennt: Zeitreihen-
momentum wurde über 58 liquide Futures aus Aktienindizes, Währungen,
Rohstoffen und Anleihen dokumentiert. Das motiviert eine Untersuchung
diversifizierter Ertragsquellen, ist aber kein Nachweis für den Trading Agent.
citeturn687841search0

## Safety

Der Code ist ausschließlich Research-/Simulationslogik. Keine Brokerimporte,
keine Orderausführung und keine Änderung von Leverage-Limits, Research-Gates
oder Produktionskandidat.

Der nächste empirische Schritt ist, den Kapital-/Entnahmepfad auf unabhängigen,
vollständig dokumentierten Return-Serien zu messen und dabei Auszahlung,
Kapitalwachstum, Drawdown und Sequence-Sensitivität gemeinsam zu archivieren.
