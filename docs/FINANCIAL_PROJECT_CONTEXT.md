# Project 500 – neue Kapitalregel (2026-10-23)

Der Nutzer hat 500 EUR als nominales Startkapital genannt. Es ist **nicht bestätigt**, ob dieser Betrag frei disponibel ist oder die gesamte Rücklage darstellt. Bis zur Klärung: `confirmed_discretionary_capital_eur=0`, `authorised_experiment_spend_eur=0`. Keine Transaktionen, Trading-Einsätze, kostenpflichtigen Services oder sonstige Ausgaben hieraus veranlassen oder empfehlen, bevor die Liquiditäts-/Rücklagenlage klar ist.

Der historische `HYPOTHETICAL_STARTING_CAPITAL_EUR=2000`-Wert gilt ausschließlich als Simulationseinstellung der bestehenden Trading-Forschung, nicht als tatsächliches Vermögen. Der 500-EUR-Trading-Canary ist ebenfalls historisch simulativ. Project 500 beginnt mit kostenfreier Recherche und Kundenbedarfsvalidierung; Kapitalausgaben sind ein gesonderter späterer Entscheid.

# Trading Agent — Finanzielle Zielparameter

Stand: 2026-09-25

## Kapitalannahme
- Simulation und ein späteres, nur nach separater formaler Freigabe zulässiges Echtgeldszenario unterstellen **2000 EUR Anfangs-/Grundkapital**.
- Das Grundkapital ist als dauerhaft arbeitendes Kapital gedacht.
- Spätere Aufstockung oder sinnvolle Anpassung entsprechend validierter Strategien ist möglich, aber eine separate Kapitalentscheidung.

## Familienabsicherung und Entnahme
- Praktisches Langfristziel: finanzielle Absicherung der Familie.
- Vorgesehen ist eine regelmäßige Entnahme aus einem später tatsächlich verfügbaren und ausreichend validierten Konto.
- **Kein fixer monatlicher Euro-Betrag wurde festgelegt.** Die Entnahmehöhe hängt von tatsächlich realisierten und aktuell vorhandenen Gewinnen bzw. dem ausschüttbaren Überschuss ab.
- Bei Verlusten oder ohne realisierten Überschuss: ausschüttbare Summe **0 EUR**.
- Das Grundkapital soll grundsätzlich erhalten und weiterarbeiten.

## Sicherheitsbindung
Diese Finanzparameter ändern keine Research- oder Safety-Gates. Insbesondere bleiben `PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, keine Live-Orders und keine automatische Echtgeldpromotion bestehen.
