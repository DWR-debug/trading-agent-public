"""Evidence-aware research priority and planning forecasts for the dashboard.

This module ranks research allocation, not expected returns. Time ranges are
explicitly low-confidence planning estimates until candidate-specific duration
history can be calibrated. Strategy success probabilities remain null unless
independent cost-aware out-of-sample evidence exists.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ASSESSMENT_VERSION = "2026-10-10.2"
INVENTORY_PATH = "research/candidates/orthogonal_candidate_specs_2026-10-05.json"
ACTIVE_PORTFOLIO_CODES = ("Q104:I19", "Q220", "Q218")

PORTFOLIO_METHODOLOGY = {
    "version": ASSESSMENT_VERSION,
    "purpose": "Active three-candidate research-resource priority only; not a return, alpha, or candidate-performance ranking.",
    "active_candidate_scope": ["Q104:I19", "Q220", "Q218"],
    "dimensions": [
        "economic mechanism distinctiveness and overlap risk",
        "historical public-observation clock / PIT and identity feasibility",
        "source coverage and completeness",
        "cheap falsifiability and cost of the next decisive test",
        "expected useful information gain per unit of compute",
        "current distance to the next evidence-backed gate",
    ],
    "duration_basis": "Low-confidence work-planning ranges based on documented remaining gates and blockers. They are not empirical completion-time forecasts; the current verified candidate-specific duration benchmark count is zero.",
    "success_probability": "Not estimable. No candidate has the required independent, cost-aware out-of-sample evidence and robustness package to support a calibrated strategy-success probability.",
    "promotion_rule": "No dashboard field authorizes performance, holdout selection, ranking by returns, tuning, promotion, orders, or live execution.",
    "review_rule": "Re-estimate after each material receipt and calibrate a gate family only after at least three comparable completed, non-cancelled runs are available.",
}

# Order reflects expected research value per compute and evidence maturity. It is
# deliberately not derived from the observed return in a performance experiment.
A: dict[str, dict[str, Any]] = {
    "Q104:I19": {
        "rank": 1, "tier": "VERY_HIGH", "potential": "Sehr hoch",
        "next_gate": "Vollständige historische 13F-Identitäts-/Receipt-Abdeckung und SEC-Acceptance-Time-Closure; danach den eingefrorenen XBRL-PIT-Compiler speisen.",
        "next_eta": "1–3 Arbeitstage", "pit_eta": "3–7 Arbeitstage",
        "blocker": "Der historische Census muss terminal sein; fehlende Shards und Acceptance-Header müssen gezielt geschlossen werden. Der Compiler und unabhängige Reproduktion bleiben downstream gates.",
        "why": "Reifster Weg zu einem formal prüfbaren Kandidaten: exakte XBRL-Konzepte, bestehende SEC-/PIT-Infrastruktur und deterministische Mutationstests. Der kritische Engpass ist jetzt konkret identifizierbar.",
        "first_falsifier": "Fehlende oder nicht reproduzierbare Security-Identität, nicht geschlossene Acceptance-Zeit oder Concept-/PIT-Mutation muss den Gate fail-closed beenden.",
        "portfolio_action": "FOCUS_NOW",
    },
    "Q220": {
        "rank": 2, "tier": "VERY_HIGH", "potential": "Sehr hoch",
        "next_gate": "As-filed-SEC-Archiv und XBRL-Narrative-/Presentation-Linkage deterministisch einfrieren; Taxonomie- und TextBlock-Mapping über den fixierten Filing-Pool testen.",
        "next_eta": "2–5 Arbeitstage", "pit_eta": "5–10 Arbeitstage",
        "blocker": "Taxonomie-/Schema-Drift und instabiles TextBlock-/Presentation-Mapping; unvollständiges Mapping muss den Kandidaten stoppen.",
        "why": "Klar unterscheidbarer Mechanismus mit historischem SEC-As-filed-Material; relevante Information ist die Repräsentationslücke, nicht generische Länge oder Sentiment.",
        "first_falsifier": "Stabilität bricht auf der eingefrorenen Taxonomie, Future-Text kontaminiert den Prefix oder Länge/Readability erklärt das Signal vollständig.",
        "portfolio_action": "FOCUS_NOW",
    },
    "Q218": {
        "rank": 3, "tier": "VERY_HIGH", "potential": "Hoch, aber unbestätigt",
        "next_gate": "Receipt/code-hash cross-check is already positive: source and event-pair implementation fingerprints match master, the independent PIT receipt references those exact receipts, and the frozen fresh-symbol replication receipt is complete. Do not launch duplicate Q218 work unless a fingerprint or frozen-contract input changes.",
        "next_eta": "bereits erfüllt; 0 zusätzliche Arbeitstage", "pit_eta": "unabhängige PIT-Reproduktion abgeschlossen",
        "blocker": "Keine offene Source/Event/independent-PIT-/Fresh-Symbol-Receipt-Lücke im derzeitigen Codekontext. Breite kostenbereinigte OOS-Evidenz ist weiterhin nicht vorhanden; keine neue Performance-Ausführung, Tuning, Auswahl oder Promotion aus diesem Status ableiten.",
        "why": "Distinct channel-allocation mechanism und abgeschlossene initiale Event-/PIT-/One-shot-Stufen; weiterführende Erfolgsaussage ist nicht zulässig.",
        "first_falsifier": "Channel-label permutation, same-event shuffle oder Erklärung durch Länge/generische Ähnlichkeit hebt den eigenständigen Mechanismus auf.",
        "portfolio_action": "FOCUS_MONITOR",
    },
    "Q221": {
        "rank": 4, "tier": "HIGH_CONDITIONAL", "potential": "Hoch, bedingt",
        "next_gate": "Historische USAspending-Transaktions-/Veröffentlichungsclock und DoD/USACE-Ausnahmen prüfen; Recipient-to-Issuer-Mapping für eine eingefrorene Population fixieren.",
        "next_eta": "3–7 Arbeitstage", "pit_eta": "1–3 Wochen",
        "blocker": "Historische Anwendbarkeit der Public-Clock, agency-spezifische Verzögerungen, Award-vs-Modification-Semantik und Entity-Mapping.",
        "why": "Plausibler Innovations-zu-Procurement-Optionsmechanismus, sofern Information vor künftiger Beschaffung tatsächlich öffentlich war.",
        "first_falsifier": "Nur Award-Größe erklärt den Zustand, zukünftige Production Contracts leaken hinein oder historische Public Visibility ist nicht rekonstruierbar.",
        "portfolio_action": "TOP4",
    },
    "Q219": {
        "rank": 5, "tier": "CONDITIONAL", "potential": "Mittel bis hoch, bedingt",
        "next_gate": "Kurzer, abschließender Free-Data-Breadth-Go/No-Go-Test für historische Einzelaktien-Optionen; nicht bei SPY/QQQ/IWM als breiten Equity-PIT behandeln.",
        "next_eta": "1–3 Arbeitstage bis Go/No-Go", "pit_eta": "5–10 Arbeitstage nur falls Breadth-Gate positiv ist",
        "blocker": "Die bisher verifizierte Q129-Historie belegt nur SPY/QQQ/IWM; Einzeltitel-Historie, Exchange-/Contract-Kalender und strikt nachgelagerter EOD-Zeitpunkt sind offen.",
        "why": "Orthogonaler Cross-Market-Mechanismus; ein früher Source-Breadth-Test hat hohen Informationsgewinn und vermeidet unnötige Vollentwicklung bei strukturellem Datenmangel.",
        "first_falsifier": "Kein reproduzierbarer gratis Einzelaktien-Optionsbestand oder der Effekt kollabiert auf Options-only/Text-only bzw. verletzt den Post-Filing-Clock.",
        "portfolio_action": "TOP4_SOURCE_GO_NO_GO",
    },
    "Q224": {
        "rank": 6, "tier": "HIGH_CONDITIONAL", "potential": "Hoch, mit Datenrisiko",
        "next_gate": "EDGAR-Log-Archive, altes/neues Schema, fehlende/beschädigte Dateien und Filing-to-request URI-Zuordnung für ein festes Zeitfenster auditieren.",
        "next_eta": "3–7 Arbeitstage", "pit_eta": "2–4 Wochen",
        "blocker": "Bekannte Log-Datenlücke Juli 2017–Mai 2020 sowie unvollständige/damaged traffic, Bots/Bulk und Schemawechsel.",
        "why": "Eigenständige Informationsbeschaffungsnachfrage mit starker direkter Literaturmotivation; die nächste Entscheidung ist ein begrenzter Source-Quality-Test.",
        "first_falsifier": "Automatisierter/Bulk-Traffic dominiert, geschlossene historische Fenster ändern sich durch spätere Logs oder Legacy-/Modern-Schema ist nicht semantisch überbrückbar.",
        "portfolio_action": "RESERVE_HIGH_INFORMATION_GAIN",
    },
    "Q228": {
        "rank": 7, "tier": "HIGH_CONDITIONAL", "potential": "Hoch, mit Coverage-Risiko",
        "next_gate": "Historische SEC-Comment-Letter-Population, UPLOAD/CORRESP-Provenienz und Filing-/Review-Cycle-Linkage für einen fixen Issuer-Pool prüfen.",
        "next_eta": "3–7 Arbeitstage", "pit_eta": "1–3 Wochen",
        "blocker": "Selektive SEC-Prüfung, nicht triviale Review-to-Filing-Verknüpfung, öffentlicher Release-Zeitpunkt sowie Amendment-/Closure-Lineage.",
        "why": "Regulatorische Nachfrage und Antwortzustand unterscheiden sich vom bloßen Filing-Umfang; genügend Abstand zu Q195/Q217/Q218 muss nachgewiesen werden.",
        "first_falsifier": "Review-Zyklus kann nicht deterministisch verknüpft werden oder wird vollständig durch Filing-Complexity/Enforcement/Release-Lag erklärt.",
        "portfolio_action": "RESERVE",
    },
    "Q201": {
        "rank": 8, "tier": "MEDIUM_HIGH", "potential": "Mittel bis hoch",
        "next_gate": "ClinicalTrials.gov-Ergebnis-Versionen, posted-time-Semantik und Sponsor-to-Issuer-Mapping an historischen Record-Snapshots auditieren.",
        "next_eta": "2–5 Arbeitstage", "pit_eta": "1–2 Wochen",
        "blocker": "Version-/Revision-Lineage und korrekter erster öffentlicher Ergebniszeitpunkt sind nicht vollständig gesichert.",
        "why": "Receipt-backed source component ist vorhanden; das nächste Problem ist ein klar benannter historischer Clock-/Revision-Gate.",
        "first_falsifier": "Ergebnisstand oder Sponsormapping benötigt nachträgliche Information, die am ursprünglichen Public Boundary nicht vorhanden war.",
        "portfolio_action": "RESERVE",
    },
    "Q204": {
        "rank": 9, "tier": "MEDIUM_HIGH", "potential": "Mittel bis hoch",
        "next_gate": "Pro Eventklasse ersten öffentlichen Beobachtungszeitpunkt, fixe Prozessstufe und Korrektur-/Widerrufs-Lineage rekonstruieren.",
        "next_eta": "2–5 Arbeitstage", "pit_eta": "1–3 Wochen",
        "blocker": "Öffentliche Publikationsclock muss vom latenten Ereignis und späteren Bestätigungen sauber getrennt werden.",
        "why": "Breit wiederverwendbare Informationsankunfts-Hypothese; hohe methodische Relevanz, aber Overlap mit Q218/Q223 muss kontrolliert werden.",
        "first_falsifier": "Nur Kalendertiming/Release-Lag bleibt übrig oder ein späterer Snapshot verändert den damaligen Informationsstand.",
        "portfolio_action": "RESERVE",
    },
    "Q203": {
        "rank": 10, "tier": "MEDIUM", "potential": "Mittel",
        "next_gate": "Historischen Award-/Modification-Public-Boundary mit eingefrorenem Pre-Event-Finanzierungszustand und Recipient-/Issuer-Mapping verbinden.",
        "next_eta": "3–7 Arbeitstage", "pit_eta": "1–3 Wochen",
        "blocker": "USASpending-Revision-/Public-Clock und stabile, vor Ereignis eingefrorene Unternehmensbeziehung.",
        "why": "Interessanter Procurement×Financing-Mechanismus, derzeit aber geringerer marginaler Informationsgewinn als Q221 und verwandte Quellen.",
        "first_falsifier": "Finanzierungsconstraint oder Recipient-Mapping nutzt Post-Event-Vintage bzw. zukünftige Award-Information.",
        "portfolio_action": "RESERVE",
    },
    "Q202": {
        "rank": 11, "tier": "MEDIUM_HIGH", "potential": "Mittel bis hoch",
        "next_gate": "Historische Record-Versionen und Meldeschluss-/Extension-/Certification-Lineage für den festen Sponsor-/Issuer-Pool einfrieren.",
        "next_eta": "3–7 Arbeitstage", "pit_eta": "1–3 Wochen",
        "blocker": "Anwendbarkeit der Meldefrist, Zertifizierungs-/Extension-Zustand und historische Versionen müssen am jeweiligen Public Boundary bewiesen werden.",
        "why": "Source-ready administrative-state-Kandidat mit falsifizierbarer Deadline-/Missing-State-Definition; PIT ist noch nicht bestätigt.",
        "first_falsifier": "Historischer damaliger Status lässt sich nicht rekonstruieren oder nachträgliche Result-Versionen ändern den Event-Zustand.",
        "portfolio_action": "RESERVE",
    },
    "Q227": {
        "rank": 12, "family": "SEC_FOIA_ACQUISITION", "tier": "MEDIUM_HIGH", "potential": "Mittel bis hoch",
        "next_gate": "Mit Q231 zu einem einzigen SEC-FOIA-Kontrakt konsolidieren; Monats-/Jahres-Log-Publication, Requester-Taxonomie und deterministische Ziel-Mappings testen.",
        "next_eta": "2–5 Arbeitstage", "pit_eta": "1–3 Wochen nach Konsolidierung",
        "blocker": "Latenter Request-Zeitpunkt ist nicht der handelbare Public Boundary; Historie, Beschreibungs-Mapping, Bulk-Requester und Redaktions-/Revision-Lineage.",
        "why": "Eigenständige gezielte Informationsbeschaffung, aber Q227 und Q231 sind aktuelle near-duplicates. Ein gemeinsamer Vertrag spart redundante Arbeit.",
        "first_falsifier": "Request-Beschreibung erfordert Hindsight, öffentliche Release-Clock ist nicht rekonstruierbar oder Identität kann nicht deterministisch gemappt werden.",
        "portfolio_action": "CONSOLIDATE_WITH_Q231",
    },
    "Q231": {
        "rank": 12, "family": "SEC_FOIA_ACQUISITION", "tier": "MEDIUM_HIGH", "potential": "Mittel bis hoch",
        "next_gate": "Keinen separaten Compute-Lauf starten; in den gemeinsamen Q227/Q231-Kontrakt und dessen Go/No-Go integrieren.",
        "next_eta": "Gemeinsamer Q227/Q231-Gate", "pit_eta": "Gemeinsamer Q227/Q231-Gate",
        "blocker": "Duplikat zur Q227-Informationsbeschaffungsfamilie; separates Workpack erhöht Konvergenz- und Multiple-Trial-Risiko ohne nachgewiesene Orthogonalität.",
        "why": "Gleiche zugrunde liegende Quelle und eng verwandter zweistufiger Public-Clock-Mechanismus. Zuerst separierbare zusätzliche Information beweisen.",
        "first_falsifier": "Keine unterscheidbare kontraktierbare Feature-Familie gegenüber Q227 nach fixiertem Taxonomie-/Clock-Schema.",
        "portfolio_action": "DO_NOT_DISPATCH_SEPARATELY",
    },
    "Q229": {
        "rank": 13, "tier": "MEDIUM", "potential": "Mittel",
        "next_gate": "CFPB-Archiv-/Veröffentlichungsselektion, Beschwerde-zu-Response-Lineage und eingefrorenes Company-to-Issuer-Mapping für ein fixes Panel prüfen.",
        "next_eta": "3–7 Arbeitstage", "pit_eta": "1–3 Wochen",
        "blocker": "Publikation hängt an Weiterleitung/Antwort oder 15-Tage-Grenze; Response- und Complaint-Datum dürfen nicht verwechselt werden.",
        "why": "Ein Prozess-/Response-Zustand ist aussagekräftiger als rohe Beschwerdezahlen; Signifikanz hängt an Mapping und Selektionskontrolle.",
        "first_falsifier": "Nur Firmengröße/Rohzählung/Publikationsverzögerung trägt die Variation oder Antwortzustand bringt keine zusätzliche Struktur.",
        "portfolio_action": "RESERVE",
    },
    "Q199": {
        "rank": 14, "tier": "MEDIUM", "potential": "Mittel",
        "next_gate": "Historische USPTO-Publication-State-Archive, Assignee-/Technologie-Exposure und erste öffentliche Publikationsgrenze konsistent aufbauen.",
        "next_eta": "2–5 Arbeitstage", "pit_eta": "1–3 Wochen",
        "blocker": "Assignee-/Issuer-Identität, Technologie-Exposure und Revision-/Correction-Lineage.",
        "why": "Historischer Source-Component ist vorhanden; die unabhängige Wissens-/Patent-Publication-Clock bleibt zu schließen.",
        "first_falsifier": "Nur Patentzahl oder nachträgliche assignee mapping erklärt den Zustand; first-publication boundary ist nicht reproduzierbar.",
        "portfolio_action": "RESERVE",
    },
    "Q197": {
        "rank": 15, "tier": "MEDIUM", "potential": "Mittel",
        "next_gate": "Historischen USASpending-Award-Public-Boundary, vorab eingefrorenes Relationship-Network und transaction-amendment lineage abgleichen.",
        "next_eta": "2–5 Arbeitstage", "pit_eta": "1–3 Wochen",
        "blocker": "Award-/Modification-/Correction-Uhr und Pre-Event-Netzwerk-Identität.",
        "why": "Öffentlicher Government-Demand-Source-Component ist vorhanden; der Netzwerk-Transmissionspfad ist die eigentliche offene Hypothese.",
        "first_falsifier": "Nur direkte Award-Größe erklärt Variation oder Netzwerk/Issuer-Link verwendet zukünftige Beziehungen.",
        "portfolio_action": "RESERVE",
    },
    "Q222": {
        "rank": 16, "tier": "MEDIUM_HIGH", "potential": "Mittel bis hoch, mit Orthogonalitätsrisiko",
        "next_gate": "Historische öffentliche Implementierungs-Belege mit eigenem Veröffentlichungszeitpunkt und reproduzierbarer Verbindung zum vorab fixierten SEC-Technologie-Claim kontraktieren.",
        "next_eta": "3–7 Arbeitstage", "pit_eta": "2–4 Wochen",
        "blocker": "Externes Implementierungs-PIT und Taxonomie/Entity-Mapping; muss von Q220/Q217/Q211 getrennt werden.",
        "why": "Credibility gap ist konzeptionell eigenständig, sofern die externe Action-Evidenz historisch und ohne Hindsight messbar ist.",
        "first_falsifier": "Q220-Repräsentationslücke oder Keyword-/Längenmaß erklärt die Konstruktion vollständig; Action-Timestamp ist nicht belegbar.",
        "portfolio_action": "RESERVE",
    },
    "Q215": {
        "rank": 17, "tier": "MEDIUM", "potential": "Mittel",
        "next_gate": "Beide öffentlichen Kanäle, Event-Identität und Veröffentlichungsuhren als vollständige historische Zweikanalpopulation einfrieren.",
        "next_eta": "3–7 Arbeitstage", "pit_eta": "1–3 Wochen",
        "blocker": "Zweikanal-Linkage, erste öffentliche Beobachtung beider Quellen und identitätsstabile historische Zuordnung.",
        "why": "Nützlich als Mess-/Observability-Konzept; muss im Vergleich zu spezifischeren Kanalkandidaten inkrementellen Informationsgewinn zeigen.",
        "first_falsifier": "Eine einzelne Quelle erklärt vollständig den Zustand oder Linkage braucht Hindsight.",
        "portfolio_action": "RESERVE",
    },
    "Q216": {
        "rank": 18, "tier": "MEDIUM_RISK_STATE", "potential": "Mittel (Risikozustand)",
        "next_gate": "Vollständiges historisches Vintage-Panel, erste Veröffentlichungs-Semantik und eingefrorene Exposure-Mapping-Regeln für einen fixen Markt-/Issuer-Pool prüfen.",
        "next_eta": "2–5 Arbeitstage", "pit_eta": "1–3 Wochen",
        "blocker": "Vintages und Revisionen können sonst späteren Datenstand rückwirkend in den historischen Zustand tragen.",
        "why": "Kann als Risikomessung nützlich sein; nicht mit Alpha oder einem Return-Signal gleichsetzen.",
        "first_falsifier": "Revisionen verändern den historischen Prefix oder das Ergebnis ist nicht von trivialen Macro-Leveln zu trennen.",
        "portfolio_action": "RISK_STATE_ONLY",
    },
    "Q217": {
        "rank": 19, "tier": "MEDIUM", "potential": "Mittel, derzeit gebündelt",
        "next_gate": "Nur einen Komponenten-/Orthogonalitätsvergleich gegen Q220 und Q224 ausführen; kein eigenständiges Voll-Workpack bis Separation besteht.",
        "next_eta": "2–5 Arbeitstage", "pit_eta": "1–3 Wochen nur wenn separierbar",
        "blocker": "Starke Überschneidung mit Repräsentationslücke, EDGAR-Akquisitionsintensität und allgemeiner Filing-Complexity.",
        "why": "Literaturmotivierter Mechanismus, aber marginaler Wert muss gegen bereits spezifischere Komponenten gemessen werden.",
        "first_falsifier": "Mechanismus kollabiert auf Länge, Readability, Q220 oder Q224.",
        "portfolio_action": "ORTHOGONALITY_FIRST",
    },
    "Q196": {
        "rank": 20, "tier": "MEDIUM", "potential": "Mittel",
        "next_gate": "Patent citation provenance/vintage, früheste öffentliche Citation und eingefrorene assignee-/issuer exposure für den festen Panel prüfen.",
        "next_eta": "2–5 Arbeitstage", "pit_eta": "1–3 Wochen",
        "blocker": "Korrekte öffentliche Citation-Uhr und historische, nicht nachträglich korrigierte Patent-Identität.",
        "why": "Weniger untersuchter Wissensflusskanal, aber die Public-Clock- und Patent-Lineage-Schließung ist noch nötig.",
        "first_falsifier": "Später aktualisierte Citation-Datei ändert den historischen Stand oder die Information kommt aus einem erst späteren Patentereignis.",
        "portfolio_action": "RESERVE",
    },
    "Q205": {
        "rank": 21, "tier": "MEDIUM", "potential": "Mittel",
        "next_gate": "NLRB-Zertifizierungs- und Arbeitskampf-Ereignis-Population sowie früheste öffentliche Uhr und Unternehmenszuordnung vollständig abdecken.",
        "next_eta": "3–7 Arbeitstage", "pit_eta": "1–3 Wochen",
        "blocker": "Event coverage, historischer Firmen-/Standort-to-Issuer-Link und selektive Eskalation.",
        "why": "Klares diskretes Ereignis, aber kleine Population und Unternehmenszuordnung können die nutzbare Stichprobe begrenzen.",
        "first_falsifier": "Ereignis-Population ist stark selektiv/unvollständig oder Firmen-Link benötigt Hindsight.",
        "portfolio_action": "RESERVE",
    },
    "Q194": {
        "rank": 22, "tier": "MEDIUM", "potential": "Mittel",
        "next_gate": "Historischen Produkt-/Wirkstoff-Engpass, Substitute/therapeutic-equivalence graph und Hersteller-Issuer-Zuordnung für festen Produktpool abgleichen.",
        "next_eta": "3–7 Arbeitstage", "pit_eta": "1–3 Wochen",
        "blocker": "Substitutionsgraph und Manufacturer/product-to-issuer mapping müssen zum damaligen öffentlichen Zustand eingefroren werden.",
        "why": "Potenziell klare reale Transmissionskette, aber Produkt-/Zulassungs-/Hersteller-Identität erhöht die historische Datenarbeit.",
        "first_falsifier": "Substitute sind nicht ex ante bestimmbar oder der Exposure-Graph wird rückwirkend aus späterer Nutzung gebaut.",
        "portfolio_action": "RESERVE",
    },
    "Q195": {
        "rank": 23, "tier": "MEDIUM", "potential": "Mittel",
        "next_gate": "Historische Inspection-to-enforcement states, erste öffentliche Veröffentlichungsgrenze und Korrektur-/Closure-Lineage erfassen.",
        "next_eta": "3–7 Arbeitstage", "pit_eta": "1–3 Wochen",
        "blocker": "Selektive regulatorische Kontrolle, ungleiche Fallverläufe und Enforcement-/Disclosure-Overlap.",
        "why": "Mechanismus ist diskret und interpretierbar, aber Auswahl in die Prüfung ist endogen und muss früh falsifiziert werden.",
        "first_falsifier": "Ergebnis wird vollständig durch Enforcement, issuer size oder Q228 Regulatory-Scrutiny erklärt.",
        "portfolio_action": "RESERVE",
    },
    "Q230": {
        "rank": 24, "tier": "BLOCKED_SOURCE", "potential": "Konzeptionell hoch, derzeit blockiert",
        "next_gate": "Kurzer Go/No-Go nur zu kostenloser historischer FINRA TRACE-Abdeckung, Bond-Security-Master und PIT-stabiler Issuer-Verknüpfung.",
        "next_eta": "1–2 Arbeitstage für kostenfreien Source-Go/No-Go", "pit_eta": "2–4 Wochen nur bei positivem kostenfreiem Daten-Gate",
        "blocker": "Historische kostenlose TRACE-Abdeckung und stabile Bond-/Issuer-Zuordnung nicht belegt. Bezahlte Daten sind ausgeschlossen.",
        "why": "Ökonomisch interessant, aber ein großer Teil des Nutzenversprechens hängt an Feldern/History, die kostenlos und revisionsfest erst verifiziert werden müssen.",
        "first_falsifier": "Kostenfreie historische Breite/Required fields fehlen oder PIT-stabiles Bond-to-Issuer-Mapping ist nicht reproduzierbar.",
        "portfolio_action": "BLOCKED_UNTIL_FREE_SOURCE",
    },
}

def _code_aliases(code: str) -> set[str]:
    value = str(code or "")
    aliases = {value}
    if value.startswith("Q"):
        aliases.add(value[1:])
    if value.isdigit():
        aliases.add("Q" + value)
    if value == "Q104:I19":
        aliases.add("104")
    return aliases


def _current_state_index(evidence: dict[str, Any]) -> dict[str, dict[str, Any]]:
    root = evidence.get("active_research_registry", {})
    if not isinstance(root, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for key in ("active_design_families", "active_trials"):
        rows = root.get(key, [])
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict) or not row.get("code"):
                continue
            code = str(row["code"])
            for alias in _code_aliases(code):
                # active trials are read after design families and override their
                # older broad design state for the same candidate.
                out[alias] = row
    return out


def build_candidate_portfolio(
    root: Path,
    evidence: dict[str, Any],
    candidate_progress: Any = None,
) -> list[dict[str, Any]]:
    """Build a status-enriched portfolio for the active three-candidate focus from the frozen inventory."""
    inventory = json.loads((root / INVENTORY_PATH).read_text(encoding="utf-8"))
    specs = {
        str(row.get("id")): row
        for row in inventory.get("candidates", [])
        if isinstance(row, dict) and row.get("id")
    }
    status_index = _current_state_index(evidence)
    progress_index: dict[str, dict[str, Any]] = {}
    progress_rows: Any = candidate_progress
    if isinstance(candidate_progress, dict):
        nested = candidate_progress.get("candidates")
        if isinstance(nested, dict):
            progress_rows = [
                {"code": str(code), **row}
                for code, row in nested.items()
                if isinstance(row, dict)
            ]
        elif isinstance(candidate_progress.get("items"), list):
            progress_rows = candidate_progress["items"]
        else:
            progress_rows = list(candidate_progress.values())
    if isinstance(progress_rows, (list, tuple)):
        for row in progress_rows:
            if isinstance(row, dict) and row.get("code"):
                progress_index[str(row["code"])] = row

    portfolio = []
    for code in ACTIVE_PORTFOLIO_CODES:
        assessment = A[code]
        spec = specs.get(code, {})
        aliases = _code_aliases(code)
        current = next((status_index[a] for a in aliases if a in status_index), {})
        live = progress_index.get(code, {})
        next_gate = assessment["next_gate"]
        current_milestone = str(live.get("current_milestone") or "")
        if code in {"Q104:I19", "Q220", "Q218"} and current_milestone:
            if code != "Q218" or str(live.get("current_milestone_status") or "").lower() not in {"complete", "completed"}:
                next_gate = current_milestone
            else:
                next_gate = str(live.get("next_gate") or "Q218 current-context receipts complete; no duplicate workpack needed")
        state = str(
            live.get("current_milestone_status")
            or current.get("state")
            or (current.get("next_gate") if current else "")
            or "DESIGN_ONLY / NOT RECORDED"
        )
        if code == "Q104:I19":
            parent = status_index.get("104", {})
            contract = parent.get("candidate_contracts", {}).get("Q104:I19", {}) if isinstance(parent.get("candidate_contracts"), dict) else {}
            state = str(live.get("current_milestone_status") or contract.get("state") or parent.get("state") or state)
        portfolio.append({
            "code": code,
            "name": str(spec.get("name") or ("Institutional demand × accrual state" if code == "Q104:I19" else code)),
            "mechanism": str(spec.get("mechanism") or "Fixed-concept accrual state × institutional ownership transitions with acceptance-time PIT."),
            "event_clock": str(spec.get("event_clock") or "SEC acceptance timestamp; filing prefix frozen at the public boundary."),
            "source_gates": list(spec.get("gates", [])),
            "first_cheap_falsifiers": list(spec.get("cheap_falsifiers", []))[:4],
            "rank": int(assessment["rank"]),
            "tier": str(assessment["tier"]),
            "potential": str(assessment["potential"]),
            "current_state": state,
            "next_gate": next_gate,
            "next_gate_eta": str(assessment["next_eta"]),
            "independent_pit_eta": str(assessment["pit_eta"]),
            "blocker": str(assessment["blocker"]),
            "why": str(assessment["why"]),
            "first_falsifier": str(assessment["first_falsifier"]),
            "portfolio_action": str(assessment["portfolio_action"]),
            "family": str(assessment.get("family") or code),
            "separate_workpack_allowed": assessment.get("portfolio_action") != "DO_NOT_DISPATCH_SEPARATELY",
            "duration_estimate_confidence": "LOW_PLANNING_RANGE",
            "strategy_success_probability": None,
            "strategy_success_probability_status": "NOT_ESTIMABLE",
        })
    return sorted(portfolio, key=lambda x: (x["rank"], x["code"]))

