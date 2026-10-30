# Vollständige Literaturverzeichnisse und Quellenhinweise

Maschinelle Originaltextauszüge für Provenienz; originale PDF-Dateien sind maßgeblich. PDF-Seiten sind 1-basiert. Keine eigene Übersetzung.

## eurocontrol_smartwx2021

===== PDF PAGE 59 / 61 =====

EUROCONTROL   Network Management Directorate 

Edition Number:   1-1   Edition Validity Date:   04-03-2021   Classification:   Green   Page:   53 

References 

[1]   Network Function Implementing Rule EU 2019/123; 

[2]   NM ATFCM Operations Manual edition 24.1 from 18 January 2021; 

[3]   Cross-border Procedure Operational Instruction from 2020; 

[4]   Arrival Planning Information (API) Implementation Guide edition 1.0   from 01 July 2020; 

[5]   Report of the APOC/CONTINGENCY Task Force (from 2018); 

[6]   Report of the APOC-NMOC Task Force (from 2020); 

[7]   Reports of the NDOP Airport Integration Task Force (from 2018 and 2019); 

[8]   European Commission “Study on the current level of protection of air passenger rights in

the EU” from January 2020, Ref [8]; 

[9]   European Commission “Commission Staff Working Document: IMPACT ASSESSMENT

Accompanying the document Proposal for a regulation of the European Parliament and of

the   Council amending Regulation   (EC) No 261/2004   establishing   common   rules on

compensation and assistance to passengers in the event of denied boarding and of

cancellation or long delays of flights and Regulation (EC) No 2027/97 on air carrier liability

in respect of the carriage of passengers and their baggage by air” from 13/03/2013, Ref [9]. 



## eurocontrol_nor2025

===== PDF PAGE 65 / 66 =====

EUROCONTROL   Network Manager 

Edition Number:   1.0   Edition Validity Date:   04-05-2026   Classification:   Green   Page:   56 

References 

[1]   EUROCONTROL   Air   Navigation   Inter-site   Acronym   List   (AIRIAL) 

http://www.eurocontrol.int/airial/definitionListInit.do?skipLogon=true&glossary 

Uid=AIRIAL 

[2]   Reporting   Assumptions   and   Descriptions   Document 

https://www.eurocontrol.int/publication/reporting-assumptions-and- 

descriptions 

[3]   European Network Operations Plan 2025_2029 

eurocontrol-nop-2025-2029-ed-2.pdf 

[4]   Flight Efficiency Plan 

https://www.eurocontrol.int/publication/flight-efficiency-plan 



## eurocontrol_atmap2011

===== PDF PAGE 25 / 37 =====

22 

9   Reference documents 

   ICAO Annex 3 “Meteorological Services for International Air Navigation”, in particular

Appendix 3 "Technical specifications related to Meteorological observations and reports." 

   ICAO Annex 14 “Aerodromes” 

   Aerodrome Design Manual (ICAO Doc 9157) 

   Airport Services Manual (ICAO Doc 9137) 

   Manual of Aircraft Ground De-icing/Anti-icing Operations (CIAO Doc 9640) 

   Definition of freezing conditions in the Swedish AIC circular B160/2002 

   Definition of freezing conditions in the "Fly Fokker" magazine "Safe Cold Weather Operation"

issued in November 2009 

   FAA Advisory Circular (AC No: 150/5200-30C) "Airport Winter Safety and Operations" ;

Dated: 12/09/08 (09 December 2008) 

   Winter Operation at Zurich Airport (Revision 8 dated 1.11.2009) 

10 PL/SQL description of the algorithm 

The first version of the algorithm has been developed in PL/SQL on Oracle Toad. This query

language used for databases permit also the use of procedural programming.

Once a METAR is parsed and insert into the METAR database, it is available for processing.

Each METAR is treated individually by a function specially design for each weather class. The result

is stored in a table that contains basic information about the METAR and all the results from the

previous functions: 

   METAR id number; 

   airport; 

   date, time; 

   functions result.

The second processing built a table that contains basic information of each day and the final results: 

   airport; 

   date; 

   number of METAR provided during 16 hours analysed; 

   average value of each weather class results; 

   average value of the sum of each weather class results; 

   main cause of bad weather with a minimum of R   ≥   0.5; 

   status of the day; 

   relevant KPIs computed at day level (optional). 

Parsed

METAR

Processed

METAR

Daily

results

Parsed

METAR

Processed

METAR

Daily

results 

Figure 13 Weather algorithm: databases flowchart. 



## nlr_tailwind2001

===== PDF PAGE 21 / 26 =====

-21-

NLR-TP-2001-003 

6   References 

[1]   Private communication with Eric Poquillon, JAA-DGAC-CEV, Toulouse, France, 2000.

[2]   Private communication with Joop Wagenmakers, Aviation Consultant, The Netherlands,

2000.

[3]   Critchley, JB & Foot, PB,"UK CAA Wake Vortex Database: Analysis of incidents

reported between 1982 and 1990," CAA PAPER 91015, 1991. 

Acknowledgements 

The authors would like to thank Mr. Eric Poquillon and Mr. Joop Wagenmakers for providing

valuable information on tailwind operations and certification. The authors also thank Mr.

Franck Iannarelli of EADS Airbus for his help. 



## nlr_crosswind2001

===== PDF PAGE 45 / 46 =====

-45-

NLR-TP-2001-217 

7   References 

1.   Anon. ,"Aviation Safety, FAA has not Fully Implemented Weather-Related

Recommendations," GAO/RCED-98-30, 1998.

2.   Wieringa, J., "Gust Factors over Open Water and Built-up Country,", Boundary-Layer

Meteorology, 1973 (pages 424-441).

3.   Van Es, G.W.H. et. al., "Safety Aspects of Aircraft Performance on Wet and Contaminated

Runways", paper presented at the 10 
th  
annual European Aviation Safety Seminar (FSF),

Amsterdam, March 16-18, 1998.

4.   Anon. , "Fokker flight test certification reports", Fokker Aircraft.

5.   "Private communication with Boeing Commercial Airplane Group", Dept. of Flight

Operations Engineering", 1998.

6.   Fender, C.,"Published Crosswind Values," FAA, 1996. 



## eurocontrol_coda2024

===== PDF PAGE 15 / 17 =====

CODA Digest Annual 2024 

Weather 

71 (WO)   DEPARTURE STATION 

72 (WT)   DESTINATION STATION 

73 (WR)   EN ROUTE OR ALTERNATE 

75 (WI)   DE-ICING OF AIRCRAFT, removal of ice and or snow, frost prevention excluding unserviceability of equipment 

76 (WS)   REMOVAL OF SNOW, ICE, WATER AND SAND FROM AIRPORT 

77 (WG)   GROUND HANDLING IMPAIRED BY ADVERSE WEATHER CONDITIONS 

Air Traffic Flow Management Restrictions 

81 (AT)   ATFM due to ATC EN-ROUTE DEMAND CAPACITY, standard demand capacity problems 

82 (AX)   ATFM due to ATC STAFF EQUIPMENT EN-ROUTE, reduced capacity caused by industrial action or staff shortage,

equipment failure, military exercise or extraordinary demand due to capacity reduction in neighbouring area 

83 (AE)   ATFM due to RESTRICTION AT DESTINATION AIRPORT, airport and or runway closed due to obstruction, industrial

action, staff shortage, political unrest, noise abatement, night curfew, special flights 

84 (AW)   ATFM due to WEATHER AT DESTINATION 

Airport and Government Authorities 

85 (AS)   MANDATORY SECURITY 

86 (AG)   IMMIGRATION, CUSTOMS, HEALTH 

87 (AF)   AIRPORT FACILITIES, parking stands, ramp congestion, lighting, buildings, gate limitations, etc. 

88 (AD)   RESTRICTIONS AT AIRPORT OF DESTINATION, airport and or runway closed due to obstruction, industrial action,

staff shortage, political unrest, noise abatement, night curfew, special flights 

89 (AM)   RESTRICTIONS AT AIRPORT OF DEPARTURE WITH OR WITHOUT ATFM RESTRICTIONS, including Air Traffic

Services, start-up and pushback, airport and or runway closed due to obstruction or weather 0F 

1 
, industrial action, staff

shortage, political unrest, noise abatement, night curfew, special flights 

Reactionary 

91 (RL)   LOAD CONNECTION, awaiting load from another flight 

92 (RT)   THROUGH CHECK-IN ERROR, passenger and baggage 

93 (RA)   AIRCRAFT ROTATION, late arrival of aircraft from another flight or previous sector 

94 (RS)   CABIN CREW ROTATION, awaiting cabin crew from another flight 

95 (RC)   CREW ROTATION, awaiting crew from another flight (flight deck or entire crew) 

96 (RO)   OPERATIONS CONTROL, re-routing, diversion, consolidation, aircraft change for reasons other than technical 

Miscellaneous 

97 (MI)   INDUSTRIAL ACTION WITH OWN AIRLINE 

98 (MO)   INDUSTRIAL ACTION OUTSIDE OWN AIRLINE, excluding ATS 

99 (MX)   OTHER REASON, not matching any code above 

SOURCE: IATA – Airport Handling Manual (730 & 731) 

Standard IATA Delay Code Sub-Codes (AHM 731) 

73 (WR)   WEATHER: EN ROUTE OR ALTERNATE 

Z   OUTSIDE AIRCRAFT LIMITS 

Y   OUTSIDE CREW LIMITS 

X   ETOPS 

81 (AT)   ATFM DUE TO ATC EN-ROUTE DEMAND CAPACITY, standard demand capacity problems 

Z   ATC ROUTEING 

Y   HIGH DEMAND OR CAPACITY 

X   ENVIRONMENTAL 

W   WEATHER 

G   OTHER 

82 (AX)   ATFM DUE TO ATC STAFF EQUIPMENT EN-ROUTE, reduced capacity caused by industrial action or

shortage or equipment failure, extraordinary demand due to capacity reduction in neighbouring area 

Z   INDUSTRIAL ACTION 

Y   EQUIPMENT FAILURE 

X   STAFF SHORTAGE 

W   MILITARY ACTIVITY 

V   SPECIAL EVENT 

1  
Restriction due to weather in case of ATFM regulation only, else refer to code 71 (WO) 


===== PDF PAGE 16 / 17 =====

CODA Digest Annual 2024 

83 (AE)   ATFM DUE TO RESTRICTION AT DESTINATION AIRPORT, airport and or runway closed due to obstruction,

industrial action, staff shortage, political unrest, noise abatement, night curfew, special flights 

Z   HIGH DEMAND   ATC CAPACITY 

Y   INDUSTRIAL ACTION 

X   EQUIPMENT FAILURE 

W   STAFF SHORTAGE 

V   ACCIDENT   INCIDENT 

U   MILITARY ACTIVITY 

T   SPECIAL EVENT 

S   NOISE ABATEMENT NIGHT CURFEW 

P   HIGH DEMAND AIRPORT FACILTIES 

G   OTHER 

85 (AS)   MANDATORY SECURITY 

Z   MANDATORY SECURITY CHECK 

Y   SECURITY CONTROL CHECKPOINTS 

X   BAGGAGE AVI SECURITY 

W   BAGGAGE IDENTIFICATION UNLOADING INTENDED 

V   AIRPORT TERMINAL SECURITY 

U   AIRLINE AIRCRAFT SECURITY CHECK 

T   EXTRAORDINARY SECURITY EVENTS 

G   OTHER 

86 (AG)   IMMIGRATION, CUSTOMS, HEALTH 

Z   IMMIGRATION EMMIGRATION 

Y   CUSTOMS 

X   HEALTH 

G   OTHER 

87 (AF)   AIRPORT FACILITIES, parking stands, ramp congestion, lighting, buildings, gate limitations, etc. 

Z   PARKING STANDS LIMITATION NO PARKING STANDS AVAILABLE, EXCLUDING EARLY ARRIVALS 

Y   RAMP CONGESTION, ABNORMAL STAND ACCESS LIMITATION (NON-ATC) 

X   BUILDINGS 

W   GATE LIMITATION   NO GATE AVAILABLE EXCLUDING EARLY ARRIVALS 

V   BAGGAGE SORTING SYSTEM DOWN   SLOW 

U   NO PUSH BACK CLEARANCE DUE TO INFRASTRUCTURE (NON-ATC) 

T   JET BRIDGE INOPERATIVE 

S   LACK OF CHECK IN COUNTERS 

R   AIRFIELD   ELECTRICAL SYSTEM FAILURE 

P   PASSENGER TRANSPORT SYSTEM FAILURE 

N   PUBLIC ADDRESS FLIGHT INFORMATION DISPLAY SYSTEM FAILURE 

M   INSUFFICIENT FIRE COVER 

J   LATE POSITIONING OF AIRCRAFT (WHEN RESPONSIBILITY OF AIRPORT) 

I   SERVICE ROAD RESTRICTION 

H   LATE ARRIVAL OR LACK OF FOLLOW ME VEHICLE 

G   ANY OF THE ABOVE AT THE DESTINATION AIRPORT 

89 (AM)   RESTRICTIONS AT AIRPORT OF DEPARTURE WITH OR WITHOUT ATFM RESTRICTIONS, including Air

Traffic Services, start-up and pushback, airport and/or runway closed due to obstruction or weather. 

Z   ATC DEMAND/CAPACITY 

Y   ATC INDUSTRIAL ACTION 

X   ATC STAFFING 

W   ATC EQUIPMENT 

V   ATC ACCIDENT/INCIDENT 

U   MILITARY ACTIVITY/SPECIALFLIGHTS/VIP 

T   ATC SPECIAL EVENT 

S   ATC WEATHER 

O   ENVIRONMENTAL BENEFIT, DELAYED START-UP/PUSHBACK DUE TO USE OF REDUCED STANDARD TAXI TIMES 

N   ATC ENVIRONMENTAL 

M   AIRPORT CLOSURE 

L   RUNWAY/TAXIWAYCLOSURE 

K   MISCELLANEOUS START-UP DELAY (LOCAL ATC) 

J   LOST FLIGHT PLAN BY ATC 

I   LATE PUSHBACK GIVEN DUE TO OTHER REASONS THAN INFRASTRUCTURE 

H   CONTRUCTION WORK/MAINTENANCE 

G   OTHER 

93 (RA)   AIRCRAFT ROTATION, LATE ARRIVAL OF AIRCRAFT FROM ANOTHER FLIGHT 

Z   LATE ARRIVAL DUE DEPARTURE DELAY AT PREVIOUS STATION 

Y   LATE ARRIVAL DUE ENROUTE DELAY 

X   LATE ARRIVAL DUE DELAY AFTER LANDING 

W   LATE ARRIVAL DUETO HIGH DEMAND FOR DESTINATION STATION 

V   LATE ARRIVAL DUE TO WEATHER AT DESTINATION 

U   LATE ARRIVAL DUE TO TECHNICAL REASONS 



## DWD2022 und übrige Berichte

Kein zusammenhängendes akademisches Literaturverzeichnis. Sämtliche Fußnoten/Quellenangaben sind in den vollständigen PDFs und Seitenextrakten erhalten. DWD2022 verweist u.a. auf EUROCONTROL PRR2022/NOR2022 (PDF31), ICICLE (PDF52), ICON-Migration und ICAO METPWGMOG7/IP15 (PDF53), EUR-SWIM Registry (PDF56). Diese weiteren Originale wurden nicht zusätzlich beschafft.
