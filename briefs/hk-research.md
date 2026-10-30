# hk-research · how FRA decides the operating direction, and which data we can get (research worker)

Worktree `C:\olawt\aiw-wt-model`, branch `jayden/research`. This is research only: no model, no app code. The head lane merges and talks to you through this terminal. Worker `hk-data` downloads data in parallel (branch `jayden/data`, writes `data/` and `data/README.md`).

Read first: `AGENTS.md` (repo rules; **never mention any AI agent in commit messages or trailers**), `frankfurt-airport-operating-direction-forecast.md` (official brief), `CHALLENGE_FRAALLIANCE.md`, `briefing/`.

## TOP PRIORITY (first 30 minutes): ground-truth labels
The jury grades against **the operating directions actually flown at FRA**, so we need their hourly history. Check these in this order and report which works:
1. **DFLD.de** operating-direction (Betriebsrichtung) history for Frankfurt.
2. **UNH (umwelthaus.org)** monthly reports and any INAA exports.
3. **OpenSky Network** flights API: EDDF departures and arrivals with runway or track. Does it work without an account, and for which period?
4. **Deriving the OD from ADS-B departure or arrival headings** (OpenSky live state vectors are anonymous; history may need an account).

If a source is downloadable without an account, fetch it into `data/ground_truth/` (you own that folder) as hourly UTC rows (`time`, `od`, `source`) and document it. If none is usable, the fallback is labels from METAR plus the official rules, and they must be marked **INFERRED** everywhere. If a source needs an account, write ONE line for Jayden with the source, why we need it and the sign-up URL. **No agent creates accounts.**

## Deliverable: `DATA_AND_DECISIONS.md` (repo root), cited, plain English
1. **Who decides and how.** Who sets the operating direction (OD 25/07) and closes runway 18 at Frankfurt: the DFS tower supervisor, Fraport (Verkehrsleitung, Vorfeldkontrolle), FraAlliance? How the decision is made in practice: lead time, coordination, and the official rules (tailwind limits, the 30-minute tolerance, any noise-abatement preference for 25). Separate clearly what the official brief states from what other sources say.
2. **The data points behind the decision.** For each one, where it comes from and whether we can get it publicly:
   - runway anemometers and touchdown-zone wind (2-minute mean, gusts)
   - METAR and TAF
   - DWD forecasts (ICON-D2, ICON-EU, aviation products)
   - forecast tailwind
   - the hysteresis rule
   - noise rules
3. **The specific systems Jayden asked about,** each with what it is, what it holds, and whether any of it is public:
   - DFS **PHOENIX** (radar data processing and tracker)
   - DFS **Tower Suite** or the tower systems used at FRA
   - how **Fraport** monitors and publishes the OD
   - any public **Betriebsrichtungsprognose** (UNH Umwelthaus, Fraport, DFLD). If one exists, it's our benchmark, so give the URL and say whether a history is available.
   - **BTS** (US Bureau of Transportation Statistics) and FAA ASPM runway-configuration data, as an analogous public ops dataset: useful as a reference or not?
4. **Public sources we can actually use,** as a table: source | what it gives | URL | keyless? | granularity | history depth | use (label, feature, validation, live). Must include:
   - IEM ASOS/METAR and IEM TAF for EDDF
   - Open-Meteo Previous Runs API, Historical Forecast API and Forecast API
   - DWD Open Data (CDC station 01420 Frankfurt/Main hourly and 10-minute wind, and the ICON open data)
   - DFLD
   - UNH / Fraport statistics
   - OpenSky Network (live REST is anonymous; history needs an account)
5. **Ground truth for "the OD actually flown".** The jury grades against it. List every public source of historical OD at FRA you can find, with its granularity, period and URL. If none is good enough, say how to derive it, from ADS-B tracks or from METAR plus the rules, and what each costs.
6. **Not public.** What we cannot get: DFS internal systems, anemometer raw feeds, and so on.
7. **Accounts needed.** One line per source that needs a login: source, why we need it, sign-up URL. **Never create an account, type a password or enter a key yourself.**

## Rules
- Cite every claim with a URL. If a page is German, translate the relevant line into English and give the original term in brackets.
- Time-box: a first complete version pushed within 40 minutes. Push early and often (`docs: ...`). `git fetch && git rebase origin/main` before every push, `git push -u origin jayden/research`. **Don't touch `main`.**
- Report in one line when you push, and finish with the 5 most important findings.
