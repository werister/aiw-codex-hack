# Was sich an unserer Flughafen-Prognose verbessert hat

Unser Fortschritt: Die Prognose startet mit dem richtigen bisherigen Zustand,
und ihre Qualität wird genauer gemessen. Dafür bleibt das bestehende Modell
erhalten. Die wichtigsten Änderungen sind auch ohne ML-Vorkenntnisse verständlich.

## 1. Die Uhr wird nicht mehr auf null gesetzt

Für einen Richtungswechsel zählt nicht nur, woher der Wind kommt, sondern auch,
wie lange bereits Rückenwind besteht. Bisher vergaß die Regel-Prognose beim
Start diese vergangene Zeit.

Beispiel: Um 12 Uhr besteht seit 20 Minuten leichter Rückenwind. Wenn er laut
Vorhersage anhält, muss die Berechnung diese 20 Minuten berücksichtigen. Das tut
sie jetzt in allen drei Rechenwegen: mit dem normalen Wettermodell, mit der
Kombination mehrerer Wettermodelle und im Ersatzbetrieb ohne trainiertes Modell.

## 2. Ein historischer Test darf nicht in die Zukunft schauen

Eine um 12 Uhr erstellte Prognose darf keine Wetterdaten benutzen, die erst um
14 Uhr herausgegeben oder abgerufen wurden. Vorhandene Zeitangaben werden jetzt
auch bei archivierten Wetterdaten geprüft. Sind mehrere Zeitangaben vorhanden,
müssen alle passen.

Nicht jedes Archiv enthält den genauen Veröffentlichungszeitpunkt. Wo er fehlt,
bleibt unsere bisherige vorsichtige Zeitannahme ausdrücklich als Einschränkung
sichtbar.

## 3. Ein Richtungswechsel bleibt ein Ereignis

Mehrere Prognosen können denselben späteren Wechsel vorhersagen. Wir zeigen
deshalb jetzt sowohl die bisherigen Ergebnisse je Prognosefenster als auch
eine zusätzliche Auswertung tatsächlich unterschiedlicher Wechsel.

Ein bereits vor Prognosestart erfolgter Wechsel zählt nicht als vorhergesagter
künftiger Wechsel. Eine Vorhersage in die falsche Richtung zählt auch dann
nicht als Treffer, wenn die Uhrzeit ungefähr passt. Fehlalarme werden mitgezählt.

## 4. Bei Bahn 18 sagen wir genauer, was wir wissen

Wetterbedingt ungeeignete Stunden sind selten. Eine sehr hohe Gesamtquote kann
deshalb täuschen: Wer immer „nutzbar“ sagt, liegt oft richtig und kann trotzdem
alle problematischen Stunden verpassen.

Die Auswertung zeigt jetzt Treffer, übersehene Fälle und Fehlalarme. Dafür muss
das gesamte untersuchte Zeitfenster bekannt sein. Fehlende Daten gelten nicht
als „alles offen“. Die Zahlen beschreiben überlappende Prognosefenster, keine
Anzahl voneinander unabhängiger Flughafenschließungen.

Fehlt nur die Information zu Bahn 18, bleibt eine vorhandene Beobachtung der
Betriebsrichtung trotzdem sichtbar. Beim Testtag 28. Oktober sind dadurch
wieder alle 47 aufgezeichneten Richtungswerte enthalten; vorher waren es nur 40.

Außerdem kann die kurzfristige Prognose den zuletzt beobachteten Zustand stärker
berücksichtigen. Wie stark, wird nur mit älteren Trainingsdaten festgelegt.
Fehlen dort Schließungsfälle, bleibt die ursprüngliche Modellwahrscheinlichkeit.

## 5. Die Anzeige bleibt über 48 Stunden vollständig

Auch die Auswahl eines zukünftigen Testtags liefert die vollständige aktuelle
48-Stunden-Prognose. Dadurch geht ein vorher liegender, bereits vorhergesagter
Wechsel nicht mehr verloren. Der tatsächliche Ausgabezeitpunkt bleibt sichtbar.

## Ergebnis auf den zwölf historischen Testmonaten

Anteil der richtig vorhergesagten Betriebsrichtungen; jede Zeile vergleicht dieselben Stunden:

| Vorlauf | Unser Modell | Offizielle Regeln | Richtung einfach beibehalten |
|---|---:|---:|---:|
| 1 Stunde | 95,7 % | 93,1 % | 95,9 % |
| 6 Stunden | 92,7 % | 88,1 % | 88,8 % |
| 24 Stunden | 91,8 % | 87,7 % | 75,1 % |

Das sind Messwerte aus unserer historischen Auswertung, keine Zusage für jeden zukünftigen Tag. Bei einer Stunde Vorlauf liegt das einfache Beibehalten der Richtung etwas vorn.

**Offene Schwäche bei Bahn 18:** In 307 vollständig auswertbaren 24-Stunden-Fenstern erkennt das Modell 0 von 12 Fenstern mit einer aus Wetterdaten abgeleiteten Schließung. 1.125 Fenster sind ausgeschlossen. Das erlaubt noch keine belastbare Aussage über die Vorhersage tatsächlicher betrieblicher Schließungen.

## Was geprüft ist – und was noch offen bleibt

Die gezielten Fehlerfälle und die übrige ML-Testsuite bestehen mit **mehr als 100 Tests**.
Die zwölf zeitlich getrennten Testmonate, die Vergleichswerte und ihre Grenzen
stehen im [Modellbericht](MODEL_CARD.md). Dort vergleichen wir das Modell mit
„Richtung beibehalten“ und mit den offiziellen Regeln auf zwei Wettergrundlagen.

Der Fortschritt liegt vor allem in der zuverlässigeren Berechnung und der
ehrlicheren Auswertung. Ein allgemeiner Genauigkeitssprung gegenüber unserer
vorherigen Modellversion ist nicht belegt.

Die aufgezeichnete Betriebsrichtung ist eine öffentliche Näherung. Die Bahn-18-
Zielwerte werden aus Wetter und Regeln abgeleitet; sie sind keine bestätigte
Historie betrieblicher Schließungen. Die Testmonate haben bereits mehrere
Entwicklungsentscheidungen beeinflusst. Ein späterer, bisher unberührter Zeitraum
bleibt deshalb der nächste wichtige Praxistest.


Drei zusätzlich trainierte Modellideen und ihre Grenzen sind im
[Vergleich der Prognoseansätze](ml/PREDICTION_EXPERIMENTS.md) erklärt. Die
Messwerte rechtfertigen bisher keinen Austausch des bestehenden Modells.
