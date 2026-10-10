"""Claude-only entry point for the work-log-codex pipeline.

  parse    -> JSON report on stdout (same contract as wl_parser.work_log_parser)
  generate -> deterministic report files (same options as generate_work_log.py),
              default output root docs/work-logs/claude
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
CODEX_SKILL = REPO_ROOT / ".agents/skills/work-log-codex"
sys.path.insert(0, str(CODEX_SKILL))

from wl_parser import work_log_parser as wlp  # noqa: E402

# ponytail: the Claude reader is work-log-codex's own scripts/source_claude.py; only the
# Codex inputs are switched off here instead of forking ~4k lines.
# Ceiling: breaks if work-log-codex renames these names (tests/test_claude_projects.py
# guards it). Upgrade path: give build_report() a sources option.
wlp.load_codex_events = lambda *_args, **_kwargs: []
wlp._parse_codex_index_sessions = lambda *_args, **_kwargs: []


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in {"parse", "generate"}:
        print("usage: work_log_claude.py parse|generate [options]", file=sys.stderr)
        return 2
    command, rest = argv[0], argv[1:]
    if command == "parse":
        wlp.main(rest)
        return 0
    from scripts import generate_work_log  # noqa: PLC0415

    if not any(arg.startswith("--output-root") for arg in rest):
        rest = ["--output-root", str(REPO_ROOT / "docs/work-logs/claude"), *rest]
    sys.argv = ["work-log-claude", *rest]
    return generate_work_log.main()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
