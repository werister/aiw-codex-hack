# Betriebslabels: frühere Lücke geschlossen, Auflösung bleibt begrenzt

Geprüfter Projektstand: `33a7847`, 30.10.2026. Die frühere Übergabe fand keine
verwendbare historische Stundenserie. **Diese Aussage ist durch den aktuellen
Projektstand überholt:** `data/ground_truth/` enthält DFLD-Betriebsrichtungen.

Die unabhängige Rekonstruktion ergibt aus **154.752 Halbstundenwerten genau
76.588 Stundenlabels**, einschließlich identischer Reihenfolge und Quellen-URLs.
Alle 788 ausgeschlossenen Stunden stimmen ebenfalls überein: 770 haben zwei
verschiedene Richtungen; 18 besitzen keine eindeutige UTC-Zuordnung beim
Sommerzeitwechsel. Alle 2.880 Halbstundenwerte der frisch geladenen Stichproben
Januar 2025 und Oktober 2026 bis einschließlich 29.10. stimmen mit dem
gespeicherten Bestand überein. [Prüfbericht](report.json),
[Abrufbelege](raw/receipts.json).

Die Quelle unterscheidet ihre **reale Betriebsrichtungsverteilung** ausdrücklich
von einer Windregel. Damit ist der Bestand ein belegter öffentlicher
Betriebsrichtungs-Proxy, kein aus METAR erzeugtes Label. Er ist weder ein
zertifiziertes Bewegungsprotokoll noch ein Nachweis für Starts in jeder Stunde.
Die lokalen Zeitangaben werden weiterhin gemäß der dokumentierten Annahme
`Europe/Berlin` interpretiert; die genaue Veröffentlichung und Abtastung innerhalb
eines Halbstundenintervalls sind nicht nachgewiesen.
[DFLD-Erklärung](https://www.dfld.de/Mess/Language/StatWettHelpG.html),
[Datenherkunft](https://www.dfld.de/Mess/Language/MessHelpG.html).

## Welche Aussagen die Labels tragen

In aufeinanderfolgenden, eindeutig nach UTC umrechenbaren Halbstundenwerten
finden sich **1.681 Richtungswechsel**: 911 beginnen mit einer vollen Stunde,
770 mit einer halben. Damit liegen **45,8 %** der erkennbaren Wechsel in den
aus dem Stunden-Datensatz entfernten Wechselstunden. Dies ist eine
Bestandsbeschreibung über den gesamten Zeitraum, keine Fehlerrate des Modells.

Stunden-Accuracy bewertet folglich stabile angezeigte Richtungen. Sie genügt
nicht zur Bewertung des nächsten Wechsels. Der aktuelle Code berücksichtigt
diesen Unterschied bereits: `ml/train.py` reicht die Halbstundenquelle an
`ml/quality.py::next_change_timing` weiter. Dieser zählt 48-Stunden-Ausgabefenster,
nicht unabhängige Ereignisse. Seine Kennzahlen deshalb zusammen mit
ausgeschlossenen Fenstern und Fehlalarmen berichten; den vollen Bestand von 1.681
Wechseln nicht mit der Anzahl seiner Testereignisse verwechseln.

Die Datenprüfung deckt Januar 2018 bis Oktober 2026 ab, also auch Jahre vor
dem aktuellen Trainingszeitraum. Inzwischen liegt ein DFLD-Betriebsstatus für
Bahn 18 bis Mai 2022 vor; er deckt den Prognosevergleich 2025–2026 nicht ab.
Für die aktuelle Bahn-18-Wetternutzbarkeit bleiben die Zielgrößen aus Wetterregeln abgeleitet. DFLD-OD beweist
weder wetterbedingte Bahn-18-Nutzbarkeit noch die Ursache einer Betriebspause.

## Wiederholen

Vom Repository-Verzeichnis:

```bash
python3 resources/ml-depth/labels/audit_labels.py --truth-dir data/ground_truth
```

Der Prüfer benötigt nur die Python-Standardbibliothek und Zeitzonendaten.
Er rekonstruiert den gesamten gespeicherten Stundenbestand und liest die zwei
unveränderten HTML-Stichproben mit einem eigenen Parser erneut ein.
Die übrigen 104 ursprünglichen Monatsseiten wurden in dieser Runde nicht erneut
geladen; deren ursprüngliche HTML-Hashes sind allein kein vollständiger
Rohdaten-Reproduktionsnachweis. Der inzwischen ergänzte Team-Extraktor
`ml/dfld.py` kann die gesamte Serie neu abrufen; unser Prüfer rekonstruiert sie
unabhängig aus den gespeicherten Halbstundenwerten. Eine erfolgreiche Prüfung bestätigt die
Umwandlung und die beiden Stichproben, keine historischen Publikationszeiten.
