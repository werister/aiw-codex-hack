# Spec Delta

## Purpose
Predict the hourly operating direction and runway-18 usability up to 48 h ahead and prove the skill on held-out data.

## ADDED Requirements

### Requirement: No leakage
Features for issue time T SHALL use only observations up to T and weather-model runs issued before T.

#### Scenario: Leakage test
- **WHEN** the leakage test inspects features for an issue time T
- **THEN** no feature uses data from after T

### Requirement: Skill at the required leads
The backtest SHALL report accuracy and Brier score at 1, 6 and 24 h (and 48 h) for the model, the rule baseline and persistence on a period never used for training.

#### Scenario: Skill table
- **WHEN** `python -m ml.train` finishes
- **THEN** it prints and saves the skill table for all three methods at each lead
