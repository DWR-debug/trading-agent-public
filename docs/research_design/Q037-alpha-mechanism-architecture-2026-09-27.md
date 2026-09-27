# Q037 — Ex-ante Alpha-Mechanism-Architecture

**Stand:** 2026-09-27  
**Status:** PREREGISTERED / DESIGN-ONLY  
**Vorgänger:** Q036 / T-2026-09-27-057

## Ausgangslage
Q036 zerlegte das bereits eingefrorene T056-Ergebnis ausschließlich deskriptiv. Die vier Risikomechanismen veränderten vor allem Exposition, Drawdown und Aktivierungszustände. Kein Arm erfüllte alle 13 unveränderten Gates. Damit liegt kein Nachweis vor, dass zusätzliche Risikoregeln das zugrunde liegende Return-/Alpha-Problem lösen.

Insbesondere RISK-B arbeitete über eine starke Expositionsreduktion: mittlere Bruttoexposition rund 0,308x; 74,09 % der ausgewerteten Perioden lagen im 0,25x-Zustand. Die Holdout-Drawdown-Reduktion gegenüber CONTROL ging dabei nicht mit einem ausreichenden Profit-Factor-/Return-Nachweis einher.

## Forschungsziel
Die nächste Phase verschiebt den Schwerpunkt von **Risk Overlay** zu **Alpha Mechanism**. Vor jeder Performanceausführung wird ein kleiner, ex-ante definierter Katalog orthogonaler Mechanismen dokumentiert. Es gibt in dieser Phase keine Rangfolge und keine Auswahl eines vermeintlich besten Mechanismus.

## Festgelegte Mechanismusklassen
**A1 — Multi-Horizon Trend Continuation:** Richtungspersistenz über mehrere Signalhorizonte.

**A2 — Cross-Sectional Momentum:** Relative Stärke zwischen Assets; Signalbildung über Querschnittsränge.

**A3 — Residual / Relative Value:** Signal auf dem idiosynkratischen Residuum nach expliziter Entfernung gemeinsamer Markt-/Faktorkomponenten.

**A4 — Point-in-Time Event / Information:** externe Informationen mit strikt gebundenem Veröffentlichungszeitpunkt.

**A5 — Carry / Income / Defensive Premium:** Renditequellen aus Carry-, Einkommens- oder defensiven Prämien.

Diese Klassen sind eine **Forschungskategorie**, keine getestete Rangfolge.

## Verfahrensregeln
Eine spätere Performanceprüfung benötigt eine neue, vollständig symbol-disjunkte Coverage-Phase, danach PIT-Prüfung und anschließend eine separat autorisierte Fixed-Rule-Performanceausführung. Die bestehenden 13 Gates bleiben unverändert; Gebühren-/Kostenstress, Rolling und OOS/IS-Verhältnis bleiben Bestandteil des Evidence Contracts.

Q037 selbst erzeugt **keine** Performance-Evidence, kein Holdout-Signal und keine Promotion. Keine Parameter-, Threshold-, Asset-, Horizon- oder Family-Selection wird aus Holdout-Daten abgeleitet.

## Sicherheitszustand
`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`ORDERS_ENABLED=False`  
`AUTOMATIC_PROMOTION=False`
