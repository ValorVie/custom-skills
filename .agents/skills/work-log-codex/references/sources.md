# Sources

`work-log-codex` currently reads these local histories:

## Codex

- `~/.codex/session_index.jsonl`
- `~/.codex/history.jsonl`
- `~/.codex/sessions/**/*.jsonl`

Use per-session JSONL as the authoritative event stream whenever available. Index and history files are supporting evidence.

## Claude Code

- `~/.claude/transcripts/*.jsonl`
- `~/.claude/history.jsonl`
- `~/.claude/sessions/*.tmp`
- `~/.claude/projects/*/*.jsonl` as fallback only

Exclude observer-style project records by default, especially `*-claude-mem-observer-sessions`.

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
