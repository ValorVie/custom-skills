# Upstream Reference

## Source

- User-provided `/simplify` workflow in this session:
  run three parallel review agents for reuse, code quality, and efficiency, then apply worthwhile fixes

## Adaptation Notes

This skill is a Codex-native version of the `/simplify` workflow.

Key differences:
- In Codex, the three reviewers should be spawned as read-only subagents
- The main agent remains the only one that edits files
- Verification is explicit because Codex should report concrete checks after cleanup
