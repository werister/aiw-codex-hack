# Starttest: Fehler reproduziert, Integrationskorrektur bestätigt

**Abgeschlossen:** Nach den Änderungen der zentralen Integration laufen beide
Aufrufe auf Basis `658acdf` erfolgreich. Die Datenprüfung hat weder ML-Code
geändert noch Abhängigkeiten installiert oder Modelle neu trainiert.

```bash
python -m ml.forecast --day 2026-10-31 --out /tmp/forecast-day.json
python -m ml.forecast --now --out /tmp/forecast-48h.json
```

Der erste liefert die 24 Stunden des gewählten Tages, der zweite alle 48
Prognosestunden. Beide enden mit Exit 0, verwenden `walk-forward-v3` und
liefern Wahrscheinlichkeiten im gültigen Bereich. Geprüfte Laufzeit: Python
3.13.13, pandas 3.1.0, NumPy 2.5.4, scikit-learn 1.7.2. Zeitpunkte,
Code-Hashes und Ausgabe-Hashes stehen im [Messprotokoll](runtime-check.json).
Das ist eine Start-/Schnittstellenprüfung, kein neuer Güte- oder Kalibrierungstest.

## Gefundene Ursachen

Auf `33a7847` scheiterte der Start vor der Prognose: METAR-Zeitstempel lagen als
`datetime64[ns, UTC]`, die aus CSV gelesene DFLD-Verfügbarkeit als
`datetime64[us, UTC]` vor. Der gemeinsame `merge_asof` benötigt identische Typen.
Ein unabhängiger Versuch mit speicherintern vereinheitlichten Spalten verband
alle 67.119 METAR-Zeilen erfolgreich. Die Integration vereinheitlichte danach
die Join-Spalten. [pandas-Referenz](https://pandas.pydata.org/docs/reference/api/pandas.Series.dt.as_unit.html).

Der folgende Start erreichte das Modellladen, scheiterte aber mit
`ModuleNotFoundError: No module named '_loss'`. Die Laufzeit nutzte scikit-learn
1.9.1, während die Warnung 1.7.2 als Erzeugerversion eines gespeicherten
Estimators nannte. Nach Abstimmung der Laufzeit und der Integrationskorrektur
ist der vollständige Start bestätigt. Die genaue Aufteilung der Ursache
zwischen Versionsunterschied und Modulauflösung wurde von dieser Datenprüfung
nicht abschließend untersucht.

**Für die Übergabe beibehalten:** Trainings- und Laufzeitabhängigkeiten zusammen
mit dem Modellartefakt festhalten. Versionsübergreifendes Laden wird von
scikit-learn nicht unterstützt; Warnungen zu unterdrücken beweist keine
Kompatibilität. [Offizielle Hinweise zur Modellpersistenz](https://scikit-learn.org/stable/model_persistence.html).
