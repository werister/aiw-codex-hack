# METAR-Böen, variable Richtung und DWD-Vergleich

Geprüfter Projektstand: `33a7847` vom 30.10.2026. Der Prüfer liest die IEM-Rohmeldungen erneut, schneidet Trendabschnitte vor der Windsuche ab und vergleicht die Hauptwindgruppe mit der normalisierten CSV. Er trainiert kein Modell und erzeugt keine Labels aus Flugdaten.

## METAR-Rohdaten und Regelwirkung

Die 46 gehashten IEM-Antworten enthalten **32.156** EDDF-Meldungen von 29.12.2024 bis 29.10.2026 UTC: 16.082 IEM-Typ 3 und 16.074 Typ 4. Alle enthalten eine lesbare Hauptwindgruppe in KT; erneutes Parsen fand **0 Abweichungen** zur normalisierten Datei. Die Typnummern sind IEM-Abfrageklassen und belegen für sich nicht, dass jede Typ-4-Zeile eine tatsächliche SPECI-Meldung ist. In 1.268 Meldungen folgt später eine Windgruppe in einem Trendabschnitt; sie darf die beobachtete Hauptgruppe nicht ersetzen.

**Kein `G` ist ein Berichtsergebnis, kein numerischer Böenwert und kein expliziter Sensorausfallcode.** 31.696 Hauptgruppen enthalten kein `G`, 460 enthalten eine codierte Böe; die größte codierte Böe beträgt 40 kt. Der DWD beschreibt `G` als höchstes gleitendes 3-Sekunden-Mittel innerhalb der letzten 10 Minuten (oder seit einer markanten Änderung im kürzeren Fenster), wenn es den gemeldeten Mittelwind um mindestens 10 kt übersteigt. Ein normales Windfeld ohne `G` belegt daher, dass in diesem Berichtsfenster kein die Meldeschwelle erreichender Spitzenwert codiert wurde; es liefert keinen exakten Böenwert und beweist für sich allein nicht, dass der Böensensor fehlerfrei war. Die DWD-Vorschrift codiert ausgefallene Windmessungen gesondert mit Schrägstrichen; im Bestand gibt es keine Hauptgruppe mit fehlendem Wind. `gust_status=NOT_ENCODED` sollte deshalb nicht als null, Sensorfehler oder als beobachtete Böe gleich Mittelwind ausgegeben werden.

Im Bestand ist der maximale Mittelwind ohne `G` 29 kt; 40 kt ist die größte codierte Böe. Unter der METAR-Meldeschwelle überschreitet damit kein dekodierter Windwert die FraAlliance-Grenze **Crosswind > 40 kt** selbst im ungünstigsten Richtungswinkel. Das ist eine bedingte Aussage über codierte Regelwerte und Berichtsfenster, keine Garantie über physikalische Spitzen, Messrundung oder Betriebsfreigabe. Beim Training sollten fehlende Böen entweder als fehlend mit Status erhalten oder durch eine ausdrücklich dokumentierte Ableitung ergänzt werden.

### `VRB` und `dddVddd`

| Befund | Rohmeldungen | In `train.py` as-of zugeordnete DFLD-Stunden |
| --- | ---: | ---: |
| `VRB`: 4.289 Fälle, Mittelwind max. 12 kt; 86 davon mit `G`, max. 25 kt | 4.289 | 2.067 von 15.919 eindeutigen DFLD-Stunden im überlappenden Zeitraum 2024-12–2026-10 |
| `dddVddd`: 9.782 Fälle; 231 mit Mittelwind ≥ 15 kt | 9.782 | 12 der eindeutigen DFLD-Stunden, in denen der Mittelrichtungstest unter 15 kt liegt, der kodierte Richtungsbogen aber 15 kt erreichen kann |

Für alle vorhandenen `VRB`-Fälle bleibt der richtungsunabhängige Tailwind unter 15 kt; auch Mittelwind beziehungsweise codierte Böe bleiben nach der obigen bedingten Schranke unter der Crosswindgrenze. Unter den bestehenden FraAlliance-Regeln lässt sich R18 damit für diese Stichprobe regelbasiert als nutzbar ableiten. Der aktuelle `ml/rules.py::r18_usable` gibt bei nicht-calm `direction=None` stattdessen `None` zurück; entsprechend bleiben die 2.067 zugeordneten DFLD-Stunden unbekannt. Der Datenbefund trennt damit eine vorsichtige Code-Policy von fehlenden Messdaten. `ml/features.py::normalize_obs` füllt außerdem fehlende Böen mit dem Mittelwind auf; das ist eine Imputation, keine beobachtete Böe.

Bei 24 der 9.782 `dddVddd`-Fälle liegt die Tailwindkomponente der codierten Mittelrichtung unter 15 kt, während der Richtungsbogen bei gleicher mittlerer Geschwindigkeit 15 kt erreichen kann. Beispiel: `EDDF 150950Z AUTO 03017KT 360V060 ...`; Mittelrichtung ergibt 14,722 kt, das Intervall reicht bis 17 kt. Das ist eine Sensitivität der Interpretation, kein Beleg für gleichzeitige Extremrichtung und Mittelgeschwindigkeit. Wenn der Projektvertrag die Mittelrichtung als Regelinput festlegt, ist dies kein nachgewiesener Regelcodefehler.

## DWD-Stundenwerte als Vergleich

DWD-Metadaten nennen Station 01420 „Frankfurt/Main“ mit 50,0259° N, 8,5213° E und 99,7 m Stationshöhe. Zum Fraport-Flughafenbezugspunkt aus Abschnitt 1.1 der Airport User Regulations sind es rechnerisch 3,606 km. Das belegt weder einen Standort außerhalb des Flughafengeländes noch die Identität des DWD-Sensors mit dem EDDF-METAR-Referenzsensor. Für den Überschneidungszeitraum sind 10-m-Ultraschall-Anemometer-Metadaten (2D compact) dokumentiert, mit einer Metadatenlücke am 27.–28.08.2025.

Das DWD-Produkt `F`/`D` ist ein stündliches Mittel in m/s und Grad; die für 2025–2026 gültigen Stationsmetadaten sagen UTC und beschreiben die Ableitung aus 10-Minuten-Mitteln. Die genauen Fenstergrenzen relativ zu jedem `MESS_DATUM` sind damit nicht belegt. `FX_911` ist laut Metadaten die höchste Windspitze der letzten Stunde. Das ist ein anderes Fenster als METAR-`G` und nicht direkt gleichzusetzen. Im exportierten DWD-Überlappungs-CSV liegen 13.090 Zeitpunkte von 13.200 erwarteten Stunden vor; 110 Zeitpunkte fehlen. Getrennt davon fehlen Mittelwind und Stundenmaximum in 11 Zeilen; Richtung fehlt in keiner. Das „recent“-Produkt ist laut DWD noch nicht abschließend qualitätsgeprüft. Die Reihe eignet sich als separate Referenz, nicht als stiller METAR-Ersatz oder R18-Labelquelle.

## Reproduktion

Vom entpackten Übergabepaket-Root (`weather/` enthält den Support-Bestand, `audit/` diesen Prüfer):

```bash
python3 audit/observations/verify_raw_metar.py --source weather/observations --rules weather/reference/rules.json --truth project-data/ground_truth/dfld_hourly.csv --output /tmp/ml-depth-observations-audit.json
```

Das Skript nutzt nur Python-Standardbibliothek. Es prüft die 46 Rohdatei-Hashes, Hauptwindgruppen, Trends und normalisierte Werte erneut. Der explizite `--output` hält den Paketbericht unverändert. Ohne `--rules` sucht es im Projekt und anschließend neben dem `--source`-Paket unter `reference/rules.json`.

## Quellen

- [DWD Handbuch Flugwetterdienste, Band Obs](https://www.dwd.de/DE/leistungen/lf_11_flugwetterbetriebsdienste/handbuch_flugwetterdienst_obs_4.0.pdf?__blob=publicationFile&v=2), Abschnitte 1.3.5 und 2.1, S. 11 und 15 (Mittelwind und Böenmeldung).
- [DWD Handbuch Flugwetterdienste, Band Tech](https://www.dwd.de/DE/leistungen/lf_11_flugwetterbetriebsdienste/handbuch_band_tech_v4.0.pdf?__blob=publicationFile&v=2), Abschnitt 9.10.4, S. 87 (Umgang mit ausgefallenen Windmessungen).
- [DWD Stundenmittel Wind](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/wind/DESCRIPTION_obsgermany_climate_hourly_wind_en.pdf), S. 1–2 (Felder, Einheiten, Stundenmittel, Qualitätsstatus „recent“).
- [DWD stündliche Windspitzen](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/extreme_wind/DESCRIPTION_obsgermany_climate_hourly_extreme_wind_en.pdf), S. 1–2 (FX_911 und stündliches Maximum).
- [Fraport Airport User Regulations](https://sslapps.fraport.de/webportalAVS/pdf/Airport-user-regulations.pdf), Abschnitt 1.1 (Flughafenbezugspunkt).
- [IEM ASOS/METAR-Archiv](https://mesonet.agron.iastate.edu/request/download.phtml?network=CI__ASOS) (Rohdatenfelder und Archivklassen).
