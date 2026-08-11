---
name: code-simplifier
description: Use when user asks to simplify, clean up, or refactor recently modified code for readability, consistency, or maintainability without changing behavior, especially after implementation and before broader review.
---

# Code Simplifier

## Overview

Simplify touched code without changing behavior. Prefer explicit, readable code over clever or overly compact rewrites, and keep scope limited to the files or sections the user just changed unless they request broader cleanup.

## When to Use

- The user asks to "simplify", "clean up", "tidy", or "refactor without changing behavior"
- Recently modified code works, but has duplication, deep nesting, noisy comments, or inconsistent naming
- A feature is complete and you want a maintainability pass before formal review
- You want one focused simplification pass, not a multi-agent review workflow

Do not use this skill for:
- Behavior changes, feature work, or bug fixes that alter requirements
- Large architectural redesigns across untouched modules
- Spec alignment review, security review, or performance review
- Three-reviewer cleanup workflows; use `simplify` for that

## Workflow

### 1. Define the Scope

- Use user-specified files or ranges if provided
- Otherwise inspect recent changes with `git diff`, `git diff --name-only`, or `git status`
- Default to touched code only; do not expand into unrelated cleanup

### 2. Read Local Standards

- Check project instructions first such as `AGENTS.md`, local skill rules, and repo conventions
- Follow existing naming, formatting, and structure in the touched files
- If local conventions conflict with generic cleanup preferences, local conventions win

### 3. Simplify Without Changing Semantics

- Reduce unnecessary nesting
- Remove duplication that is truly local and obvious
- Rename variables or helpers only when clarity improves and the rename is safe
- Prefer straightforward control flow over dense one-liners
- Avoid nested ternaries; use `if/else` or `switch` for multi-branch logic
- Remove comments that only restate the code; keep comments that explain intent or constraints
- Preserve helpful abstractions; do not flatten structure just to reduce line count

### 4. Guardrails

- Do not add features, options, or speculative generalization
- Do not broaden API surface or change data contracts
- Do not rewrite untouched modules for style consistency alone
- Do not claim "no behavior change" without verification

### 5. Verify

- Run the narrowest meaningful verification for the changed area
- Prefer targeted tests first, then broader lint/build checks if appropriate
- If no automated verification exists, state that explicitly and mention residual risk

## Quick Reference

| Goal | Prefer | Avoid |
|------|--------|-------|
| Readability | Clear names, explicit branches, small coherent helpers | Dense one-liners, clever tricks |
| Scope control | Touched files, recent diff, user-specified paths | Repo-wide cleanup without request |
| Safety | Targeted verification after edits | Assuming refactor is safe |
| Comments | Intent and constraints | Narrating obvious code |

## Common Mistakes

- Turning simplification into redesign
- Extracting abstractions too early
- Renaming broadly across unrelated files
- Optimizing for fewer lines instead of easier maintenance
- Skipping verification because the change "looks mechanical"

## Upstream Reference

This Codex skill is adapted from Anthropic's `code-simplifier` plugin agent. See [references/upstream-agent.md](references/upstream-agent.md) for the source location and adaptation notes.
