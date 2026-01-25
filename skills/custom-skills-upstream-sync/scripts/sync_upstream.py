#!/usr/bin/env python3
"""
Upstream Sync Script

Track upstream repositories for updates and generate reports.
For deep quality analysis, use upstream-compare skill.
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


def get_project_root() -> Path:
    """Get the custom-skills project root."""
    current = Path.cwd()
    while current != current.parent:
        if (current / "upstream").exists() or (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_sources(project_root: Path) -> dict:
    """Load sources.yaml configuration."""
    sources_file = project_root / "upstream" / "sources.yaml"
    if not sources_file.exists():
        print(f"Error: {sources_file} not found")
        sys.exit(1)

    with open(sources_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_current_commit(repo_path: Path) -> str:
    """Get current HEAD commit hash."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def check_updates(sources: dict) -> dict:
    """Check each source for updates."""
    updates = {}

    for name, config in sources.get("sources", {}).items():
        local_path = Path(config["local_path"]).expanduser()

        if not local_path.exists():
            print(f"  [{name}] Not cloned: {local_path}")
            continue

        last_synced = config.get("last_synced_commit", "")
        current = get_current_commit(local_path)

        if not current:
            print(f"  [{name}] Failed to get commit")
            continue

        if current != last_synced:
            updates[name] = {
                "old_commit": last_synced,
                "new_commit": current,
                "local_path": local_path,
                "config": config,
            }
            print(f"  [{name}] Has updates: {last_synced[:7] if last_synced else '(none)'}..{current[:7]}")
        else:
            print(f"  [{name}] Up to date")

    return updates


def count_resources(repo_path: Path) -> dict:
    """Count resources in a repository."""
    counts = {
        "agents": 0,
        "commands": 0,
        "skills": 0,
        "rules": 0,
        "hooks": 0,
        "contexts": 0,
    }

    # Count agents
    agents_dir = repo_path / "agents"
    if agents_dir.exists():
        counts["agents"] = len(list(agents_dir.glob("*.md")))

    # Count commands
    commands_dir = repo_path / "commands"
    if commands_dir.exists():
        counts["commands"] = len(list(commands_dir.glob("*.md")))

    # Count skills
    skills_dir = repo_path / "skills"
    if skills_dir.exists():
        counts["skills"] = len([d for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()])

    # Count rules
    rules_dir = repo_path / "rules"
    if rules_dir.exists():
        counts["rules"] = len(list(rules_dir.glob("*.md")))

    # Count hooks
    hooks_file = repo_path / "hooks" / "hooks.json"
    if hooks_file.exists():
        counts["hooks"] = 1

    # Count contexts
    contexts_dir = repo_path / "contexts"
    if contexts_dir.exists():
        counts["contexts"] = len(list(contexts_dir.glob("*.md")))

    return counts


def list_resources(repo_path: Path) -> dict:
    """List all resources in a repository."""
    resources = {
        "agents": [],
        "commands": [],
        "skills": [],
        "rules": [],
        "contexts": [],
    }

    # List agents
    agents_dir = repo_path / "agents"
    if agents_dir.exists():
        resources["agents"] = [f.stem for f in agents_dir.glob("*.md")]

    # List commands
    commands_dir = repo_path / "commands"
    if commands_dir.exists():
        resources["commands"] = [f.stem for f in commands_dir.glob("*.md")]

    # List skills
    skills_dir = repo_path / "skills"
    if skills_dir.exists():
        resources["skills"] = [d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]

    # List rules
    rules_dir = repo_path / "rules"
    if rules_dir.exists():
        resources["rules"] = [f.stem for f in rules_dir.glob("*.md")]

    # List contexts
    contexts_dir = repo_path / "contexts"
    if contexts_dir.exists():
        resources["contexts"] = [f.stem for f in contexts_dir.glob("*.md")]

    return resources


def get_existing_resources(project_root: Path) -> dict:
    """Get existing resources in custom-skills."""
    resources = {
        "agents": [],
        "commands": [],
        "skills": [],
    }

    # List agents (from agents/claude/)
    agents_dir = project_root / "agents" / "claude"
    if agents_dir.exists():
        resources["agents"] = [f.stem for f in agents_dir.glob("*.md")]

    # List commands (from commands/claude/)
    commands_dir = project_root / "commands" / "claude"
    if commands_dir.exists():
        resources["commands"] = [f.stem for f in commands_dir.glob("*.md")]

    # List skills
    skills_dir = project_root / "skills"
    if skills_dir.exists():
        resources["skills"] = [d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]

    return resources


def generate_diff_report(updates: dict, project_root: Path) -> Path:
    """Generate diff report for updated sources."""
    report_file = project_root / "upstream" / f"diff-report-{datetime.now().strftime('%Y-%m-%d')}.md"

    lines = [
        "# Upstream Diff Report",
        f"\nGenerated: {datetime.now().isoformat()}",
        "\n## Summary\n",
    ]

    for name, info in updates.items():
        old = info['old_commit'][:7] if info['old_commit'] else '(none)'
        new = info['new_commit'][:7]
        lines.append(f"- **{name}**: {old}..{new}")

    lines.append("\n---\n")

    for name, info in updates.items():
        lines.append(f"\n## {name}\n")
        lines.append(f"- Old commit: `{info['old_commit'] or '(none)'}`")
        lines.append(f"- New commit: `{info['new_commit']}`")
        lines.append(f"- Local path: `{info['local_path']}`\n")

        if info['old_commit']:
            result = subprocess.run(
                ["git", "log", "--oneline", f"{info['old_commit']}..{info['new_commit']}"],
                cwd=str(info["local_path"]),
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                lines.append("### Commits\n")
                lines.append("```")
                lines.append(result.stdout.strip())
                lines.append("```\n")

            result = subprocess.run(
                ["git", "diff", "--name-status", info["old_commit"], info["new_commit"]],
                cwd=str(info["local_path"]),
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                lines.append("### Changed Files\n")
                lines.append("```")
                lines.append(result.stdout.strip())
                lines.append("```\n")

    lines.append("\n## Next Steps\n")
    lines.append("1. Review changes above")
    lines.append("2. Run `/upstream-sync --assess` for integration assessment")
    lines.append("3. Use `/upstream-compare` for deep quality analysis")

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return report_file


def generate_assessment_report(sources: dict, project_root: Path) -> Path:
    """Generate integration assessment report."""
    report_file = project_root / "upstream" / f"integration-assessment-{datetime.now().strftime('%Y-%m-%d')}.md"

    existing = get_existing_resources(project_root)

    lines = [
        "# Upstream Integration Assessment Report",
        f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d')}",
        f"**Analyst**: upstream-sync script",
        "\n---\n",
        "## Executive Summary\n",
        "| Source | Agents | Commands | Skills | Rules | Contexts | Status |",
        "|--------|--------|----------|--------|-------|----------|--------|",
    ]

    source_data = {}

    for name, config in sources.get("sources", {}).items():
        local_path = Path(config["local_path"]).expanduser()

        if not local_path.exists():
            lines.append(f"| {name} | - | - | - | - | - | Not Cloned |")
            continue

        counts = count_resources(local_path)
        resources = list_resources(local_path)
        source_data[name] = {
            "counts": counts,
            "resources": resources,
            "local_path": local_path,
            "config": config,
        }

        lines.append(
            f"| {name} | {counts['agents']} | {counts['commands']} | "
            f"{counts['skills']} | {counts['rules']} | {counts['contexts']} | Available |"
        )

    lines.append("\n---\n")

    # Detailed analysis for each source
    for name, data in source_data.items():
        lines.append(f"\n## {name}\n")
        lines.append(f"**Local Path**: `{data['local_path']}`\n")

        resources = data["resources"]

        # Agents analysis
        if resources["agents"]:
            lines.append("### Agents\n")
            lines.append("| Agent | Recommendation | Notes |")
            lines.append("|-------|----------------|-------|")
            for agent in sorted(resources["agents"]):
                if agent in existing["agents"]:
                    lines.append(f"| {agent} | Skip | Already in custom-skills |")
                else:
                    lines.append(f"| {agent} | **High** | New capability |")

        # Commands analysis
        if resources["commands"]:
            lines.append("\n### Commands\n")
            lines.append("| Command | Recommendation | Notes |")
            lines.append("|---------|----------------|-------|")
            for cmd in sorted(resources["commands"]):
                if cmd in existing["commands"]:
                    lines.append(f"| {cmd} | Skip | Already in custom-skills |")
                else:
                    lines.append(f"| {cmd} | **Medium** | Review needed |")

        # Skills analysis
        if resources["skills"]:
            lines.append("\n### Skills\n")
            lines.append("| Skill | Recommendation | Notes |")
            lines.append("|-------|----------------|-------|")
            for skill in sorted(resources["skills"]):
                if skill in existing["skills"]:
                    lines.append(f"| {skill} | Low | Already in custom-skills |")
                else:
                    lines.append(f"| {skill} | **High** | New skill |")

        # Rules analysis
        if resources["rules"]:
            lines.append("\n### Rules\n")
            lines.append("| Rule | Recommendation |")
            lines.append("|------|----------------|")
            for rule in sorted(resources["rules"]):
                lines.append(f"| {rule} | **Medium** |")

        # Contexts analysis
        if resources["contexts"]:
            lines.append("\n### Contexts\n")
            lines.append("| Context | Recommendation |")
            lines.append("|---------|----------------|")
            for ctx in sorted(resources["contexts"]):
                lines.append(f"| {ctx} | **Low** |")

        lines.append("")

    # Summary statistics
    lines.append("\n---\n")
    lines.append("## Integration Summary\n")

    total_new = {"agents": 0, "commands": 0, "skills": 0, "rules": 0, "contexts": 0}
    total_overlap = {"agents": 0, "commands": 0, "skills": 0}

    for name, data in source_data.items():
        resources = data["resources"]
        for agent in resources["agents"]:
            if agent in existing["agents"]:
                total_overlap["agents"] += 1
            else:
                total_new["agents"] += 1
        for cmd in resources["commands"]:
            if cmd in existing["commands"]:
                total_overlap["commands"] += 1
            else:
                total_new["commands"] += 1
        for skill in resources["skills"]:
            if skill in existing["skills"]:
                total_overlap["skills"] += 1
            else:
                total_new["skills"] += 1
        total_new["rules"] += len(resources["rules"])
        total_new["contexts"] += len(resources["contexts"])

    lines.append("| Category | High | Medium | Low | Skip |")
    lines.append("|----------|------|--------|-----|------|")
    lines.append(f"| Agents | {total_new['agents']} | 0 | 0 | {total_overlap['agents']} |")
    lines.append(f"| Commands | 0 | {total_new['commands']} | 0 | {total_overlap['commands']} |")
    lines.append(f"| Skills | {total_new['skills']} | 0 | {total_overlap['skills']} | 0 |")
    lines.append(f"| Rules | 0 | {total_new['rules']} | 0 | 0 |")
    lines.append(f"| Contexts | 0 | 0 | {total_new['contexts']} | 0 |")

    lines.append("\n---\n")
    lines.append("## Next Steps\n")
    lines.append("1. Review resources marked **High** priority")
    lines.append("2. Use `/upstream-compare` for detailed quality comparison")
    lines.append("3. Create OpenSpec proposal: `/openspec:proposal upstream-integration`")
    lines.append("\n---\n")
    lines.append("*Report generated by upstream-sync skill*")

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return report_file


def main():
    parser = argparse.ArgumentParser(description="Track upstream repositories for updates")
    parser.add_argument("--check", action="store_true", help="Check for updates only")
    parser.add_argument("--diff", action="store_true", help="Generate diff report")
    parser.add_argument("--assess", action="store_true", help="Generate integration assessment")
    parser.add_argument("--source", type=str, help="Check specific source only")
    args = parser.parse_args()

    project_root = get_project_root()
    print(f"Project root: {project_root}")

    sources = load_sources(project_root)

    # Filter to specific source if requested
    if args.source:
        if args.source not in sources.get("sources", {}):
            print(f"Error: Source '{args.source}' not found")
            sys.exit(1)
        sources["sources"] = {args.source: sources["sources"][args.source]}

    updates = {}

    if args.check or args.diff or args.assess:
        print("\n[1/2] Checking for updates...")
        updates = check_updates(sources)

        if not updates and not args.assess:
            print("\nNo updates found.")
            return

        print(f"\nFound {len(updates)} source(s) with updates.")

    if args.diff:
        if updates:
            print("\n[2/2] Generating diff report...")
            report_file = generate_diff_report(updates, project_root)
            print(f"\nDiff report: {report_file}")

    if args.assess:
        print("\n[2/2] Generating integration assessment...")
        assess_file = generate_assessment_report(sources, project_root)
        print(f"\nAssessment report: {assess_file}")
        print("\nNext: Use /upstream-compare for deep quality analysis")
    elif args.diff:
        print("\nNext: Run --assess for integration assessment")


if __name__ == "__main__":
    main()
