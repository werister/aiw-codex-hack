# Spec Delta

## Purpose
Turn wind observations or forecasts into operating-direction and runway-18 states using exactly the official FraAlliance rules.

## ADDED Requirements

### Requirement: Official rules as pure code
The rule engine SHALL read all thresholds from `ml/rules.json` and compute tailwind as speed x cos(direction - runway heading - 180 degrees).

#### Scenario: Brief example, OD
- **WHEN** wind is from 090 degrees at 20 kt and the OD is 25
- **THEN** the tailwind on 25 is about 19 kt and the OD changes to 07 at once

#### Scenario: Brief example, runway 18
- **WHEN** wind is from 330 degrees at 20 kt
- **THEN** the tailwind on 18 is about 17.3 kt and runway 18 is not usable

### Requirement: 30-minute hysteresis
A tailwind between 0 and 10 kt SHALL change the OD only after it has persisted for more than 30 minutes, and calm or variable wind SHALL keep the current OD.

#### Scenario: Short tailwind tolerated
- **WHEN** a 5 kt tailwind lasts 20 minutes
- **THEN** the OD does not change

#### Scenario: Long tailwind switches
- **WHEN** a 5 kt tailwind lasts 40 minutes
- **THEN** the OD switches to the headwind direction
