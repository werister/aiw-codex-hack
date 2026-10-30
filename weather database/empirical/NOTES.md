# Empirische Wetterliteratur: Volltextprüfung

Stand: 30.10.2026. Gelesen wurden Borsky2019 (17 PDF-Seiten), Schultz2018 (19), Rodriguez2021 (9), Sasse2003 (10, Web-PDF), Stevens2019 (6, Web-PDF), Allan2000 (7). Die 2022er Zeitschriftenfassung von Rodríguez-Sanz war nicht im Volltext zugänglich. Lektüre umfasst Haupttext, Tabellen, Schlussfolgerungen und Quellenverzeichnis. Keine Neuberechnung mit Original-Flugdatensätzen. Seitenangaben bezeichnen gedruckte Seiten, sofern nicht ausdrücklich PDF-Seiten angegeben. Die Original-PDFs bleiben unverändert. Textauszüge sind Suchhilfen; insbesondere Borsky enthält fehlerhaft extrahierte Ziffern. Für dessen Tabellen 1–4 und A1–A14 wurden zusätzlich gerenderte Seiten gelesen.

Hauptzweck dieser Sammlung ist, allgemeine Ursachen und Verspätungskaskaden zu verstehen und BTS-Auswertungen korrekt einzuordnen. FRA ist ergänzender Anwendungskontext, kein behauptetes Trainingsziel der BTS-Daten. Wetter beeinflusst Kapazität und Abfertigung; Auslastung, zeitlicher Rückstau und Folgeumläufe bestimmen, wie daraus Verspätung wird. Ursachenanteile aus administrativen Meldungen, Korrelationen mit beobachtetem Wetter und geschätzte kausale Zusatzeffekte sind unterschiedliche Messgrößen. Die unten genannten Modelle und Fallstudien dürfen deshalb nicht als unmittelbar vergleichbare Rangliste von Wetterursachen gelesen werden.

## Borsky & Unterberger (2019)

[Original und DOI](https://doi.org/10.1016/j.ecotra.2019.02.002), CC BY-NC-ND 4.0. Methoden: Difference-in-Differences für Regen, Schnee und Wind; Prais–Winsten für Temperatur, Flughafen-/Zeitkontrollen. Zehn US-Flughäfen, Verbindungen untereinander, 2012–2017; Tabellen nennen 2.146.535 Beobachtungen (Fließtext rundet anders). Tab.1–3, S.17: bevorzugte DiD-Schätzungen Regen 13,470 bzw. stärkste Klasse 23,280 Minuten, Schnee 11,500, Wind ≥16 mph 2,016 und ≥25 mph 3,422 Minuten. Kein allgemeiner 23-Minuten-Mittelwert. Tab.4, S.18: ≤−3°C 2,058 Minuten. Hitze nicht signifikant; seltene Extreme schränken Aussagekraft ein.

Grenzen: S.12/15–16 selektiert Verspätungen <300 Minuten, setzt Tagesreset voraus und diskutiert durch Folgeverzögerungen verletzbare Kontrollgruppen. Tab.A13, S.25 zeigt Sensitivität der Effektgröße gegen Ausreißergrenze. Niederschlagsschwellen sind zwischen Fließtext und Tabellen unterschiedlich gerundet; nicht als operative Grenzwerte übernehmen. MPH sind keine Knoten, Windrichtung/Böen werden nicht als FRA-Betriebsregeln modelliert. Für FRA: Begründung lokaler Kalibrierung und zeitlicher Nachwirkung; keine OD25/07- oder RWY18-Prognose und kein Nachweis für 48-Stunden-Prognosegüte. Sasse2003 als zitierte Primärquelle vollständig nachverfolgt.

## Schultz et al. (2018)

[DLR-Original](https://elib.dlr.de/123469/), CC BY 4.0. 20,5 Mio. Flugdatensätze 2013, 84 europäische Flughäfen; FRA etwa 440.000 Bewegungen. METAR → fünf ATMAP-Kategorien → Gesamtverspätungsverteilungen; Burr-Anpassung mit Maximum Likelihood nach Flughafengröße (S.14, Tab.6). FRA: S.9/Abb.5 berichtet 3,39 Minuten mehr Ankunftsverspätung je zusätzlichem täglichen Scorepunkt, R²=87%; Abb.5 betrifft bereits verspätete Flüge, nicht alle Flugbewegungen. Das ist deskriptive Regression gruppierter Mediane, keine validierte Stundenprognose. S.11: aus 2013 abgeleiteter Schwellenwert 2,7, nicht universell gültiges Sicherheitslimit.

Besonders nützlich: Tab.5, S.9 zeigt ähnliche Gesamtscores bei drastisch verschiedenen Ausfallquoten (2% gegenüber 58% Ankunft/64% Abflug). Wetterkomponenten daher getrennt erhalten. S.12/Abb.11 diskutiert Nachwirkungen; S.16 warnt explizit: modellierte Verspätung enthält sämtliche Ursachen und Reaktionen, sonst droht Doppelzählung. Fehlende Flugzeugregistrierungen verhindern saubere Umlaufanalyse (S.3). Für FRA: gute Wettermerkmale/Erklärungsebene, aber ATMAP ersetzt weder Windkomponenten noch Brief-Grenzwerte oder Zustandswechselregeln. Referenz37 ATMAP2011 wird in der Europa-Spur geprüft; Referenz36 Buxi/Hansen2013 nur bibliografisch verfolgt.

## Sasse & Hauf (2003)

[Verlags-PDF](https://rmets.onlinelibrary.wiley.com/doi/pdf/10.1017/S1350482703005036), Free Access, Copyright RMetS. Vollständig im Web gelesen; lokaler Originaldownload durch Cloudflare blockiert. Zehn ausgewählte Gewittertage 1997/1998 versus je fünf Referenztage/Jahr; Auswahl laut S.23 ausdrücklich nicht repräsentativ. DFS-STANLY misst Abweichungen idealisierter Flugwege, nicht einfach Gate-Ankunftspünktlichkeit. Tab.3, S.29: im Mittel 112 Flugzeuge, 1.021 Gesamt-, 280 Referenz- und 741 zusätzliche Minuten pro Ereignis; das sind Summen, keine Minuten pro Flug.

Interner Fehler: Schluss S.30 vertauscht Jahre gegenüber Abstract/Tab.3. Nachrechnung der Tabellenwerte: Zusatz-/Referenzsumme 1997 = 5.135/810 ≈6,34; 1998 =2.270/1.990 ≈1,14. Auch S.27 bezeichnet 14–20 UTC als vier Stunden; Tab.3 enthält das sechsstündige Intervall. Diese Fehler nicht fortschreiben.

Für FRA: Gewitter im Anfluggebiet und anschließende Warteschlangen getrennt betrachten; historische Flughafenkonfiguration und geringe Fallzahl verhindern direkte Übertragung. Keine Untersuchung von OD25/07 oder RWY18. Referenz Allan/Gaddy2000 vollständig gelesen.

## Rodríguez-Sanz, Cano & Rubio Fernández (2021), Konferenzfassung

[IOP-Original](https://doi.org/10.1088/1757-899X/1024/1/012107), CC BY 3.0. Dies ist die 9-seitige PDF-Konferenzfassung, nicht die 19-seitige Emerald-Zeitschriftenfassung 2022 (10.1108/AEAT-12-2020-0318). Madrid-Barajas 2015–2018, >750.000 Flüge; Hybrid-Bayes-Netze, 13 Variablen; MCMC mit drei Ketten/100.000 Iterationen (S.4–5). Betrachtet Anflug, Taxi-in und In-block; Abschnitt6 nennt bessere Tests und Übertragbarkeit als zukünftige Arbeit.

Prüfbefunde: S.4/Tab.2 dupliziert X2/X3 und lässt X1 aus; Tab.3 definiert angebliches Off-block-Delay mit AIBT statt tatsächlichem Off-block-Zeitpunkt. S.5 nennt 180–360° „east“, geografisch widersprüchlich. S.6 wiederholt exakt 3,39 Minuten und R²=87%, die Schultz2018 für Frankfurt berichtet; keine dort sichtbare eigene Regressionstabelle erlaubt unabhängige Bestätigung für Madrid. Das ist eine auffällige Übereinstimmung, kein belegter Nachweis eines Kopierfehlers.

Für FRA: probabilistische Abhängigkeiten konzeptionell nützlich. Aussagen über Kausalität aus Bayes-Netzen allein sind methodisch nicht gesichert; Schwellen und Trefferwahrscheinlichkeiten nicht übernehmen. Keine demonstrierte 48h-RWY-Prognose. Vollständiges Quellenverzeichnis enthält 47 Einträge.

## Stevens (2019)

[NOAA-Original](https://repository.library.noaa.gov/view/noaa/45302), Copyright AMS. Sechs Seiten vollständig via Web gelesen; lokaler Download durch Serverzugriff blockiert. METAR/ASOS 1973–2017 an 30 US-Flughäfen; ein letzter Messwert/Stunde vermeidet Übergewicht zusätzlicher Schlechtwettermeldungen. Theil–Sen-Trends und Kendall-Signifikanz, keine Delay-Regression. S.618/Abb.2: 28 von 30 Flughäfen mit sinkender IFR-Häufigkeit, 18 signifikant. S.616–617 definiert einheitliche Vergleichsgrenzen 2.500ft/3 statute miles; lokale Verfahren können abweichen.

Tab.1, S.617 ergibt Odds Ratio ≈46 für geringe Sicht bei geringer Taupunktdifferenz. S.619 beschreibt dies als etwa 46-fache Wahrscheinlichkeit: Odds Ratio ist jedoch kein Risikoverhältnis. Aus den Tabellenzellen ergibt sich Risikoverhältnis ≈39,6, daher nur Odds Ratio zitieren. Sensorwechsel und verkürzte Reihen zweier Flughäfen werden behandelt.

Für FRA: Sicht/Taupunktdifferenz ergänzen windbasierte Prognosen; US-IFR-Kriterien nicht als FRA-Regel nutzen. Keine Untersuchung von Betriebsrichtungswechseln, RWY18 oder Prognosekalibrierung. Alle 24 Referenzeinträge sind gesondert dokumentiert.

## Allan & Gaddy (2000), nachverfolgte Referenz

[MIT-Original](https://archive.ll.mit.edu/mission/aviation/publications/publication-files/ms-papers/Allan_2000_ARAM_MS-14148_WW-10159.pdf). Sieben PDF-Seiten vollständig gelesen. Deckblatt verlangt für erneutes Serverposting Genehmigung; PDF und Volltextextrakt daher nur lokale Prüfkopien, nicht ins Repo übernehmen. Referenz aus Sasse2003.

Newark September1998–August1999: ASQP deckt etwa 60% des Verkehrs ab; Auswahl von Tagen mit mindestens zwei aufeinanderfolgenden Stunden mittlerer Verspätung >15min (PDF-S.2). Tab.1, PDF-S.3: Gewitter 31,8%, niedrige Wolken/Sicht 35,3%, Starkwind 13,2% der erfassten Verspätung. Klassifizierung überlappt Wettermechanismen; keine kausale Attribution aller Minuten. Queuing-Modell nutzt konstruierte Nachfrage/Kapazität, teils abgeleitet aus beobachteten Ankunftsraten. Tab.2, PDF-S.6 trennt modellierte potenzielle von tatsächlich durch Nutzer berichteten Nutzenfällen. Geldbeträge hängen von historischen Kostensätzen und Faktor0,8 für Folgeverspätung ab.

Für FRA: Vorhersage von Beginn/Ende kapazitätsbegrenzenden Wetters und Windrichtung relativ zur Bahn sind sachlich relevant. Keine Übernahme von Newark-Limits, Kosten oder 1–3h-Nutzenbehauptung als Beleg für 48h-FRA-Güte.

## Anwendung auf den Projektbrief (eigene Ableitung)

Der Brief verlangt stündliche Wahrscheinlichkeiten über 48 Stunden für RWY18-Nutzbarkeit, OD25/07, Sicherheit und nächsten Wechsel. Keine der geprüften Studien validiert genau diese Aufgabe. Briefregeln (10kt Landungsrückenwind sofort; 0<TW<10 bis30min; RWY18 TW≥15 geschlossen; Crosswind einschließlich Böen >40 geschlossen) stammen aus dem Projektbrief, nicht aus diesen Papern. Für Implementierung: historische Prognosen zum jeweiligen Ausgabezeitpunkt, Zustandslogik mit Zeitgedächtnis und lokaler Kalibrierung gegen tatsächliche Betriebsdaten. METAR beobachtet den Zustand; es darf nicht als künftige Prognose in rückwirkende Tests gelangen. Wetter-/Delay-Zusammenhang begründet weder Wahrscheinlichkeitsschärfe noch sicherheitskritische Freigabe. Forschungsvalidierung sollte Kalibrierung und Wechselzeitfehler separat messen.

## Referenzketten und Archivstatus

- Borsky2019 → Sasse2003 → Allan2000: vollständig gelesen, Sasse nur Web zugänglich, Allan lokal ohne erneute Veröffentlichung.
- Rodriguez2021 → Schultz2018: vollständig gegengeprüft; identische Ergebniswerte ausdrücklich gekennzeichnet.
- Schultz2018 Ref37 / Rodriguez2021 Ref47 → ATMAP2011: Zuständigkeit Europa-Spur.
- Schultz2018 Ref36 → Buxi/Hansen2013: Titel, Autoren, DOI 10.1016/j.trc.2012.12.006 bestätigt; kein frei herunterladbarer Artikel gefunden. Gleichnamige Buxi2012-Dissertation ist eine andere Publikation, nicht als Ersatz-Volltext ausgegeben.
- Referenzdateien erfassen die kompletten Bibliografien der gelesenen Kerntexte, aber belegen nicht, dass jeder zitierte Titel selbst vollständig gelesen wurde. Keine unbegrenzte rekursive Recherche.
