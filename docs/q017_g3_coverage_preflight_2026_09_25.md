# Q017 G3 — Coverage-First Preflight

Stand: 2026-09-25

## Zweck

Q017 G3 prüft ausschließlich, ob die drei präregistrierten orthogonalen Mechanismusfamilien technisch mit einem belastbaren historischen Daten-/Point-in-Time-Contract untersuchbar sind.

Es werden keine Renditen berechnet, keine Parameter optimiert, keine Assets nach Performance ausgewählt und kein Performance-Trial autorisiert.

## Fester Prüfrahmen

Studienfenster: 2011-01-01 bis 2025-09-24.

Frischer Universumsblock:

SMH, SOXX, IGE, DBO, UNG, PPLT, CIBR, LIT.

Für Yahoo werden 3.520 Rohkerzen angefordert und anschließend auf das feste Fenster gefiltert; mindestens 3.500 gemeinsame Tageskerzen sind erforderlich.

## Familien

**Macro-surprise state transition:** ALFRED, CPIAUCSL und UNRATE. Der Runner untersucht die historischen Vintage-Termine und baut pro Beobachtung den ersten beobachteten Vintage-Termin auf. Für eine spätere tägliche Anwendung gilt eine konservative Next-Bar-Regel.

**CFTC positioning/crowding:** CFTC Disaggregated Futures Only, Jahresarchive 2011–2025. Die fünf festen Mappings sind DBO→CRUDE OIL, UNG→NATURAL GAS, PPLT→PLATINUM. Die Jahresarchive werden mit SHA-256 im Laufmanifest erfasst. Da CFTC keine vollständige historische Liste tatsächlicher Veröffentlichungszeitpunkte bereitstellt, bleibt die historische PIT-Zertifizierung bis zu einer separaten Release-Schedule-Rekonstruktion offen.

**Abnormal turnover/liquidity shock:** Yahoo Finance Daily OHLCV für das gesamte feste Q017-Universum.

## Entscheidungslogik

Coverage darf nur technische Eignung feststellen.

COVERAGE_SOURCE_VALIDATED bedeutet: technische Quelle/Abdeckung ausreichend, aber noch keine Performance-Evidence.

DATA_INSUFFICIENT bedeutet: Quelle oder Point-in-Time-Nachweis reicht für die definierte Prüfung nicht aus.

DATA_INVALID bedeutet: Daten widersprechen dem fest eingefrorenen Coverage-Vertrag.

Unabhängig vom Ergebnis bleibt performance_trial_authorized=false.

## Provenienz

Jeder Lauf erzeugt:

- q017_g3_coverage_first_result.json
- run_manifest.json
- SHA-256 der CFTC-Quelldateien
- normalisierte Yahoo-CSV-Snapshots
- ALFRED-Vintage-/First-availability-Metadaten

## Sicherheitsinvarianten

PAPER_ONLY=True, LIVE_TRADING_ENABLED=False, orders_enabled=False, automatic_promotion=False.

Q017-G3 ist ein Coverage-/PIT-Preflight und keine Renditeprüfung.
