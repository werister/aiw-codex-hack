# FraAlliance: Quellenabgleich und geschärfter Auftrag

Stand: 30. Oktober 2026. Ergebnis: **Kein originales Challenge-PDF oder Folienset
gefunden bzw. heruntergeladen.** Die vorliegende Abschrift ist eine brauchbare
Arbeitsgrundlage, aber noch kein seitengetreuer Quellenbeleg.

## Welche Unterlagen die Details festlegen sollen

| Unterlage | Wofür sie gebraucht wird | Fundstand |
| --- | --- | --- |
| FraAlliance „Frankfurt Airport Operating Direction Forecast“, One-Pager | Grenzwerte, Zustandsregeln, Abgabe und Bewertung | [Abschrift im Repo](../frankfurt-airport-operating-direction-forecast.md), eingeführt mit `b90eadd`; Original fehlt |
| FraAlliance Challenge-Pitch | Betriebsszenario, Bahngrafik, Geschäftswirkung | [Pitch-Mitschrift](../briefing/transcripts/FRAALLIANCE_PITCH_FULL.md); Folien fehlen |
| Veranstalter-Unterlagen zu Abgabe und Jury, sofern separat vorhanden | Format, Termin, Bewertungskriterien und Testtage | [Kick-off-Mitschrift](../briefing/transcripts/01_kickoff_organiser_and_codex_showcase.md) und [Zusammenfassung](../briefing/README.md); eigenständiges Folienset nicht bestätigt |

Die [Registrierungs-Mitschrift](../briefing/transcripts/03_registration.md) nennt
das Teilnehmer-Dashboard als Downloadort der Firmenbriefings, enthält aber weder
Dashboard-URL noch den erwähnten Kurzlink. Dieser Link ist beim Nutzer angefragt.

Gesucht wurde nach passenden Dateinamen in Downloads, Desktop, Documents und dem
Haupt-Checkout; zusätzlich nach heute geänderten PDF/PPT/PPTX-Dateien in Downloads
und Desktop bis eine Unterordnerebene. Die Suche in verbundenen Pages nach
„FraAlliance“ ergab keinen Treffer. Öffentliche Suchen bei AI Week, statworx und
OpenAI sowie die Prüfung der verlinkten Skripte der
[Veranstalterseite](https://ai-week-frankfurt.com/hack) ergaben keinen direkten
Download- oder Teilnehmer-Dashboard-Link. Das ist ein begrenztes Suchergebnis,
kein Nachweis, dass die Unterlagen nicht existieren.

## Anforderungen: vorläufig fixiert, Herkunft sichtbar

Alle Zeilen „Abschrift“ beziehen sich auf die jeweiligen Abschnitte der oben
verlinkten Markdown-Datei. Originalseiten und mögliche Fußnoten sind ungeprüft.

| Aussage | Herkunft | Konsequenz |
| --- | --- | --- |
| Jede Stunde bis +48 h: Nutzungswahrscheinlichkeit Bahn 18, OD 25/07, certainty und nächster Wechsel | Abschrift, Deliverables 1 | Zwei Zielgrößen; Auflösung nicht als minutengenaue Prognose verkaufen |
| Landungs-Rückenwind ≥10 kt: sofort wechseln; kleinerer positiver Rückenwind höchstens 30 Minuten | Abschrift, Operating direction | Ausgangszustand und zeitlicher Verlauf nötig; genau 30 Minuten von länger als 30 Minuten unterscheiden |
| Bahn 18: Rückenwind ≥15 kt schließt; Seitenwind einschließlich Böen >40 kt schließt eine Bahn | Abschrift, Wind and runway limits / Runway 18 | Grenzwerte 10/15 einschließlich, 40 ausdrücklich überschritten; Böenkomponente beachten |
| Geometrie für die Aufgabe: 250°T, 070°T, 180°T | Abschrift, Runway system | Beobachtungsrichtung und Berechnung müssen dieselbe Winkelreferenz verwenden |
| Zeitlich zurückgehaltene Daten, nur damals verfügbare Information; Güte bei 1/6/24 h | Abschrift, Deliverables 3 | Ausgabe-/Verfügbarkeitszeit prüfen; ein heutiger Reanalysewert ist kein damaliger Forecast |
| Repository, einseitige Model Card und Prognosen für Jury-Testtage; Vergleich mit tatsächlich geflogener OD | Abschrift, Deliverables 4 | Ersatzlabels separat ausweisen; Jury-Testtage sind in der Abschrift nicht benannt |
| Bei Windstille oder variablem Wind aktuelle OD beibehalten | Nur [Team-Regeldatei](../ml/rules.json), notes | Implementierungsannahme; Originalabgleich ausstehend. Fehlende Windrichtung nicht automatisch als variabel behandeln |
| Bedeutung von „certainty“ und genauer Geltungsbereich der Seitenwindregel | Abschrift ohne Definition bzw. mit allgemeiner Formulierung „the runway“ | Mit Original/FraAlliance klären; weder eine bestimmte Scoreformel noch die Anwendung auf alle Bahnen als bestätigt ausgeben |
| Kalibrierung, Fehlalarme, nutzbarer Vorlauf, Fensterbreite und zusätzlicher +48-h-Test | Eigene Konzeptvorschläge | Prüfen die Produktbehauptung; keine nachgewiesenen Jury-Pflichtmetriken |

## Better: tieferer Nachweis für dieselbe Idee

1. Ein Fachteam würde für jede Produktbehauptung Zielzustand, Quelle und
   Beweisführung festlegen. Wetterbedingte Nutzbarkeit ist nicht automatisch
   eine tatsächliche Betriebsfreigabe.
2. Die Rohbasis wären Original-Brief und Folien, archivierte Prognoseläufe samt
   damaliger Verfügbarkeit sowie tatsächliche Betriebszustände mit Zeitstempel.
   Aus Regeln erzeugte Labels bleiben als Ersatzlabels gekennzeichnet.
3. Methoden sind Quellenabgleich, gezielte Grenzfallprüfung und ein zeitgetreuer
   Rücktest gegen Regeln und Persistenz. Zuordnung und Breite von Warnfenstern
   werden vor der Bewertung festgelegt.
4. Unabhängiger Nachweis wären Treffer, Fehlalarme und nutzbarer Vorlauf auf
   zurückgehaltenen echten Ereignissen. Eine gute Demo oder hohe Sicherheit des
   Klassifikators genügt dafür nicht.

**Geschärfter Auftrag:** Baue die bereits geplante 48-Stunden-Prognose so, dass
jede Aussage über Bahn 18 und die Richtung auf eine benannte Zielgröße und Quelle
zurückgeht. Zeige am historischen Fall, was zum damaligen Ausgabezeitpunkt
vorhergesagt wurde, wann eine Änderung tatsächlich eintrat und ob daraus gegenüber
Regeln und Persistenz zusätzlicher Planungsvorlauf entstand. Fehlen echte Labels,
zeige das Ergebnis als Wetterregel-Vergleich und halte die Betriebsbehauptung offen.

Zwei Randfälle präzisieren die Darstellung: Variabler Wind ist keine Windstille;
ein Richtungswechsel beseitigt hohen Seitenwind auf derselben Bahnachse nicht.
Die Richtung allein darf deshalb nicht als Freigabe gelesen werden. Ein
zusätzliches Produktmodul ist dafür nicht nötig; entscheidend sind die Bedeutung
der vorhandenen Aussagen und die sichtbare Datenqualität.

## Was diese Runde nachgewiesen hat

Die vorhandene Abschrift trägt die oben aufgeführten Anforderungen. Die Annahme
zum variablen Wind stammt dagegen aus der Team-Regeldatei. Die Quellenprüfung
hat keinen Originalbeleg geliefert; die zuvor zu starke Bezeichnung „offizielle
Aufgabenstellung liegt vor“ wurde in den eigenen Konzept-/Ressourcendokumenten
präzisiert. Anwendungscode und Team-Regeln wurden nicht verändert.

Eine unabhängige Textprüfung bestätigte die offenen Punkte Originalquelle,
Windstille/variabler Wind, Seitenwind-Geltungsbereich und certainty-Definition.
Eine synthetische Geometrieprüfung ergibt bei Wind aus 160° mit 41 kt für beide
Richtungen 07 und 25 jeweils 41 kt Seitenwind. Das belegt die Aussage zur gleichen
Bahnachse, aber keine konkrete betriebliche Entscheidung. Die Grenze selbst
bleibt gemäß Abschrift strikt >40 kt.

Mit dem Dashboard-Link folgt der Originalabgleich: Originaldateien herunterladen,
Herkunft und SHA-256 dokumentieren, Seiten einschließlich Grafiken/Fußnoten prüfen,
Abweichungen in obiger Tabelle mit Seitenbeleg auflösen. Erst dann sind diese
Details gegen die Folien verifiziert. Modellgüte und betrieblicher Nutzen bleiben
bis zum Rücktest eigenständige offene Nachweise.
