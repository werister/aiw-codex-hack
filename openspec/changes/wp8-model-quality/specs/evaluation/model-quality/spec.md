# Spec Delta

## Purpose
Give the dashboard and the model card honest, out-of-sample numbers on how good the forecast is and how far its confidence can be trusted.

## ADDED Requirements

### Requirement: Out-of-sample by walk-forward
Quality numbers SHALL come from walk-forward folds where each fold is evaluated only on data after its training period, and SHALL show in-sample and out-of-sample results side by side.

#### Scenario: Judge asks about overfitting
- **WHEN** the presenter opens the model quality panel
- **THEN** it shows in-sample and out-of-sample accuracy at 1, 6 and 24 h for the model, the rules and persistence

### Requirement: Calibrated confidence
The quality output SHALL include a reliability table that compares stated confidence with the observed hit rate.

#### Scenario: Confidence check
- **WHEN** the model says 80% for a set of hours
- **THEN** the reliability table shows how many of those hours were correct
