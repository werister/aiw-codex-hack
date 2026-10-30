# Fertiges Datenpaket für den ML-Kollegen

Stand: 30.10.2026. Die Daten-Zuarbeit ist ausgeführt: Abruf, Normalisierung, Quellenprüfung und Qualitätskontrolle. Training und Anwendungscode wurden nicht übernommen. **Start mit den beiden CSVs für METAR und ICON; die übrigen Dateien erklären Herkunft und Grenzen.**

## Enthaltene Daten

| Datei | Tatsächlich enthalten | Grenze |
| --- | --- | --- |
| [EDDF-METAR](observations/eddf_metar_observations.csv) | **32.156 Beobachtungen**, 29.12.2024–29.10.2026 UTC, inklusive dreier Tage Vorlauf vor dem Prognosezeitraum; Rohmeldungen und getrennte Wind-/Böenstatus | Vier fehlende halbstündige Meldungen; 4.289 VRB-Meldungen, 76 Windstillen; 31.696 Meldungen ohne kodierte Böe. IEM-Reporttyp 3/4 nicht ungeprüft als tatsächliche METAR/SPECI-Unterscheidung interpretieren. |
| [ICON-Global-Prognosen](forecast/normalized/open-meteo-icon-global.csv) | **16.008 Stunden**, 01.01.2025–29.10.2026, jeweils Archivabstände day1/day2/day3; Wind, Richtung, Böen, Druck, Temperatur | Wind/Böen vollständig. Je 77 fehlende Werte bei Temperatur day1/day3 und Druck day3. Rasterpunkt 50.000/8.625; keine historische Veröffentlichungszeit pro Stunde. |
| [DWD-CDC-Vergleichsdaten](observations/dwd_01420_hourly_wind_gust_overlap.csv) | **13.090 Stunden**, 28.04.2025–29.10.2026, Wind und Stundenmaxima der Böen, Originaleinheiten und Knoten | 110 fehlende Zeitpunkte innerhalb der Grenzen; zusätzlich je elf leere Windmittel-/Böenwerte. Separate Messprodukte; kein stiller Ersatz für METAR. |
| [Einzelner historischer Modelllauf](forecast/single-runs-probe.json) | ICON-Lauf vom 29.10.2026 00 UTC, 72 Stunden, erfolgreich abrufbar | Eine Böe fehlt; heutiger Archivabruf beweist keine damalige Veröffentlichung. |
| [Live-Zugriffstest](live/findings.md) | Sechs aktuelle METARs und 49 ICON-Prognosestunden, Abruf am 30.10.2026 | Eingefrorener Snapshot, kein laufender Dienst und kein ML-Ergebnis. |

Die unveränderten IEM-/Open-Meteo-Antworten und DWD-Archive sind mitgeliefert. Quellen-URLs, Abrufzeiten, Größen, Einheiten und SHA-256 stehen in den jeweiligen Manifesten. UTC ist das Austauschformat; lokale Anzeige erst danach in Europe/Berlin umrechnen.

## Was die Prüfungen entschieden haben

- **Direktquellen verwenden:** [Kaggle wurde über API, Metadaten, Dateilisten und eine tatsächliche Frankfurt-Datei geprüft](kaggle/findings.md). Die untersuchten Kandidaten bieten für EDDF keinen passenden Zusatznutzen; kein Konto nötig.
- **Alle Prognosestunden haben einen Vergleichswert:** Der [unabhängige Quellenabgleich](qa/findings.md) fand 16.005 Beobachtungen zehn Minuten und drei vierzig Minuten vor der Zielstunde. ICON unterschätzt die Windstärke in diesem Vergleich im Mittel um etwa 3,3 kt. Das ist eine Datenauffälligkeit, kein gemessener ML-Gewinn.
- **TAF vorerst verwerfen:** Beide [IEM-EDDF-Archivproben](taf/findings.md) lieferten null Datensätze.
- **Tatsächliche Betriebslabels bleiben extern offen:** [DFLD, UNH, Fraport und OpenSky wurden geprüft](ground-truth/findings.md). Kein verwendbares historisches Stundenlabel-Paket gefunden. OpenSky verweigerte den konkreten anonymen Historienabruf mit HTTP 403. Der erneut geladene Fraport-Status war mehr als sieben Stunden alt und ist keine historische Serie.
- **Zeit-Lecks verhindern:** Previous-Day-Felder sind Archivabstände, kein exakt belegter gemeinsamer Initialisierungs-/Veröffentlichungszeitpunkt. [Zeitsemantik und Grenzen](forecast/findings.md) vor dem Rücktest berücksichtigen. Fehlende Böen oder Betriebszustände nicht als „offen“ etikettieren.

## Direkt benutzen und prüfen

Im entpackten Paketverzeichnis, mit Python 3.11 oder neuer und ohne zusätzliche Pakete:

```bash
python3 verify_package.py
python3 qa/compare_weather_sources.py
```

Der erste Befehl prüft Paketdateien, SHA-256, JSON-Lesbarkeit und protokollierte CSV-Zeilen. Der zweite reproduziert den Quellenvergleich. Eine bestandene Integritätsprüfung besagt nicht, dass alle Datenfelder vollständig oder Flughafenentscheidungen validiert sind.

Der Beobachtungsabruf lässt sich mit `python3 observations/fetch_verify.py --skip-fetch` aus dem mitgelieferten Cache normalisieren; ohne `--skip-fetch` werden fehlende Rohdateien geladen. Die Prognoseprüfung läuft mit `python3 forecast/fetch_forecast_data.py verify --start 2025-01-01 --end 2026-10-29`; `fetch` lädt fehlende Monatsdateien. Reproduktion aktualisiert Prüfberichte; für den unveränderten Lieferstand zuerst `verify_package.py` ausführen. Details stehen in den beiden Quellenordnern.

## Übergabe und verbleibende Verantwortung

[evaluation-handoff.md](evaluation-handoff.md) enthält die Rücktest-Prüfpunkte und einen direkt verwendbaren Datenabschnitt für die Model Card. [Offizielle Regeln](reference/rules.json), [Challenge-Brief](reference/frankfurt-airport-operating-direction-forecast.md) und [UI-Vertrag](reference/forecast-types.ts) liegen unverändert bei; [reference/provenance.json](reference/provenance.json) nennt den Projektstand und Hashes.

Der Kollege übernimmt Labelstrategie, Modelltraining, zeitlichen Rücktest, Ergebniskennzahlen, CLI und UI-Export. Diese Leistungen sind hier weder ausgeführt noch als bestanden markiert. Für eine tatsächliche Betriebsvalidierung braucht das Team weiterhin freigegebene Zeitreihen von DFS/Fraport oder eine andere belegte betriebliche Quelle. METAR-Regel-Labels müssen bis dahin ausdrücklich als Ersatzlabels bezeichnet werden.

Quellenangaben: Iowa Environmental Mesonet ([Public-Domain-Nutzungshinweis](https://mesonet.agron.iastate.edu/disclaimer.php)); DWD-CDC mit den Originalmetadaten in den ZIP-Dateien; DWD ICON über [Open-Meteo](https://open-meteo.com/) ([CC BY 4.0](https://open-meteo.com/en/licence), [API-Nutzungsbedingungen](https://open-meteo.com/en/terms)). Alle Normalisierungen, Umrechnungen und Prüfstatistiken sind als abgeleitete Daten gekennzeichnet; Rohantworten bleiben unverändert.
