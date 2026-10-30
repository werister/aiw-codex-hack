# Vertiefte Datenprüfung für den ML-Kollegen

Stand: 30.10.2026; geprüfter Projektstand `33a7847`. Die erste Datenübergabe
wurde anhand der Rohdaten und des inzwischen vorhandenen Modellcodes geprüft.
Training, Modellparameter und Anwendungscode bleiben beim zuständigen Kollegen.

**Vor der Demo beheben:** Der zusätzliche CLI-Starttest scheitert mit einer
laut Anforderungen zulässigen pandas-Version an `ns`-/`us`-Zeitstempeln beim
METAR/DFLD-Join. [Reproduktion und eingegrenzte Abhilfe](runtime-check.md)
sind für den ML/CLI-Verantwortlichen dokumentiert; der vollständige Start ist hier nicht
als bestanden markiert.

**Die vorhandenen Trainingsdaten behalten.** Das Projekt trainiert inzwischen
mit Open-Meteo `best_match` und aufgezeichneten DFLD-Betriebsrichtungen. Unser
zusätzlicher ICON-Global-Bestand ist ein separat dokumentierter Vergleichsbestand;
er ersetzt weder diese Quellenwahl noch den weiter zurückreichenden Projektcache.

## Was gegenüber der ersten Übergabe korrigiert wurde

| Punkt | Belastbarer Stand | Konsequenz |
| --- | --- | --- |
| Historische Betriebsrichtung | DFLD-Labels liegen jetzt vor; alle 76.588 Stunden sind aus 154.752 Halbstundenwerten exakt rekonstruierbar | OD als öffentlichen Betriebsrichtungs-Proxy beschreiben; Bahn 18 bleibt ein Wetterregel-Proxy |
| Richtungswechsel | 770 der 1.681 erkennbaren Wechsel liegen in ausgeschlossenen Wechselstunden | Stunden-Accuracy und Wechselwarnung getrennt bewerten; der aktuelle Code nutzt bereits Halbstundenwerte für die Wechselmetrik |
| Modell vorhanden | `walk-forward-v3` und ein trainierter Bestand liegen im geprüften Projekt vor | Die frühere Aussage „noch kein ml.train/ml.forecast“ ist überholt; diese Prüfung hat selbst kein Modell trainiert |
| Veröffentlichungspuffer | Der aktuelle Code nutzt day1 bis +18 h, day2 bis +42 h, dann day3 | Die alte Warnung vor fehlendem Sechs-Stunden-Puffer ist überholt; tatsächliche historische Veröffentlichungen bleiben gesondert nachzuweisen |
| ICON-Windunterschied | Der frühere Vergleich betrifft ausdrücklich ICON Global | Keinen Modellgüte- oder Bias-Befund daraus ungeprüft auf `best_match` übertragen |

Die vertieften Prüfungen und ihre reproduzierbaren Ergebnisse:

- [Zeitlogik und einzelne Modellläufe](temporal/audit.md).
- [METAR-Rohmeldungen, Böen und DWD-Metadaten](observations/audit.md).
- [Windvergleich nach Zeit und Wetterlage](comparability/audit.md).
- [Unabhängige Rekonstruktion der DFLD-Labels](labels/audit.md).

Die geprüften Dateien sind in [project-snapshot.json](project-snapshot.json)
mit Commit und SHA-256 festgehalten. Befunde gelten für diesen Stand; die
parallel weiterentwickelte Anwendung kann inzwischen abweichen. Eine erfolgreiche
Quellenprüfung ist weder ein neuer Modellrücktest noch eine Betriebsfreigabe.
