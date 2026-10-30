# Ausgeführte Prüfungen

30.10.2026, im gemeinsamen Hauptzweig. Alle Datenprüfer liefen mit der
Python-Standardbibliothek und ohne Netzwerkzugriff. Ausgabe-Dateien wurden
für die Gegenprüfung außerhalb des Pakets geschrieben.

| Prüfung | Ergebnis |
| --- | --- |
| `labels/audit_labels.py` mit aktuellem `data/ground_truth` | Exit 0; 76.588 Stundenlabels exakt rekonstruiert; 788 ausgeschlossene Stunden stimmen; 2.880 Roh-HTML-Stichproben stimmen |
| `observations/verify_raw_metar.py` mit Wetterpaket, Regeln und DFLD | Exit 0; 46/46 Rohdatei-Hashes stimmen; 32.156 Hauptwindgruppen; null Normalisierungsabweichungen |
| `comparability/analyze_comparability.py` | Exit 0; 144.072 Windwerte aus 22 Monatsantworten stimmen; Kennzahlen und 1-/3-/7-Tage-Blockauswertung reproduziert |
| `temporal/probe.py --verify` | Exit 0; 14 Abrufbelege stimmen; 72 Stundenvektoren mit 216 Windwerten stimmen mit den zugeordneten Einzel-Läufen |
| Erneute Ergebnisprüfung | Label-, METAR- und Windvergleichs-JSON semantisch identisch; nur der Ausführungszeitpunkt des METAR-Prüfers wird ausgenommen |
| `resources/ml-support/verify_package.py` | Exit 0; alle 133 Dateien des ursprünglichen Wetterpakets unverändert |
| Python-Syntax aller Prüfscripte | Bestanden |

Die unabhängige Gegenprüfung prüfte außerdem Sommerzeitlücke, doppelte Stunde,
Unterscheidung von Windpfeilen und OD-Titeln sowie Beobachtung gegenüber
TREND-Windgruppen. Es wurde kein Modell trainiert.

Der echte CLI-Start ist **nicht bestanden**: erst unterschiedliche
Zeitauflösungen, nach der laufenden Integrationskorrektur ein Fehler beim
Modellladen. Siehe [Laufzeitprotokoll](runtime-check.md).

`openspec --version` und `openspec list --json` waren nicht ausführbar
(`command not found`). Keine OpenSpec-Artefakte wurden geändert und keine
OpenSpec-Validierung als bestanden bezeichnet.
