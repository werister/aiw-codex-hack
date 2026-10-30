# DFS forecast layout prototype

Throwaway comparison: a simplified operations reference and the same layout with a 48-hour forecast. All values are illustrative; exact Frankfurt installed screens are unverified. No feeds, dependencies, aircraft positions, operational controls or learned results.

Run from any directory:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory /Users/hugohader/dev/aiw-docs-spec/web/prototypes/dfs-forecast
```

Open http://127.0.0.1:8765/?variant=reference or http://127.0.0.1:8765/?variant=forecast . The forecast-hour slider updates the map and forecast values; the query parameter preserves selection between views and reloads. Baseline values remain pinned to the sample issue time. Expand forecast detail for margin certainty, signed tailwinds and method comparison. Performance and learned predictions are unavailable.

Reference: https://dfs-as.aero/en/portfolio/dfs-tower-suite/
