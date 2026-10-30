# European literature archive: status and evidence

Updated 2026-10-30. Destination verified through GitHub repository metadata: **werister/aiw-codex-hack**, private, with push permission. Intended folder: `weather database/europe/`.

## What is available

- **18 complete original documents are stored locally:** 17 PDFs and one PowerPoint file. All original headers and SHA-256 checksums were checked. The `.pps` file is actually an OOXML ZIP container; its original filename/content was preserved.
- **17 originals and their 17 text extracts have verified GitHub blob uploads.** Each returned Git blob SHA matched the locally calculated SHA-1 over the Git blob header and original bytes.
- The research notes, source-reference extracts, manifest, and local archive whitelist also have verified uploads: **38 files before this status document**.
- This status document is an additional research artifact. The parent agent integrates uploaded blobs into a Git tree/commit. A successful blob upload alone does not prove that a path is already committed on the default branch.
- **Two files remain local only:** `smartwx_appendix_b.pdf` and `smartwx_appendix_b.txt`. They are deliberately absent from the verified upload map.

The authoritative integration map is `europe-uploaded.json` in the task's shared tools directory. It records repository paths, Git blob SHAs, file sizes and SHA-256 hashes. `manifest.json` describes acquisition and reading status; its `downloaded_full_original` status means locally downloaded, not necessarily uploaded. `archive-whitelist.txt` is the original local archive inventory, so its inclusion of the withheld Appendix B is not a claim that B is on GitHub.

| Original | Local full copy | Verified Git blob |
|---|---|---|
| EUROCONTROL Annual Network Operations Report2025 | Yes | Yes |
| EUROCONTROL CODA Annual2024 | Yes | Yes |
| EUROCONTROL SMART-Wx2021 main report | Yes | Yes |
| SMART-Wx Appendix B: Heathrow operational presentation | Yes | **Withheld** |
| SMART-Wx Appendices C,D,E,F,G,H,I | Yes | Yes, all seven |
| DWD Flugwetterdienst Jahresbericht2022 | Yes | Yes |
| DWD Flugwetterdienst Jahresbericht2024 | Yes | Yes |
| ATMAP weather algorithm v2.3,2011 | Yes | Yes |
| EUROCONTROL Reporting Assumptions v6.42 | Yes | Yes |
| EUROCONTROL ATFCM Operations Manual24.1 | Yes | Yes |
| NLR Safety aspects of tailwind operations,2001 | Yes | Yes |
| NLR Safety aspects of aircraft operations in crosswind,2001 | Yes | Yes |

## Review restriction and resolved transport issues

The automatic approval review rejected the Heathrow Appendix B text with this reason:

> The blob contains material repeatedly labeled “Confidential” with Heathrow internal operational data and contact information; the broad request to upload literature does not specifically authorize disclosing this sensitive third-party content to GitHub.

The PDF was consequently withheld as well; no alternate format or upload route was used to disclose that artifact. EUROCONTROL publicly links the attachment from its [official SMART-Wx publication page](https://www.eurocontrol.int/publication/collaborative-best-practices-handling-adverse-weather-european-aerodromes), but that fact did not remove the review restriction. Further disclosure requires resolving that specific restriction.

Initial authorization rejections for ATMAP, Appendix F, the ATFCM text, and the NLR crosswind PDF were resolved through one renewed review after checking the explicit full-literature request, exact private repository, and official public originals. ATMAP identifies public distribution; ATFCM identifies internet accessibility; the NLR report identifies its title as unclassified. All four subsequent uploads succeeded with matching hashes. Two technical chunk-length checks failed before uploading the PowerPoint and ATFCM PDF; smaller local-read chunks resolved those failures. No damaged or partial original was uploaded.

## Reading coverage

The full extracted text was read for CODA2024 (17 pages), NOR2025 (66), SMART-Wx2021 (61), DWD2022 (84), and ATMAP2011 (37), including ATMAP's validation discussion and SQL appendix. SMART-Wx appendices B,C,D,E,F,I were read through their complete extracted text. All four image-only pages of G were locally rendered and visually inspected. All16 slide texts of H were extracted and read.

Embedded figures were not systematically visually checked across every document. The DWD2024 follow-up was archived and extracted but not read. Reporting Assumptions, the275-page ATFCM manual, and both NLR reports received focused partial reading; exact page coverage is in `manifest.json` and `NOTES.md`. These limits are retained rather than describing every archived document as fully read.

## Main findings in English

1. **Weather becomes delay through operational constraints and demand.** Wind can change runway configuration, visibility can require larger spacing, precipitation can lengthen runway occupancy, and thunderstorms or winter weather can interrupt ground services. The same meteorological event has different consequences under different infrastructure, demand and recovery capacity.
2. **Weather-coded ATFM delay is not the whole weather burden.** CODA2024 reports17.5 departure-delay minutes per flight, including8.0 reactionary minutes, about46%. Reactionary includes many causes. Weather can also appear in de-icing, ground-handling, destination-flow and late-aircraft codes. These measures must not be treated as interchangeable or summed without checking overlap.
3. **The source chain corrects an attractive cascade claim.** SMART-Wx's main text says roughly34 initial weather-ATFM minutes and400 resulting delay minutes. Its Appendix F instead documents42 weather-ATFM minutes across the rotation and449 summed arrival-delay minutes, with a later106-minute weather ground-handling event. This is not a causal tenfold amplification of a single initial shock.
4. **ATMAP is a retrospective weather descriptor, not an airport-performance forecast.** Its daily index omits demand timing and does not capture important spatial/aloft weather. The printed wind table and SQL differ: above30kt, the table assigns4 while the code assigns3; the narrative's handling of gust speed also differs from the code. An implementation therefore needs explicit choices and independent validation.
5. **Cancellations and interventions change what delay statistics show.** Heathrow's Ciara presentation reports4,376 minutes among210 regulated flights, but also474 cancellations. A mean delay among operated or regulated flights cannot alone measure total disruption. The source is retained locally under the restriction above; this paragraph is a research finding, not a substitute copy of its detailed artifact.
6. **Safety evidence and delay evidence have different outcomes and denominators.** The NLR reports explain interactions among wind, runway condition and aircraft handling. Their historical accident/incident samples cannot establish current delay multipliers or Frankfurt operating thresholds.

The detailed notes and complete reference-list extracts preserve the chain from headline finding to cited appendix, operational definitions, original algorithm, or historical dataset description. Frankfurt runway25/07 and runway18 remain secondary application context; local operational rules must be validated separately.
