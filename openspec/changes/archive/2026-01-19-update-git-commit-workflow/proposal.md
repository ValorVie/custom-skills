# Proposal: Update Git Commit Workflow for Multi-Branch Merge

## Summary
Extend the `git-commit` workflow (command/claude/git-commit.md) to support a new merging strategy for teams without a dedicated integration manager. This adds a `merge` subcommand to automatically create a transient test branch and merge multiple feature branches into it.

## Why
As described in `example.md`, the current workflow assumes a single developer committing to local or remote. The user requires a flow where any developer can self-serve an integration test environment by merging multiple feature branches (e.g., `feature/A`, `feature/B`) into a fresh, timestamped test branch (e.g., `test-dev-20240115090000`). This avoids the bottleneck of a single "Lead" managing a long-lived dev branch and allows for ad-hoc integration testing.

## What Changes
- Modify `command/claude/git-commit.md`:
    - Add `merge` subcommand documentation.
    - Define a new execution flow for `git-commit merge <branch1> <branch2> ...`.
    - Specify the logic:
        1. Checkout/Update `master`.
        2. Create `test-dev-$TIMESTAMP` from `master`.
        3. Iterate and merge provided branches with `--no-ff`.
        4. Push the new branch.
- Add a new OpenSpec capability `git-workflow` to govern this logic formally.
