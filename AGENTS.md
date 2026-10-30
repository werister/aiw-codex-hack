# AGENTS.md

Instructions for Codex (and any other coding agent) working in this repo.
Context: 6 hour hackathon (AI Week Codex hack). Speed matters, but `main` must always run.

## Project

- **What we are building:** _TBD, fill in one or two sentences once the idea is locked_
- **Stack:** _TBD (language, framework, package manager)_
- **Entry point:** _TBD_
- **Run locally:** _TBD, e.g. `npm run dev` or `uv run main.py`_
- **Demo path:** _TBD, the exact click/command sequence we show the judges_

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

## Team notes

_Add who owns what, decisions made, and the demo script here as the day goes on._
