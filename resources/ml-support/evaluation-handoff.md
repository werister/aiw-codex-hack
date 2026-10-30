# Übergabe an den ML-Kollegen: Rücktest und Model Card

Diese Punkte beschreiben die Abnahme des späteren Modells. Sie sind keine bereits erzielten Modellresultate. In dem für diese Arbeit geprüften `origin/main`-Stand `0f22742` liegen noch keine Implementierungen von `ml.train` oder `ml.forecast` vor.

## Zeitlich korrekter Rücktest

1. Pro Vorhersage `issued_at`, Zielstunde und `lead_h` getrennt speichern. Beobachtungen und Prognosen müssen am Ausgabezeitpunkt verfügbar gewesen sein; Beobachtungszeit, Modellinitialisierung und Veröffentlichung sind unterschiedliche Zeitpunkte. Der Datenbefund zu Open-Meteo steht in [forecast/findings.md](forecast/findings.md).
2. Training und Validierung nach **Zielzeit** trennen: Eine Trainingszeile mit frühem Ausgabezeitpunkt, deren 48-Stunden-Ziel bereits im Testzeitraum liegt, gehört nicht ins Training. Beim Walk-forward-Verfahren dürfen Fit, Imputation, Kalibrierung und Parametersuche nur den jeweiligen Trainingsblock sehen. Gemeinsame zeitliche Blöcke für beide Zielgrößen verwenden.
3. Modell, Regelbaseline und Persistenz auf genau denselben bekannten Labels und Ausgabezeiten vergleichen. Den Startzustand der Regelbaseline nur aus damals verfügbarer Historie bilden. Unbekannte Zustände und unbestimmbare Böenprüfungen zählen als unbekannt, nicht automatisch als „offen“.
4. Für 1/6/24/48 Stunden Accuracy und Brier Score sowie Anzahl gültiger Fälle berichten. Zusätzlich Basisraten, ausgeschlossene Fälle und Treffer bei Wechseln bzw. Runway-18-Sperrungen zeigen. Hohe Gesamtaccuracy allein belegt bei seltenen Ereignissen wenig.
5. Regel-Proxy und tatsächliche Betriebsrichtung getrennt benennen. Bessere Vorhersage eines Regel-Proxys belegt noch keine Verbesserung gegenüber realen Flughafenentscheidungen. Die Jury-Tage nicht zur nachträglichen Modell-/Schwellenauswahl verwenden.

Dies sind methodische Prüfkriterien aus dem Projektauftrag und der zeitlichen Datenstruktur, keine Aussage über eine bereits ausgeführte Evaluation. Verbindliche Zielwerte und JSON-Formate stehen in den mitgelieferten Referenzdateien; sie wurden hier nicht verändert.

## Datenabschnitt für die spätere Model Card

> Eingangsdaten sind EDDF-METARs aus dem Iowa Environmental Mesonet sowie DWD-ICON-Prognosen über Open-Meteo. Beobachtungen, Prognosegültigkeit und Datenverfügbarkeit werden getrennt behandelt. Fehlende oder variable Windwerte bleiben erkennbar. DWD-CDC-Stundenwerte dienen als unabhängiger Datenvergleich, nicht als stiller Ersatz für Flughafen-METARs. Ohne zusätzliche betriebliche Historie sind die Zielgrößen aus den offiziellen Challenge-Regeln abgeleitete Ersatzlabels. Die Evaluation misst in diesem Fall deren Vorhersagbarkeit, nicht die tatsächlich geflogene Betriebsrichtung oder reale Runway-18-Schließungen.

Vom ML-Kollegen zu ergänzen, sobald tatsächlich berechnet: Modell/Version, Trainings- und Testzeiträume, Labelstrategie, Verfügbarkeitsannahmen, gültige Fallzahlen, Accuracy/Brier je Horizont und Baseline, Kalibrierung sowie wichtige Eingangsgrößen. **Keine Beispielzahlen als Ergebnis eintragen.**

## Offener betrieblicher Nachweis

Benötigt wird eine freigegebene CSV/Parquet-Datei mit UTC-Zeitpunkt oder Zustandsintervall, tatsächlicher BR25/BR07, Runway-18-Status und Quellenangabe. „Unbekannt“ muss darstellbar bleiben. Schon ein klar abgegrenzter Validierungszeitraum wäre nützlich. Eine Anfrage an FraAlliance/DFS/Fraport wurde nicht gesendet; der Hinweis ist für das Team vor Ort.
