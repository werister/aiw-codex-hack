# c27 · Make the UI look like FraAlliance: clean, calm, unmistakably theirs (WP5 design)

Worktree `C:\olawt\aiw-wt-design`, branch `jayden/design`. You work for the head lane `hackathon`, which built the current UI and merges. Jayden asked for this lane himself: "check the website of FraAlliance, their design system, and really make it look extremely clean and good with their design. Really scrape their HTML."

## Push rule
After each small commit: `git pull --rebase origin main && git push origin HEAD:main`. Never force, never merge. **No AI assistant, model or vendor names in commits or files.** Plain messages like `style: FraAlliance colour tokens`.

## Step 1 · Extract their design system (first 25 minutes)
1. Fetch FraAlliance's public website (start at https://www.fraalliance.de/ and follow the main pages; also check the links on fraport.com and lufthansagroup.com that describe FraAlliance). Save the raw HTML and the CSS it links to into `C:\olawt\aiw-wt-design\.design-scrape\` (git-ignored, never committed).
2. From the CSS and HTML, extract:
   - colour tokens (primary, secondary, accents, greys, backgrounds)
   - font families and weights, heading and body sizes, line heights
   - spacing scale, border radius, shadows, button and card styles
   - icon style
3. Write `web/DESIGN.md` (short, committed): each token with its source (the URL and CSS selector or variable it came from). If something isn't public, say so and pick a sober substitute. Fonts: use the same family if it's on Google Fonts; otherwise the closest free match, named.
4. Don't copy their logo files, photos or text. Write the name "FraAlliance" as text only.

## Step 2 · Apply it to the app
Files you own now: `web/src/app/globals.css`, `web/src/app/layout.tsx`, `web/src/components/*.tsx` (styling and layout only), `web/DESIGN.md`. **Don't change** data loading, props, types (`web/src/lib/forecast-types.ts`), anything in `ml/`, `data/` or `web/public/`.

The persona is the people in the tower, under stress every day (see `briefing/brainstorm-268.md` and `openspec/changes/wp5-ui-timeline/`):
- Three answers readable from two metres in under 3 seconds: current operating direction, runway 18 open or closed, next change time with its probability.
- Plain yes/no states first, details on click.
- High contrast, generous whitespace, no decoration that doesn't carry information. Colour means something: one colour for OD 25, one for OD 07, green/red only for runway 18.
- Decide light vs dark from their brand. If their brand is light, keep a dark "tower mode" toggle (tower rooms are dim).
- It must still work on an iPad (`/widget`, 1180×820) and down to 390 px wide.

Pages: `/` (full view) and `/widget` (iPad). Keep every element that is there now: now panel, 48 h timeline with the flown-vs-forecast row, simulated ops map, hour detail, model quality panel.

## Step 3 · Check it visually before every push
- `cd web && npx next build && npx next start -p 3002` (port 3001 belongs to the head lane; don't touch it). Stop your server when you're done.
- Screenshots with headless Chrome: `"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu --no-first-run --user-data-dir=<your temp dir> --hide-scrollbars --window-size=1440,1600 --virtual-time-budget=20000 --screenshot=<file>.png "http://localhost:3002/?day=2026-10-28"`, plus `/widget` at 1180×820 and `/` at 390×1600. Look at each one before pushing.
- `npx eslint src` and `npx tsc --noEmit` must pass.

Report in a few lines when the tokens are extracted, and when the restyle is on main with the screenshot paths. Memory on this PC is tight: keep a single dev or production server running and close Chrome after each screenshot.
