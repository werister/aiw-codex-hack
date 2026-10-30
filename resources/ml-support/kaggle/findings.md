# Kaggle: Auswahl abgeschlossen

Geprüft am 30.10.2026: vier öffentliche API-Suchen (`EDDF`, `Frankfurt weather`, `METAR`, `runway configuration`), fünf vollständige Datensatz-Metadaten, drei Dateilisten und eine kleine Frankfurt-Datei. Alle Abrufe lieferten HTTP 200 ohne Login. Die erste Suchseite enthielt jeweils 7, 6, 20 und 0 Treffer; dies ist keine vollständige Katalogsuche.

| Kandidat | Beleg und Entscheidung |
| --- | --- |
| [26 Global Cities, 2024–2026](https://www.kaggle.com/datasets/rngrng/metar-weather-26-global-cities-2024-2026) | Die Herausgeberbeschreibung nennt alle 26 Flughäfen: EDDM/München enthalten, **EDDF nicht**. Roh-METAR von IEM; CC0 laut Kaggle. Direkter IEM-Abruf für EDDF passt besser. |
| [METAR weather time series](https://www.kaggle.com/datasets/fbykov/metar-weather-time-series) | Vollständige Dateiliste: `ICAO.csv`, `QNH.csv`, `Tair.csv`, `Tdew.csv`. Kein Wind-/Böen-Datensatz; kein Ersatz für die benötigten Eingaben. |
| [AIRPORTS TEMPERATURE](https://www.kaggle.com/datasets/jorgerobinat/airports-temperature) | Dateiliste nennt EGLL, FACT, KJFK, LEMD, RJAA, SAEZ, TJSJ, UUEE, VIDP und YSSY; kein EDDF. |
| [Rohlik Weather Data](https://www.kaggle.com/datasets/mexwell/rohlik-order-forecast-weather-data-for-test) | `frankfurt.csv` tatsächlich heruntergeladen: nur `time`, `precipitation_sum (mm)`, `snowfall_sum (cm)`, tägliche Zeilen. Kein Wind und keine Betriebsrichtung. Herausgeber nennt Open-Meteo als Quelle und CC BY 4.0. |
| [Vigo weather forecasting](https://www.kaggle.com/datasets/jorgerobinat/weather-forecasting-at-vigo-airport-using-ai) | Metadaten bestätigen LEVX, WRF und METAR. Gut als Methodenbeispiel, geografisch ungeeignet. Version 18, entpackte Gesamtgröße laut Detailmetadaten 11.606 GB; nicht heruntergeladen. |

**Entscheidung:** Keiner dieser geprüften Kandidaten ergänzt die EDDF-Eingaben sinnvoll. Der Kaggle-Account ist dafür nicht erforderlich. Kein Kaggle-Datensatz liefert hier verifizierte tatsächliche Betriebsrichtungen.

Prüfbelege: [Suchabfragen](public-catalog-check.json), [Detailmetadaten](candidate-metadata.json), [Dateilisten](candidate-files.json), [Frankfurt-Dateiprüfung](frankfurt-file-check.json). Die unveränderten Antworten liegen unter `raw/`; URLs und Prüfsummen sind protokolliert. Suchtreffer und Dateimetadaten beweisen keine allgemeine Abwesenheit passender Datensätze auf Kaggle.

Die frühere Übergabe beruhte noch auf indexierten Karten; diese Prüfung ersetzt jene Einschränkung für die hier aufgeführten Kandidaten. Die fremden Kaggle-Daten werden nicht als Trainingsdaten empfohlen. Die kleine Rohlik-Datei dient allein als prüfbarer Ausschlussbeleg (unverändert; Quelle mexwell/Open-Meteo, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)).
