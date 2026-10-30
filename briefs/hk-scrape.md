# hk-scrape · collect FraAlliance's public web design, completely, for the design lane

Worktree `C:\olawt\aiw-wt-design` (shared with design lane `c27`). **You write only into `C:\olawt\aiw-wt-design\.design-scrape\`.** It is git-ignored: never commit it, never touch `web/` or anything else. `c27` builds our UI from what you collect.

## Collect (public pages only, no logins, no forms)
1. Start at https://www.fraalliance.de/ (try www and non-www, de and en). Crawl every page linked from its own navigation and footer on the same domain, up to about 40 pages. Also save the pages on fraport.com and lufthansagroup.com that describe FraAlliance.
2. For each page, save:
   - the raw HTML (`pages/<slug>.html`)
   - every linked CSS file (`css/`), plus inline `<style>` blocks
   - web fonts as references: URL and family name in `fonts.json`. Don't download font files.
   - the image and SVG URLs it uses (`assets.json`: URL, type, size, where used)
   - **any 3D or animation:** WebGL/three.js scripts, canvas elements, Lottie JSON, video backgrounds. Record each script URL and what it renders (`motion.json`).
   - a full-page screenshot at 1440 px and 390 px: `"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu --no-first-run --user-data-dir=<temp> --hide-scrollbars --window-size=1440,4000 --virtual-time-budget=15000 --screenshot=shots\<slug>-1440.png <url>`. Close Chrome after each shot, because memory is tight.
3. **Extract the design system** into `.design-scrape\TOKENS.md` and `.design-scrape\tokens.json`. Each token cites its source file and the selector or CSS variable it came from.
   - colour palette with frequency of use
   - typography: families, weights, sizes, line heights per element (h1–h4, body, small, button)
   - spacing scale, container widths, grid, breakpoints
   - border radius, shadows, borders
   - component styles: buttons, cards, nav, footer, tables, badges, form fields
   - icon set
   - motion: durations and easing
4. `.design-scrape\INVENTORY.md`: one line per page and component found, with its screenshot path, so the design lane can find any element fast.

## Rules
- Be polite: about 1 request per second, a normal User-Agent, respect robots.txt.
- Their logo, photos and copy are for reference only. The design lane won't copy them into our app.
- No AI assistant, model or vendor names in any file.
- When done, print the paths of `TOKENS.md` and `INVENTORY.md` and the 10 most important tokens, then stop. **Target: within 25 minutes.**
