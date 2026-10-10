# Sources

`work-log-codex` currently reads these local histories:

## Codex

- `~/.codex/session_index.jsonl`
- `~/.codex/history.jsonl`
- `~/.codex/sessions/**/*.jsonl`

Use per-session JSONL as the authoritative event stream whenever available. Index and history files are supporting evidence.
Read JSONL one line at a time, filter by the requested timestamp window before creating events, and keep only
the `raw` fields needed for roles, tool counts, token counts, and commit-command evidence. Do not retain world
state, full tool output, or other large payloads that do not affect the report.

## Claude Code

Claude Code 2.x session logs only:

- `~/.claude/projects/<cwd-slug>/<session>.jsonl` — main session
- `~/.claude/projects/<cwd-slug>/<session>/subagents/*.jsonl` — subagent runs, grouped as
  `<sessionId>/<file-stem>` so the parent session stays a main session

Rules:

- Keep only `user` / `assistant` rows inside the requested window.
- Project is the session's first `cwd` (launch directory); later `cd` does not move the session.
- User prompt text excludes tool results, `isMeta` rows and harness wrappers
  (`<command-*>`, `<local-command-*>`, `<system-reminder>`, `<task-notification>`). Pasted
  prompts that start with `<pasted_content>` are kept.
- Skip sessions whose `entrypoint` starts with `sdk` (memory-plugin helper sessions) and
  `*observer-sessions` directories.
- Do not read `~/.claude/transcripts/`, `history.jsonl` or `sessions/*.tmp`; they are older or
  non-Claude-Code formats.

## Unified Event Contract

Collectors should output:

```json
{
  "tool": "codex|claude",
  "session_id": "string",
  "project_key": "string",
  "project_path": "string|null",
  "cwd": "string|null",
  "timestamp": "ISO-8601|string|number",
  "event_type": "string",
  "title": "string|null",
  "text": "string|null",
  "evidence_path": "absolute path",
  "confidence": "high|medium|low",
  "raw": {}
}
```
