# Forecast interactions

The existing FraAlliance tokens and component rules in `DESIGN.md` remain the visual authority.

- [Design Systems Surf](https://designsystems.surf/) and [Carbon data tables](https://www.carbondesignsystem.com/building-blocks/core/components/data-table/guidelines): references for readable data, consistent selection and progressive disclosure.
- [Bencho time scrubber](https://bencho.dev/blocks/time-scrubber): reference for snapping between hours. Our implementation uses a native range input, explicit previous/next controls and a next-change shortcut. It is independently written; no paid component source is included.
- [assistant-ui LocalRuntime](https://www.assistant-ui.com/docs/runtimes/custom/local-runtime): conversation primitives and state for the forecast guide. Answers are deterministic summaries of the selected forecast, with no model service, API key or external request. Unsupported questions return guidance instead of invented answers.
- [Panoramic information display](https://www.bmwgroup.com/en/news/general/2025/newidrive.html): visual reference for grouping the primary direction and its time context into one quiet band. This adaptation has not been shown to reduce workload for airport users.
- [FAA human-factors color guidance](https://hfcc.dot.gov/publications/docs/GeneralGuidance/zz_FAA_GeneralGuidanceDoc_Chapter_03_Section_07.html): reference for retaining interpretable information when color is degraded. Direction and runway status also use text and an arrow; this is design guidance, not certification of the application.

The selected hour is shared by the scrubber, timeline, runway view and guide. Changing the forecast or hour starts a fresh guide conversation. All displayed times use the supplied Europe/Berlin local values. Forecast loading, missing data and failures have explicit states; failed loads cannot retain a previous day's guide.

The [preparation and handover workflow](SHIFT_PLANNING.md) adds simultaneous event tracks, a bounded six-hour briefing and a preparation-time replay. Source UTC hours determine ordering and repeated local hours retain their offsets. The pitch uses saved historical forecasts and separate model-quality evidence; synthetic weather examples are not displayed.
