# Research entry points

The serving research model is the historical revision evaluated in [EVALUATION.md](EVALUATION.md). The cleanup replayed its saved fits without training or tuning. Alternative model fitting was not rerun, so the earlier exploratory scorecards are excluded from this distribution rather than presented as newly verified evidence.

`ml/challengers.py` retains two research approaches: predict whether target direction differs from the issue-time direction, and blend the baseline model with a corrected multimodel weather-rule forecast. Each approach chooses weights using earlier validation data. A differing target direction is not the same event as a first transition: multiple changes can return to the original direction.

`ml/first_event_experiment.py` instead constructs cumulative first-transition targets and enforces nondecreasing event probabilities across the horizon. This is an event probability, distinct from the probability of OD 25 at an hour. Training/validation boundaries must respect the complete future target window.

Both entry points require lawfully supplied direction labels and compatible local fits. Their outputs are exploratory and are kept separate from production artifacts. A candidate needs a fresh prospective comparison of direction accuracy, Brier score, unique-event recall, false alarms, lead time and coverage before promotion. Differences in complete-window cohorts must remain explicit.
