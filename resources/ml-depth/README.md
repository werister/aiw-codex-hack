# Vertiefte Datenprüfung für den ML-Kollegen

Stand: 30.10.2026; geprüfter Projektstand `33a7847`. Die erste Datenübergabe
wurde anhand der Rohdaten und des inzwischen vorhandenen Modellcodes geprüft.
Training, Modellparameter und Anwendungscode bleiben beim zuständigen Kollegen.

**Vor der Demo beheben:** Der zusätzliche CLI-Starttest deckte einen
`ns`-/`us`-Konflikt beim METAR/DFLD-Join auf. Die laufende Integration behebt
diesen; der nächste Starttest scheitert beim Laden des Modellartefakts in
einer anderen scikit-learn-Version. [Reproduktion und eingegrenzte Abhilfe](runtime-check.md)
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
| Veröffentlichungspuffer | 72 ICON-Stundenvektoren stimmen mit den zugeordneten Einzel-Läufen überein; der Code nutzt day1 bis +18 h, day2 bis +42 h, dann day3 | Zykluszuordnung und historische Veröffentlichung unterscheiden; der Sechs-Stunden-Puffer bleibt eine Annahme |
| ICON-Windunterschied | −3,32 kt im Mittel, über Monate und Blocklängen stabil; bei Starkwind größer | Kein Einheitenfehler gefunden; keine pauschale Korrektur oder Übertragung auf `best_match` ableiten |
| Böen ohne `G` | 31.696 gültige Hauptwindgruppen ohne kodierte Böe; DWD-Meldeschwelle liefert Information | Weder Nullböe noch Sensorfehler unterstellen; Rohstatus erhalten und Imputation von Regelinferenz trennen |
| Variable Richtung | 4.289 VRB-Meldungen liegen unter den relevanten Geschwindigkeitsgrenzen; 24 Richtungsspannen machen die 15-kt-Grenze bei einer Sensitivitätsprüfung uneindeutig | Labelpolitik ausdrücklich festlegen; das ist weder ein Nachweis tatsächlicher Schließungen noch eine Betriebsfreigabe |

Die vertieften Prüfungen und ihre reproduzierbaren Ergebnisse:

- [Zeitlogik und einzelne Modellläufe](temporal/audit.md).
- [METAR-Rohmeldungen, Böen und DWD-Metadaten](observations/audit.md).
- [Windvergleich nach Zeit und Wetterlage](comparability/audit.md).
- [Unabhängige Rekonstruktion der DFLD-Labels](labels/audit.md).

Die geprüften Dateien sind in [project-snapshot.json](project-snapshot.json)
mit Commit und SHA-256 festgehalten. Befunde gelten für diesen Stand; die
parallel weiterentwickelte Anwendung kann inzwischen abweichen. Eine erfolgreiche
Quellenprüfung ist weder ein neuer Modellrücktest noch eine Betriebsfreigabe.

[Ausgeführte Prüfungen und ihre Grenzen](verification.md).
