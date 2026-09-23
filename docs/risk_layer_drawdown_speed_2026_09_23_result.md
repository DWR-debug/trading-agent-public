# Risk-Layer-Drawdown-Speed — Ergebnis 2026-09-23

## Fragestellung

Geprüft wurde, ob die unveränderte 63-Session-/10%-Realized-Volatility-
Risikosteuerung bei schnellen maximalen Drawdown-Episoden systematisch später
de-risked als bei langsamen Episoden.

Auswertung ausschließlich der fünf festen Research-Rolling-Fenster in jedem
der vier unabhängigen Validierungssets: 20 Research-Fenster insgesamt.

## Feste Definitionen

- Rapid: maximale Drawdown-Episode <= 31 Sessions (floor(63/2)).
- Slow: > 31 Sessions.
- Delayed: erste De-Risking-Session >= 2 Drawdown-Tage nach Episodenbeginn
  oder kein De-Risking bis zum Trough.
- Onset-active: Scale < 1,0 am ersten Drawdown-Tag.

## Ergebnis je Validierung

| Validierung | Rapid Episoden | Rapid delayed | Slow Episoden | Slow delayed | Rapid onset-active | Slow onset-active |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1/1 | 4 | 3/4 | 0/1 | 1/4 |
| 2 | 0 | — | 5 | 1/5 | — | 3/5 |
| 3 | 2 | 2/2 | 3 | 2/3 | 0/2 | 1/3 |
| 4 | 1 | 1/1 | 4 | 3/4 | 0/1 | 1/4 |

Die präregistrierte Replikationsregel wird erreicht:

- Rapid hat eine höhere Delayed-or-Never-Rate als Slow in 3/4 Datensätzen.
- Rapid ist in 4/4 Datensätzen am Episodenbeginn seltener bereits de-risked.

Entscheidungsbefund: replicated_rapid_drawdown_onset_lag.

## Detailbefund

Die beiden schnellsten maximalen Episoden im ersten und vierten Validierungssatz
lagen im Februar/März 2020 und zeigten De-Risking erst nach 2 bzw. 3 Drawdown-Tagen.
Im dritten Validierungssatz hatten beide Rapid-Episoden ebenfalls keine aktive
De-Risking-Position am ersten Drawdown-Tag; die Verzögerungen betrugen 9 Tage bzw.
keine Aktivierung vor dem Trough.

Der Befund ist weiterhin deskriptiv. Er beweist keine Kausalität und rechtfertigt
noch keine Produktionsänderung.

## Konsequenz

Die präregistrierte nächste Forschungsfrage ist nun eng definiert: Kann eine
halbierte Risk-Layer-Schätzperiode von 31 statt 63 Sessions bei unverändertem
10%-Volatilitätsziel die Rapid-Drawdown-Onset-Unterdeckung im Research reduzieren,
ohne dass die langfristigen Risiko-/Rolling-Eigenschaften unvertretbar verschlechtert
werden?

Dies wird als einzelne Fixed-Hypothesis-Ablation gegen den bestehenden 63-Session
Control durchgeführt. Es werden keine Zwischenwerte optimiert und der Holdout
bleibt bis zu einer späteren unabhängigen Validierung unberührt.

## Provenienz

- PR #47, Research: rapid versus slow drawdown onset diagnosis
- Run: `35869892043`
- Artifact: `10754138069`
- Artifact-Digest: `sha256:8d5f0416c8c3e4f85b19c2609e2e7fb6a4b3c2f4f988aa13ab9149765db474f6`
- Ergebnis-Fingerprint: `c62f63b28a3a3cce86496d3919d02ef390f1babfc0fbf1c28894db2eb24cf81a`
- Volltests: bestanden
- Paper-only Safety: bestanden

## Sicherheitsvertrag

- `PAPER_ONLY=True`
- `LIVE_TRADING_ENABLED=False`
- keine Orders
- keine Produktionsänderung
- Holdout nicht zur Auswahl verwendet