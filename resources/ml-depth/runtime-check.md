# Starttest: Zeitauflösung und Modell-Laufzeit abstimmen

Der dokumentierte Startbefehl wurde auf Projektstand `33a7847` mit Python
3.13.13, pandas 3.1.0 und den vorhandenen Projektdateien ausgeführt:

```bash
python -m ml.forecast --day 2026-10-31 --out /tmp/forecast-smoke.json
```

Er endet mit Exit-Code 1 vor der Prognose. `ml/forecast.py::build_forecast`
verbindet METAR-Zeitstempel mit der DFLD-Verfügbarkeit per `merge_asof`.
Beide Spalten sind UTC, haben aber unterschiedliche Auflösung:
`datetime64[ns, UTC]` gegenüber `datetime64[us, UTC]`. pandas verlangt für
diesen Join identische Typen. Die aktuelle Anforderung `pandas>=2.2` schließt
die geprüfte Version ein.

Der Fehler wurde mit den tatsächlichen Eingabedateien isoliert reproduziert.
Nach ausschließlich speicherinterner Umstellung beider Join-Spalten auf
Nanosekunden gelingt der Join mit allen 67.119 METAR-Zeilen. Die Anwendung,
Quelldaten und Modellartefakte wurden dabei nicht verändert.
[Messprotokoll](runtime-check.json).

**An den ML/CLI-Verantwortlichen:** Zeitauflösung an den gemeinsamen
Eingabegrenzen vereinheitlichen, etwa über `Series.dt.as_unit("ns")`, und
danach Live-/historischen CLI-Pfad sowie den Trainings-Join erneut prüfen.
Die erfolgreiche isolierte Verbindung beweist noch keinen vollständigen
CLI-Lauf. [pandas-Referenz](https://pandas.pydata.org/docs/reference/api/pandas.Series.dt.as_unit.html).

## Nachprüfung im gemeinsamen Hauptzweig

Die Integration enthält inzwischen eine noch uncommittete Vereinheitlichung
der Join-Spalten. Der erneute Starttest gelangt damit bis zum Modellladen,
endet aber erneut mit Exit-Code 1: `ModuleNotFoundError: No module named '_loss'`.
Die Laufzeit verwendet scikit-learn 1.9.1; die vorgeschaltete Warnung nennt
1.7.2 als Erzeugerversion eines gespeicherten Estimators. Commit-Basis,
Hash der geprüften Forecast-Datei und Zeitpunkt stehen im Messprotokoll.

Für den Kollegen ist deshalb auch die **exakte Trainingsumgebung** Teil der
Übergabe: Abhängigkeiten mit dem vorhandenen Artefakt abstimmen oder das
Artefakt in der festgelegten Zielumgebung neu erzeugen und prüfen. Der genaue
Ursprung des fehlenden Moduls ist hier nicht abschließend diagnostiziert.
Versionsübergreifendes Laden wird von scikit-learn nicht unterstützt; ein
einfaches Unterdrücken der Warnung ist kein Nachweis der Kompatibilität.
[Offizielle Hinweise zur Modellpersistenz](https://scikit-learn.org/stable/model_persistence.html).

Die Integration bearbeitet diese Laufzeitprobleme. Diese Datenprüfung hat weder
deren Quellcodeänderung übernommen noch die gemeinsame Umgebung verändert.
Ein vollständiger erfolgreicher CLI-Lauf liegt aus diesen beiden Starttests
nicht vor.
