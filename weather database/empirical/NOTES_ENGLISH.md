# Empirical weather literature: full-text review

Updated 2026-10-30. Fully read: Borsky2019 (17 PDF pages), Schultz2018 (19), Rodriguez2021 (9), Sasse2003 (10, web PDF), Stevens2019 (6, web PDF), Allan2000 (7). The 2022 Rodríguez-Sanz journal version was not accessible in full. Reading included methods, tables, conclusions and references; underlying flight datasets were not independently replicated. Page numbers below are printed pages unless explicitly labelled PDF pages. Originals are unchanged. Text extraction is a search aid; Borsky's extracted digits contain errors, so tables 1–4 and A1–A14 were also visually checked.

The literature explains mechanisms and supports hypotheses for FraAlliance. Administrative cause shares, observed correlations and estimated causal increments are different quantities. No paper here validates the complete Frankfurt task: hourly probabilities over 48 hours for direction 07/25, runway 18 availability and the next change.

## Borsky & Unterberger (2019)

[Original and DOI](https://doi.org/10.1016/j.ecotra.2019.02.002), CC BY-NC-ND 4.0. Difference-in-differences for rain, snow and wind; Prais–Winsten for temperature, with airport/time controls. Connections among ten US airports, 2012–2017; tables report 2,146,535 observations. Tables 1–3, p.17: preferred estimates include rain 13.470 minutes, strongest rain class 23.280, snow 11.500, wind ≥16 mph 2.016 and ≥25 mph 3.422. The 23-minute figure is not an overall mean. Table 4, p.18: temperatures ≤−3°C correspond to 2.058 minutes. Heat is not significant; rare extremes limit power.

Limits: pp.12,15–16 exclude delays ≥300 minutes, assume a daily reset and discuss spillovers contaminating controls. Table A13, p.25 shows sensitivity to outlier cutoffs. Precipitation thresholds have different rounding between prose and tables. MPH is not knots; these are not runway thresholds. Relevant to persistence and local calibration, not direct evidence about OD07/25, runway 18 or 48-hour forecast skill. The cited Sasse study was followed and read.

## Schultz et al. (2018)

[DLR original](https://elib.dlr.de/123469/), CC BY 4.0. Approximately 20.5 million flight records at 84 European airports in 2013, including around 440,000 Frankfurt movements. METAR → five ATMAP categories → total-delay distributions; Burr fits by airport size using maximum likelihood (p.14, Table 6).

For Frankfurt, p.9/Figure 5 reports 3.39 additional arrival-delay minutes per daily score point, R²=87%. This is a descriptive regression of grouped medians among already-delayed flights, not all movements or a validated hourly prediction. The 2.7 threshold on p.11 was derived from 2013, not a universal safety limit.

Table 5 shows similar aggregate scores with cancellation rates of 2% versus 58% arrivals / 64% departures. Preserve individual weather components and cancellations. Figure 11/p.12 discusses after-effects. Page 16 says modeled delay includes all causes and reactions: adding a separate reactionary component could double-count. Missing registrations prevent clean aircraft-rotation reconstruction (p.3). ATMAP does not replace runway-relative wind, the project brief's limits or state-transition logic. Reference 37 leads to ATMAP2011; reference 36 to Buxi/Hansen2013, not obtained in full.

## Sasse & Hauf (2003)

[Publisher PDF](https://rmets.onlinelibrary.wiley.com/doi/pdf/10.1017/S1350482703005036), free access, RMetS copyright. Fully read on the web; local original download was blocked by Cloudflare. Ten selected thunderstorm days in 1997/1998 compared with five reference days per year. The selection is explicitly nonrepresentative (p.23). DFS STANLY measures deviations from idealized flight paths, not ordinary gate-arrival punctuality.

Table 3/p.29 averages 112 aircraft, 1,021 total minutes, 280 reference minutes and 741 additional minutes per event. These are event totals, not minutes per aircraft. The conclusion on p.30 swaps the year attribution relative to the abstract/table: additional/reference totals are 5,135/810≈6.34 in 1997 and 2,270/1,990≈1.14 in 1998. Page 27 also describes 14–20 UTC as four hours despite the six-hour interval.

Useful mechanism: weather in the approach region and queues persisting afterward. Historical configuration and selected small samples prevent direct transfer. No OD07/25 or runway 18 forecast. The Allan/Gaddy reference was followed in full.

## Rodríguez-Sanz, Cano & Rubio Fernández (2021), conference version

[IOP original](https://doi.org/10.1088/1757-899X/1024/1/012107), CC BY 3.0. This nine-page conference paper is not the 19-page 2022 Emerald article, DOI 10.1108/AEAT-12-2020-0318. Madrid-Barajas 2015–2018, more than 750,000 flights; hybrid Bayesian networks, 13 variables; three MCMC chains / 100,000 iterations (pp.4–5). Outcomes include approach, taxi-in and in-block time. Section 6 lists better testing and transferability as future work.

Checks: Table 2/p.4 duplicates X2/X3 and omits X1; Table 3 defines a purported off-block delay with AIBT. Page 5 calls 180–360° “east.” Page 6 repeats exactly the 3.39 minutes and R²=87% Schultz reports for Frankfurt, without a visible independent regression table verifying the result for Madrid. This is a notable match, not proof of copying.

Probabilistic dependencies are conceptually relevant, but a Bayesian network alone does not identify causality. No demonstrated 48-hour runway forecast. All 47 bibliography entries were extracted.

## Stevens (2019)

[NOAA original](https://repository.library.noaa.gov/view/noaa/45302), AMS copyright. Six pages fully read via web; local download blocked by the server. METAR/ASOS from 30 US airports, 1973–2017; one last observation per hour avoids overweighting additional bad-weather reports. Theil–Sen trends and Kendall significance, not a delay regression. Figure 2/p.618: decreasing IFR frequency at 28 airports, significant at 18.

Pages 616–617 use uniform comparison criteria of 2,500 ft / 3 statute miles; local procedures can differ. Table 1/p.617 gives an odds ratio of about 46 for low visibility with a small dewpoint spread. Page 619 describes this as a probability multiplier, but odds and risk ratios differ; the table's risk ratio is about 39.6. Cite the odds ratio correctly. Sensor changes and shortened series at two airports are discussed.

Relevant as a visibility/dewpoint hypothesis, not a Frankfurt operating rule or evidence of direction-switch/RWY18 forecast calibration. All 24 references are separately recorded.

## Allan & Gaddy (2000), followed reference

[MIT original](https://archive.ll.mit.edu/mission/aviation/publications/publication-files/ms-papers/Allan_2000_ARAM_MS-14148_WW-10159.pdf). Seven PDF pages fully read. The cover requires permission for reposting to servers; original PDF and full text remain local review copies and are not republished here. Found through Sasse2003.

Newark September 1998–August 1999; ASQP covers around 60% of traffic. Selected days have at least two consecutive hours with average delay >15 minutes (PDF p.2). Table 1/PDF p.3 attributes 31.8% of recorded delay to thunderstorms, 35.3% to low cloud/visibility, 13.2% to strong wind. Selected historical shares are not universal causal fractions.

The queueing model uses constructed demand/capacity, sometimes inferred from arrival rates. Table 2/PDF p.6 distinguishes modeled potential benefit from user-reported realized cases. Cost results depend on historical rates and a 0.8 reactionary-delay factor. Relevant ideas include forecasting onset/end of capacity-constraining weather and runway-relative wind, not importing Newark thresholds, costs or 1–3-hour benefit claims into a 48-hour Frankfurt task.

## Application to the brief: our synthesis

The project brief, not these papers, supplies the 10 kt immediate landing-tailwind limit, up-to-30-minute tolerance for smaller tailwind, runway 18 tailwind ≥15 kt and crosswind including gusts >40 kt. Empirical validation requires independently recorded local states and inputs available at the prediction issue time. Observed future METAR must never enter predictors in a retrospective forecast test.

A weather–delay relationship establishes neither a calibrated runway-state probability nor a safety clearance. Test probability calibration and change timing separately. An inferred label created by a wind rule cannot independently validate that same rule.

## Source chains and archive status

- Borsky2019 → Sasse2003 → Allan2000: fully read; Sasse accessible via web only; Allan retained locally without reposting.
- Rodriguez2021 → Schultz2018: cross-checked; repeated numerical results flagged.
- Schultz reference 37 / Rodriguez reference 47 → ATMAP2011: [European review](../europe/NOTES.md).
- Schultz reference 36 → Buxi/Hansen2013: authors/title/DOI 10.1016/j.trc.2012.12.006 verified, article not obtained in full. Buxi's similarly titled 2012 dissertation is a different publication.
- Extracted bibliographies are source-discovery records, not proof that every referenced work was read.
