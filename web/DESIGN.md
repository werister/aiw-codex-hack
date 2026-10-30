# Design tokens

The UI follows FraAlliance's public website. All brand values come from one stylesheet, `https://www.fraalliance.de/assets/dist/assets/index.c0b57268.css` (called "brand CSS" below), read on 30 Oct 2026. We copy no logo, photo or copy from their site. The name FraAlliance appears as plain text only.

Their brand is light, so light is the default. Tower mode is a dark variant for dim rooms, built from their own dark scheme.

## Colour

| Token | Light | Tower | Source |
| --- | --- | --- | --- |
| `--bg` | `#ffffff` | `#100e44` | brand CSS `:root, .cs--blue-white` → `--color-background`. Tower: darker step of `.cs--blue-blue` `--color-background` `#1d1a78` (derived) |
| `--panel` | `#ffffff` | `#16144d` | as above (tower: derived) |
| `--panel-2` | `#eeeeee` | `#1d1a78` | `.cs--blue-grey` → `--color-background`; tower `.cs--blue-blue` → `--color-background` |
| `--ink` | `#1d1a78` | `#ffffff` | `:root` → `--color-text`; tower `.cs--blue-blue` → `--color-text` |
| `--muted` | `#5d5b94` | `#adb0f9` | derived: `--color-text` mixed with white, 6.2:1 on white. Tower: `.cs--blue-blue` → `--color-navigation` |
| `--line` | `#dcdcea` | `#2e2b8a` | derived hairline. Their only border is `.select` → `border: .5px solid black` |
| `--accent` | `#3c36da` | `#3c36da` | `:root` → `--color-cta-bg` |
| `--select` | `#e3e4fd` | `#2a2790` | derived from `--color-teaser-secondary` `#adb0f9` (selected hour) |

Signal colours. Each one means one thing: OD 25, OD 07, or runway 18 open or closed. All four pass a colour-vision check: protan, deutan and tritan simulation, OKLab ΔE of at least 6, with the stripes and the words open/closed as a second cue.

| Meaning | Light | Tower | Source |
| --- | --- | --- | --- |
| OD 25 West | `#3c36da` | `#7a75ff` | `--color-cta-bg`. Tower: lighter step for contrast on indigo |
| OD 07 East | `#9d2f7f` | `#c24fae` | not in the brand. Their warm accent, rose `#ce8982` (`.cs--pink-white` → `--color-cta-bg`), reads grey at chart size and sits too close to runway red, so we deepened it to a berry |
| Runway 18 open | `#15803d` | `#22a463` | not in the brand; sober green |
| Runway 18 closed | `#d9381e` | `#e8642c` | not in the brand; sober red, plus diagonal stripes |

## Type

| Role | Value | Source |
| --- | --- | --- |
| Family | Inter Tight (Google Fonts) | They use Söhne (`@font-face` `soehne-leicht`, `soehne-buch`, `soehne-kraeftig`), a commercial face that isn't on Google Fonts. Inter Tight is the closest free match we tested: same compact width, single-storey g, similar figures |
| Page headline | 40 px / 28 px mobile, weight 300, line height 1.15 | `.hl--big` 4rem / 2.4rem, `soehne-leicht` |
| Body | 15–17 px, weight 400 | `body` 1.8rem / 1.5rem, line height 1.8, letter-spacing .005em. We use Buch weight rather than Leicht for small text in dim rooms |
| Label (`.eyebrow`) | 12 px uppercase, weight 500, tracking .06em | `.hl--small, .pill` 1.2rem, `soehne-buch` |
| Buttons, nav | 15 px | `.button, .navigation` 1.5rem, line height 1.8rem |
| Big answers | 88 px / 64 px, weight 400, tabular figures | `.hl--title` 9rem / 5rem, scaled down to fit three tiles |

One brand rem is 10 px at 1440 px (`html { font-size: .694vw }`), so 1.5rem is 15 px.

## Shape, space, motion

| Token | Value | Source |
| --- | --- | --- |
| Card radius | 10 px | `.teaser-card`, `.project-card` → `border-radius: 1rem` |
| Button radius | 999 px | `.button`, `.pill` → `border-radius: 999px` |
| Select radius | 8 px | `.select` → `border-radius: .8rem` |
| Gap | 10 px | `.grid` → `column-gap: 1rem` |
| Gutter | 16–20 px | `.container` → `padding: 0 2rem` |
| Card padding | 20–24 px | `.teaser-card` → `padding: 2rem` |
| Shadows | none | surfaces are flat. Their only shadow is the button hover ring `0 0 0 .3rem` (`.button:hover`), which we reuse |
| Easing | `cubic-bezier(.25,.46,.45,.94)` 0.3 s | `.project-card` transition |
| Button hover | `cubic-bezier(.34,1.56,.64,1)` 0.15 s | `.button` transition |

## Icons

Thin 1 px outline icons drawn by us: arrow, chevron, moon, sun, tick, bar. The style follows their inline outline arrows and the chevron in `.select__wrap`. We use none of their SVGs.
