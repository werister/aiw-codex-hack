# Schatzsuche: von Aussagen zu Originaldaten und Analyseideen

Diese Pfade wurden tatsächlich verfolgt. „Gelesen“ bedeutet Volltext einschließlich Quellenverzeichnis, „offen“ bezeichnet eine begrenzte Zugangslücke. Analyseideen sind eigene Vorschläge, keine bereits erzielten BTS-Ergebnisse.

## 1. Wetterverursachung und Nachwirkung auseinanderhalten

**Ausgangspunkt:** Borsky2019, Einleitung S.11, beruft sich für Wettereffekte in Deutschland auf Sasse/Hauf2003.

**Originalquelle geprüft:** [Sasse & Hauf2003](https://doi.org/10.1017/S1350482703005036), alle zehn Seiten. Daten: DFS-STANLY-Bewegungen, DWD-METAR/Radar/Warnungen und Blitzdaten; zehn ausgesuchte Gewittertage. Details im empirischen NOTES-Eintrag.

**Gewinn durch die Quellenprüfung:** Die oft zitierte Zahl 740 ist eine ereignisbezogene Summe zusätzlicher Flugminuten, keine individuelle Flugverspätung. Gewitter am Airport, Gewitter im Anflugraum und nachlaufende Warteschlangen sind zeitlich verschiedene Zustände. Eine bloße „TS im aktuellen METAR“-Variable verfehlt Teile des Wirkungsfensters. Der Primärtext enthält einen Jahreszahlendreher im Schluss, der durch Table3 erkennbar wird.

**Konkrete BTS-Analysechance:** Bei Flughafen-Stunden nicht nur Wetter zum planmäßigen Abflug prüfen, sondern Wetterbeginn sowie 1–6 Stunden danach; Tageszeit, Verkehrsangebot und Vorverspätung getrennt kontrollieren. Beobachtete Reaktion nach Wetterende nicht automatisch als neue Primärursache zählen. Für echte Kaskaden einzelne Flugzeugumläufe verknüpfen; ein monatliches Airport-Carrier-Aggregat erlaubt das nicht. Das sind Analysevorschläge, keine kausalen Resultate der Aggregatdaten.

## 2. Warum besseres Wetter nicht sofort Pünktlichkeit bedeutet

**Ausgangspunkt:** Sasse2003, S.22 und Quellenliste S.30, verweist für vermeidbare Verzögerungen auf Allan/Gaddy2000.

**Originalquelle geprüft und lokal heruntergeladen:** [Allan & Gaddy2000, MIT](https://archive.ll.mit.edu/mission/aviation/publications/publication-files/ms-papers/Allan_2000_ARAM_MS-14148_WW-10159.pdf), sieben PDF-Seiten. ASQP, METAR, ITWS-Berichte, CATER-Flugstreifen und technische Kapazitätstabellen. Veröffentlichungsrecht beschränkt: nur Quellenlink/Notizen ins Repo.

**Gewinn:** Der Befund ist stark messmethodenabhängig: ASQP erfasst nur einen Teil des Verkehrs; die Zuordnung erfolgt nach primärer Wetterklasse des Tages. Der Ansatz trennt meteorologisch reduzierte Kapazität von zusätzlich anhaltender Kapazitätsbegrenzung durch Verkehrsmanagement. Das ist kein Beweis, dass alle „Nicht-Wetter“-Meldungen tatsächlich wetterunabhängig sind. Projektiertes Einsparpotenzial und realisierte, durch Nutzer gemeldete Verbesserungen werden im Original getrennt.

**Konkrete BTS-Analysechance:** NAS-Delay und Weather-Delay nicht als unabhängige physikalische Ursachen interpretieren. Berichtskategorien können unterschiedliche operative Stationen derselben Störung abbilden. Prüfen, ob hohe Weather/NAS-Minuten im Folgemonat bzw. bei Carrier-Airport-Paaren gemeinsam mit Late-Aircraft-Minuten auftreten; solche Aggregatkorrelationen als Hinweise, nicht als identifizierte Übertragungswege bezeichnen. Für stündliche Kausalketten sind Flugdatensätze plus Wetter erforderlich.

## 3. Einen Wetterindex zerlegen statt als Ursache behandeln

**Ausgangspunkt:** Rodríguez2021 verweist in Ref27 auf Schultz2018; Schultz Ref37 und Rodríguez Ref47 führen zur [ATMAP-Originalnote2011](https://www.eurocontrol.int/sites/default/files/publication/files/algorithm-met-technical-note.pdf). ATMAP-Volltextprüfung übernimmt die Europa-Spur.

**Tatsächlich gegengeprüft:** Rodríguez2021 und Schultz2018 vollständig. Die auffällig identischen 3,39min/R²87% sind in Schultz eindeutig Frankfurt zugeordnet. Im Madrid-Konferenztext fehlen sichtbare eigene Regressionstabellen für die Wiederholung. Daher nicht zwei unabhängige Studien als Bestätigung zählen.

**Gewinn:** Schultz Tab.5 enthält Tage mit praktisch gleichem Gesamtscore, aber stark unterschiedlicher Ausfallquote. Der Score ist eine Verdichtung mehrerer Bedingungen; Zusammenspiel und betriebliche Reaktion bleiben wichtig. Die Burr-Verteilungen enthalten Gesamtverspätung und dürfen nicht zusätzlich zu separat modellierten Folgeverspätungen addiert werden.

**Konkrete BTS-Analysechance:** Ursachenanteile zusätzlich nach Saison/Flughafen und Ereignisschwere vergleichen. Neben mittlerer Verspätung Ausfallquote, Anteil verspäteter Flüge und Verspätungsminuten pro verspätetem Flug ausweisen. Dadurch werden Fälle sichtbar, in denen viele Flüge annulliert wurden und die beobachtete Verspätung der verbleibenden Flüge irreführend niedrig wirkt.

## 4. Offene, ergiebige Fortsetzung: probabilistische Kapazität

Schultz2018 Ref36 nennt Buxi/Hansen2013, [DOI](https://doi.org/10.1016/j.trc.2012.12.006), [Autoreninstitut](https://its.berkeley.edu/publications/generating-day-operation-probabilistic-capacity-scenarios-weather-forecasts). Dort ist die Verwendung von TAF/STRATUS für probabilistische Kapazitätsszenarien und anschließende GDP-Entscheidungen bibliografisch/über Abstract bestätigt. Der Zeitschriftenvolltext war nicht frei beschaffbar. Die [frei verfügbare Dissertation Buxi2012](https://escholarship.org/uc/item/9gz9c989) ist eine andere Publikation; nicht als gelesener Artikel ausgegeben.

Analysechance: Operationalisierungsfehler vermeiden, indem Wetterprognose, Kapazitätsprognose und Delay-Kosten getrennt evaluiert werden. Der Abstractwert von 17–23% modellierter Kostensenkung ist ohne Volltextprüfung kein geeigneter belastbarer Projekt-KPI.

## Quelleninventar statt vorgetäuschter Vollständigkeit

Die kompletten Quellenlisten der gelesenen Kerntexte sind in *.references.txt bzw. den Original-PDFs vorhanden. Alle Bibliografien wurden gelesen; nicht jeder darin zitierte Titel wurde heruntergeladen oder vollständig geprüft. Die drei oben dokumentierten Pfade liefern konkrete neue Unterscheidungen für Ursachen- und Kaskadenanalysen. Kein Quellenpfad macht BTS-Daten zu Frankfurt-Trainingsdaten.
