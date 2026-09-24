undefined

## Aktueller Checkpoint — Trial 030 Sleeve Volatility Parity Confirmation — 2026-09-24

Trial T-2026-09-24-030 wurde vollständig auf `DWR-debug/trading-agent-public` ausgeführt und als **NO_SUPPORT / archived_rejected** abgeschlossen.

### Technischer Nachweis

- Coverage-Preflight: `36040186007`
- Research-Workflow: `36040997311`
- Artifact: `10825679094`
- Artifact-SHA256: `sha256:cc46dfadb3581fab21012b651b857b32e06a43dc37399d45479423da899f2191`
- Report-Fingerprint: `26cc96a1d7210a97443016f5374fccc2e1c466ce2eb1f6859ca778c9a3eefabe`
- Manifest-Fingerprint: `9ef4c9fa58e6a8a573d0836379572d7a441a2fb5300fc4eca33155b2059cf224`
- 3.498 gemeinsame PIT-Returns
- 2.798 Research / 700 Holdout
- vollständige Vorprüfungen und Ergebnisintegrität grün
- keine Orders

### Befund

Die feste monatliche inverse-Volatilitäts-Parität zwischen den beiden Sleeves verschlechtert im neuen Datensatz Research-Return, Research-DD, Research-PF, Rolling-PF und durchschnittlichen Rolling-DD. Holdout verbessert sich nur marginal.

### Konsequenz

Keine weitere Risk-Parity-/Volatility-Parity-Suche und kein Tuning dieses Controls.

### Nächster Fokus

Der nächste Research-Zweig wechselt von Kapitalallokationsänderungen zu einem
signalbasierten Cross-Sectional-Control: Fixed-Window-Risk-Adjusted Momentum,
bei dem die bestehende 12-1-Rangfolge durch 12-1 Return geteilt durch die
formation-periodische Realized Volatility ersetzt wird. Die Regel wird einmalig,
präregistriert und auf einem neuen, vollständig disjunkten Universum getestet.

### Sicherheitsstatus

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Research-Orders
- keine Live-Ausführung
