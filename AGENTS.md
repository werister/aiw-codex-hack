# AGENTS.md

Instructions for Codex (and any other coding agent) working in this repo.
Context: 6 hour hackathon (AI Week Codex hack). Speed matters, but `main` must always run.

## Project

- **What we are building:** A 48 h hourly forecast for Frankfurt Airport (FraAlliance challenge). For every hour it gives the operating direction (25 or 07), the probability that runway 18 is usable, a certainty score and the next likely direction change. It is trained on public data (EDDF METAR, archived Open-Meteo model runs) and evaluated against the official rule baseline and persistence at 1, 6 and 24 h.
- **Stack:** Python 3.13 in `ml/` (pandas, scikit-learn) for data, labels, model, backtest and the forecast CLI. Next.js 16 + TypeScript + Tailwind 4 in `web/` (npm) for the ops timeline UI, deployed on Vercel from `web/`.
- **Entry point:** `python -m ml.forecast --day YYYY-MM-DD` (CLI, first-class deliverable). Web: `web/src/app/page.tsx`.
- **Run locally:** `python -m pip install -r ml/requirements.txt` then `python -m ml.forecast --day 2026-10-31`. Web: `cd web && npm install && npm run dev` (http://localhost:3000).
- **Demo path:** open the web app, read the next 48 h (OD per hour, runway 18, certainty, next change), switch to a jury test day, open the backtest panel (skill at 1/6/24 h vs rules and persistence), show the model card (`MODEL_CARD.md`).
- **Rules:** `ml/rules.json` holds the official FraAlliance limits. Contract between ML and UI: `web/src/lib/forecast-types.ts`.

Keep this section current. If you change the stack, the run command or the entry point, update it in the same commit.

## Golden rules

1. **`main` always runs.** Never push something that breaks the run command above.
2. **Small, frequent commits.** One logical change per commit, commit at least every 20 to 30 minutes of work.
3. **Rebase, never merge.** Linear history only. No merge commits.
4. **Demo over polish.** Prefer the simplest thing that works end to end. No premature abstractions, no speculative config, no large refactors.
5. **Stay in your lane.** Only touch files related to the current task. Do not reformat or rename files you were not asked to change; that causes rebase conflicts for everyone else.

## Git workflow

Before starting any task:

```bash
git fetch origin
git rebase origin/main
```

Work on a short-lived branch named `<person>/<feature>` (e.g. `aditya/upload-ui`), or directly on `main` for trivial fixes if the team agrees.

Before every push:

```bash
git fetch origin
git rebase origin/main      # resolve conflicts, keep both sides' intent
# run the app / quick check, confirm it still starts
git push --force-with-lease # on your own branch only
```

- Never `git push --force` to `main`. Never use plain `--force`; always `--force-with-lease`.
- Land branches on `main` via fast-forward (rebase first, then `git merge --ff-only` or a PR with "Rebase and merge").
- If a rebase conflict is non-trivial and touches someone else's code, stop and ask instead of guessing.

**No AI names anywhere.** Never name an AI assistant, agent, model or vendor in commit messages, trailers (no `Co-Authored-By:` agent lines, no session links), author fields or files. Say "head agent" or "our agents". Commits are authored by the human who runs the agent.

Commit message format (keep it short, imperative):

```
feat: add file upload endpoint
fix: handle empty response from API
chore: add .env.example
docs: update run instructions
```

## Code conventions

- Readable over clever. Short functions, clear names, minimal comments that explain *why*.
- Put new modules where a teammate would look for them first; avoid deep folder nesting.
- Add a dependency only if it saves real time; note why in the commit message.
- Pin versions in the lockfile; commit the lockfile.
- Hardcoding is fine for the demo if it is marked with `# HACK:` (or `// HACK:`) and a one-line reason.

## Secrets and config

- Never commit API keys or tokens. Read them from environment variables.
- Keep `.env` in `.gitignore`; maintain `.env.example` with every variable name and a placeholder value.
- If you add a new env var, add it to `.env.example` in the same commit.

## Testing and checks

- No full test suite required. Minimum bar before pushing: the app starts and the demo path works.
- Add a tiny smoke test only for logic that is easy to break and painful to debug live.
- If a linter/formatter is configured, run it only on files you touched.

## How the agent should work

- Read this file and the relevant code before editing.
- For any task bigger than ~30 minutes, write a 3 to 5 bullet plan first and confirm before coding.
- Make the smallest change that completes the task. Show the diff summary when done.
- Report what you ran to verify the change (command and result). Do not claim it works without running it.
- If something is ambiguous, ask one focused question rather than inventing requirements.
- Do not delete files, rewrite history on `main`, or change CI/deploy config without explicit approval.

## Cross-checking

Four people and several agents work in parallel branches and worktrees. Nobody sees unpushed work, so:

- Before each task, and at least every 15 minutes, pull main (`git fetch origin && git rebase origin/main`) and read `NOTICES.md`.
- Use subagents to look at what the other branches and worktrees are doing (`git branch -r`, `git log origin/main..origin/<branch>`, `git worktree list`) before you build something. If it already exists, use it.
- When you see something wrong anywhere in the repo or in any workspace, add one line to `NOTICES.md` or message the head agent. Examples: main doesn't run, the same thing built twice, code that disagrees with `frankfurt-airport-operating-direction-forecast.md`, leakage in the backtest, a committed secret, an AI name.
- Commit to main as soon as your change runs. Small commits, rebased, never force-pushed.

`NOTICES.md` has one line per open problem: time (Berlin), severity (`STOP`, `FIX` or `FYI`), what is wrong, where, who acts. Delete the line once it is fixed. A guardian checks all branches and worktrees every 10 minutes until 16:30 and keeps the file current.

## Team notes

- Kai Detmers: ML and data pipeline co-lead (`ml/`).
- Jayden Bruck (head agent, with our agents in separate worktrees on branches `jayden/<package>`): owns `web/` and integration, and drives the worker packages. Leaves at 16:45.
- Hugo Hader: pitch and demo at 17:00. Luca Schultz: data review, sanity checks, business-case numbers, backup presenter.
- Decision 11:40: labels come from the official rules on EDDF METAR, validated against flown ODs if a public source exists. The model must beat the rule baseline on held-out days.
