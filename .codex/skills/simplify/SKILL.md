---
name: simplify
description: Use when user wants a pre-review cleanup pass on changed code by running parallel reviews for reuse, code quality, and efficiency, then applying worthwhile fixes without changing behavior.
---

# Simplify

## Overview

Use this as a pre-review cleanup gate. The goal is not formal approval; it is to inspect changed code for reuse opportunities, code quality issues, and efficiency issues, then fix the worthwhile findings without changing behavior.

## When to Use

- The user wants a `/simplify`-style cleanup pass before `reviewer` or `code-reviewer`
- A feature is complete and the diff likely contains duplication, rough edges, or avoidable inefficiency
- You want to reduce avoidable reviewer comments before formal review
- The change spans enough files or logic that one simplification pass is not enough

Do not use this skill for:
- Tiny diffs where a single local cleanup is enough
- Behavior changes, feature work, or bug fixes that alter requirements
- Large architectural redesigns across untouched modules
- Formal spec validation or security review

## Place in Review Flow

Recommended placement:

```text
implement -> simplify -> code-reviewer and/or reviewer -> receiving-code-review
```

Skip the full three-agent pass when:
- the change is tiny and obvious
- only one or two trivial lines changed
- the user wants immediate formal review instead of cleanup

## Workflow

### Phase 1: Identify Changes

- If the user gives a base/head range, use that
- If staged changes exist, inspect `git diff HEAD` so both staged and unstaged changes are included
- Otherwise use `git diff`
- If there is no git diff, review the most recently modified files the user mentioned or that you edited earlier in the session
- Keep a compact summary of touched files plus the full diff text for the reviewers

### Phase 2: Read Local Standards

- Check local instructions first such as `AGENTS.md`, repo conventions, and any relevant skills
- Follow existing naming, formatting, and structure in the touched files
- If local conventions conflict with generic cleanup preferences, local conventions win

### Phase 3: Launch Three Review Agents in Parallel

For medium or large diffs, spawn three read-only subagents in parallel in a single round. Use `explorer` agents when possible because this is codebase analysis, not implementation.

Each agent must receive:
- the full diff
- the touched file list
- the cleanup constraint: no behavior changes, no edits, findings only

The three review domains are:
- Code reuse review
- Code quality review
- Efficiency review

Use the prompt templates in:
- [references/reuse-reviewer.md](references/reuse-reviewer.md)
- [references/quality-reviewer.md](references/quality-reviewer.md)
- [references/efficiency-reviewer.md](references/efficiency-reviewer.md)

Important:
- Review agents are read-only; they do not edit files
- The main agent aggregates findings and performs the fixes
- Do not spawn multiple worker agents to edit the same touched files in parallel

### Phase 4: Fix the Worthwhile Issues

- Wait for all reviewers to finish
- Aggregate findings and remove duplicates
- Fix issues directly if they improve the code without changing behavior
- If a finding is a false positive or not worth the churn, note that and skip it without arguing at length

### Phase 5: Verify

- Run the narrowest meaningful verification for the changed area
- Prefer targeted tests first, then lint/build if appropriate
- If no automated verification exists, state that explicitly and mention residual risk
- Briefly summarize what was fixed, or state that the code was already clean enough

## Quick Reference

| Goal | Prefer | Avoid |
|------|--------|-------|
| Readability | Clear names, explicit branches, small coherent helpers | Dense one-liners, clever tricks |
| Scope control | Touched files, recent diff, user-specified paths | Repo-wide cleanup without request |
| Safety | Targeted verification after edits | Assuming refactor is safe |
| Comments | Intent and constraints | Narrating obvious code |
| Agent usage | Three parallel read-only reviewers, one controller applying fixes | Multiple editing agents touching the same files |

## Common Mistakes

- Turning simplification into redesign
- Extracting abstractions too early
- Renaming broadly across unrelated files
- Optimizing for fewer lines instead of easier maintenance
- Skipping verification because the change "looks mechanical"
- Letting all three agents edit code instead of only reporting findings
- Using this skill as a substitute for formal review or spec validation

## Upstream Reference

This Codex skill adapts the `/simplify` flow used in Claude-based workflows into a Codex-native skill. See [references/upstream-agent.md](references/upstream-agent.md) for the source notes and adaptation details.
