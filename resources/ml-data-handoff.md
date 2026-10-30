> **Aktualisiert:** Die vollständige Daten-Zuarbeit ist jetzt im [ausgeführten Datenpaket](ml-support/README.md) dokumentiert: 32.156 METAR-Meldungen, 16.008 Prognosestunden, DWD-Vergleich, geprüfte Quellen und reproduzierbare Qualitätsberichte. Die folgende Notiz hält den früheren Stichprobenstand fest.

# ML-Zuarbeit: Daten für Frankfurt in fünf Stunden

Stand: 30.10.2026. Empfehlung: EDDF-METAR + archivierte Wetterprognosen verwenden. Kaggle ist für die geprüften Treffer kein schnellerer Weg. Training, Modellwahl und Integration bleiben beim ML-Kollegen; diese Übergabe liefert Quellen und geprüfte Stichproben.

## Direkt verwendbares Paket

| Quelle | Nutzen | Tatsächlich geprüft |
| --- | --- | --- |
| [IEM METAR](https://mesonet.agron.iastate.edu/request/download.phtml), Station EDDF | Beobachteter Wind und Rohmeldungen; Grundlage für die offiziellen Regel-Labels | 01.–07.10.2025: **336 Meldungen**, alle 30 Minuten, UTC, Wind/Böen in Knoten, keine doppelten Zeitstempel. [CSV](ml-data-samples/eddf-metar-2025-10-01_07.csv) |
| [Open-Meteo Previous Runs](https://open-meteo.com/en/docs/previous-runs-api), `icon_global`, 50.033/8.570 | Archivierte Prognosen für denselben Zeitraum | **168 Stunden**, Windrichtung/-geschwindigkeit, Böen, Druck, Temperatur; jeweils `previous_day1` und `previous_day2`, kein Nullwert. [JSON](ml-data-samples/eddf-icon-global-previous-runs-2025-10-01_07.json) |
| [DWD Station 01420](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/wind/) | Reserve und Plausibilitätsprüfung | Im ursprünglichen Projektarbeitsbaum liegen bereits Wind- und Böenarchive; Inventar in [data-inventory.json](data-inventory.json). Diese wurden hier nicht erneut vollständig geprüft. |

Die beiden Stichproben wurden ohne Account/API-Schlüssel geladen. Vollständige Abruf-URLs, UTC-Abrufzeit, SHA-256, Felder, Einheiten und Fehlwerte stehen in [IEM-Prüfprotokoll](ml-data-samples/iem-verification.json) und [Open-Meteo-Prüfprotokoll](ml-data-samples/open-meteo-verification.json). Das Paket belegt den Datenzugang, noch keine ausreichende Trainingsmenge oder Modellgüte. Der zurückgegebene Wettermodellpunkt liegt bei 50.000/8.625, nicht exakt auf der angefragten Flughafenkoordinate.

## Kaggle: kurze Auswahlentscheidung

| Datensatz | Warum heute zurückstellen |
| --- | --- |
| [Weather forecasting at Vigo airport using AI](https://www.kaggle.com/datasets/jorgerobinat/weather-forecasting-at-vigo-airport-using-ai) | Methodisch ähnlich: METAR und Wettermodellprognosen. Standort **LEVX/Vigo statt EDDF**; Kaggle-Karte nennt 11,61 GB gesamt, `LEVX.csv` 42,04 MB und „EU ODP Legal Notice“. Allenfalls Methodenbeispiel. |
| [Jena Climate](https://www.kaggle.com/datasets/mnassrib/jena-climate) | Zehnminütige Wetterdaten 2009–2016, aber **Jena statt Frankfurt**; keine bestätigten Betriebsrichtungslabels. |
| [Historical climate data from Germany / DWD](https://www.kaggle.com/datasets/vaclavpechtor/dwd-daily-hist) | Keine bestätigte EDDF-Stundenreihe oder passende Prognoseläufe; Originalquelle DWD liegt bereits vor. |

Prüfgrenze: Kaggle-Angaben stammen aus den indexierten Herausgeberkarten. Direktes Öffnen lieferte keine auslesbaren Tabellen; Dateien und API-Metadaten wurden nicht heruntergeladen. In dieser begrenzten Suche fand sich kein sofort nutzbarer EDDF-Datensatz mit tatsächlich geflogener Betriebsrichtung. Der vorhandene Kaggle-Account wird für den empfohlenen Datenweg nicht gebraucht.

## Drei Punkte für den ML-Kollegen

1. **Regel-Labels sind Ersatzlabels.** Die offiziellen Regeln aus `ml/rules.json` auf METAR anwenden und in der Model Card als `rule-derived` kennzeichnen. Das misst zunächst Vorhersage der regelbasierten Zustände, nicht tatsächliche Flughafenentscheidungen. Der [UNH-Bericht 2015–2018](https://www.umwelthaus.org/media/betriebsrichtung_und_windverhaeltnisse_in_den_jahren_2015-2018_v2.pdf) verwendet echte Fraport-Daten, veröffentlicht aber aggregierte Anteile. [DFLD](https://www.dfld.de/Mess/Language/MessHelpG.html) zeigt laut eigener Hilfe echte Betriebsrichtungen ab März 2004; ein dokumentierter Bulk-Export wurde nicht gefunden, und das [Impressum](https://www.dfld.de/DFLDimprint.php) schränkt Weiterverwendung ein. Eine historische Runway-18-Verfügbarkeitsreihe fehlt ebenfalls. Keine Abflüge bedeuten nicht automatisch eine Sperrung. Sinnvolle Frage an FraAlliance vor Ort: Gibt es freigegebene Trainings-/Validierungsdaten mit Zeitstempel und BR25/BR07 beziehungsweise Runway-18-Status?
2. **Vorhersagezeit und Datenverfügbarkeit unterscheiden.** `previous_day1/2` bezeichnet laut [Dokumentation](https://open-meteo.com/en/docs/previous-runs-api) 24/48 Stunden vor der Zielstunde, keinen gemeinsamen Lauf für die gesamte 48-Stunden-Prognose. Die Zuordnung in `briefs/hk-model.md` ist deshalb allein noch kein Nachweis gegen Informationsleckage. Besonders bei 24/48 Stunden Vorlauf muss geprüft werden, ob die verwendete Prognose am Ausgabezeitpunkt bereits veröffentlicht war. [Single Runs](https://open-meteo.com/en/docs/single-runs-api) erlaubt einen konkreten Lauf; Initialisierung und Veröffentlichung liegen laut Dokumentation bei globalen Modellen typischerweise 4–6 Stunden auseinander. **Empfehlung:** Verfügbarkeit je Lauf prüfen oder eine konservative, ausdrücklich dokumentierte Verzögerung ansetzen; unsichere Fälle ausschließen. Ein pauschaler Sechs-Stunden-Puffer ist eine Annahme, kein historischer Verfügbarkeitsbeleg. Single Runs ist eine Option, hier nicht praktisch getestet; die kurze Stichprobe ersetzt diesen Nachweis nicht.
3. **Fehlwerte und Zeitgrenzen erhalten.** In der CSV sind 18 Windrichtungen `M`, alle mit `VRB` in der Rohmeldung; 330 Böenwerte sind `M`. Fehlend bedeutet nicht 0. Für Runway 18 muss der Umgang mit nicht gemeldeten Böen dokumentiert werden; ist die Seitenwindprüfung einschließlich Böen nicht bestimmbar, bleibt das Label unbekannt statt automatisch „nutzbar“. IEM weist auf geringe Qualitätskontrolle und unterschiedliche Ursachen fehlender Felder hin. Beobachtungen zeitlich rückwärts zuordnen, keine spätere Meldung verwenden, Rohtext behalten. Die erste Meldung liegt bei 00:20 UTC: Für Zustand/Regelhistorie um 00:00 braucht es Daten vor dem Stichprobenbeginn. Die 30-Minuten-Hysterese zunächst auf den Beobachtungen auswerten; eine schon stündlich aggregierte Reihe verliert diese Information. [IEM-Feldbeschreibung](https://mesonet.agron.iastate.edu/request/download.phtml)

## Vorschlag für die verbleibenden fünf Stunden

| Zeit ab Start | Unsere Zuarbeit | ML-Kollege |
| --- | --- | --- |
| 0–30 min | Dieses Paket übergeben; echte Betriebsrichtungsdaten vor Ort klären | Zeitraum, Datenquelle und Umgang mit Ersatzlabels festlegen |
| 30–120 min | Größeren Datenabruf auf Lücken, Einheiten und Zeitzuordnung prüfen | Vorhandene Daten-/Label-Pipeline und erstes einfaches Modell |
| 120–210 min | Rücktest auf Zeit-Lecks und seltene Wechsel/Sperrungen prüfen | Chronologischer Test gegen Regeln und Persistenz bei 1/6/24 h |
| 210–270 min | Quellen, Grenzen und Ergebnistabelle für Model Card aufbereiten | Jury-Tage und JSON gemäß bestehendem UI-Vertrag exportieren |
| 270–300 min | Demo-Durchlauf und Übergabe prüfen | Fehler beheben, Modellstand einfrieren |

Das ist ein Arbeitsvorschlag, keine bereits ausgeführte Modellarbeit. Drei unabhängige Rechercheaufträge wurden für Kaggle, Wetterprognosen und reale Betriebsrichtungen eingesetzt. Weitere parallele Aufträge lohnen sich für Datenprüfung, Rücktestprüfung und Model Card; das eigentliche Training behält einen Verantwortlichen. Für heute keine zusätzlichen Flughäfen, große Parametersuche oder eigene Flugspurrekonstruktion einplanen.

## Herkunft und Prüfstatus

METAR: Iowa Environmental Mesonet, unbearbeitete CSV, [Nutzungshinweise](https://mesonet.agron.iastate.edu/disclaimer.php). Wettermodell: DWD ICON über [Open-Meteo](https://open-meteo.com/), unbearbeitete JSON-Antwort; [CC BY 4.0](https://open-meteo.com/en/licence). Die kostenlose API ist laut [Nutzungsbedingungen](https://open-meteo.com/en/terms) auf nichtkommerzielle Nutzung beschränkt. Datenlizenz und API-Zugang sind getrennte Fragen.

Ausgeführt: zwei öffentliche HTTP-Abrufe (je 200), CSV-/JSON-Parsing, Stations-/Zeitraum-/Feldprüfung, Einheiten-/Fehlwertzählung, Prüfung von Zeitabständen und Duplikaten, SHA-256. Kein ML-Code, Training, Backtest oder App-Start wurde ausgeführt; keine Aussage über Modellgenauigkeit.
