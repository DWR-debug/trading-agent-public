# Trading Agent — Copilot Repository Instructions

## Rollenmodell

Der primäre Forschungsagent koordiniert die Gesamtforschung. Copilot ist ein nachgeordneter Spezialagent.

Copilot unterstützt mit Hypothesen, Gegenhypothesen, Mechanismensynthese und Forschungsdesign. Er besitzt keine Entscheidungshoheit über Research, Präregistrierung oder Promotion.

## Harte Grenzen

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- automatic_promotion=False
- kein Holdout-basierter Hypothesensieg
- keine rückwirkende Trial-Optimierung
- keine Änderung der Research-Gates
- keine geheime Parameter-, Asset- oder Threshold-Suche

## Kostenregel

Kostenfreie Agentenressourcen sind für Hypothesenbildung und Forschungsdesign reserviert. Deterministische Berechnung bleibt lokal. Bezahlte API-Nutzung darf nicht aktiviert werden.

## Evidenzregel

Agentenoutput ist Ideenmaterial, keine Evidenz. Formale Forschung benötigt eine neue Präregistrierung, Coverage-Preflight und unveränderte Evidence-Gates.


## Ressourcenrouting

Für dieses Projekt gilt docs/GITHUB_FREE_RESOURCE_OPERATING_MODEL.md.

Copilot Cloud Agent ist ein nachgeordneter Worker. Bevorzuge klar abgegrenzte Engineering-, Test-, Dokumentations- und technische Reviewaufgaben. Ziel pro Session sind 15–45 Minuten; die GitHub-Obergrenze von 59 Minuten ist kein normales Arbeitsbudget.

Delegiere keine finale Research-Entscheidung, Holdout-Auswahl, Parameter-/Asset-/Horizon-Selektion, Gate-Änderung oder Promotionentscheidung. Agentenoutput ist niemals selbst Evidence.

Paid usage bleibt verboten. Cloud Agent darf nur verwendet werden, wenn die Funktion im Account bereits ohne Zusatzkosten verfügbar ist.