# Spec Delta

## Purpose
Give the jury and the UI one command that forecasts the next 48 hours from any issue day.

## ADDED Requirements

### Requirement: Any day
The CLI SHALL forecast any day, past or future, using only information available at that day's issue time.

#### Scenario: Jury test day
- **WHEN** the jury runs `python -m ml.forecast --day 2026-11-02`
- **THEN** it prints 48 hourly rows with OD, P(18 usable), certainty and the next change

### Requirement: Machine-readable output
With `--json` the CLI SHALL print a valid `ForecastResponse`.

#### Scenario: UI reads it
- **WHEN** the CLI writes `web/public/forecasts/2026-11-02.json`
- **THEN** the web app shows that day without code changes
