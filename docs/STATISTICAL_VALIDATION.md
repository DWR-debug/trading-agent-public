# Selection-aware Statistical Validation

Unser Research-Prozess dokumentiert die Größe des Suchraums bereits, behandelt
Multiple Testing aber bislang nur deskriptiv. Dieser Baustein schließt die
methodische Lücke, ohne eine künstliche Signifikanzbehauptung in bestehende
Research-Gates einzubauen.

## Probabilistic Sharpe Ratio

Die Probabilistic Sharpe Ratio (PSR) bewertet einen beobachteten,
nicht annualisierten Sharpe Ratio gegen einen vorgegebenen Benchmark. Die
Varianzkorrektur berücksichtigt Stichprobengröße, Schiefe und Roh-Kurtosis der
Return-Serie.

## Deflated Sharpe Ratio

Die Deflated Sharpe Ratio (DSR) verwendet statt eines Null-Benchmarks einen
Selection-Benchmark, der die erwartete maximale Sharpe Ratio einer Familie von
Trial-Ergebnissen unter einer Nullhypothese ohne Skill approximiert. Der
Benchmark steigt mit der Zahl der deklarierten unabhängigen Trials und deren
Sharpe-Streuung. Die Methode adressiert damit explizit Selection Bias und
Nicht-Normalität.

Referenz: David H. Bailey und Marcos Lopez de Prado, The Deflated Sharpe Ratio:
Correcting for Selection Bias, Backtest Overfitting and Non-Normality,
Journal of Portfolio Management 40(5), 94–107 (2014), DOI 10.3905/jpm.2014.40.5.94.

### Bewusste Designentscheidung

Die Implementierung leitet die Zahl unabhängiger Trials nicht automatisch aus
der Parameterraumgröße ab. 1.280 Parameterkombinationen sind nicht automatisch
1.280 unabhängige Experimente. Der Aufrufer muss die
independent_trial_count explizit deklarieren und gleichzeitig die zugehörigen
Trial-Sharpe-Werte liefern.

Das verhindert Scheingenauigkeit und passt zu unserem bestehenden Prinzip,
dass Daten-, Selection- und Evidenz-Scope explizit dokumentiert werden.

### Voraussetzungen

DSR wird nur auf einer zeitlich geordneten Return-Serie angewendet. Die
Trial-Sharpes müssen die tatsächlich zur Auswahl gehörende Trial-Familie
repräsentieren. Die Zahl unabhängiger Trials ist ein Modellinput und darf
nicht stillschweigend mit der Zahl aller Parameterkombinationen gleichgesetzt
werden.

Die aktuelle Legacy-Backtest-Schicht besitzt noch keine universelle
zeitbasierte Equity-/Return-Serie für jeden Backtest. Deshalb wird DSR in
diesem Ausbau zunächst als verfügbarer und getesteter Analysebaustein
eingeführt und nicht rückwirkend auf ungeeignete Trade-PnL-Serien angewandt.

## Beziehung zu den bestehenden Gates

DSR/PSR sind diagnostische Statistik, keine automatische Freigabe. Ein
Research-Kandidat bleibt durch die bestehenden Daten-, OOS-, Rolling-,
Robustheits-, Overfit- und Holdout-Gates beschränkt. Eine hohe DSR kann einen
BLOCKED-Status nicht aufheben.

## Nächster methodischer Ausbau: PBO

Die Probability of Backtest Overfitting (PBO) über Combinatorial Symmetric
Cross-Validation (CSCV) ist eine komplementäre Prozessdiagnose. Sie untersucht,
wie häufig der In-Sample-Sieger out-of-sample unter den Kandidaten zurückfällt.
Das ist für unsere Auswahlfamilien perspektivisch besonders relevant.

Referenz: David H. Bailey, Jonathan Borwein, Marcos Lopez de Prado und Qiji
Jim Zhu, The Probability of Backtest Overfitting, Journal of Computational
Finance (2015), DOI 10.2139/ssrn.2326253.
