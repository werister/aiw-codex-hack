# Review: how useful is the `weather database` for our case?

> **Opinion of Jayden's agent, not a team decision.** Written 30 Oct about 13:45, after reading Luca's `weather database/` on `main` and the extra commit on `luca/weather-database` (0c8f4da). It covers the READMEs, TOP_ERKENNTNISSE.md, the file lists and the abstracts and key passages of the papers. It doesn't cover every full text. Luca and the team decide.

**Our case:** forecast, hourly and 48 h ahead, the operating direction at FRA (25/07) and whether runway 18 can be used. It's graded against the directions actually flown.

## Short answer

The collection is careful, well-sourced research on **why flights get delayed**. It's strongest as **background and pitch material**. Two papers are **directly useful for the model**. Most of the data, including the US BTS delays, doesn't feed the forecast.

## Directly useful for the model

| item | why it matters | how to use it |
|---|---|---|
| `models/fra-icon-d2-runways.*`: Zinkhan et al. 2023, *Intrinsic Explainable Self-Enforcing Networks Using the ICON-D2-Ensemble Prediction System for Runway Configurations*, Eng. Proc. 39, 41, CC BY. Co-authored by the DWD in Offenbach. | It's **our exact problem at FRA**. It uses the ICON-D2 **ensemble** forecast to estimate how certain the operating direction forecast is, and explains it with Shapley values. | Add the **ensemble spread** (ICON-D2-EPS or ICON-EU-EPS) as a model input and for the certainty score. Cite it in `MODEL_CARD.md` as prior work by the DWD itself. |
| `models/nasa-runway-configurations-2023.*`: Puranik et al., NASA Ames, *Predicting airport runway configurations for decision-support using supervised learning*. | It's the same task type at US airports: supervised learning with METAR-derived features. It reports 93% (CLT) and 73% (DEN) accuracy and names its features. | Use it as a reference for our feature set and as a benchmark sentence in the model card. Its airports and horizons differ, so don't claim direct comparability. |

## Useful as context or for the pitch, not as training data

- **`europe/` EUROCONTROL reports** (CODA 2024, NOR 2025, SmartWX, ATFCM manual) and the DWD *Flugwetter* reports. They hold European and German figures on weather-related delays and capacity, which fit FRA far better than US data. One cited number on what a direction change or weather capacity loss costs would make the business case concrete.
- **`europe/nlr_tailwind2001`, `nlr_crosswind2001`**. They cover where tailwind and crosswind limits come from and their safety background. That's helpful for explaining the official rules (10 kt and 15 kt tailwind, 40 kt crosswind) in the pitch.
- **`empirical/Schultz2018` (DLR) and Sasse & Hauf 2003.** These are weather impact studies for German airports and Frankfurt thunderstorms. They give good context, and Luca's note on correctly reading the 741 minutes per event figure is valuable.

## Not useful for our forecast

- **US BTS delay data** (`bts/`, about 2025). It's carefully analysed, but its delay causes come from US carriers and airports. It contains no operating direction, no runway configuration and no FRA data, so it can't train or test our model. Luca's own README says the same: "BTS dient der Ursachenanalyse, nicht als Ersatz für Frankfurt-Betriebsdaten".
- **General forecasting method papers** (Lim et al. TFT 2019, Vandal 2018, Kim and Park 2024, Liu 2024, Yuan 2025). They're interesting, but deep sequence models are too much for today's data size and time. Gradient boosting with good weather features and honest walk-forward testing is the better use of the remaining hours.

## Why this opinion

1. **The jury grades one thing:** forecast accuracy against flown directions at FRA. Only data that contains FRA weather forecasts or FRA operating directions can move that score. Of the whole collection, only the two papers above relate to that, and they point to methods and inputs, not to datasets.
2. **The biggest open gap in our model is certainty and the 6 to 48 h edge** over the rules and persistence. The DWD ensemble paper addresses exactly that, so it's the most valuable find in the folder.
3. **Delay-cause data explains the impact, not the wind.** That makes it valuable for the "why it matters" slide, but irrelevant to the forecast itself.

## Recommendation for the repo

- Keep the **citations and takeaways**, this file plus Luca's NOTES and TOP_ERKENNTNISSE, on `main`.
- Move the **third-party PDFs and full-text copies** (about 12.9 MB on `main` plus about 101k lines on the branch) off `main`. They pose a copyright risk in a submission repository, and the folder name contains a space.
- The two model-relevant papers are cited above. That's enough for the model card.
