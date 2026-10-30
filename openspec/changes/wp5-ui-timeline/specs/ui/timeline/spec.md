# Spec Delta

## Purpose
Show the 48 h forecast, its certainty and the next change at a glance, on a laptop and on an iPad.

## ADDED Requirements

### Requirement: Timeline shows every deliverable
The timeline SHALL show, for each of the 48 hours, the OD, P(runway 18 usable) and the certainty, and SHALL highlight the next likely change time.

#### Scenario: Next change
- **WHEN** the forecast has an OD change at 14:00
- **THEN** the timeline marks 14:00 and shows the change window and probability

### Requirement: Backtest visible
The UI SHALL show the skill at 1, 6 and 24 h for the model, the rules and persistence from `backtest.json`.

#### Scenario: Judge asks how good it is
- **WHEN** the presenter opens the backtest panel
- **THEN** the three methods are compared at each lead
