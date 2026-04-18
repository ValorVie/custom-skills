"""由 npx 管理的 skill 與 ai-dev manifest 的同步邏輯。

提供兩個互補能力：
1. 查詢哪些 skill 被 `upstream/npx-skills.yaml` 宣告由 npx 管理
2. 從 ai-dev 的 target manifest 移除這些條目，避免：
   - clone 的 conflict 誤判（source 與 target 哈希不一致）
   - upstream prescan 把已交接給 npx 的 skill 重新記入 tracker
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from script.services.npx_skills.config import NpxSkillsConfig
from script.utils.paths import (
    get_npx_skills_project_yaml,
    get_npx_skills_user_yaml,
)

# clone 分發的所有 target（對齊 command_manifest.TARGETS）
_ALL_TARGETS = ("claude", "codex", "gemini", "opencode", "antigravity")


def get_npx_managed_skill_names(yaml_path: Path | None = None) -> set[str]:
    """回傳 npx-skills.yaml 宣告由 npx 管理的 skill 名稱集合。

    優先讀 user-level yaml（執行期實際對照來源），缺少時回退到專案 yaml。
    任何讀取或解析失敗都回傳空 set（呼叫端應將空 set 視為「無 npx 管理名單」）。
    """
    if yaml_path is None:
        candidate = get_npx_skills_user_yaml()
        if not candidate.exists():
            candidate = get_npx_skills_project_yaml()
        yaml_path = candidate
    if not yaml_path.exists():
        return set()
    try:
        config = NpxSkillsConfig.load(yaml_path)
    except Exception:
        return set()
    return {entry.skill for entry in config.entries}


def cleanup_skills_from_manifests(
    skill_names: Iterable[str],
    *,
    targets: Iterable[str] = _ALL_TARGETS,
) -> dict[str, list[str]]:
    """從指定 target manifest 移除給定 skill 的追蹤條目。

    回傳 {target: [已移除的 skill 名稱]}，僅包含實際有移除的 target。
    若 manifest 不存在則略過該 target。
    """
    # 延遲 import 避免與 npx_skills 產生循環匯入
    from script.utils.manifest import read_manifest, write_manifest

    skill_set = set(skill_names)
    if not skill_set:
        return {}

    removed_by_target: dict[str, list[str]] = {}
    for target in targets:
        manifest = read_manifest(target)
        if not manifest:
            continue
        skills = manifest.get("files", {}).get("skills", {})
        removed = [name for name in list(skills.keys()) if name in skill_set]
        if not removed:
            continue
        for name in removed:
            skills.pop(name, None)
        write_manifest(target, manifest)
        removed_by_target[target] = sorted(removed)

    return removed_by_target
