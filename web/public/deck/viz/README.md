# Deck visualizations

Self-contained ES modules. Each one renders into an element, plays its animation on mount, and replays on demand. No libraries and no network calls. Data is embedded in a sibling `*.data.js` file. Colours come from the page's CSS variables (`--west`, `--east`, `--accent`, `--ink`/`--fg`, `--muted`, `--line`, `--scene`/`--bg`) and fall back to blue/amber/greys when those are missing. The element needs a size, since each module fills it.

```js
import { mount } from './viz/accuracy.js';
const v = mount(el);   // draws and animates
v.replay();            // call on slide enter; the module-level replay() restarts the last mount
```

| File | Shows | Data source |
|---|---|---|
| `barcode.js` | 8 years of flown directions: day (x) by local hour (y), west/east, with total hours, switches and the west/east split | `data/ground_truth/dfld_hourly.csv` |
| `accuracy.js` | Held-out accuracy at 6/24/48 h: our model vs official rules vs same as now, 95% whiskers on the model | `web/public/data/quality.json` (`out_of_sample.od`, `significance.od`) |
| `tree.js` | Tree 1 of 80 in the real direction model, top 3 levels in plain words, drawn node by node, edge width = hours that pass | `ml/models/forecast.joblib` |
| `drivers.js` | Top 8 inputs the model relies on, relative bars (held-out shuffle test, Brier based) | `web/public/data/quality.json` (`drivers`) |
| `example.js` | One real 48 h hindcast (28 to 29 Oct 2026): model chance of west, official rules, actual flown strip, switch at 10:00 marked. `mount(el, { day: "2026-10-29" })` picks the other embedded day | `web/public/forecasts/2026-10-28.json`, `2026-10-29.json` |
| `pipeline.js` | How it works: inputs to 45 signals to 80 trees to the next 48 h with how sure | `ml/models/metadata.json`, `tree.data.js`, `example.data.js` |

`test.html` mounts all of them (serve `web/public` over HTTP, since browsers block ES modules from `file://`). `python web/public/deck/viz/build_data.py` regenerates every `*.data.js` from the sources above.
