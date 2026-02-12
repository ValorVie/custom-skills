#!/usr/bin/env python3
"""SessionStart hook: inject auto-skill knowledge-base and experience index into conversation context."""

import json
import os


def find_skill_root():
    """Search for auto-skill directory in known locations."""
    candidates = [
        os.path.expanduser("~/.claude/skills/auto-skill"),
        os.path.join(os.getcwd(), "skills", "auto-skill"),
    ]
    for path in candidates:
        if os.path.isdir(path):
            return path
    return None


def load_json(filepath):
    """Load and parse a JSON file, returning None on any error."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def main():
    root = find_skill_root()
    if not root:
        return

    output_parts = []

    # Knowledge base index
    kb_index = load_json(os.path.join(root, "knowledge-base", "_index.json"))
    if kb_index and kb_index.get("categories"):
        categories_with_content = [
            c for c in kb_index["categories"] if c.get("count", 0) > 0
        ]
        if categories_with_content:
            output_parts.append("[Auto-Skill Knowledge Base]")
            for cat in categories_with_content:
                keywords = ", ".join(cat.get("keywords", []))
                output_parts.append(
                    f"  {cat['name']} ({cat['file']}): "
                    f"{cat['count']} entries | keywords: {keywords}"
                )

    # Experience index
    exp_index = load_json(os.path.join(root, "experience", "_index.json"))
    if exp_index and exp_index.get("skills"):
        valid_skills = [
            s
            for s in exp_index["skills"]
            if s.get("skillId") and s.get("file")
        ]
        if valid_skills:
            output_parts.append("[Auto-Skill Experience]")
            for skill in valid_skills:
                output_parts.append(
                    f"  {skill['skillId']} ({skill['file']}): "
                    f"{skill.get('count', 0)} entries"
                )

    if output_parts:
        print("\n".join(output_parts))


if __name__ == "__main__":
    main()
