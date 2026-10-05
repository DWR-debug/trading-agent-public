# Trading Agent OS — Projektstatuten

**Status:** BINDING / ACTIVE  
**Effective:** 2026-10-05  
**Canonical language source:** `docs/TRADING_AGENT_PROJECT_STATUTES.md`  
**Machine-readable mirror:** `research/governance/project_statutes.json`

## 1. Zweck und Dauerhaftigkeit

Diese Statuten sind die verbindliche sprachliche Regelung für die kontinuierliche Weiterentwicklung des Trading-Agent-OS. Sie verbinden Projektziel, Gedächtnis, wissenschaftliche Arbeitsweise, Ressourcenorchestrierung, Sicherheitsgrenzen und Kontinuität über Chats hinweg.

Repository-Dateien speichern dauerhafte Projektentscheidungen, Ziele, Regeln, Arbeitsfortschritt und Handoffs. Ein Chat ist niemals der alleinige Zustandsspeicher. Aktuelle technische und operative Tatsachen müssen trotzdem gegen den aktuellen öffentlichen `master`, Live-Workflows, Runner und Evidence verifiziert werden.

## 2. Nicht verhandelbare Nutzkapazitäts-Regel

> **Es darf keine künstliche Arbeit erzeugt werden. Es darf ausschließlich wertvolle und hilfreiche Rechenarbeit ausgeführt werden. Und das so viel wie möglich, kontinuierlich. Wir müssen immer besser werden.**

Das bedeutet operativ:

- Freie erreichbare Kapazität wird sofort auf den höchsten echten, zulässigen und unabhängigen Nutzen geroutet.
- Nach erfolgreichem Abschluss eines bounded Workpacks soll der logisch nächste zulässige Workpack ereignisgesteuert nachbeschickt werden; Cron-/Schedule-Läufe sind Recovery-/Health-Mechanismen.
- Idle ist nur zulässig, wenn kein sinnvoller ausführbarer unabhängiger Backlog existiert, eine echte Abhängigkeit blockiert, eine höherpriorisierte Aufgabe die Ressource bindet oder eine harte Plattform-/Quota-/Entitlement-Grenze die Ausführung verhindert.
- Erfolgreiche Arbeit wird nicht nur zur Auslastung wiederholt.
- Laufende oder identische Arbeit wird niemals dupliziert.
- Laufzeit wird niemals künstlich verlängert, um Kapazität zu verbrauchen.
- Wissenschaftliche Gates, Holdout-Blindheit, Promotion und Live-Ausführung werden durch diese Nutzkapazitäts-Regel niemals gelockert.

**Leitsatz:** maximale sinnvolle Auslastung, nicht maximale Aktivität.

## 3. Kontinuierliches Projektgedächtnis

Wichtige neue dauerhafte Informationen werden nach jedem materialisierenden Meilenstein in die passende kanonische Ebene überführt:

- **Projektstatuten:** dauerhafte Prinzipien und verbindliche Arbeitsregeln.
- **Projektgedächtnis:** gemeinsame Ziele, langfristige Entscheidungen, dauerhafte Kontextinformationen.
- **Projektkontext / Nordstern:** Zweck, Ziele, Prioritäten und finanzielle/organisatorische Absicht.
- **Current Status / Operational State:** aktueller technischer und operativer Stand.
- **Evidence / Ledger:** wissenschaftliche Ergebnisse und unveränderliche Provenienz.
- **Decision Basis:** verifizierte Entscheidungsgrundlage.
- **Chat Handoff:** kompakte Wiederaufnahmespur für den nächsten Chat.

Eine neue Chat-Aussage wird nicht allein deshalb zur Projekttatsache, weil sie im Chat genannt wurde. Dauerhafte technische oder wissenschaftliche Aussagen müssen in der passenden kanonischen Quelle verankert und gegen die Quellenhierarchie geprüft werden.

## 4. Kontinuität und Quellenhierarchie

Bei Widersprüchen gilt:

1. technischer Zustand: aktueller öffentlicher `master`;
2. aktuelle operative Tatsachen: `docs/CURRENT_STATUS.md` + `research/evidence/current_operational_state.json`;
3. wissenschaftliche Wahrheit: Trial Ledger, Checkpoints, Reports, unveränderliche Workflow-/Artifact-Provenienz;
4. Projektziele und dauerhafte Absicht: `docs/PROJECT_CONTEXT.md` + `research/governance/project_north_star.json`;
5. Statuten: verbindliche Arbeitsregeln für die Ausführung und Kontinuität.

Statuten dürfen keine technischen oder wissenschaftlichen Fakten erfinden. Umgekehrt dürfen aktuelle Läufe und Chats die Statuten nicht stillschweigend verändern.

## 5. Wissenschaftliche Arbeitsweise

Die operative Schleife lautet:

**Beobachten → Hypothesen bilden → billig falsifizieren → Evidenz verdichten → unabhängig prüfen → formalisieren → robust prüfen → reproduzieren → nächste Frage.**

Priorität hat echte Informationsorthogonalität gegenüber weiteren Preis-/Momentumvarianten. Negative Evidence, `DATA_INSUFFICIENT`, `NO_SUPPORT` und technische Fehlschläge mit belastbarer Diagnose sind gültiger Fortschritt.

Kein Kandidat wird aufgrund eines schönen Backtests, einer Literaturbehauptung oder einer Agentenmeinung ausgewählt, gerankt oder promotet.

## 6. Ressourcen

Kostenlose und tatsächlich erreichbare Ressourcen werden nach Nutzen, Unabhängigkeit, Reproduzierbarkeit und erwarteter Informationsausbeute eingesetzt.

Primär:

- Windows A = Formal Readiness;
- Windows B = Frontier Discovery / Data-QA;
- Windows C = lange deterministische Läufe / unabhängige Reproduktion;
- GitHub-hosted Linux/ARM = deterministische Gegenprüfung und Frontier;
- S10 = bounded mechanical QA;
- kostenlose AI-Worker = Gegenhypothesen, Design, Review und Engineering, niemals wissenschaftliche Autorität.

Die Ressourcenklassifikation **verfügbar / belegt / deaktiviert / nicht zugänglich / nicht sinnvoll** bleibt verpflichtend.

## 7. Sicherheitsinvarianten

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`ORDERS_ENABLED=False`  
`AUTOMATIC_PROMOTION=False`  
`paid_api_budget_usd=0`

Nutzkapazität erhöht ausschließlich Geschwindigkeit und Forschungsbreite. Sie erzeugt niemals eine neue Autorisierung.

## 8. Regel für Kandidatenentwicklung

Neue Kandidaten werden als ungerankte Designobjekte angelegt. Jeder Kandidat benötigt eine explizite Mechanismushypothese, Event-/Informationsuhr, Features, Cheap-Falsifiers, Daten-/PIT-Gates und Abgrenzung zu bestehenden Linien.

Bei möglicher Überschneidung gilt zuerst **merge-or-kill**: keine zusätzliche Kandidatenfamilie ohne nachweisbaren eigenständigen Mechanismus.

## 9. Änderungsregel

Eine materialisierende dauerhafte Entscheidung wird in derselben Änderung:

1. in diesen Statuten oder ihrem Maschinenmirror festgehalten,
2. in der jeweils betroffenen kanonischen Ebene referenziert,
3. im Handoff/Status anschlussfähig gemacht,
4. durch einen Regressionstest abgesichert, wenn die Regel technisch prüfbar ist.

## 10. Qualitätsmaxime

**Schneller werden bedeutet nicht nachlässiger werden. Mehr Kapazität bedeutet nicht mehr Rauschen. Kontinuierliche Entwicklung bedeutet: Jede nächste Runde muss einen echten wissenschaftlichen, technischen, reproduzierbaren oder governance-seitigen Informationsgewinn erzeugen.**
