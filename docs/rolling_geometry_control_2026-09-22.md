# Rolling-WF Geometry- und Zeitphasen-Control

Stand: 2026-09-22

Der Horizon-2x2-Control hat gezeigt, dass zusätzliche Trainingshistorie die
Rolling-WF-Passrate nicht verbessert und der Holdout keinen Einfluss auf das
Rolling-WF-Gate hat. Der verbleibende Rolling-WF-Unterschied wird deshalb mit
einem reinen Rolling-Control weiter zerlegt.

Design:

- identische Benchmark-Research-Basis: 4.500 Candles je Asset
- Small-Geometrie: 1.125 Training / 225 Test / 225 Step = 15 Fenster
- Large-Geometrie: 2.250 Training / 450 Test / 450 Step = 5 Fenster
- kein Holdout
- unveränderte Strategie, Parameterraum, Selection-Profile und Gates

Die fünf Large-Testblöcke entsprechen exakt den Small-Fensterpaaren 6-7,
8-9, 10-11, 12-13 und 14-15. Damit können dieselben finalen 2.250
Test-Candles unter zwei Rolling-Geometrien verglichen werden.

Zusätzlich werden unter der Small-Geometrie drei Zeitphasen ausgewertet:
Fenster 1-5, 6-10 und 11-15. Dadurch kann geprüft werden, ob die
Rolling-Probleme auf bestimmte relative Abschnitte der Research-Historie
konzentriert sind.

Die Auswertung bleibt deskriptiv. Sie verändert keine Gate-Schwellenwerte
und wird nicht als Profil- oder Parameter-Ranking verwendet.
