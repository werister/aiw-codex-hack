# FRA Runway Outlook

**Lernen, wann eine Wetterprognose die entscheidenden Bahngrenzen zu früh,
zu spät oder fälschlich überschreiten lässt – damit die Planung Vorlauf gewinnt.**

Stand: 30. Oktober 2026. Die [Abschrift des Challenge-Briefs](../frankfurt-airport-operating-direction-forecast.md)
und die daraus abgeleitete [Regeldatei](../ml/rules.json) liefern die vorläufige
Arbeitsgrundlage. Original-PDF und Pitchfolien liegen dieser Prüfung noch nicht
vor; der [Quellenabgleich](challenge-source-audit.md) hält die offenen Belege fest.
Dieses Konzept präzisiert den gewählten Modell-/UI-Ansatz; es ist kein Implementierungsnachweis.

## Der geschärfte Auftrag

Entwickle ein Modell, das für jede Stunde der nächsten 48 Stunden die
Nutzungswahrscheinlichkeit von Bahn 18, die Richtung 07/25, die Sicherheit der
Prognose und den nächsten Wechselzeitpunkt liefert. Lerne aus dem Unterschied
zwischen früheren Wetterprognosen und späteren Beobachtungen. Zeige bevorstehende
Änderungen mit begründetem Zeitfenster und einer bedingten Planungsmarke. Vergleiche
die Prognose bei 1, 6 und 24 Stunden mit Regeln und Persistenz; prüfe zusätzlich
48 Stunden und die rechtzeitige Erkennung von Änderungen. Unterscheide die
Bewertung gegen wetterbasierte Zielzustände von der gegen echten Flugbetrieb.

## Eine Person, eine Entscheidung

Unsere **zu prüfende Nutzerhypothese** ist die Schichtleitung im Ground Handling.
Sie prüft bei der Übergabe, ob für ein bestimmtes Zeitfenster eine alternative
Einsatzverteilung vorbereitet werden sollte. Handlung und Zuständigkeit bestimmt
das Betriebsteam. Es gibt außerdem seine benötigte Vorbereitungszeit vor.

Die bedingte Planungsmarke lautet: **frühester Beginn im gewählten Szenario minus
Vorbereitungszeit**. Sie macht die Annahmen sichtbar und bezeichnet den Zeitpunkt
einer Planprüfung, keine garantierte Einsatzfrist. Ohne betriebliche Zeitvorgabe
wird keine solche Marke erfunden. Eine Prognoseänderung verschiebt oder entfernt
sie mit sichtbarer Begründung.

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
Ein fehlender oder alter Betriebsstatus wird als unbekannt sichtbar. „Bahn 18
wetterbedingt nutzbar“ und „Bahn 18 tatsächlich freigegeben“ bleiben unterscheidbar:
Die zweite Aussage braucht einen Betriebsstatus. „Richtung 07“ allein sagt noch
nichts darüber aus, ob Seitenwind den Betrieb auf dieser Bahn zulässt.

**Beispiel, vollständig fiktiv:** „Bahn 18: Einschränkung könnte morgen zwischen
14 und 16 Uhr beginnen und zwei bis vier Stunden dauern. Richtung weiter 25.
Bei eurer angegebenen Vorbereitungszeit von 60 Minuten: Plan bis 13 Uhr prüfen.“
Verschiebt sich der früheste Beginn auf 16 Uhr, wird die Planungsmarke auf 15 Uhr
aktualisiert. Stabilität zwischen Wetterläufen ist sichtbar, aber kein Ersatz
für eine empirisch geprüfte Eintrittswahrscheinlichkeit.

Eine Betriebsrichtungsprognose existiert bereits öffentlich, mit achtstündigen
Intervallen. Unsere Differenzierungshypothese ist die für die Planung nutzbare
Verknüpfung von Bahn 18, bevorstehenden Änderungen und nachvollziehbaren
Aktualisierungen. Sie ist noch kein belegter Wettbewerbsvorteil.
[Bestehende Umwelthaus-Prognose](https://www.umwelthaus.org/fluglaerm/anwendungen-service/aktuelle-betriebsrichtung-und-prognose/)

## Was das Modell lernen soll

Die Team-Architektur bleibt ein kleines Klassifikationsmodell auf archivierten
Wetterprognosen, Windkomponenten, Horizont und damals bekanntem Ausgangszustand.
Sein Mehrwert liegt besonders in der Nähe der Grenzen: Bei fast gleichem
vorhergesagtem Rückenwind können Horizont, Böen und Windverlauf zu unterschiedlicher
späterer Nutzbarkeit führen. Ob das Modell diese Unterschiede nützlich lernt,
muss der Vergleich auf zurückgehaltenen Tagen zeigen.

**Wichtige Präzisierung der bisherigen Idee:** Regeln auf künftig **gemessenen**
Winden ergeben brauchbare Ersatzlabels für Regeln auf früher **vorhergesagten**
Winden. So kann das ML Vorhersagefehler lernen und die Regel-Baseline übertreffen.
Zirkulär wäre es, Ein- und Zielwerte lediglich aus derselben Wetterinformation
abzuleiten. Die Ersatzlabels belegen jedoch weder eine tatsächliche Freigabe
noch eine geflogene Richtung. Diese zweite Behauptung braucht Betriebsdaten.

Der Brief macht den Zustand zeitabhängig: Bahn 18 schließt bei Rückenwind
**≥15 kt** oder Seitenwind einschließlich Böen **>40 kt**. Die Richtung wechselt
bei Landungs-Rückenwind **≥10 kt** sofort; kleinerer positiver Rückenwind darf
höchstens **30 Minuten** bestehen. Eine Stunde mit Rückenwind allein belegt keine
30-minütige Persistenz. Für Labels braucht es passende Beobachtungsfolgen und
einen definierten Umgang mit Lücken; unterstündliche Interpolation bleibt eine
Modellannahme. Beide Zustände werden unabhängig ausgegeben, die zeitlichen
Übergänge müssen aber konsistent sein. [Team-Regeldatei](../ml/rules.json)

Zwei Randfälle werden nicht durch zusätzliche Annahmen versteckt: Die Anweisung
„bei Windstille oder variablem Wind aktuelle Richtung beibehalten“ steht in der Team-Regeldatei,
aber nicht ausdrücklich in der Abschrift. Variabler Wind ist außerdem weder
Windstille noch eine fehlende Messung. Und ein Wechsel von 25 auf 07 beseitigt
keinen zu hohen Seitenwind: Die Bahnachse bleibt gleich. Die binäre
Richtungsprognose darf deshalb nicht als Betriebsfreigabe dargestellt werden.
Dies sind Abgleichpunkte für den Original-Brief, keine neu erfundenen Regeln.
Auch der genaue Geltungsbereich der allgemein formulierten Seitenwindregel
bleibt bis zum Originalabgleich offen.

Ein synthetisches Gegenbeispiel wurde nachgerechnet, jeweils mit Ausgangsrichtung
25: 20 Minuten Ostwind mit 6 kt und danach 40 Minuten Windstille behalten 25 bei;
eine ganze Stunde Ostwind mit 2 kt führt nach Ablauf der Toleranz zu 07. Beide
haben denselben mittleren Windvektor von 2 kt aus Ost. Der Zeitverlauf enthält
hier entscheidende Information, die im Stundenmittel verloren geht.

Die verlangten Wahrscheinlichkeiten werden gegen die benannte Labelart bewertet
und nach Möglichkeit kalibriert. Ein Wert weit weg von 0,5 beschreibt zunächst
die Entschiedenheit des Modells. Er beweist weder Zuverlässigkeit noch eine
gemeinsame Sicherheit beider Bahnaussagen. Ebenso ergibt eine stündliche
Zustandswahrscheinlichkeit noch keine Wahrscheinlichkeit für den nächsten
Wechselzeitpunkt. Zeitfenster brauchen eine eigene Überdeckungs-/Breitenprüfung.

## Woran die Idee bestehen muss

Die Demo spielt einen belegten historischen Wechsel und ein Zeitfenster ohne
Wechsel nach. Sie zeigt nur Informationen, die damals verfügbar waren, und blendet
anschließend den tatsächlich eingetretenen Zustand ein. Ein einzelner Fall zeigt
den Ablauf; mehrere zeitlich getrennte Ereignisse müssen die Prognosegüte tragen.
Fehlen echte Betriebslabels, wird dieselbe Ansicht ausdrücklich als Prüfung gegen
Wetterregel-Ersatzlabels gezeigt. Sie belegt dann die Wetterkorrektur, aber noch
keinen gewonnenen Vorlauf gegenüber einer tatsächlichen Tower-Entscheidung.

- Vergleich: Zustand beibehalten und reine Wetterregel; Umwelthaus zusätzlich,
  falls dessen damalige Prognosen verfügbar sind.
- Bahn 18: übersehene Sperrungen, Fehlalarme pro Tag, Fehler bei Beginn/Dauer.
- Richtung: übersehene/falsch angekündigte Wechsel und Fehler des Wechselzeitfensters.
- Für beide: Vorwarnzeit und Ergebnisse nach Prognosehorizont, insbesondere +48 h.
  Die Güte auf langen unveränderten Zeitabschnitten genügt nicht.
- Wahrscheinlichkeiten: Brier-Score und Kalibrierung, getrennt für beide Ziele.
- Jede Warnung wird höchstens einem tatsächlichen Ereignis zugeordnet. Ein
  ganztägiges Warnfenster zählt nicht automatisch als hilfreicher Treffer:
  zulässige Fensterbreite und Mindestvorlauf werden vorher festgelegt.
- Für die Planprüfung zählt eine Warnung nur dann als rechtzeitig, wenn sie vor
  der tatsächlichen Änderung minus benötigter Vorbereitungszeit verfügbar war.
  Verschiebungen, Rücknahmen und dauerhaft aktive Warnstunden werden mitgezählt.
- Zeitliche Trennung von Training und Prüfung, ohne überlappende Zielzeiträume;
  aktuelle Zustände und Prognose-Updates dürfen nicht aus der Zukunft einfließen.

Bei echten Betriebslabels bleiben bekannte nichtwetterbedingte Sperrungen im
Gesamtergebnis sichtbar; nach Ursache wird zusätzlich ausgewertet. Unbekannte
Ursache ist kein Grund, einen bekannten Zustand auszusortieren. Fehlender Zustand
ist nicht bewertbar und wird als fehlende Abdeckung ausgewiesen.

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

Die Konzeptprüfung findet drei Schein-Erfolge, die die Bewertung ausschließen
muss: „immer unverändert“ mit hoher Stunden-Accuracy; ein 48 Stunden breites
Warnfenster, das jedes Ereignis trifft; richtiges Warnen erst nach Ablauf der
Vorbereitungszeit. Ereignis-Erkennung, Fensterbreite und nutzbarer Vorlauf machen
alle drei sichtbar. Rücknahmen und unbekannte Zustände bleiben im Bericht.

Die vorhandene +48-h-Stichprobe enthält 72 Zeitpunkte mit jeweils einem passenden,
vollständigen Windmesswert. Das belegt den Datenanschluss. Standort, Einheiten und
Mittelungsfenster müssen vor einem Gütevergleich angeglichen werden; Böen und
Betriebszustände sind dadurch noch nicht vollständig abgedeckt. Die zwei
Windbeispiele aus dem Brief wurden nachgerechnet: 330°/20 kt ergibt 17,32 kt
Rückenwind auf 18; 090°/20 kt ergibt 18,79 kt auf 25. Modellgüte, Kalibrierung,
Wechselzeitfenster und Disponenten-Nutzen sind weiterhin ungeprüft.

Für die sechs Stunden konzentriert sich die Umsetzung auf diese Zeitleiste,
die Begründung eines Ereignisses und den historischen Vergleich. Flugtracking,
Personaloptimierung und Anschlussflugberechnung gehören nicht zur ersten Demo.
