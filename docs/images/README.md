# Running application captures

Captured from the production static export in headless Chromium on 31 October 2026. Screens show the actual 48-hour `rules-demo` forecast computed by:

```sh
python -m ml.forecast --demo --json --out web/public/forecasts/latest.json
```

The fixed example issues at 00:00 Europe/Berlin on 28 October 2026. It uses committed IEM METAR and archived Open-Meteo weather, with no recorded direction outcomes or fitted model. The historical model-quality page is separate. No screenshot content or displayed numbers were composited or replaced. Reduced motion pauses illustrative aircraft during capture; the 3D scene uses software WebGL.

| Image | Capture |
|---|---|
| [Dashboard](dashboard.png) | 1440 × 1060 desktop viewport |
| [48-hour timeline](timeline.png) | Element capture of the expanded timeline |
| [Tablet view](ipad.png) | `/widget/`, 1180 × 820 landscape viewport |
| [Model quality](model-quality.png) | Full `/quality/` page with historical accuracy and intervals |
| [Airport illustration](airport-3d.png) | Element capture of the running forecast-controlled 3D scene |
| [Measured comparison](model-comparison.svg) | Matplotlib chart of the replayed historical aggregate; not a screenshot |
| [Contact sheet](contact-sheet.jpg) | Resized overview of the images above |

Browser checks also exercised hour selection, six-hour handover, method/model-card routes, an unavailable day, ordinary static navigation and a 390-pixel mobile viewport. The missing-day request deliberately returns 404 and the app displays a retry state. No unexpected HTTP or page errors remained.
