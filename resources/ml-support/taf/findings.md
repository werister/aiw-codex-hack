# EDDF-TAF: Archivzugang geprüft

Die [IEM-TAF-Dokumentation](https://mesonet.agron.iastate.edu/cgi-bin/request/taf.py?help) beschreibt `valid` als Ausgabezeit und `fx_valid` als Vorhersagezeit. Das wäre eine sinnvolle Ergänzung für die Prüfung damaliger Verfügbarkeit.

Zwei konkrete EDDF-Abfragen wurden ausgeführt: 01.–07.10.2025 und 23.–29.10.2026, jeweils UTC. Beide lieferten **HTTP 200, aber nur die CSV-Kopfzeile und null Datensätze**. Sie sind kein nutzbares historisches EDDF-TAF-Dataset. Das belegt nur diese zwei abgefragten Zeiträume, nicht eine generelle Abwesenheit aller EDDF-TAFs bei IEM.

Abruf-URLs, Zeitpunkte, Hashes und Zeilenzahlen stehen in [access-check.json](access-check.json); die Antworten liegen daneben. Kein Parser oder Modell wurde auf den leeren Dateien aufgebaut. Für den zeitlich begrenzten Datenweg bleiben METAR und archivierte Modellprognosen die tragfähige Kombination.
