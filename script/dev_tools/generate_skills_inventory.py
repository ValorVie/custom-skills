"""產生 skills / commands / agents 清單（docs/skills-inventory.md）。

稽核報告的手抄數字會漂移（skills-source-audit-2026-03-21.md 寫 52、實際 25）；
現況一律以本腳本輸出為準：

    uv run python script/dev_tools/generate_skills_inventory.py
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "skills-inventory.md"


def _skill_entries() -> list[str]:
    entries = []
    for path in sorted((ROOT / "skills").iterdir()):
        if path.is_dir() and (path / "SKILL.md").is_file():
            entries.append(path.name)
    return entries


def _flat_entries(dirname: str, suffix: str = ".md") -> list[str]:
    base = ROOT / dirname
    if not base.is_dir():
        return []
    return sorted(
        p.stem for p in base.rglob(f"*{suffix}") if p.is_file() and p.name != "README.md"
    )


def main() -> None:
    skills = _skill_entries()
    commands = _flat_entries("commands")
    agents = _flat_entries("agents")

    lines = [
        "# Skills / Commands / Agents 清單（自動生成）",
        "",
        f"由 `script/dev_tools/generate_skills_inventory.py` 產生於 {date.today().isoformat()}。",
        "手動編輯無效；數字或清單過期時重跑腳本。",
        "",
        f"## Skills（{len(skills)}）",
        "",
        *[f"- {name}" for name in skills],
        "",
        f"## Commands（{len(commands)}）",
        "",
        *[f"- {name}" for name in commands],
        "",
        f"## Agents（{len(agents)}）",
        "",
        *[f"- {name}" for name in agents],
        "",
    ]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"skills={len(skills)} commands={len(commands)} agents={len(agents)} -> {OUTPUT}")


if __name__ == "__main__":
    main()
