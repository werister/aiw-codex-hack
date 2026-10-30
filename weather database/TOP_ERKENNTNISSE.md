# Top-Erkenntnisse: Wie Flugverspätungen entstehen

Stand: 30. Oktober 2026. Erster geprüfter Stand; weitere Quellenketten folgen. Ziel ist Ursachenverständnis, keine Übertragung amerikanischer Daten als Frankfurt-Trainingsdatensatz.

## 1. Ein großer Anteil der Verspätung wird von vorherigen Flügen weitergegeben

Eigene Auswertung des vollständigen BTS-Ursachenexports 2025: **49.886.915 von 124.695.986 erfassten Verspätungsminuten (40,01%)** stehen unter `late_aircraft_delay`. Airline-Ursachen tragen 31,83%, das National Aviation System 21,58%, die explizite Wetterkategorie 6,45% und Security 0,13% bei. 3.569 Minuten sind in den Ursachensummen nicht zugeordnet und werden nicht stillschweigend verteilt.

**Learning:** Ein Flug ist Teil eines Umlaufs. Die Analyse muss unmittelbare Störung und Weitergabe getrennt behandeln. Der Anteil von 40,01% zeigt keine Wetterquote und erlaubt nicht, alle Folgeverspätungen dem Wetter zuzurechnen.

Beleg: [unveränderter BTS-CSV-Export](bts/raw2025/Airline_Delay_Cause.csv), [Rechenergebnisse](bts/analysis_results.json), [Auswertungsskript](bts/analyze_bts.mjs), [BTS-Ursachendefinitionen](https://www.bts.gov/topics/airlines-and-airports/understanding-reporting-causes-flight-delays-and-cancellations).

## 2. Das Wetterfeld allein misst nicht den gesamten Wettereinfluss

`WeatherDelay` erfasst eine eigene administrative Kategorie. Wetter kann zusätzlich NAS-Verzögerungen und verspätete Vorflüge auslösen. **6,45% explizite Wetterminuten sind deshalb keine Schätzung des gesamten Wettereinflusses.** Ebenso wäre es falsch, sämtliche NAS- und Folgeverspätungen als wetterbedingt zu zählen.

**Schatzsuche:** Die BTS-Dokumentation verweist auf FAA/OPSNET für die Wetterunterteilung der NAS-Verzögerungen. Für konkrete Ursachenketten sind einzelne Flugumläufe und zeitlich/räumlich zugeordnete Wetterbeobachtungen ergiebiger als die fünf Hauptkategorien allein. [BTS-Originalerklärung](https://www.bts.gov/topics/airlines-and-airports/understanding-reporting-causes-flight-delays-and-cancellations).

## 3. Jahresmittel verdecken starke Unterschiede zwischen Monaten und Flughäfen

Eigene BTS-Auswertung 2025: Im Juli waren **27,71%**, im September **16,15%** der gemeldeten geplanten Ankünfte mindestens 15 Minuten verspätet. Die erfassten Verspätungsminuten je geplanter Ankunft lagen bei **22,84** bzw. **10,86**. Januar hatte mit **3,13%** eine höhere Ausfallquote als Juli (**2,58%**). Eine reine Pünktlichkeitskennzahl unterschlägt somit einen Teil der Störung.

Bei Flughäfen mit mindestens 100.000 gemeldeten geplanten Ankünften betrug der NAS-Anteil an den Verspätungsminuten beispielsweise **52,13% in Newark**, aber **12,74% in Charlotte**. Das beschreibt unterschiedliche gemeldete Störungsprofile; es identifiziert keine Ursache des Unterschieds und ist kein bereinigtes Flughafenranking.

**Learning:** Häufigkeit, Dauer, Ausfälle und Ursachenmix gemeinsam betrachten; Wetterbeobachtungen, Auslastung und Netzstruktur sind die nächsten erklärenden Daten. Beleg: [monatliche und Flughafenaggregate](bts/analysis_results.json).

## 4. Quellenprüfung schützt vor scheinbar präzisen, aber falsch interpretierten Zahlen

Sasse/Hauf berichten für historische Frankfurt-Gewitter im Mittel **741 zusätzliche Minuten über ein gesamtes Ereignis mit durchschnittlich 112 Flugzeugen**; das sind keine 741 Minuten pro Flug. Ihre Schlussfolgerung vertauscht zudem die Jahreszuordnung zweier Faktoren gegenüber Tabelle 3. Schultz et al. modellieren Gesamtverspätung einschließlich Folgeeffekten; diese Größe darf nicht erneut zu separat gezählten Folgeverspätungen addiert werden. Belege, vollständige Literaturverzeichnisse und Zugangsstatus werden in `empirical/` abgelegt.

Quellen: [Sasse & Hauf (2003), Tabelle 3](https://doi.org/10.1017/S1350482703005036), [Schultz et al. (2018), Abschnitt 5](https://elib.dlr.de/123469/).

## Datenbasis und Grenzen

Der BTS-Export enthält 22.687 Flughafen–Carrier–Monat-Zeilen, 364 Flughäfen, 21 Carrier-Codes und alle zwölf Monate 2025. Die verfügbaren Werte summieren sich auf 7.736.770 geplante Ankünfte, 1.685.334 verspätete Ankünfte, 118.168 Ausfälle und 21.106 Umleitungen. Dies ist die Population des abgefragten BTS-Exports, nicht sämtliche Flugbewegungen in den USA.

Elf Zeilen enthalten fehlende numerische Werte; fehlende Werte bleiben im Import `null`, Summen berücksichtigen verfügbare Werte. Zwölf Zeilen weichen bei der Minutenzuordnung ab (zusammen 3.569 Minuten, rund 0,0029% der erfassten Verspätungsminuten). Ursache der Abweichung ungeklärt. `_ct`-Felder sind anteilig zugeordnete Flugäquivalente, keine Anzahl eigenständiger Wetterereignisse. Diese Analyse enthält keinen Wetterdaten-Join, keine kausale Effektschätzung und keine Rekonstruktion individueller Flugumläufe.