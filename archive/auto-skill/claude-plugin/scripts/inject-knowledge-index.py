#!/usr/bin/env python3
"""SessionStart hook: inject auto-skill knowledge-base and experience index into conversation context."""

import json
import os


def find_all_skill_roots():
    """Search for user/project auto-skill directories in known locations."""
    candidates = {
        "user": os.path.expanduser("~/.claude/skills/auto-skill"),
        "project": os.path.join(os.getcwd(), "skills", "auto-skill"),
    }
    roots = {}
    for source, path in candidates.items():
        if os.path.isdir(path):
            roots[source] = path
    return roots


def load_json(filepath):
    """Load and parse a JSON file, returning None on any error."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def normalize_count(value):
    """Convert arbitrary count values to non-negative integers."""
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return 0


def merge_knowledge_base(roots):
    """Merge knowledge-base categories from multiple roots by category id."""
    merged = {}
    for source, root in roots.items():
        kb_index = load_json(os.path.join(root, "knowledge-base", "_index.json"))
        if not kb_index:
            continue

        categories = kb_index.get("categories")
        if not isinstance(categories, list):
            continue

        for category in categories:
            category_id = category.get("id")
            if not category_id:
                continue

            entry = merged.setdefault(
                category_id,
                {
                    "id": category_id,
                    "name": category.get("name", ""),
                    "file": category.get("file", ""),
                    "keywords": [],
                    "counts": {"user": 0, "project": 0},
                },
            )

            if not entry["name"] and category.get("name"):
                entry["name"] = category["name"]
            if not entry["file"] and category.get("file"):
                entry["file"] = category["file"]

            for keyword in category.get("keywords", []):
                if keyword and keyword not in entry["keywords"]:
                    entry["keywords"].append(keyword)

            entry["counts"][source] += normalize_count(category.get("count", 0))

    return sorted(merged.values(), key=lambda item: (item["name"], item["id"]))


def merge_experience(roots):
    """Merge experience skills from multiple roots by skillId."""
    merged = {}
    for source, root in roots.items():
        exp_index = load_json(os.path.join(root, "experience", "_index.json"))
        if not exp_index:
            continue

        skills = exp_index.get("skills")
        if not isinstance(skills, list):
            continue

        for skill in skills:
            skill_id = skill.get("skillId")
            skill_file = skill.get("file")
            if not skill_id or not skill_file:
                continue

            entry = merged.setdefault(
                skill_id,
                {
                    "skillId": skill_id,
                    "file": skill_file,
                    "counts": {"user": 0, "project": 0},
                },
            )

            if not entry["file"] and skill_file:
                entry["file"] = skill_file

            entry["counts"][source] += normalize_count(skill.get("count", 0))

    return sorted(merged.values(), key=lambda item: item["skillId"])


def format_count_annotation(counts):
    """Format count text with single-source or dual-source annotations."""
    user_count = normalize_count(counts.get("user", 0))
    project_count = normalize_count(counts.get("project", 0))
    total = user_count + project_count

    if total <= 0:
        return ""

    if user_count and project_count:
        return f"{total} entries ({user_count} [使用者] + {project_count} [專案])"

    source = "使用者" if user_count else "專案"
    return f"{total} entries [{source}]"


def main():
    roots = find_all_skill_roots()
    if not roots:
        return

    output_parts = []

    # Knowledge base index
    merged_categories = merge_knowledge_base(roots)
    categories_with_content = [
        c
        for c in merged_categories
        if normalize_count(c["counts"].get("user", 0))
        + normalize_count(c["counts"].get("project", 0))
        > 0
    ]
    if categories_with_content:
        output_parts.append("[Auto-Skill Knowledge Base]")
        for cat in categories_with_content:
            annotation = format_count_annotation(cat["counts"])
            if not annotation:
                continue
            keywords = ", ".join(cat.get("keywords", []))
            output_parts.append(
                f"  {cat['name']} ({cat['file']}): {annotation} | keywords: {keywords}"
            )

    # Experience index
    merged_skills = merge_experience(roots)
    skills_with_content = [
        s
        for s in merged_skills
        if normalize_count(s["counts"].get("user", 0))
        + normalize_count(s["counts"].get("project", 0))
        > 0
    ]
    if skills_with_content:
        output_parts.append("[Auto-Skill Experience]")
        for skill in skills_with_content:
            annotation = format_count_annotation(skill["counts"])
            if not annotation:
                continue
            output_parts.append(f"  {skill['skillId']} ({skill['file']}): {annotation}")

    if output_parts:
        print("\n".join(output_parts))


if __name__ == "__main__":
    main()
