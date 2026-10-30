# Was bringt eine andere Art der Vorhersage?

**Ergebnis vom 30. Oktober 2026: Beide bisher abgeschlossenen Kandidaten verfehlen
unsere Verbesserungskriterien. Die laufende Prognose bleibt bei v6.**
Wir haben die Alternativen implementiert und gemessen. Ein anderer Modellansatz
allein ist noch kein Fortschritt.

## Die zwei Fragen hinter einer guten Prognose

„Welche Richtung gilt in 24 Stunden?“ ist nicht dasselbe wie „Wann kommt der
nächste Wechsel?“. Bei zwei Wechseln kann die Richtung nach 24 Stunden wieder
dieselbe sein. Für die Planung zählen deshalb richtige Stunden **und** erkannte
Wechsel, Fehlalarme und Vorwarnzeit.

## Was wir ausprobiert haben

1. **Eine andere Lernaufgabe:** Das Modell lernt, ob die spätere Richtung von der
   aktuellen Richtung abweicht. Daraus berechnet es die Wahrscheinlichkeit für
   Richtung 25. Merkmale und Größe des Lernverfahrens bleiben gleich. Das ist
   noch kein Modell des ersten Wechselzeitpunkts.
2. **Eine zusätzliche Wetterstimme:** Wir mischen die bisherige Modellprognose
   mit der offiziellen Regel auf der korrigierten Wetterkombination. Wie stark
   die Regel zählt, wird nur anhand älterer Daten gewählt. Fehlt ihr Eingang,
   bleibt die bisherige Prognose erhalten.

Beide nutzen die bestehenden 45 Merkmale und dieselben vier Testmonate Juli bis
Oktober 2026. Lernen und Gewichtswahl erfolgen jeweils vor dem Testmonat. Der
innere Validierungsabschnitt umfasst 60 Tage; Zielwerte über dessen Grenze
werden aus dem davorliegenden Training entfernt. Das zweite Verfahren wählt
zusätzlich je Vorlaufgruppe einen Mischanteil in Zehntelschritten.

## Gemessene Stundenprognose

Jede Zelle zeigt **Trefferquote / Brier-Fehler**. Ein kleinerer Brier-Wert ist
besser: Er bestraft falsche, sehr sichere Wahrscheinlichkeiten stärker.
Verglichen werden exakt die Vorläufe 1, 6, 24 und 48 Stunden, keine vermischten
Vorlaufbereiche. Je Zeile sind die ausgewerteten Stunden identisch.

| Vorlauf | Stunden | Bisheriges v6 | Andere Lernaufgabe | Zusätzliche Wetterstimme |
|---|---:|---:|---:|---:|
| 1 h | 469 | 94.67 % / 0.04127 | 92.96 % / 0.05117 | 94.46 % / 0.04097 |
| 6 h | 469 | 91.68 % / 0.06935 | 92.11 % / 0.06991 | 91.90 % / 0.06948 |
| 24 h | 460 | 91.30 % / 0.07659 | 91.09 % / 0.07658 | 91.30 % / 0.07656 |
| 48 h | 448 | 88.84 % / 0.09040 | 87.95 % / 0.09245 | 88.17 % / 0.09177 |

Bei sechs Stunden steigt die Trefferquote der Alternativen geringfügig, während
der Wahrscheinlichkeitsfehler wächst. Bei 48 Stunden verschlechtern sich beide
Werte. Kleine Einzelvorteile erfüllen damit unser Kriterium nicht: bessere
Wechselwarnungen ohne Verschlechterung der längeren Richtungsvorhersage.

## Was bei tatsächlichen Wechseln passiert

Ein echter Wechsel wird nur einmal gezählt. Ein passender Hinweis muss vor dem
Wechsel ausgegeben worden sein, die richtige Richtung haben und innerhalb von
±3 Stunden liegen. Mehrere falsche Hinweise zum selben Zeitpunkt werden zu
Warnungsgruppen zusammengefasst.

| Vergleich innerhalb derselben Ereignisstichprobe | v6 | Kandidat |
|---|---:|---:|
| Andere Lernaufgabe: erkannte Wechsel von 67 | 44 | 42 |
| Andere Lernaufgabe: falsche Warnungsgruppen | 50 | 59 |
| Andere Lernaufgabe: Fehlalarme je abgedecktem Tag | 0,416 | 0,491 |
| Wetterstimme: erkannte Wechsel von 65 | 41 | 41 |
| Wetterstimme: falsche Warnungsgruppen | 49 | 53 |
| Wetterstimme: Fehlalarme je abgedecktem Tag | 0,410 | 0,444 |

**Die beiden Versuche haben verschiedene Ereignisstichproben.** Beim ersten
bleiben vollständige Prognosefenster über Monatsgrenzen für die Ereignisprüfung
erhalten: 467 gültige Fenster und 120,25 abgedeckte Tage. Beim zweiten werden
Zielstunden hinter der Monatsgrenze entfernt: 443 gültige Fenster und 119,5 Tage.
Dort gab es vor der Prüfung der historischen Halb-Stunden-Daten 451 vollständige
Prognosen. In beiden Versuchen entfallen weitere acht Fenster wegen fehlender
historischer Abdeckung. Daher sind jeweils nur die beiden Werte **innerhalb**
einer Vergleichszeile unmittelbar vergleichbar. Die Stundenmetriken verwenden
in beiden Versuchen dieselbe zeitliche Grenze.

## Was diese Ergebnisse nicht beweisen

Juli bis Oktober wurden bereits während der Entwicklung von v6 betrachtet.
Die Gewichtswahl benutzt ihre Testwerte nicht, aber es ist trotzdem kein neuer,
unberührter Abschlusstest. Überlappende 48-Stunden-Fenster sind voneinander
abhängig. Kleine Unterschiede sind kein nachgewiesener allgemeiner Vorteil.
Die Zielrichtung stammt aus einer öffentlichen Betriebsaufzeichnung; die
Einschränkungen stehen im [Modellbericht](../MODEL_CARD.md).

Die geänderte Lernaufgabe zeigt insbesondere nicht, dass eine echte Vorhersage
des **ersten** Wechselzeitpunkts unmöglich wäre. Sie untersucht nur, ob die
Zielrichtung anders ist. Ein eigener Versuch für das erste Ereignis muss auch
zwei Wechsel sowie fehlende historische Abschnitte korrekt behandeln.

## Was wir aus anderen Projekten übernehmen können

Die [NASA-Wettbewerbssieger](https://github.com/drivendataorg/nasa-airport-config)
nutzten neben Wetter und Betriebsverlauf teilweise Verkehrsinformationen und
vorgelagerte Wechselmodelle. Die [MIT-Arbeit zur Konfigurationswahl](https://dspace.mit.edu/entities/publication/4056dede-4acc-4f64-8d5e-2bc7d4969c4e)
berücksichtigt auch die Neigung, eine bestehende Konfiguration beizubehalten.
Das stützt diese Fragestellungen, liefert aber keine übertragbare Frankfurt-Quote.

Der nächste größere Datenversuch sollte eine historische Quelle für bestätigte
Betriebsentscheidungen oder geplanten Verkehr ergänzen und ihren Zusatznutzen
separat messen. Nötig ist jeweils, was **damals bekannt** war. Heutige Live-Werte
ersetzen dieses Archiv nicht. Ein größeres Netz mit denselben Eingängen ist
hier noch keine belegte Verbesserung.

Die Einzelwerte, Gewichte und Daten-/Modellhashes stehen in
[challenger-results.json](challenger-results.json). Die optionale Forschungs-CLI
wird getrennt von der produktiven Vorhersage ausgeführt; sie aktiviert kein
neues Modell automatisch.

## Selbst ausführen

Im Projektordner mit installierten ML-Abhängigkeiten:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m ml.challengers \
  --candidate opposite-direction --out /tmp/runway-opposite
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m ml.challengers \
  --candidate physical-blend --out /tmp/runway-physical
```

Der Standard vergleicht Juli bis Oktober 2026. Die gespeicherten v6-Monatsmodelle
und die vorhandenen Eingabedaten müssen verfügbar sein. Ein Bericht hält die
Gewichte, Zeitgrenzen und Herkunft fest; die einzelnen Prognosezeilen bleiben
für weitere Auswertungen erhalten. Die Beispiele schreiben außerhalb des Repositories. Im Projekt sind nur eigene
Unterordner von `verification/` oder `resources/raw/` erlaubt. Der Befehl
schreibt keine produktiven Modelle oder Forecast-Dateien.

Eine erneute Auswertung derselben gespeicherten Zeilen braucht kein Training:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m ml.challengers \
  --candidate physical-blend --out /tmp/runway-physical --rescore
```


Prüfung der zusammengeführten CLI: Der vollständige Juli-Lauf für die zusätzliche
Wetterstimme reproduziert die Gewichte und Punktmetriken des ursprünglichen
Versuchs. Eine anschließende Auswertung aus den gespeicherten Zeilen liefert
dieselben Punkt- und Ereigniswerte. Das ist ein Paritätscheck für diesen Lauf;
die vollständigen Vier-Monats-Werte oben stammen aus den ursprünglichen
Versuchsläufen. Ein selbst mitgebrachter Cache ohne geprüfte Referenz wird im
Bericht ausdrücklich als ungeprüfte Eingabe markiert.
