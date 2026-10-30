# Gewinnen mit einem nachweisbaren Planungsvorsprung

Stand: 30. Oktober 2026. Strategie und Sprechentwurf für Hugo/Luca als Beitrag zu
WP6; keine Änderung der Arbeitspakete oder der laufenden Implementierung. Drei
Minuten Pitch sind eine Arbeitsannahme, keine bestätigte Veranstaltervorgabe.

**Umsetzung:** Im Cockpit führt „Pitch mode“ zu `/pitch`. Schritt 1 zeigt das
interaktive, als synthetisch gekennzeichnete Windbeispiel. Schritt 2 lädt gespeicherte
Fälle und blendet deren DFLD-Richtungslabels erst auf Knopfdruck ein; Tageswechsel
setzen die Aufdeckung zurück. Modell, Wetterregel und Persistenz werden auf
denselben vorhandenen Stunden verglichen. Eine eingegebene Vorbereitungszeit
ergibt eine bedingte Planungsmarke. Schritt 3 zeigt den separaten Qualitätsbericht
einschließlich Fehlalarmen und Grenzen der Bahn-18-Labels. Die gespeicherten Fälle
weisen Version v2 aus; sie sind historische Illustrationen und dürfen nicht als
Nachweis des neueren Modellstands oder einer exakt damaligen Datenverfügbarkeit
ausgegeben werden. Die Anwendung kennzeichnet diese Trennung.

## Die Empfehlung

**Eine überraschende Betriebssituation zeigen, dann am historischen Fall belegen,
dass unsere Prognose früher zur Vorbereitung taugt.** Der Satz, der hängen bleiben
soll: „Die Richtung bleibt gleich. Trotzdem ändert sich der Abflugbetrieb.“

Der Produktanspruch lautet: **„Wir machen bevorstehende Änderungen an den Bahnen
früh genug sichtbar, damit der Flughafen seine Vorbereitung planen kann.“**
Das ist ein zu belegender Nutzen. Wie viel Vorlauf das Modell tatsächlich bringt,
muss vor dem Pitch aus der Auswertung kommen.

Die [Brief-Abschrift](../frankfurt-airport-operating-direction-forecast.md) verlangt
48 Stunden, zwei Ziele, Sicherheit, nächsten Wechsel und Bewertung bei 1/6/24 h.
Repository, Model Card und Jury-Testtage bleiben Pflicht. Ein offizielles
Punkteschema liegt nicht vor. Problemverständnis, demonstrierter Nutzen und ein
funktionierendes Produkt sind unsere Strategieannahmen, keine erfundenen Jurygewichte.
Der [Originalquellen-Abgleich](challenge-source-audit.md) bleibt offen.

## Der überraschende Fakt und sein sichtbarer Beweis

**Eine unveränderte Betriebsrichtung 25 bedeutet nicht, dass Bahn 18 weiter
nutzbar ist.** Fraport beschreibt Bahn 18 als weitgehend unabhängig von der
Betriebsrichtung des Parallelbahnsystems.
[Fraport: Operation Direction](https://www.fraport.com/en/sustainability/dialog-with-neighbors/noise-and-air/flight-operations/operation-direction.html)

Eine einfache, nachgerechnete Illustration nach den transkribierten Challenge-Regeln:

| Situation | Wind | Richtung 25 | Bahn 18 |
| --- | --- | --- | --- |
| A | aus 250°, 20 kt | 20 kt Gegenwind, bleibt 25 | 6,84 kt Gegenwind, wetterbedingt nutzbar |
| B | aus 330°, 20 kt | 3,47 kt Gegenwind, bleibt 25 | 17,32 kt Rückenwind, nach der 15-kt-Regel nicht nutzbar |

Annahmen: Ausgangsrichtung 25, Böen ebenfalls 20 kt, keine anderen Sperrgründe;
beide Situationen liegen unter der Seitenwindgrenze. Dies ist ein **synthetisches
Regelbeispiel**, keine beobachtete Schließung und kein Nachweis einer ML-Leistung.
Rechenwerte und Annahmen: [pitch-evidence-check.json](pitch-evidence-check.json).

**Inszenierung in 15 Sekunden:** vereinfachte Flughafengrafik, zwei Zeitleisten.
Windrichtung verschieben. Der große Pfeil „25“ bleibt stehen, Bahn 18 wechselt
zu „wetterbedingt nicht nutzbar“. Keine zusätzliche Flugzeugsimulation erforderlich.
Die Grafik erklärt das Problem; der folgende Rücktest beweist die Vorhersage.

Die Challenge nennt ungefähr sechs von zehn Abflügen über Bahn 18. Im Pitch
gegebenenfalls ausdrücklich „laut Challenge-Pitch“ sagen; keine daraus abgeleitete
Behauptung von 60 % verlorener Flughafenkapazität. Primärbeleg hierfür ist derzeit
die [Pitch-Mitschrift](../briefing/transcripts/FRAALLIANCE_PITCH_FULL.md).

## Was an unserem Angebot neu sein muss

Eine öffentliche Betriebsrichtungsprognose existiert bereits: Das Umwelthaus zeigt
mehrere Tage, Wahrscheinlichkeiten und achtstündige Zeitfenster mit drei Updates
pro Tag. „Wir sagen die Richtung 48 Stunden voraus“ allein ist keine belastbare
Differenzierung. [Umwelthaus-Prognose](https://www.umwelthaus.org/fluglaerm/anwendungen-service/aktuelle-betriebsrichtung-und-prognose/)

Unsere zu prüfende Kombination: **stündliche 07/25- und Bahn-18-Prognosen,
erkennbare Änderungsfenster und nachvollziehbare Aktualisierungen, bewertet auf
rechtzeitiges Vorbereiten.** Ob dies bestehende betriebliche Systeme übertrifft,
ist unbekannt. Ein Vergleich mit dem öffentlichen Angebot belegt keine Lücke in
den internen Systemen von Flughafen oder Flugsicherung.

**Empfohlene Pitch-Persona: die Schichtleitung im Ground Handling.** Ihre eine
Entscheidung lautet: Soll für das angekündigte Zeitfenster eine alternative
Einsatzverteilung vorbereitet werden? Die Bahnfreigabe ist eine andere Entscheidung
und bleibt bei den dafür Zuständigen. Das entspricht der Nutzerhypothese im
[Konzept](runway-concept.md); reale Zuständigkeit und Vorbereitungszeit sind zu prüfen.

Die Team-UI wurde für Tower-Personal geplant. Diese Pitch-Empfehlung muss vor der
Probe mit dem Team abgestimmt werden; sie ändert weder dessen Produktentscheidung
noch den UI-Code. In der Erzählung nicht zwischen Tower-Freigabe und
Ground-Handling-Planung als angeblich derselben Handlung wechseln.

## Die drei Minuten

| Zeit | Bild und Handlung | Aussage, die die Jury mitnehmen soll |
| --- | --- | --- |
| 0:00–0:25 | Zwei Windzustände, unveränderter 25-Pfeil, Bahn 18 wechselt Zustand | Eine Richtungsprognose allein beschreibt den Betrieb nicht vollständig |
| 0:25–0:45 | 48-h-Ansicht mit beiden Spuren; nächste Änderung hervorgehoben | Genau diese bevorstehende Änderung machen wir sichtbar |
| 0:45–1:45 | Historischen Ausgabezeitpunkt zeigen; Zukunft zunächst verborgen; Prognose und Baselines einfrieren, anschließend Beobachtung aufdecken | Die Vorhersage entstand mit damals verfügbaren Daten; Vorlauf und Fehler sind nachprüfbar |
| 1:45–2:20 | Kleine Ergebnistabelle: 1/6/24 h, plus +48 h sofern geprüft; Wechsel erkannt/verpasst, Fehlalarme, Vorlauf | Der Einzelfall ist Teil einer ausgewerteten Testmenge |
| 2:20–2:45 | Eine Planprüfung mit vom Betrieb vorgegebener Vorbereitungszeit | Prognose wird für eine konkrete Vorbereitung relevant |
| 2:45–3:00 | Model Card und ein klarer nächster Schritt | Das Team kennt Daten, Grenzen und den Weg zu einem Pilotversuch |

**Zielskript für die Demo, derzeit kein gemeinsamer Leistungsnachweis:** Die
Ansicht ist inzwischen umgesetzt; gespeicherte Replays und der neuere Qualitätsbericht
haben getrennte Herkunft. Der folgende Text setzt passend belegte Ergebnisse
für den jeweils genannten Modellstand voraus. Bei fehlenden Ergebnissen
auf eine ausdrücklich als Regelillustration bezeichnete Demo kürzen und den
ML-Nachweis als offen nennen.

**Sprechentwurf:**

„Die Betriebsrichtung bleibt 25. Und trotzdem kann Bahn 18 für Abflüge ausfallen.
Hier sehen Sie ein vereinfachtes Beispiel: Die Windgeschwindigkeit bleibt gleich,
aber der Wind dreht. Auf den Parallelbahnen bleibt Gegenwind. Auf Bahn 18 entsteht
zu viel Rückenwind. Deshalb braucht der Flughafen zwei getrennte Prognosen.

Unsere Anwendung zeigt beide Zustände für die nächsten 48 Stunden. Sie hebt hervor,
wann eine Änderung zu erwarten ist und wie unsicher deren Zeitpunkt noch ist.

Jetzt springen wir zu einem historischen Prognosezeitpunkt. Alles rechts davon
war damals Zukunft. Diese Wetterdaten waren verfügbar, diese Änderung hat unser
Modell angekündigt. Jetzt blenden wir ein, was später tatsächlich beobachtet wurde.
[Hier ausschließlich geprüfte Ergebnisse einsetzen: Labelart, Vorlauf und
Vergleich zur Regel-Baseline.]

Dieser Fall gehört zu [N] zeitlich zurückgehaltenen Ereignissen. Davon haben wir
[K] rechtzeitig erkannt, bei [F] Fehlalarmen pro Tag. [Den Vergleich zur Baseline
und die benötigte Vorbereitungszeit ergänzen.] Die Stundenqualität bei 1, 6 und
24 Stunden sehen Sie hier; die Quellen und Grenzen stehen in unserer Model Card.

So kann die Schichtleitung im Ground Handling früher prüfen, ob sie einen anderen Einsatzplan
vorbereiten muss. Unser nächster Schritt ist ein begleitender Vergleich mit echten
Betriebsdaten. Wir wollen zeigen, wie viel nutzbare Vorbereitungszeit entsteht.“

**Vor Einsatz des Entwurfs:** Ansicht und Rücktest einmal vollständig vorführen;
jede Klammer durch geprüfte Zahlen ersetzen oder den Satz entfernen. 1/6/24-h-
Ergebnisse sind noch zu liefern. Einen 48-h-Vorsprung nur mit eigenem Nachweis
nennen. Liegen nur Wetterregel-Ersatzlabels vor, muss der Demo-Text
„später nach Wetterregeln abgeleitet“ statt „tatsächlich beobachteter Betrieb“ sagen.
Ein solcher Vergleich beweist noch keinen Vorsprung vor einer Tower-Entscheidung.

## Der Beweismoment entscheidet über die Demo

Ein Fall muss Ausgabezeit, verfügbare Eingabedaten, Modellversion, Prognose,
Baseline und spätere Zielwerte zusammenbringen. Für alle Modelle gelten derselbe
damalige Wissensstand, Horizont und dieselbe Zielart. Regeln auf später gemessenem
Wetter sind Labels; Regeln auf damaligen Wetterprognosen sind die Vergleichsprognose.

Den Hauptfall vorher nach einer nachvollziehbaren Regel wählen, etwa dem ersten
vollständig belegten Wechsel im reservierten Testabschnitt. Ergebnis der gesamten
Testmenge mitzeigen. Eine zweite vorbereitete Ansicht zeigt einen Fehlalarm,
verpassten Wechsel oder unsicheren Fall. Diese Reserve ist für die Fragerunde,
nicht zwingend für die drei Minuten.

Für einen Bahn-18-Fall brauchen wir echte historische Nutzbarkeits-/Statuslabels.
Ausbleibende Starts reichen nicht. Wenn nur eine tatsächliche Richtungsänderung
belegt ist, beweist der Rücktest nur die Richtungsprognose; das Bahn-18-Regelbeispiel
bleibt getrennt. Zeigt nur ein kürzerer Horizont Skill, diesen nennen. Ein 48-h-
Ausgabefenster belegt keine treffsichere Warnung 48 Stunden vor jedem Ereignis.

**Konkreter Rechercheansatz:** Die am 30.10. abgerufene Umwelthaus-Seite zeigt
„BR 07 Ost seit 29. Oct., 09.54 Uhr“ und nennt DFS als Statusquelle. Das ist ein
Kandidat für einen belegten Richtungswechsel, noch keine vollständige Historie.
Jahr/Zeitzone, vorheriger Zustand und zeitliche Abdeckung sichern. Unser archivierter
Prognoselauf vom 28.10. ist ein möglicher Eingang, dessen damalige Veröffentlichungszeit
noch geprüft werden muss. [Quelle](https://www.umwelthaus.org/fluglaerm/anwendungen-service/aktuelle-betriebsrichtung-und-prognose/)

## Die Reihenfolge bis zur Abgabe

| Priorität | Ergebnis | Passende bestehende Verantwortung |
| --- | --- | --- |
| 1 | Prüfbarer Daten-/Labelpfad, CLI für Jury-Tage, faire Baselines und erste gehaltene Testmenge | Kai und Daten-/Modellarbeitspakete |
| 2 | Ein reproduzierbarer Demo-Fall mit Ausgabezeit, verdeckter Zukunft und späterer Auflösung; beide Prognosespuren | Jayden mit Modellteam |
| 3 | Model Card und eine geprüfte Ergebnistabelle; Labelart und Quellen direkt bei Zahlen | Hugo/Luca mit Qualitätspaket |
| 4 | Drei-Minuten-Pitch samt Fragerunde und lokal gespeicherter Demo-Aufzeichnung | Hugo präsentiert; Luca bedient und übernimmt als Backup |
| 5 | Bestehende 3D-Szene nur verwenden, wenn sie den ersten Moment schneller erklärt und stabil läuft | Separates optionales Demo-Paket |

Parallel soll Luca einem FraAlliance-Ansprechpartner einen konkreten Fall zeigen:
Welche Vorbereitung wäre dadurch früher möglich? Wie viel Vorlauf braucht sie?
Wann wird ein Fehlalarm lästig oder teuer? Antworten mit Rolle und Kontext
festhalten; nur tatsächlich erhaltene Aussagen als Feedback darstellen.

Nach Teamplan: **15:00 vollständiger Probelauf**, optionales 3D bei Unreife streichen;
vor **16:00** Abgabe von Repository, Model Card und Jury-Prognosen prüfen. Nach der
Abgabe Presentation/Demo-Handoff abschließen, bevor Jayden um 16:45 geht; Finals
um 17:00. Termine stammen aus den [Teamnotizen](../briefing/README.md), der
3D-Abbruchpunkt aus [WP9](../openspec/changes/wp9-3d-demo/tasks.md).

Die technische Übergabe umfasst gespeicherten Datenstand, Startfolge und eine
Aufzeichnung desselben Falls. Live-Ausfall darf den Beweismoment nicht verhindern.
Bei der ersten Probe muss eine unbeteiligte Person anschließend sagen können:
Was wird prognostiziert? Was wurde nachgewiesen? Wer kann dadurch früher was tun?
Dieser menschliche Verständlichkeitstest wurde noch nicht durchgeführt.

## Drei Argumente für die Fragerunde

**„Warum reicht ein gutes Accuracy-Ergebnis nicht?“** In einem konstruierten Jahr
mit 8.760 Ein-Stunden-Prognosen und 156 getrennten Wechseln erreicht „nächste
Stunde wie jetzt“ 98,22 % korrekte Zustände und kündigt keinen Wechsel im Voraus
an. Die 156 stammen aus dem Pitch; die Zeitreihe und das Ergebnis sind synthetisch.
Das ist keine gemessene FRA-Baseline und kein 24-/48-h-Ergebnis. Darum bewerten wir
auch Vorlauf, verpasste Ereignisse, Fehlalarme und die Breite der Warnfenster.

**„Warum ML, wenn die Grenzwerte bekannt sind?“** Die Grenzen sind bekannt; ob und
wann eine Wetterprognose sie in der Realität überschreitet, ist unsicher. Das
Modell kann systematische Unterschiede zwischen früher vorhergesagtem und später
gemessenem Wind lernen. Es muss diesen Vorteil gegenüber derselben Regel auf dem
damaligen Forecast zeigen. Ohne besseren Testwert behaupten wir keinen ML-Vorteil.

**„Wie groß ist die Wirkung einer Bahn-18-Sperrung?“** Die im Pitch genannten
60 % sind ein Abfluganteil. Unter der vereinfachenden Annahme unveränderter
Nachfrage und vollständiger Verlagerung auf Center steigt dort die angefragte
Last von 40 % auf 100 %, also auf das 2,5-Fache. Das ist keine ausführbare
Kapazität und keine gemessene Verspätung. Für Euro-Ersparnisse fehlen Daten.

## Ergebnis dieses Better-Durchgangs

Der fachliche Zusatz ist eine prüfbare Siegthese statt mehr Funktionsumfang. Die
Rohbasis sind Pitch-Mitschrift, Brief-Abschrift, öffentliche Betreiberquellen und
die vorhandenen Forecast-Proben. Die Methode kombiniert Quellenprüfung,
nachgerechnete Gegenbeispiele, Rücktest-Entwurf und unabhängige Jury-Kritik.

Geprüft: Windkomponenten bestätigen den unveränderten 25-Zustand bei verändertem
Bahn-18-Regelzustand; der synthetische Persistenzfall bestätigt 98,22 % bei null
Vorwarnungen. Ein unabhängiger Review bevorzugt den Bahn-18-Einstieg gegenüber
der abstrakten Accuracy-Falle. Der inzwischen vorhandene Qualitätsbericht enthält
Modellgüte nach Horizont. Offen bleiben eine gemeinsame Versionszuordnung mit den
Replays, tatsächliche Bahn-18-Sperrungen, betrieblicher Vorlauf, Nutzenfeedback und
ein zeitlich gemessener menschlicher Probelauf.

## Prüfung der eingebauten Ansicht

`cd web && npm run build` baut einschließlich TypeScript-Prüfung erfolgreich;
`/pitch` wird statisch vorgerendert. Die acht Replay-Tests bestehen mit
`node --test src/lib/pitch-replay.test.mjs`; ESLint besteht für die geänderten
Web-Dateien. Die Demo-Konstanten entsprechen den genutzten Feldern in `ml/rules.json`.

Ein lokaler Browserdurchlauf prüft Einstieg aus dem Cockpit, Wind-A/B samt
Tastaturbedienung, Aufdecken und Zurücksetzen der Ergebnisse, 42/48 bzw. 40/48
belegte Stunden, Planungsmarke und fehlgeschlagenen Datenabruf ohne alte Ergebnisse.
Alle drei Schritte passen bei 390 px ohne Seitenüberlauf; Desktop- und mobile
Screenshots wurden geprüft. Es gab keine Browser-Laufzeitfehler. Diese Checks
belegen die Ansicht, nicht einen produktiven Einsatz oder gewonnenen Vorlauf.
