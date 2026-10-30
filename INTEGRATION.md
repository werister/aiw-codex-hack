# Commit integration

The user requires all work on `main`, including the work previously held in separate worktrees. The monitor runs every five minutes, one completed cycle per invocation.

## Shared work

Use `git worktree list` to locate the single writable `main` worktree. The shared worktree is `/Users/U751725/aiw-codex-hack`. Coordinate disjoint file ownership and serialize all Git mutations. Do not force-checkout the same branch in multiple worktrees. Older worktrees remain preservation/read-only copies until their work is incorporated; never overwrite another owner's pending files.

All existing local and remote branches and worktrees are explicitly authorized for consolidation. Review exact committed and uncommitted snapshots, preserve human authorship, and record original/resulting SHAs. Import the unique changes, not stale inherited history. Existing patches must not be applied twice. No additional ready-handoff document is required for this consolidation. New work is committed directly on `main`.

## Each monitor cycle

1. Resolve the shared Git directory using `git rev-parse --git-common-dir`. Acquire its exclusive `integration-monitor/run.lock` directory and record run ID and owner. Release only the current run's lock; recover a foreign lock only after verifying its owner stopped.
2. Read `AGENTS.md`, `NOTICES.md`, relevant work packages and `integration-monitor/state.json`. Inspect status, branch, ownership and unfinished Git operations before any mutation. Fetch `origin` without pruning and pin the reviewed SHAs.
3. Review each new commit's full diff, message, standards and requirements, using independent read-only reviewers when useful. Preserve published history. When remote history is rewritten, compare old/new contents and use an explicit old-base boundary to replay only unpublished local commits.
4. Run targeted checks and the documented startup/demo checks. A failed or unavailable check is never a pass. Existing review findings remain open until fixed and verified or explicitly decided by the responsible owner. Do not publish with failed required checks, and respect scoped push pauses.
5. Fetch again before publishing. Review a moved base or source snapshot and repeat affected checks. Publish only by normal fast-forward `git push origin main`; never force-push or bypass branch protection.
6. Record reviewed SHAs, source/result mappings, checks and open findings in the shared state file. Keep concrete open problems in `NOTICES.md`, preserving other owners' entries. Notify only when integration succeeds, a material new failure appears, or a decision is needed.

Nontrivial conflicts in another owner's code require a decision; preserve the source work and abort only the coordinator's conflicting operation. Do not delete worktrees/files, change CI/deployment, or develop unrelated features. Do not send messages to other chats or external people without explicit human authorization.

## Commit messages

Use short imperative `feat:`, `fix:`, `docs:` or `chore:` subjects. Preserve human authorship. Omit agent names, agent co-author trailers and session links. Correct messages only on unpublished integration copies and record the old/new SHA mapping.
