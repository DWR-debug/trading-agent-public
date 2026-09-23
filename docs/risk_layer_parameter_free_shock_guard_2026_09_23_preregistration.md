# Parameter-Free Shock Guard — Pre-Registration 2026-09-23

## Forschungsfrage

Die 31-vs-63-Ablation zeigte, dass die beobachtete Rapid-Drawdown-Latenz nicht
universell durch die Länge des 63-Session-Fensters erklärt wird. Diese einzelne
Intervention prüft deshalb eine andere, direkt aus dem bestehenden Volatilitätsziel
abgeleitete Reaktionslogik:

effective_vol = max(trailing_63_session_realized_vol,
                    abs(previous_unscaled_portfolio_return) * sqrt(252))

Die Intervention ergänzt keinen frei gewählten Schwellwert. Der Ein-Tages-
Shock-Term ist die annualisierte Volatilität, die aus der unmittelbar vorherigen
beobachteten Portfolio-Rendite folgt; dieselbe 252er Annualisierung wird bereits
im bestehenden Risk-Layer verwendet.

## Fixierte Intervention

- Control: bestehendes 63-Session-/10%-Volatility-Budget
- Intervention: max(63-Session-vol, Ein-Tages-Shock-vol)
- gleicher 10%-Zielwert
- identische De-Risk-only-Semantik
- identische Signale, 50/50-Gewichte, PIT-Semantik und Kosten
- keine weiteren Shock-Faktoren und keine weiteren Varianten

## Datenbasis

Nur die vier vollständig symbol-disjunkten Validierungsartefakte werden verwendet:

- Run 35865847394 / Artifact 10751817990
- Run 35839443616 / Artifact 10740188093
- Run 35851876264 / Artifact 10745697729
- Run 35867637587 / Artifact 10753545703

Pro Datensatz werden nur die fünf bereits definierten Research-Rolling-Fenster
und insgesamt 2.798 Research-Returns betrachtet.

Der 700-Return-Holdout wird weder berichtet noch für Auswahl oder Entscheidung
verwendet.

## Vorab definierte Erfolgskriterien

Timing verbessert sich nur, wenn beide Kriterien in mindestens 3 von 4
Validierungssets verbessert werden:

1. Rapid-Delayed-or-Never-Rate sinkt.
2. Rapid-Onset-Active-Rate steigt.

Zusätzlich darf die Intervention in mindestens 3 von 4 Sets beim Research-
Drawdown nicht schlechter sein und in mindestens 3 von 4 Sets beim
Research-Rolling-Profit-Factor nicht schlechter sein.

## Entscheidungsregel

- Alle vier Bedingungen >=3/4: fünfte unabhängige Validierung mit derselben
  fixierten Shock-Guard-Architektur zulässig.
- Timing >=3/4, aber Risiko-Kriterien nicht ausreichend: Research-Trade-off;
  keine fünfte Validierung und keine Produktionseinführung.
- Timing nicht in >=3/4: Hypothese nicht unterstützt.

Kein Ergebnis darf nachträglich die Definition oder die Schwelle ändern.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine Parameteroptimierung
- keine Asset-Auswahl
- keine Gate-Änderung
- keine Produktionsmutation
- keine Orders