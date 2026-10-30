# Unabhängiger Abgleich von Beobachtungen und Prognosen

Ausgeführt mit `python3 qa/compare_weather_sources.py` vom Paketverzeichnis. Ergebnis: [source-comparison.json](source-comparison.json).

Für **alle 16.008 Prognosestunden** wurde eine eindeutige EDDF-Beobachtung an oder vor der jeweiligen Zielstunde gefunden: 16.005 waren zehn Minuten alt, drei waren vierzig Minuten alt. Kein späterer Messwert wurde zugeordnet; keine mehrdeutigen Zeitpunkte oder über 60 Minuten alten Beobachtungen wurden verwendet.

| Archiv-Tagesabstand | Windstärke: mittlerer Fehler Prognose minus Beobachtung | Mittlerer absoluter Fehler | Fälle |
| --- | ---: | ---: | ---: |
| day1 | −3,32 kt | 3,44 kt | 16.008 |
| day2 | −3,32 kt | 3,46 kt | 16.008 |
| day3 | −3,34 kt | 3,52 kt | 16.008 |

**Befund für den Kollegen:** Die ungeänderten ICON-Global-Werte liegen in diesem Abgleich systematisch unter den METAR-Windstärken. Standort, Modellraster und zeitliche Mittelung unterscheiden sich. Eine mögliche Korrektur muss ausschließlich am Trainingszeitraum geschätzt und danach separat geprüft werden; diese Übersicht liefert noch keinen Nachweis eines ML-Gewinns.

Es gibt 255 zugeordnete Stunden mit ausdrücklich gemeldeter Böe. Deren Fehler sind im JSON separat ausgewiesen. Diese Auswahl ist auf Fälle mit gemeldeten Böen beschränkt und darf nicht als allgemeine Böengenauigkeit verstanden werden. Eine Liste auffälliger Böenzeitpunkte ist für manuelle Plausibilitätschecks enthalten; es sind keine verifizierten Runway-Sperrungen oder Jury-Testfälle.

Die Auswertung ist eine Datenprüfung über Archivabstände. Sie ist **kein Rücktest eines 1-/6-/24-/48-Stunden-ML-Modells** und belegt nicht, wann die archivierten Prognosen ursprünglich veröffentlicht waren. Beobachtungen zur Zielzeit sind hier Vergleichswerte; sie dürfen nicht als zum früheren Ausgabezeitpunkt bekannte Modellmerkmale verwendet werden.
