# Research OS — Architecture and External Capability Frontier

Stand: 2026-09-30

## Zweck

Das Research OS ist die Betriebsschicht über den einzelnen Trading-Agent-Strategien. Es verbindet Datenquellen, Point-in-Time-Governance, deterministische Forschung, Agenten, Sandbox-Ausführung, Ressourcensteuerung und die Evidence-Kette.

Es ist **keine Trading-Strategie** und erzeugt selbst keine Performance-Evidence.

## Architektur

`Source Fabric`
→ `Evidence Bus`
→ `Research Compiler`
→ `Agent Mesh`
→ `Sandbox / Execution Boundary`
→ `Trial Ledger / Decision State`

### Source Fabric

Jede Quelle besitzt ein Capability-Profil:

- Herkunft und Verantwortlicher
- Zugriff und mögliche Authentifizierung
- Historientiefe
- Veröffentlichungs-/Verfügbarkeitszeit
- Änderungs- und Revisionsverhalten
- PIT-Eignung
- Rate-/Nutzungsgrenzen
- zulässiger Einsatz: discovery, feasibility oder formal research

Eine Quelle darf nicht still durch eine andere ersetzt werden. Jede Substitution erzeugt einen neuen Source Receipt.

### Evidence Bus

Jeder Datensatz und jedes abgeleitete Event-Objekt soll mindestens folgende Metadaten tragen:

`source_id`, `source_url`, `retrieved_at`, `published_at` bzw. `available_at`, `release_id`, `parser_version`, `raw_fingerprint`, `normalized_fingerprint`, `pit_status`.

Die entscheidende Regel lautet:

> Kein numerisches Signal wird als wissenschaftliche Information behandelt, bevor geklärt ist, wann diese Information tatsächlich verfügbar war.

### Research Compiler

Aus einem eingefrorenen Mechanismus wird deterministisch:

1. Preregistration
2. Coverage Contract
3. PIT/Leakage Contract
4. Input Bundle
5. Performance Authorization Request

Die Performance-Stufe bleibt ein separater Zustand.

### Agent Mesh

AI-Agenten sind spezialisierte Hilfsarbeiter:

- Hypothesenbildung
- adversariales Review
- Dokument-/Quellensuche
- QA und Codeprüfung
- Gegenargumente
- Synthese

Agenten dürfen keine wissenschaftliche Evidenz allein erzeugen und keine Performance-Autorisierung selbst erteilen.

Die aktuelle lokale Queue bleibt dafür der kanonische Kontrollpunkt. A2A und MCP sind mögliche Interoperabilitätsschichten, nicht Ersatz für unsere Governance.

### Sandbox / Execution Boundary

Die externe Agent-Landschaft zeigt einen klaren Trend zu policy-first Ausführungsgrenzen. NVIDIA OpenShell trennt Supervisor und Sandbox, erzwingt Dateisystem-, Prozess- und Netzwerkregeln und bindet Credentials an erlaubte Endpunkte. Diese Architektur ist für unser System als Sicherheitsreferenz interessant, aber eine direkte Übernahme ist **nicht erforderlich**.

Für Windows bleibt WSL2 ein möglicher Evaluationspfad; ein Produktivumbau erfolgt erst nach lokaler Authentifizierungs- und Sicherheitsprüfung.

### Decision State

Die letzte Instanz bleibt:

`source receipts → preregistration → coverage/PIT → input freeze → authorization → one-shot performance → immutable reconciliation → Trial Ledger`

## Neue externe Möglichkeiten

### 1. SEC/FINRA Short-Flow-Lattice

Es existieren mehrere unabhängige öffentliche Informationskanäle:

- SEC Fails-to-Deliver
- FINRA Short Interest
- FINRA Reg SHO Daily Short Sale Volume
- FINRA Threshold List

Diese Kanäle haben unterschiedliche Frequenzen und Zeitsemantiken. Die spannende Forschungsfrage ist deshalb nicht „short interest = Signal“, sondern ob **mehrere unabhängige Crowding-/Settlement-Mechanismen** als Zustandswechsel zusammenpassen.

Erste Stufe: Source/PIT-Feasibility. Noch keine Performance-Annahme.

### 2. Macro Vintage OS

ALFRED/FRED liefert explizite Real-Time-Periods und Vintage-Dates. Damit können Makrodaten so behandelt werden, wie sie zu einem historischen Zeitpunkt bekannt waren, statt mit heute revidierten Werten. Das ist strukturell näher an echtem PIT-Research als ein gewöhnlicher Macro-Download.

Kombinierbare Quellen:

- FRED/ALFRED
- BLS
- EIA
- BIS
- Treasury Fiscal Data

Erste Forschungsform: regime/event-state features, nicht sofort Preisprognosen.

### 3. Retail-Attention Layer

Nasdaq Data Link dokumentiert mit RTAT10 einen kostenlosen Datensatz für die täglichen Top-10-Titel nach Retail-Aktivität. GDELT ergänzt breit angelegte News-/Event-Signale. SEC-Filing-Bursts liefern einen dritten, regulatorisch verankerten Aufmerksamkeitssensor.

Interessant ist hier die **Konvergenz unabhängiger Aufmerksamkeitssensoren**, nicht ein einzelner Sentiment-Score.

### 4. Agent Capability OS

Das Research OS kann selbst capability-driven werden:

- MCP für Tool-/Resource-Verträge
- A2A für spezialisierte Remote-Agenten
- OpenHands als optionaler Agent-Workspace
- OpenShell als Sandbox-/Policy-Referenz

Dabei bleibt unser eigenes Control Plane kleiner und deterministischer als ein allgemeines Agent-Framework.

## Harte Leitplanken

- Keine bezahlte API wird zur notwendigen Voraussetzung.
- Keine proprietäre Quelle wird still als „public“ behandelt.
- Keine historische Performance wird aus einer aktuellen, revidierten Datenansicht rekonstruiert, wenn eine Vintage-/Release-Semantik nötig ist.
- Kein Agent darf aus einer Exploration automatisch einen Performance-Run machen.
- Keine Holdout-Daten dürfen in Discovery oder Auswahl gelangen.
- Jede Quelle bekommt einen eigenen Provenance Fingerprint.
- Fällt eine Quelle aus, wird die Spur blockiert oder explizit auf eine separate Ersatzquelle umregistriert.

## Priorisierte OS-Ausbauspuren

**A — Evidence Bus:** ein einheitliches Receipt-Schema für alle externen Quellen.

**B — Source Capability Registry:** maschinenlesbarer Katalog aus `research/governance/research_os_source_registry_2026_09_30.json`.

**C — Short-Flow Convergence:** SEC/FINRA als erster alternativer Datenverbund.

**D — Macro Vintage Engine:** Release-/Vintage-aware Features über ALFRED/BLS/EIA/BIS.

**E — Agent Protocol Adapter:** optionaler MCP/A2A-Randadapter, ohne den deterministischen Kern aufzugeben.

**F — Policy Sandbox Evaluation:** OpenShell-inspirierte Read/Write/Network-Policies für lokale Agenten, zunächst nur als sicherer Engineering-Test.

## Externe Referenzen

- SEC EDGAR APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- SEC Fails-to-Deliver: https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data
- FINRA Short Interest: https://www.finra.org/finra-data/browse-catalog/equity-short-interest
- FINRA Reg SHO Daily Short Sale Volume: https://developer.finra.org/docs/api-explorer/query_api-equity-reg_sho_daily_short_sale_volume
- FINRA Threshold List: https://developer.finra.org/docs
- CFTC COT: https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
- FRED/ALFRED Real-Time Periods: https://fred.stlouisfed.org/docs/api/fred/realtime_period.html
- EIA API: https://www.eia.gov/opendata/documentation.php
- Treasury Fiscal Data: https://fiscaldata.treasury.gov/datasets/treasury-securities-auctions-data/
- BIS Stats API: https://stats.bis.org/api-doc/v2/
- Nasdaq Data Link RTAT: https://data.nasdaq.com/databases/RTAT/documentation
- GDELT DOC API: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
- MCP 2026-07-28: https://blog.modelcontextprotocol.io/posts/2026-07-28/
- A2A: https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/
- OpenHands SDK: https://github.com/OpenHands/software-agent-sdk
- NVIDIA OpenShell: https://github.com/NVIDIA/OpenShell/
