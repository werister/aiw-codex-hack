# Live-Daten: Zugriff geprüft

Am 30.10.2026 um etwa 10:58 UTC wurden ohne Schlüssel geladen:

- [NOAA Aviation Weather Center](https://aviationweather.gov/api/data/metar?ids=EDDF&format=json&hours=3): sechs EDDF-METARs mit Beobachtungs- und Empfangszeit.
- [Open-Meteo](https://open-meteo.com/en/docs): 49 Stunden ICON-Global-Wetterdaten vom 30.10.2026 10:00 bis 01.11.2026 10:00 UTC; Wind und Böen in Knoten.

Die Dateien sind ein eingefrorener Zugriffstest, keine aktuelle laufende Vorhersage und kein ML-Ergebnis. Der erste Wetterzeitpunkt liegt vor dem Abruf: **Den Snapshot nicht rückwirkend als bereits um 10:00 bekannte Information ausgeben.** Die beobachtete Empfangsverzögerung der METARs ist ebenso wenig ein Beleg für historische Verzögerungen.

[manifest.json](manifest.json) enthält Abruf-URLs, Zeitpunkte, SHA-256 und Umfang. Wetterdaten: DWD ICON über Open-Meteo, unverändert, [CC BY 4.0](https://open-meteo.com/en/licence). NOAA-Feldbeschreibung: [Data API](https://aviationweather.gov/data/api/).
