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

Der Bias bleibt in jedem der 22 lokalen Kalendermonate negativ (Offset 1:
−2,29 bis −4,00 kt) und zu jeder lokalen Stunde negativ (−2,78 bis −3,98 kt).
Januar 2025 beginnt am UTC-Archivrand; Oktober 2025 enthält die doppelte lokale
Herbststunde. Die beiden `02`-Stunden im Herbst werden in der
Lokaluhr-Stundenstratifizierung zusammengefasst. Die
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

Die DWD-Stationsmetadaten belegen `F`/`D` in UTC und stündliche Mittel aus
10-Minutenmitteln; sie legt die genaue Mittelungsgrenze relativ zu jedem
`MESS_DATUM`-Stundenlabel nicht zweifelsfrei fest. Als **Arbeitsannahme** wurde
für DWD-Zeit `t` das METAR-Fenster `(t−70 min, t−10 min]` gewählt, gestützt
auf die veröffentlichte SYNOP-Zeitkonvention eines verwandten DWD-
Stundenwindprodukts. Darin liegen die zwei METAR-Berichte bei `t−40` und
`t−10`; ihr arithmetischer Mittelwert ist ein sparsamer Vergleich, **kein
Stundenmittel**. Die ±1-h-Sensitivität zeigt, wie der Vergleich ausfällt,
wenn die Zeilenzuordnung anders interpretiert wird:

| Verschiebung | METAR-Fenster relativ zu DWD-Label `t` | METAR−DWD Bias | MAE | RMSE | n |
| ---: | --- | ---: | ---: | ---: | ---: |
| −1 h | `(t−130 min, t−70 min]` | +0,247 kt | 1,632 kt | 2,123 kt | 13.076 |
| 0 h | `(t−70 min, t−10 min]` | +0,245 kt | 1,383 kt | 1,800 kt | 13.076 |
| +1 h | `(t−10 min, t+50 min]` | +0,244 kt | 1,725 kt | 2,265 kt | 13.076 |

11 DWD-Zeilen haben ein fehlendes Mittel; drei weitere haben in den jeweiligen
METAR-Fenstern nicht genau zwei Punkte. Bias-Richtung und Mittelwertdifferenz
bleiben über alle drei Interpretationen ähnlich, während der Fehlerbetrag im
zentralen Arbeitsfenster am kleinsten ist. Das belegt die Zeitgrenze nicht. Die
Umrechnung `1 m/s = 1,9438444924406 kt` stimmt für alle gespeicherten
DWD-Windmittel exakt. Im DWD-QN-Feld kommen 1, 3 und 10 vor; die jüngsten
Einträge sind nicht final qualitätsgeprüft.

Gegen DWD-Windmittel ist ICON am selben DWD-Stundenlabel um rund −3,07 kt
niedriger. Für Offset 1 bleibt der Bias bei −1/0/+1 h Forecast-Zeitversatz
zwischen −3,071 und −3,072 kt (n=13.078–13.079). Das stützt die Richtung des
METAR-Befunds zusätzlich, beweist aber keine allgemeine ICON-Bias-Korrektur:
Die stündlichen Mittelungsintervalle sind nicht sicher identisch. DWD-01420
ist der DWD-Stationsdatensatz `Frankfurt/Main` mit Koordinaten 50,0259 N,
8,5213 E, Stationshöhe 99,7 m und Windgeberhöhe 10 m; 2025–2026 ist ein
Ultraschall-Anemometer 2D compact dokumentiert. Die Position liegt etwa 3,6 km
von der angefragten EDDF-Koordinate und rund 8 km von der tatsächlich
gelieferten ICON-Rasterzelle entfernt. Ob dieser DWD-Sensor physisch derselbe
oder gleichwertig zum METAR/ASOS-Sensor ist, ist nicht belegt.

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

Vom exportierten Bündel-Root mit dem Support-Ordner `weather/`:

```bash
python3 audit/comparability/analyze_comparability.py --support-package weather
```

Das Skript schreibt standardmäßig `report.json` neben sich. Für einen
unveränderten Paketvergleich den Output in `/tmp` legen:

```bash
python3 audit/comparability/analyze_comparability.py \
  --support-package weather --output /tmp/comparability-reproduction.json
```

Der feste Bootstrap-Seed und das Fehlen von Abrufzeitstempeln im Ergebnis
machen die JSON-Ausgabe mit denselben Eingaben deterministisch. Ein anderer
Support-Ordner kann über `--support-package PATH` angegeben werden. Das Skript
liest nur die Eingaben, bildet keine Merkmale oder Modelle und verändert keine
Dateien im Support-Paket.

## Quellen

- [DWD-Datensatzbeschreibung Stundenmittel Wind (v24.03)](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/wind/DESCRIPTION_obsgermany_climate_hourly_wind_en.pdf)
- [DWD-Stations- und Parameterdateien der Station 01420](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/wind/recent/)
- [DWD-Beschreibung der SYNOP-Zeitzuordnung stündlicher Windmittel](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate_urban_prov/hourly/wind/recent/DESCRIPTION_obsgermany-climate_urban_prov-hourly-wind-recent_en.pdf) (Zeitkonvention als Gegenprüfung, anderes Teilprodukt)
- [IEM-ASOS-Archiv und Datenfelder](https://mesonet.agron.iastate.edu/request/download.phtml?network=CI__ASOS)
- [Open-Meteo Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api)
