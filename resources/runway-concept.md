# FRA Runway Outlook

**Bei der Schichtübergabe wissen, welche Änderung des Bahnbetriebs in den nächsten
48 Stunden vorbereitet werden muss.**

Stand: 30. Oktober 2026. Geschärfte Produktidee zur FraAlliance-Challenge;
Präsentation und verbindliches Regelwerk stehen noch aus.

## Der geschärfte Auftrag

Entwickle eine Frühwarnung für die operative Planung in Frankfurt: Prognostiziere
für die nächsten 48 Stunden die Verfügbarkeit von Bahn 18 für Abflüge und die
Betriebsrichtung 07/25. Zeige insbesondere bevorstehende Änderungen, ihr
Zeitfenster und ihre Unsicherheit. Prüfe anhand tatsächlich beobachteter
Betriebszustände, ob die Warnungen früheres Planen ermöglichen und einfache
Vergleichsverfahren übertreffen.

## Eine Person, eine Entscheidung

Unsere **zu prüfende Nutzerhypothese** ist die Schichtleitung im Ground Handling.
Sie entscheidet bei der Übergabe, ob sie für ein bestimmtes Zeitfenster eine
alternative Einsatzverteilung vorbereiten muss. Wie diese Verteilung aussieht,
bestimmt das Betriebsteam. Das Produkt liefert Anlass, Zeitraum und Begründung.

Die erste Nutzerprüfung braucht nur einen konkreten vergangenen Fall: Was musste
umgeplant werden, wann erfuhr das Team davon, welcher zusätzliche Vorlauf hätte
geholfen, und was hätte ein Fehlalarm gekostet? Erst diese Antworten rechtfertigen
eine Warnschwelle oder eine behauptete Personal-/Verspätungsersparnis.

## Das kleinste überzeugende Produkt

Eine gemeinsame 48-Stunden-Zeitleiste mit zwei unabhängigen Spuren:

| Spur | Aussage | Vorrangige Frage |
| --- | --- | --- |
| Bahn 18 | erwartete Verfügbarkeit; wetterbedingtes Einschränkungsrisiko separat erkennbar | Wann könnten Abflüge über Bahn 18 entfallen, und für wie lange? |
| Parallelbahnen | erwartete Richtung 07 oder 25, mit Wechselzeitfenster | Wann könnte die Betriebsrichtung wechseln? |

Die nächste relevante Änderung steht oben. Ein Klick zeigt Windkomponente,
Regel bzw. Modellbeitrag, Ausgabezeit der Wetterprognose und Abweichung vom
vorherigen Prognoselauf. Stundenwerte begründen keine minutengenaue Wechselzeit.
Ein fehlender oder alter Betriebsstatus wird als unbekannt sichtbar.

**Beispieltext, ausdrücklich fiktiv:** „Bahn 18: wetterbedingtes
Einschränkungsrisiko morgen 14–18 Uhr. Parallelbahnen: voraussichtlich weiter
25. Der Beginn verschiebt sich zwischen den letzten beiden Läufen um zwei
Stunden.“ Das beschreibt beobachtbare Prognosestabilität; eine Prozentangabe
braucht zusätzlich Kalibrierung gegen echte Ereignisse.

Eine Betriebsrichtungsprognose existiert bereits öffentlich, mit achtstündigen
Intervallen. Unsere Differenzierungshypothese ist die für die Planung nutzbare
Verknüpfung von Bahn 18, bevorstehenden Änderungen und nachvollziehbaren
Aktualisierungen. Sie ist noch kein belegter Wettbewerbsvorteil.
[Bestehende Umwelthaus-Prognose](https://www.umwelthaus.org/fluglaerm/anwendungen-service/aktuelle-betriebsrichtung-und-prognose/)

## Was das Modell lernen soll

Vorhandene Wettermodelle liefern den Wind. Wir berechnen daraus bahnbezogene
Gegen-, Rücken- und Seitenwindkomponenten und prognostizieren **zwei verschiedene
Betriebszustände**. Der aktuelle Zustand, Verlauf und Prognosehorizont können
zusätzliche Merkmale sein, sofern sie zum Ausgabezeitpunkt bekannt waren.

Zuerst entsteht nach Erhalt des Regelwerks eine nachvollziehbare Regel-Baseline.
Ein kleines Klassifikationsmodell, etwa Gradient Boosting, muss dann anhand
echter Betriebsdaten einen messbaren Zusatznutzen zeigen. Aus Wettergrenzwerten
erzeugte Trainingslabels würden nur die vorgegebenen Regeln reproduzieren.
Wetterbedingte Nutzbarkeit und tatsächliche Freigabe bleiben unterscheidbar;
ungeplante nichtmeteorologische Sperrungen sind aus Winddaten allein nicht
ableitbar.

Die veröffentlichte Fünf-Knoten-Regel betrifft die Parallelbahnen. Sie ist keine
bestätigte Sperrschwelle für Bahn 18. Auch Höhenwind und Prognosen beeinflussen
die Richtungsentscheidung.
[Fraport](https://www.fraport.com/en/sustainability/dialog-with-neighbors/noise-and-air/flight-operations/operation-direction.html)

## Woran die Idee bestehen muss

Die Demo spielt einen belegten historischen Wechsel und ein Zeitfenster ohne
Wechsel nach. Sie zeigt nur Informationen, die damals verfügbar waren, und blendet
anschließend den tatsächlich eingetretenen Zustand ein. Ein einzelner Fall zeigt
den Ablauf; mehrere zeitlich getrennte Ereignisse müssen die Prognosegüte tragen.

- Vergleich: Zustand beibehalten und reine Wetterregel; Umwelthaus zusätzlich,
  falls dessen damalige Prognosen verfügbar sind.
- Bahn 18: übersehene Sperrungen, Fehlalarme pro Tag, Fehler bei Beginn/Dauer.
- Richtung: übersehene/falsch angekündigte Wechsel und Fehler des Wechselzeitfensters.
- Für beide: Vorwarnzeit und Ergebnisse nach Prognosehorizont, insbesondere +48 h.
  Die Güte auf langen unveränderten Zeitabschnitten genügt nicht.
- Zeitliche Trennung von Training und Prüfung, ohne überlappende Zielzeiträume;
  aktuelle Zustände und Prognose-Updates dürfen nicht aus der Zukunft einfließen.

Wenn die Warnung gegenüber den Baselines keinen hilfreichen Vorlauf bringt oder
zu viele unnötige Vorbereitungen auslöst, ist der angenommene Planungsnutzen
widerlegt. Die benötigte Vorwarnzeit und tragbare Fehlalarmrate muss das
Betriebsteam vor der Bewertung festlegen.

## Was heute bereits belegt ist

Zwei gespeicherte API-Proben enthalten jeweils 72 vollständige Stundenwerte für
Frankfurt: feste 48-Stunden-Vorhersagewerte und einen einzelnen ICON-EU-Modelllauf.
Die erste Form prüft +48 h pro Zielzeitpunkt; **erst ein einzelner Modelllauf
rekonstruiert die zusammenhängende 48-Stunden-Sicht eines damaligen Planers**.
Initialisierungszeit und tatsächliche Veröffentlichungszeit sind dabei getrennt
zu behandeln. Der Abruf allein belegt die damalige Verfügbarkeit noch nicht.
[API-Prüfung](forecast-access-check.json),
[Previous Runs](https://open-meteo.com/en/docs/previous-runs-api),
[Historical Forecast / Single Runs](https://open-meteo.com/en/docs/historical-forecast-api)

Das veröffentlichte Fraport-Skript liefert einen aktuellen Zustand für beide
Ziele. Eine belastbare historische Zustandsreihe wurde in der begrenzten
Recherche nicht gefunden. Flugspuren können die geflogene Richtung unterstützen;
ausbleibende Abflüge beweisen keine Sperrung von Bahn 18.
[Fraport-Statusquelle](https://sslapps.fraport.de/betriebsrichtung/betriebsrichtungsvg.js),
[DFLD-Datenhinweise](https://www.dfld.de/Mess/Language/MessHelpG.html)

Die Konzeptprüfung deckt vier Gegenbeispiele ab: Richtungswechsel bei weiter
nutzbarer Bahn 18; Einschränkung von Bahn 18 bei unveränderter Richtung; zwischen
Prognoseläufen schwankender Beginn; fehlender Betriebsstatus. Die getrennten
Ziele und explizite Unsicherheit bilden alle vier ab. Prognosegüte und
Disponenten-Nutzen sind noch ungeprüft.

Für die sechs Stunden konzentriert sich die Umsetzung auf diese Zeitleiste,
die Begründung eines Ereignisses und den historischen Vergleich. Flugtracking,
Personaloptimierung und Anschlussflugberechnung gehören nicht zur ersten Demo.
