# EDDF-Wetterprognosen: Datenpaket für den ML-Kollegen

Stand: 30. Oktober 2026. Dieses Paket liefert Wettermodell-Eingaben zur eigenen Weiterverarbeitung. Es enthält weder Labels noch Training oder Modellbewertungen.

## Abruf und Dateien

Vom Open-Meteo Previous Runs API wurden 22 Monatsantworten für **icon_global** geladen, vom 1. Januar 2025 bis einschließlich 29. Oktober 2026 (UTC). Angefragt wurden Windgeschwindigkeit, Windrichtung, Böen, Luftdruck auf Meereshöhe und Temperatur für die Previous-Day-Offsets 1, 2 und 3. Alle 22 Anfragen waren HTTP 200.

- [Normalisierte Stunden-CSV](normalized/open-meteo-icon-global.csv): **16.008** eindeutige UTC-Stunden, jede Stunde des Zeitraums.
- [Monatsantworten als Roh-JSON](raw/previous-runs/): 22 unveränderte Antwortkörper; URL, Anforderungszeit, Status, Bytezahl und SHA-256 stehen je Monat im [Manifest](manifest.json).
- [Qualitätsbericht](quality.json): Zeitreihenabdeckung, Koordinaten, Einheiten, Fehlwerte und Wertebereiche.
- [Abruf- und Prüfskript](fetch_forecast_data.py): Python-Standardbibliothek, monatliche Zwischenspeicherung, 1,25 s Mindestabstand, Wiederholungen und lokale Validierung.

Reproduzieren oder vervollständigen:

    python3 resources/ml-support/forecast/fetch_forecast_data.py fetch --start 2025-01-01 --end 2026-10-29
    python3 resources/ml-support/forecast/fetch_forecast_data.py verify --start 2025-01-01 --end 2026-10-29
    python3 resources/ml-support/forecast/fetch_forecast_data.py probe-single-run --run 2026-10-29T00:00

Die erste Ausführung speichert fertige Monatsantworten und verwendet sie bei Wiederholung aus dem Cache. Die Anfragen benötigen keinen API-Schlüssel.

## Was die Datenprüfung ergab

Die Normalisierung fand 16.008 von 16.008 erwarteten Stunden, keine doppelten oder fehlenden Zeitstempel, keine Lücken und keine zusätzlichen Zeitpunkte. Die API lieferte durchgehend dieselbe Rasterzelle: **50.000° N, 8.625° E** statt der angefragten Flughafenkoordinate **50.033° N, 8.570° E**. Für räumliche Nähe ist das brauchbar, aber die Zelle liegt nicht direkt auf dem Flughafen.

Alle Windgeschwindigkeits-, Windrichtungs- und Böenfelder für alle drei Offsets sind vollständig. Bei den übrigen Eingaben fehlen Werte: 77 bei Temperatur/Tag 1, 77 bei Temperatur/Tag 3 und 77 bei Druck/Tag 3. Diese Fehlwerte fallen im Abruf vom 10. bis 13. April 2026 an. Sie bleiben in der CSV leer und werden nicht ersetzt. Darum meldet quality.json die Zeitstruktur und Windfelder als vollständig, aber validation_pass insgesamt als false.

Einheiten stimmen mit der Anfrage überein: Wind und Böen in kn, Richtung in Grad, Druck in hPa, Temperatur in °C. Die beobachteten Minima und Maxima liegen innerhalb der im Skript gesetzten groben Plausibilitätsgrenzen. Das ist ein Wertebereichscheck, keine fachliche Güteprüfung. Der Abruf verglich die Vorhersagen nicht mit Beobachtungen.

Ein zusätzlicher Single-Runs-Abruf wurde erfolgreich geprüft: icon_global, Lauf 2026-10-29T00:00Z, 72 Stunden bis 2026-10-31T23:00Z, HTTP 200. Alle fünf Variablen sind enthalten; eine Böe ist null. Rohantwort und Prüfdaten liegen unter [Single-Runs-Probe](single-runs-probe.json) und [Rohantwort](raw/single-runs/2026-10-29T00-00.json). Der Abruf am 30. Oktober beweist, dass dieser Lauf heute aus dem Archiv abrufbar ist. Er beweist nicht, wann der Lauf ursprünglich öffentlich verfügbar wurde.

## Bedeutung der Vorhersage-Offsets und Zeit-Leakage

Die [Previous-Runs-Dokumentation](https://open-meteo.com/en/docs/previous-runs-api) beschreibt die Felder als Vorhersagen mit festen Vorlauf-Offsets zur Zielzeit: nominal 24 Stunden bei previous_day1, 48 Stunden bei previous_day2 und 72 Stunden bei previous_day3. Das ist kein einziger Modelllauf für sämtliche Stunden. Eine Erläuterung eines Open-Meteo-Maintainers beschreibt für einen Sechs-Stunden-Zyklus bei Tag 1 nacheinander Vorhersagestunden 24–29 aus dem 00Z-Lauf, 30–35 aus dem 06Z-Lauf, dann 12Z und 18Z ([Primärquelle](https://github.com/open-meteo/open-meteo/issues/1750)). Die JSON-Antwort enthält keine Initialisierungszeit pro Zielstunde. Deshalb sollte man aus dem Feldnamen keinen exakten Laufzeitpunkt pro Zeile ableiten.

Die [Single-Runs-Dokumentation](https://open-meteo.com/en/docs/single-runs-api) unterscheidet ausdrücklich Lauf-Initialisierung (run=) und Veröffentlichung. Für globale Modelle nennt Open-Meteo typischerweise vier bis sechs Stunden Verarbeitung, für regionale Modelle eine bis drei Stunden. Die [Modellstatus-Dokumentation](https://open-meteo.com/en/docs/model-updates) beschreibt last_run_availability_time für die aktuelle Verfügbarkeit; sie liefert hier keinen historischen Veröffentlichungsnachweis pro archivierter Modellstunde. Ein sechs Stunden langer Puffer kann als Annahme dienen, ist aber kein Beleg dafür, dass ein bestimmter archivierter Wert zur damaligen Ausgabezeit tatsächlich verfügbar war.

Die Zuordnung im [ML-Arbeitsbrief](../reference/hk-model.md) (previous_day1 bis 24 Stunden Lead, danach previous_day2) ist daher allein kein Nachweis für einen leckagefreien historischen Backtest. Für eine strengere Rekonstruktion muss der ML-Kollege entweder einzelne run=-Läufe auswählen und eine explizite Verfügbarkeitsannahme dokumentieren oder unsichere Zeitpunkte ausschließen. Diese Übergabe nimmt die Entscheidung nicht vorweg.

## Grenzen und Lizenz

Die Daten sind Wettermodell-Prognosen, keine tatsächlichen Betriebsrichtungen und kein Flughafen-Wahrheitsdatensatz. Das Paket enthält keine OD- oder Runway-18-Labels, kein Training, keine Merkmalsauswahl und keinen Backtest. Die Mess- und Regel-Labels müssen separat bewertet werden; fehlende Werte dürfen nicht stillschweigend als 0 eingesetzt werden.

Open-Meteo verlangt Attribution unter CC BY 4.0. Die kostenlose API ist laut [Nutzungsbedingungen](https://open-meteo.com/en/terms) nur für nichtkommerzielle Nutzung bestimmt. Datenlizenz und Berechtigung für den API-Zugang sind getrennte Fragen.
