# Ausgeführte Abschlussprüfung

Stand 30.10.2026. Die folgenden Prüfungen wurden tatsächlich ausgeführt; es wurde kein ML-Modell trainiert oder eine Anwendung gestartet.

| Prüfung | Ergebnis |
| --- | --- |
| Vollständiges Paket in separates Verzeichnis kopieren; `python3 observations/fetch_verify.py --skip-fetch` | Exit 0; METAR und DWD aus mitgeliefertem Cache reproduziert, ursprüngliche DWD-Abrufzeiten erhalten. |
| `python3 forecast/fetch_forecast_data.py verify --start 2025-01-01 --end 2026-10-29` | Exit 0; Zeitstruktur, Wind-/Böenvollständigkeit und grobe Wertebereiche bestanden. Drei andere Felder haben weiterhin je 77 dokumentierte Fehlwerte. |
| `python3 qa/compare_weather_sources.py` | Exit 0; 16.008 Zuordnungen ohne zukünftige Beobachtung; unabhängige Neuberechnung der Fehlerkennzahlen ergab identische Ergebnisse. |
| SHA-256 der drei normalisierten CSVs vor/nach der portablen Reproduktion | Alle drei Dateien bytegenau identisch. |
| Syntax aller fünf Python-Skripte | AST-Parsing erfolgreich, keine zusätzlichen Bibliotheken erforderlich. |
| Original-DWD-ZIPs | Beide CRC-Prüfungen bestanden. |
| Integritätsprüfer mit unveränderter und gleich langer manipulierter Testdatei | Unveränderte Datei akzeptiert, Änderung korrekt erkannt und mit Exit 1 abgewiesen. |
| Dokumentlinks | Lokale Referenzen auf innerhalb des Pakets enthaltene Dateien geprüft. |

Der gesamte unveränderte Lieferstand ist über `package-manifest.json` und `python3 verify_package.py` prüfbar. Die Prüfung bestätigt Dateiintegrität und Lesbarkeit; sie ersetzt weder Quellenqualität noch eine betriebliche oder zeitlich korrekte Modellvalidierung. Die CSVs mit den vollen Datenmengen und Originalantworten werden im ZIP mitgeliefert, im Git-Branch über das Paket-Manifest referenziert und durch die Skripte reproduzierbar gemacht.
