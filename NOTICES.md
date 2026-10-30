# Notices

Open problems across main, branches and worktrees. One line each: time (Berlin) | severity | what is wrong | where | who acts. `STOP` breaks main or makes the submission wrong, `FIX` should be fixed before 16:00, `FYI` is worth knowing. Delete a line once it is fixed. Rules: "Cross-checking" in `AGENTS.md`.

- 12:10 | FIX | The run command `python -m ml.forecast --day ...` fails on main. `ml/forecast.py` and `ml/live.py` exist only as untracked files in the cli worktree, `ml/train.py` and `ml/quality.py` only in the model worktree | `aiw-wt-cli` (jayden/cli), `aiw-wt-ml` (jayden/model) | head agent: land them on main
