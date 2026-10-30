# Starttest: Zeitauflösung vor dem Join vereinheitlichen

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
