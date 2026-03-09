# Upstream Agent Reference

## Source

- Official plugin agent:
  [code-simplifier.md](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/code-simplifier/agents/code-simplifier.md)
- Local cached copy:
  `/Users/arlen/.claude/plugins/cache/claude-plugins-official/code-simplifier/1.0.0/agents/code-simplifier.md`

## Adaptation Notes

This skill is a Codex-native adaptation of the Claude Code plugin agent.

Key differences:
- The original plugin agent can be loaded as a dedicated Claude agent; this version is a Codex skill discovered from `~/.codex/skills`
- The original prompt says to operate proactively after edits; this version should trigger when the user explicitly asks for cleanup or when another workflow selects it
- The original prompt references `CLAUDE.md`; this version follows Codex system instructions plus local repo rules such as `AGENTS.md`
- Verification is made explicit here because Codex often performs the edits directly and should report concrete validation steps
