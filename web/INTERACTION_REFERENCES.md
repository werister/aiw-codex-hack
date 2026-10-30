# Forecast interactions

The existing FraAlliance tokens and component rules in `DESIGN.md` remain the visual authority.

- [Design Systems Surf](https://designsystems.surf/) and [Carbon data tables](https://www.carbondesignsystem.com/building-blocks/core/components/data-table/guidelines): references for readable data, consistent selection and progressive disclosure.
- [Bencho time scrubber](https://bencho.dev/blocks/time-scrubber): reference for snapping between hours. Our implementation uses a native range input, explicit previous/next controls and a next-change shortcut. It is independently written; no paid component source is included.
- [assistant-ui LocalRuntime](https://www.assistant-ui.com/docs/runtimes/custom/local-runtime): conversation primitives and state for the forecast guide. Answers are deterministic summaries of the selected forecast, with no model service, API key or external request. Unsupported questions return guidance instead of invented answers.

The selected hour is shared by the scrubber, timeline, runway view and guide. Changing the forecast or hour starts a fresh guide conversation. All displayed times use the supplied Europe/Berlin local values. Forecast loading, missing data and failures have explicit states; failed loads cannot retain a previous day's guide.
