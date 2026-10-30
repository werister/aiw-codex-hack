# Literature advisory board
Updated 2026-10-30. This is an evidence review framework, not a simulation of authors or an operational decision authority.

## Mandate and target
The primary question is which conditional or potentially sufficient indicators support the FRA Alliance target: runway direction07/25, runway18 availability, switch timing, probability and useful lead time. The immediate mandate is to establish evidence and identify testable conditions. It does not authorize operational recommendations or runway clearances.

BTS delay patterns provide supporting knowledge about disruption mechanisms. They do not supply Frankfurt runway labels, prove local operating rules, or establish predictive relevance to the FRA outputs. A condition associated with delays is neither necessary nor sufficient for a runway state. Any claim of sufficiency must specify the target, operating context, exceptions and observed counterexamples.

The accepted order is **source → live availability → demonstrated benefit against a baseline**:
1. Verify the original claim, population, version, method and exact location.
2. For a forecast claim, verify that each input existed at forecast issuance, including publication latency and revisions. For a retrospective descriptive claim this stage is not applicable; forecast relevance remains unproved.
3. Compare the proposed predictor against the specified wind-based baseline at the same lead time, with the same available information, on future or held-out events. Better forecast metrics do not alone establish operational benefit or causal effects.

Separate **empirical associations**, **predictive performance** and **causal effects**. A majority vote is not evidence. Different sources repeating one original result are not independent confirmations.

## Seven review perspectives

### 1. Causality and the counterfactual
**Question:** Is this a recorded cause, an association, or an additional effect attributable to a weather shock?

[Borsky & Unterberger2019](empirical/Borsky2019.pdf), printed pp.12,15–18, Tables1–4 and TableA13/p.25, uses difference-in-differences for precipitation/wind and a different time-series approach for temperature. Effects depend on weather class, selected US connections and exclusions. Propagated delays can contaminate comparison groups; extreme-delay exclusion affects estimates. See [empirical review](empirical/NOTES.md).

Require an explicit exposure, comparison group, period, identification assumptions and sensitivity checks. Feature importance and administrative labels do not identify causal effects. Lack of significance for rare extremes does not establish absence of an effect.

**FRA implication:** A weather–delay association does not establish that weather determines07/25 or18 availability. State which competing operational explanations remain.

### 2. Weather, demand and capacity
**Question:** Which weather mechanism changes which capacity, under what demand and operational response?

[Schultz2018](empirical/Schultz2018.pdf), p.9/Figure5/Table5 and p.16, reports descriptive grouped relationships and markedly different cancellations under similar scores. [ATMAPv2.3](europe/eurocontrol_atmap2011.pdf), PDFpp.13–14,20/§3.14,35, explicitly says the index is not an airport-performance prediction model. Wind coefficients differ between the printed table and SQL.

Keep wind, visibility, precipitation, freezing, demand, capacity and cancellations distinguishable. Document the exact algorithm variant. A score is not an operating limit or demonstrated forecast.

**FRA implication:** Preserve runway-relative wind and gust definitions and local operating constraints. Assess whether an apparently weak delay response reflects cancellations or lower demand rather than harmless weather.

### 3. Propagation and network dependence
**Question:** Is a first shock propagated, is new weather added later, or are unlike sums being divided into a misleading multiplier?

[SMART-Wx](europe/eurocontrol_smartwx2021.pdf), PDFp.37/§8.13, and [AppendixF](europe/smartwx_appendix_f.pdf), pp.1–2, document a HEL rotation with42weather-ATFM minutes and449accumulated arrival-delay minutes. It also includes106minutes of weather-related ground handling and other causes. [AppendixI](europe/smartwx_appendix_i.pdf), pp.1–3, explains traffic-wave and rotation constraints.

Trace aircraft/crew/passenger links, turnarounds, buffers and additional shocks. Do not treat a rotation sum as one flight’s delay or one case as a universal amplification factor.

**FRA implication:** A delayed arrival can reflect upstream disruption despite usable local runways. Such cases cannot label local runway unavailability.

### 4. Data quality and reporting
**Question:** What does the field measure, who reports it, and what is excluded?

[BTS definitions](bts/DEFINITIONS.md), TechnicalDirective40 §§III.5/III.9 and the dashboard footnote, distinguish gate-arrival delay, cause allocations and fractional flight equivalents. Weather appears across reporting mechanisms; NAS also receives some additional delay between departure and arrival. Missing weather codes do not establish weather-free operation; all NAS/late-aircraft delay is not automatically weather.

[DOT OIG reportAV2025003,2024](bts/oig_bts_data_quality_2024.pdf), PDFp.15/printedp.12, found three reporting approaches among six sampled carriers: two used multiple causes, three the longest predominant cause, one a root-cause approach. Its data-quality section describes117automated checks but incomplete procedures and verification. These are historical audit findings, not proof that the same shortcomings remain unresolved in2026. Exact remedy status is not assessed here.

Require year-specific coverage, carrier/reporting regime, denominator, missingness, cancellation/diversion handling and changes in coding. For2016–2025, separate the2018reporting change and pandemic period; use stable-panel sensitivity comparisons.

**FRA implication:** Administrative cause codes are not observed FRA operating states. Local labels require their own provenance and timing checks.

### 5. Forecast validation and uncertainty
**Question:** Does the gain survive future events at the intended lead time and natural event prevalence?

[Vandal2018](models/vandal-2018.pdf), pp.4–6/Table1, uses a chronological holdout and uncertainty analysis; its MAE means median absolute error. [NASA/Puranik2023](models/nasa-runway-configurations-2023.pdf), pp.5–7/TableIV, predicts the next15-minute configuration using a random80:20split. [Kim/Park2024](models/kim-park-2024.pdf), Tables4,7,10–12 and preprocessing, balances weather-delayed and normal flights1:1 before splitting. Their accuracy figures answer different questions.

Specify target, horizon, tuning, split, prevalence and baseline. Assess rare-event precision/recall, false alarms, probability calibration and switch timing separately. Adjacent observations in random train/test splits can exaggerate generalization.

**FRA implication:** Compare the same local target against the agreed wind baseline. Track lead time, confidence intervals, counterexamples, state persistence and switching episodes. Cluster membership or retrospective correlation is not a validated predictor.

### 6. Availability at forecast issuance
**Question:** Would the exact inputs have been available in live operation?

[NASA2023](models/nasa-runway-configurations-2023.pdf), pp.4–5/TableII, uses the most recent already available LAMP forecast and excludes retrospective taxi/flight-count inputs. [DWD database referencev2.5.6](models/dwd-icon-d2-database.pdf), §§1,6,13.4.3, distinguishes products, time statistics and a public subset. [Liu2024](models/liu-2024.pdf), TableI/data description, leaves the availability of future weather unresolved despite using observed ISD data.

Record issuance, valid time, publication latency, revision, station/grid, unit, averaging/max interval and outages. An accessible current product does not establish a historical as-issued archive. The cited DWD URL now serves2026documentation rather than the2023version.

**FRA implication:** A condition found with observed weather can be a mechanism hypothesis. It becomes a forecast candidate only when a suitable issued forecast or live observation has demonstrated useful lead time.

### 7. Evidence synthesis and hypothesis scouting
**Question:** Which evidence is independent, contradictory, partially read or not yet verified?

The [Sternberg arXiv review](models/carvalho-review-preprint.pdf) provides a taxonomy; it is not the same version as the Carvalho journal article. Keep the [reading/version record](models/NOTES.md) and [source chains](europe/NOTES.md). Follow important claims to original methods/data. Preserve contradictions rather than averaging incompatible estimates.

**Reddit:** Use posts to discover hypotheses, terminology, possible mechanisms and counterexamples. Claimed pilot/controller/analyst identity is unverified unless independently established. Record the link and context, avoid unnecessary private details, then pursue an original report, dataset or rule. Upvotes and repetition do not verify a claim. No Reddit search was conducted for this document.

**FRA implication:** Ask which observation would falsify the proposed condition. A convincing anecdote is a lead, not a sufficient operating criterion.

## Compact decision record

| Field | Required entry |
|---|---|
| Question | The specific uncertainty to resolve. |
| Claim and type | One testable statement: empirical / predictive / causal. |
| Target/context |07/25,18availability or switch; period, airport, denominator, horizon and conditions. |
| Supporting evidence | Original source/version, page/section/table, result and reading status. |
| Counterevidence | Exceptions, alternative explanations, failed comparisons and selection risks. |
| Validity limits | Population, conditions and time range actually supported. |
| Evidence sequence | Source:…; live availability:… or N/A; benefit against wind baseline:… or N/A. |
| Status | **Open:** evidence missing. **Testable:** claim and comparison are specified, result pending. **Supported:** the precisely bounded claim is supported by checked evidence. |
| Next evidence step | A missing source, label, timing check or empirical comparison; not an operational action. |

Example: “The SMART-Wx case proves a universal tenfold weather amplification.” Type: causal. Evidence: §8.13/AppendixF. Counterevidence: later weather, ground handling and additional causes; sums over a rotation. **Open: the universal claim is unsupported.** The bounded documented sequence is supported. The next research step would require multiple comparable rotations and explicit shock attribution.

## Reading limits
The author of this synthesis fully read Kim/Park, Vandal, NASA, Liu, Yuan, FRA-SEN and the arXiv review. DWD was read only in selected relevant sections. Borsky, Schultz, SMART-Wx, ATMAP and BTS rely on the linked documented reviews by other research agents, preserving their full/partial-reading limits. The OIG excerpt on reporting methods and checks was directly checked here; the parent agent records a full28-page reading. This synthesis is neither an independent replication nor a claim that every cited reference was read.

No reviewed study validates the complete FRA task of48-hour forecasts,07/25direction,18availability and switch timing. Project rules originate in the separate brief. The board does not present them as validated by this literature.
