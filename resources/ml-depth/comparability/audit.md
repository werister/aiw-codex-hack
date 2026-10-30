# Windvergleich: ICON Global, EDDF METAR und DWD

Stand: 30. Oktober 2026; reproduzierbar mit Python-Standardbibliothek aus den
unveränderten Dateien im Wetterpaket. Die Diagnose betrifft **nur** das
Support-Archiv `icon_global`; `ml/fetch.py` fordert im aktuellen Trainingspfad
`best_match` an. Die Kennzahlen sind daher kein Befund zum gerade trainierten
Modell.

## Befund

Für jede Zielstunde wurde der letzte METAR-Wert mit Zeitstempel höchstens zur
Zielzeit verwendet (16.005 Paare sind 10 Minuten alt, drei 40 Minuten). Es gibt
keine zukünftigen Beobachtungen und keine ausgeschlossenen Stunden. Das ist ein
Vergleich zum gültigen Zeitpunkt, **kein** Backtest mit festem Prognose- und
Ausgabezeitpunkt.

Der Fehler ist `ICON − METAR`; negativ heißt, dass ICON langsamer meldet. Über
16.008 Stunden von Januar 2025 bis Oktober 2026 ergibt sich:

| Previous-Day-Offset | Bias | MAE | RMSE |
| --- | ---: | ---: | ---: |
| 1 | −3,322 kt | 3,444 kt | 4,216 kt |
| 2 | −3,321 kt | 3,462 kt | 4,272 kt |
| 3 | −3,336 kt | 3,518 kt | 4,371 kt |

Die Rohquellenprüfung fand in 22 Open-Meteo-Monatsantworten 16.008 Stunden,
144.072 Windwerte, UTC-Offset 0, konstant `kn`/Grad-Einheiten und **keine**
Abweichung zur normalisierten CSV. Alle 32.156 METAR-Windgruppen ließen sich
aus dem Rohtext als `KT` parsen; Speed und Böen stimmen vollständig mit den
normalisierten Feldern überein. Das macht einen Einheiten- oder Parserfehler
als Erklärung für diesen ICON-Global-Befund unwahrscheinlich.

Der Bias bleibt in jedem der 22 Kalendermonate negativ (Offset 1: −2,29 bis
−4,00 kt) und zu jeder lokalen Stunde negativ (−2,78 bis −3,98 kt). Die
Tagesblock-Bootstrap-Intervalle für Offset 1 bleiben ebenfalls klar negativ:
1-Tagesblöcke [−3,43; −3,21], 3-Tagesblöcke [−3,47; −3,17],
7-Tagesblöcke [−3,49; −3,15] kt (je 2.000 Wiederholungen). Das ist deskriptive
Unsicherheit für diesen Ausschnitt; selbst 7-Tagesblöcke erfassen keine längere
saisonale oder synoptische Abhängigkeit und machen den Vergleich nicht zu
einem unabhängigen Modelltest.

Die Abweichung hängt stark von der beobachteten Windstärke ab (Offset 1): Bias
−0,91 kt bei METAR 0–<5 kt, −3,52 kt bei 5–<10 kt, −6,12 kt bei 10–<15 kt und
−9,14 kt ab 15 kt. Das sind nach dem beobachteten Zielwert gebildete
Diagnosegruppen, keine kalibrierbare Eingabeauswahl. Die Richtungssektoren
bleiben überwiegend negativ; Südost hat nur 178 Fälle. Stunden- und
Richtungsunterschiede sollten angesichts der Auswahl und wechselnden
Windverteilungen nicht als eigenständige Korrekturregel behandelt werden.

## DWD-Gegenprüfung und Grenzen

Die getrennte DWD-Stundenreihe für Station 01420 stimmt im Mittel nahe mit
einem sparsamen METAR-Vergleich überein: Das Zwei-Punkt-METAR-Mittel minus
DWD-Stundenmittel (`METAR − DWD`) hat Bias +0,245 kt,
MAE 1,383 kt und RMSE 1,800 kt über 13.076 Stunden ausgewiesen. Für jedes
DWD-Stundenlabel `t` werden die METAR-Geschwindigkeiten bei `t−40` und
`t−10` Minuten gemittelt; die untere Grenze `t−70` ist ausgeschlossen.
Das orientiert sich an der DWD-SYNOP-Zeitkonvention: Die offizielle DWD-
Beschreibung des verwandten Stunden-Windprodukts ordnet um UTC 11 den
Mittelwert der sechs 10-Minutenintervalle UTC 09:51–10:50 zu. Die lokale
Stationsmetadatei 01420 beschreibt den Bezugszeitraum als `23:51–23:50 UTC`.
Der Zweipunktwert ist weiterhin **kein Stundenmittel** und nur eine
Plausibilitätsprüfung. 11 DWD-Zeilen haben ein fehlendes Mittel; drei andere
Stundenfenster haben nicht genau zwei METAR-Punkte. DWD-Werte wurden mit
1 m/s = 1,9438444924406 kt geprüft; die gespeicherten Umrechnungen stimmen
exakt. Die jüngsten DWD-Daten sind nicht final qualitätsgeprüft; QN 1, 3 und
10 kommen vor.

Auf denselben DWD-Stundenlabels ist ICON um rund −3,07 kt niedriger als das
DWD-Stundenmittel (13.079 Paare, Offset 1). Das stützt die Richtung des
METAR-Befunds unabhängig vom IEM-Parser, beweist aber keine allgemeine
ICON-Bias-Korrektur: Die zeitlichen Mittelungsintervalle sind nicht sicher
identisch, DWD-01420 ist eine separate Station rund 3,7 km vom EDDF-Raster
entfernt, und lokale Exposition bzw. Messhöhen sind nicht gleich.

## Konsequenz für die Übergabe

- Für das Support-Archiv ist ein durchgehender Unterbias nachvollziehbar. Vor
  einer Korrektur muss derselbe Vergleich auf den tatsächlich genutzten
  `best_match`-Eingaben und mit chronologisch getrennten Trainings- und
  Validierungszeiträumen wiederholt werden.
- Nicht allein wegen dieses Ergebnisses `wind_speed_80m` als Ersatz einsetzen:
  Die METAR-Windmessung und die operative Regel zielen auf bodennahe
  Bedingungen; eine 80-m-Modellgröße hat eine andere physikalische Höhe. Eine
  solche Änderung benötigt eigene Validierung gegen die passenden Messwerte.
- DFLD-Betriebsrichtung ist ein eigener öffentlicher Betriebsrichtungs-Proxy,
  keine Wetter- oder R18-Nutzbarkeitswahrheit. Siehe
  [`../labels/audit.md`](../labels/audit.md) für Reichweite und Stundenwechsel.

## Reproduktion

Aus dem Repository mit dem Support-Ordner `weather/`:

```bash
python3 resources/ml-depth/comparability/analyze_comparability.py --support-package weather
```

Das Skript schreibt `report.json` neben sich. Ein exportiertes Paket kann mit
demselben Argument angegeben werden, etwa `--support-package
resources/ml-support`. Es liest nur die Eingaben, bildet keine Merkmale oder
Modelle und verändert keine Dateien im Support-Paket.

## Quellen

- [DWD-Datensatzbeschreibung Stundenmittel Wind (v24.03)](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/wind/DESCRIPTION_obsgermany_climate_hourly_wind_en.pdf)
- [DWD-Stations- und Parameterdateien der Station 01420](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/wind/recent/)
- [DWD-Beschreibung der SYNOP-Zeitzuordnung stündlicher Windmittel](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate_urban_prov/hourly/wind/recent/DESCRIPTION_obsgermany-climate_urban_prov-hourly-wind-recent_en.pdf) (Zeitkonvention als Gegenprüfung, anderes Teilprodukt)
- [IEM-ASOS-Archiv und Datenfelder](https://mesonet.agron.iastate.edu/request/download.phtml?network=CI__ASOS)
- [Open-Meteo Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api)
