# Lift-off — runway and compass

Asset: `../../web/public/brand/lift-off-compass.png` (2172 × 724 px, transparent PNG).
The runway remains the standalone mark; the **o** is a compass with a two-ended
needle and four short cardinal ticks. Preserve the wordmark's proportions.

The shared `BrandLogo` component displays this version in the cockpit, widget
and pitch, in indigo/violet for light mode and white for tower mode.

## Editing prompt

```text
Use case: precise-object-edit / logo-brand.
Edit target: the supplied approved transparent Lift-off logo.
Make exactly ONE localized change: turn the lowercase "o" in the word "Lift-off" into a minimal compass.
Keep the existing circular letter o as the outer compass ring, with EXACTLY its current outer dimensions, baseline, stroke thickness and position. Inside its transparent counter, add a very simple elegant slender two-ended compass needle pointing upper-right / lower-left: vivid violet #3c36da triangular upper-right half, deep indigo #1d1a78 triangular lower-left half, meeting cleanly at the center. Leave generous negative space between the needle and the letter ring. The compass should be obvious but stay clean and legible at tiny header size. At most four very short cardinal ticks just inside the ring; no N/E/S/W letters, no numbers, no detailed compass rose. The o must remain readable as a letter in the exact name "Lift-off".
STRICT INVARIANTS: preserve the left runway symbol with its violet separated top cap and negative-space markings EXACTLY as-is; preserve every other letter, hyphen, typography, weight, spacing, size, alignment, colors, flat treatment, entire canvas dimensions 2172x724 and all current transparent margins. Do not move, scale, crop or re-layout the logo. Do not redesign any part outside the o. No additional symbol outside the wordmark, no aircraft, no shadows, no gradients, no textures, no background, no labels.
Return a single transparent PNG with real alpha, preserving all existing transparency.
```
