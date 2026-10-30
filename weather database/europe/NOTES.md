# Europe: weather, capacity and flight delay

Research and reading date: 30 October 2026. Primary purpose: understand causes and mechanisms. Unless otherwise stated, page references mean **1-based PDF pages**; printed page numbers are sometimes added. Original files remain unchanged. Text files are machine extracts, not reliable transcriptions of every diagram. All publications discussed here are institutional reports, manuals or presentations, rather than independently peer-reviewed journal articles.

## Main findings

Weather changes usable capacity: a runway configuration becomes unavailable, separation or runway occupancy increases, apron work stops, aircraft require de-icing, or traffic is rerouted. Delay is particularly likely when remaining capacity falls below demand. Connections, aircraft and crew rotations, and night restrictions can then carry the original disruption forward. Weather intensity alone therefore explains neither the size nor the duration of disruption.

Statistics explicitly coded as weather ATFM minutes cover only part of the burden. They do not capture every local handling problem, subsequent rotational delay, cancellation or additional flight time. Different denominators and definitions must be preserved.

| Source and period | Supported finding | Denominator or limitation |
|---|---|---|
| CODA Annual2024, pp.3–5 | Average departure delay17.5 minutes; reactionary8.0 minutes, about46% | Minutes per flight in the CODA sample; reactionary is not exclusively weather |
| CODA Annual2024, pp.3–5 | En-route ATFM2.3 minutes per flight, including0.8 weather | Not the total weather-related delay burden |
| CODA Annual2024, pp.3–5 | Average arrival delay15.5 minutes; arrival punctuality72.4%, departure punctuality69.2% | Punctuality includes delays of up to15 minutes; the mean among delayed flights is a different measure |
| NOR2025, p.8 | Weather0.76 ATFM minutes per flight,32.0% of all ATFM minutes | Share of ATFM, not of all-causes delay |
| NOR2025, p.40 / printed31 | One minute of first-rotation ground delay corresponds to2.2 minutes of cumulative arrival delay in summer2025, compared with2.5 in2024 | First wave03–10UTC; all causes, not a causal weather multiplier |
| SMART-Wx AppendixF, p.1 | HEL28January2019:42 weather-ATFM minutes across the rotation,449 summed arrival-delay minutes | One aircraft/day; multiple additional causes and weather impacts, not a universal factor of ten |
| SMART-Wx AppendixB, pp.36,43 | Heathrow/Ciara9February2020:4,376 minutes for210 regulated flights, approximately21 minutes per regulated flight;474 cancellations | Conditional average among regulated flights; cancellations are absent from a delay-only metric |

## Citation chains: finding → source → method → new learning

### 1. Cascades: SMART-Wx → AppendixF → individual rotation data

The main report (p.37, printed31, §8.13) summarizes a case as34 initial weather-ATFM minutes and approximately400 resulting delay minutes. The directly linked **AppendixF** provides a different, more detailed account for Finnair aircraft OHLVB on28January2019:

- FIN2PD receives38 weather-ATFM minutes inbound to Helsinki and reaches71 minutes of arrival delay. Additional holding is described as likely, not demonstrated causally.
- FIN6EK has no ATFM delay, but codes91 (connection/load relationship) and89 (local ATC). The connection between the passenger problem and weather is also described only as likely.
- EFKU–EFHK incurs another4 weather-ATFM minutes and80 reactionary minutes.
- HEL–LFPG has over200 minutes:95 reactionary and **106 weather ground-handling minutes, IATA77**.
- The appendix totals42 weather-ATFM minutes and449 cumulative arrival-delay minutes.

**New learning:** The difference is neither solely amplification of the first shock nor a direct estimate of its causal weather effect. Weather acts again later and is recorded under other codes. The main-text and appendix numbers differ; use the detailed appendix when discussing this specific case. Individual flight rows are preserved in its image, but no open CSV accompanies them.

**Further evidence from AppendixI, pp.1–3:** Helsinki illustrates how weather flattens and shifts arrival/departure waves. Even without a local curfew, the destination's night restriction can threaten the final rotation. With a single mixed-mode runway and two12-minute snow-clearance breaks per hour, A-CDM actively manages arrival/departure ratios of1:1,2:1 or1:2. This explains a mechanism; it is not a controlled effectiveness estimate.

### 2. Weather labels: CODA → IATA codes → ATFCM regulation reason

CODA pp.15–16 reproduces IATA AHM730/731. Weather occurs in different process categories:71 departure,72 destination,73 en-route/alternate,75 de-icing,76 airport clearing and77 ground handling; also81W en-route ATFM,84 destination weather ATFM, and89S local ATC weather.93V identifies a late aircraft arrival caused by weather at destination; broader reactionary codes91–96 may contain further weather consequences.

SMART-Wx reference[2] leads to the **ATFCM Operations Manual24.1**,18January2021. Pages75–78 (printed74–77) define regulation-reason selection. Weather W applies to weather-related capacity loss when airport services operate as planned. Missing de-icing or snow-removal equipment may instead be **Aerodrome Services E**. The FMP makes the final reason decision with NM guidance; ANM remarks explain the trigger.

**New learning:** An absent weather label may reflect a different process category or failure to supply a planned mitigation resource. Weather observations, traffic/capacity conditions and regulation remarks together offer stronger causal context than one code. Avoid double counting: IATA, NM regulation and reactionary categories are different views of events.

The manual p.117 (printed116, REA procedure) also gives a concrete ATFM calculation: CTOT minus the sum of the latest EOBT and taxi time; for T-DPI-s, CTOT minus TTOT from the latest E-DPI/T-DPI-t. This is the operational calculation in that procedure, not a definition of every retrospective indicator. It is not actual gate departure minus scheduled gate departure.

NOR reference[2] led to **Reporting Assumptions and Descriptions6.42**. The available edition documents geographical boundaries and historical airspace/traffic-volume mappings, among other reporting choices. It matters for time-series comparisons, but does not provide a complete all-causes or reactionary attribution framework. Its title was not treated as proof that it contained every desired definition.

### 3. Capacity: SMART-Wx → Heathrow/Ciara → planning and observed cancellations

AppendixB, by Andy Knight of Heathrow, describes a pre-COVID system operating close to capacity with limited recovery room within operating hours (p.2). Before Ciara, weather, demand and capacity were combined in a Demand Capacity Balancer. Planned arrival rates were reduced from30/h for much of the day to25/h before the event (pp.22–23); the actual rate was temporarily18/h between12:00 and17:00 (p.36). A30% schedule reduction between09:00 and21:00UTC was proposed and implemented by NOTAM. Observed outcomes included34 go-arounds,14 diversions and474 cancellations, comprising300 before the operating day and174 additional tactical cancellations (pp.37–43).

**New learning:** Advance cancellations can reduce delay among remaining flights. A model evaluated only on operated flights can underestimate a severe weather disruption. The projected no-intervention scenario of over140 night movements (p.24) is a simulation result, not an observed control day. According to the slides, the detailed weather summary, NATS daily analysis and cancellation spreadsheet were held in the DvC library; they were not included in the public attachment and were not obtained.

AppendixC (Derogée/Leeman, Amsterdam,16December2020), pp.19,25,27, adds that prolonged individual disruptions become multiple disruptions through connections, crews and terminal congestion. In Amsterdam, a scenario change typically needs over two hours before it affects operations. AppendixD (Skoglund, Arlanda) describes how rigid clearance plans and poorly coordinated apron snow removal themselves caused delays. A shared winter coordinator and capacity table account for gates, de-icing, taxiways and equipment. Its p.9 capacity table explicitly states that its numbers are **not updated**.

**Archiving restriction:** AppendixB retains repeated Confidential markings. Automatic review rejected its upload despite its public EUROCONTROL hosting. Its PDF and text are local only. See ARCHIVE_STATUS.md for the exact restriction; other appendices were uploaded after successful checks.

### 4. Weather index: Schultz2018 reference37 → ATMAP2011 → original algorithm/SQL → NLR sources

The parent research team identified reference37 of Schultz2018 as the archived **ATMAP weather algorithm v2.3**, EUROCONTROL PRU,10May2011. This is a retrospective, expert-informed METAR classification. Its five classes are visibility/ceiling, wind, precipitation, freezing conditions and dangerous phenomena. Coefficients are combined per report and averaged across the day. The default window is06:00–21:59 local time, with at least20 METARs per day; the European bad-weather threshold is1.5. Local adaptation based on at least one winter season is envisaged (pp.8–10,28).

Section3.14, p.20, explicitly states that it is **not an airport-performance prediction model**. Demand timing, convection's position relative to runways, wind aloft and phenomena beyond approximately16km are inadequately represented. Section5 explains validation using local operational data, including de-icing from CDG,FRA,HEL and PRG. Complete training data and modern out-of-sample performance statistics are not published. AnnexI describes iterative expert/correlation-based adjustment, including the assumption of at most20% bad-weather days on average in a homogeneous airport sample.

**Original-code check:** The wind table on p.13 assigns coefficient4 above30kt. The SQL function on p.35 assigns3. The narrative on p.14 says gust speed replaces mean wind speed, but the printed code uses `spd_in` and only adds1 when `spd_gust_in` is present. Page23 gives another differently worded explanation. Light-rain treatment also differs between the overview table and code. A reconstruction must therefore document and test its exact variant; the publication alone does not establish an unambiguous reference implementation. No production implementation was created or validated here.

ATMAP p.13 cites two NLR originals, both downloaded. **Van Es/Karwal2001, Safety aspects of tailwind operations**, pp.10–20: tailwind increases groundspeed and required runway length; weaker braking and an unstable approach can interact. The accident analysis covers **33 selected overrun events in1980–1999**, involving civil transport aircraft of at least5,700kg, not a delay sample. The70% wet/contaminated-runway figure is a share of those selected events, not the probability for an individual flight. Page13 cites Critchley/Foot, CAA Paper91015(1991), on wake vortices; that further link was recorded bibliographically but not downloaded.

**Van Es/van der Geest/Nieuwpoort2001, Safety aspects of aircraft operations in crosswind**, pp.32–34,42–46:69 events, including15 accidents; US Part121 operations in1983–1995; exposure96,383,531 flights. Demonstrated aircraft capability, operator limits, runway condition and gusts must be distinguished. The reported factor3.5 for wet/contaminated runways concerns historical crosswind accident/incident probability during the ground roll, using an estimated24% exposure share. It is **not a flight-delay multiplier or a current Frankfurt threshold**. The report publishes aggregate evidence, not individual NLR database rows.

**New learning:** The weather index provides a comparable description under historical assumptions. Causal analysis and operating-direction forecasts additionally require runway geometry, wind components, demand, current conditions and operational responses. Following the citation through to source code exposes differences missed by headline summaries.

## Interpretation of the core reports

**CODA2024, published2025:** Airline-reported all-causes data and NM data complement one another. Reactionary delay dominates minutes but does not establish a single initiating cause. Do not mix the mean over all flights, the mean over flights delayed at least5 minutes,15-minute punctuality and ATFM shares. The IATA appendix supports a sound classification of causes.

**NOR2025, published2026:** Network constraints combine weather, staffing, capacity, traffic growth and restricted or differently used airspace. Rerouting can overload previously less affected sectors. The report estimates890,834 minutes saved through collaborative weather management; this is an operational benefit estimate, not randomized evidence. Editorial inconsistencies remain: the executive summary p.9 gives5.2million en-route weather minutes, while p.17 gives5.3million, both28.3%;2024 all-causes baselines vary against CODA (17.4/17.1 versus17.5). A summer-weather comparison on p.19 contains an implausible year reference. Do not harmonize these figures with more precision than the originals support.

**SMART-Wx2021:** This is a taskforce practice guide, not an effect study. Its focus is a common picture of weather, capacity, demand and uncertainty from advance planning to nowcasting. Zurich's O2 briefing (p.18, printed12), including a24-hour probability of a capacity-constrained bise configuration, demonstrates translation of weather into operating states. Most-likely, best- and worst-case scenarios support earlier planning. The appendices offer more concrete evidence than the general recommendations.

**DWD Flugwetterdienst Jahresbericht2022, published2023:** The full text, including development and verification sections, was read. Pages31–32 connect poor punctuality despite fewer convective events with overloaded sectors, staffing problems and rerouting. Pages48–53 discuss limitations and improvements in nowcasting, ensembles, icing and TAF guidance. Pages56–57 describe Met4Airports: combining meteorological and operational data for capacity/delay forecasts, with models trained in2022 and user evaluation planned for2023. This does not yet demonstrate validated operational benefit. Pages62–66 report TAF verification: rare visibility events and overforecasting can produce many false alarms. Wind hit rates with tolerated errors are not probabilities of a specific runway configuration. The DWD2024 follow-up was additionally archived and extracted in full, but not substantively read.

## Secondary application: Frankfurt25/07 and runway18

The literature supports the chain weather → runway-specific wind components/operating state → usable capacity → excess demand → immediate and propagated delay. A48-hour operating-direction or runway-availability model needs actual local rules and calibrated meteorological uncertainty. Frankfurt rules supplied by the parent team are project context, **not thresholds derived from or verified by these reports**. Do not transfer Zurich, Heathrow, Amsterdam or historical NLR values to Frankfurt. Airport weather alone cannot explain delays caused by distant storms, a late previous rotation or crews.

## Reading coverage and remaining limitations

Complete extracted-text reading: CODA17/17 pages, NOR66/66, SMART-Wx61/61, DWD2022 84/84, ATMAP37/37; SMART-Wx appendices B50/50,C29/29,D11/11,E5/5,F2/2,I3/3. Most diagrams were read through their extractable text, without systematic visual inspection. Embedded diagram data may therefore be missing.

Partial/unread documents: Reporting Assumptions pp.1–10 and20–28 read, mapping tables11–19 not fully read. The275-page ATFCM manual was archived; targeted reading covered weather procedures71–74 (74partially), regulation reasons75–78 and the REA definition117. NLR Tailwind pp.3–5,10–21; NLR Crosswind pp.32–35,42–46. DWD2024 was not read.

AppendixG is image-only: all four pages were subsequently rendered locally and visually inspected. It shows aggregate weather-ATFM series for2003–2020 and monthly airport series for2016–2020YTD. It distinguishes en-route and airport delay but provides no controlled causal analysis; traffic changes and2020 matter when comparing periods. AppendixH has a PPS extension but contains OOXML: all16 slide texts were extracted and read; embedded graphics and linked archive objects were not inspected. These limits remain explicit in the manifest. Preserved originals permit later examination.

REFERENCES_EXTRACTS.md preserves the complete formal bibliographies of the core documents where present, including the further NLR references. DWD and CODA have no equivalent consolidated academic bibliography; their footnotes and source acknowledgements remain in the complete PDFs and extracts. Citation tracing was targeted rather than infinitely recursive: central methods and case evidence were followed, without claiming to have read every standard, private communication or internal dataset.

AppendixH, slides14–15, extends the cross-border weather-management chain: the2018 review explicitly reports no substantial behavioral change and extra work without tangible benefit. In2019 the shared risk matrix helped, while geographical gaps, underestimated forecasts and late updates remained. This internal process assessment indicates that a common weather picture alone does not guarantee effective capacity management; it is not a controlled effect estimate.
