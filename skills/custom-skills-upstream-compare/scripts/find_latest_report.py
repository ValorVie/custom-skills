#!/usr/bin/env python3
"""
Find Latest Upstream Report

輔助工具：找到最新的 upstream-sync 報告並輸出路徑。
"""

import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get the custom-skills project root."""
    current = Path.cwd()
    while current != current.parent:
        if (current / "upstream").exists() or (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()


def find_latest_report(project_root: Path) -> Path | None:
    """Find the latest structured analysis report."""
    report_dir = project_root / "upstream" / "reports" / "structured"

    if not report_dir.exists():
        return None

    reports = list(report_dir.glob("analysis-*.yaml"))
    if not reports:
        return None

    return max(reports, key=lambda p: p.stat().st_mtime)


def main():
    project_root = get_project_root()
    latest = find_latest_report(project_root)

    if latest:
        print(latest)
    else:
        print("No report found. Run upstream-sync first:", file=sys.stderr)
        print("  python skills/upstream-sync/scripts/analyze_upstream.py", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
