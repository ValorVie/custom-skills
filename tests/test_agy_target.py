"""驗證 gemini → agy target 改名（Antigravity CLI）。

對應 OpenSpec change `migrate-gemini-cli-to-agy` 的 cli-distribution 規格：
- `agy` 為有效 target，僅分發 skills 至 `~/.gemini/skills`
- 舊值 `gemini` 不再是有效 target（無別名）
"""

from script.utils import shared
from script.commands.standards import VALID_TARGETS


def test_agy_is_valid_target_skills_only():
    assert "agy" in shared.COPY_TARGETS
    assert set(shared.COPY_TARGETS["agy"].keys()) == {"skills"}
    assert "agy" in VALID_TARGETS


def test_agy_skills_path_is_shared_gemini_dir():
    # agy 讀取共用 skills 目錄 ~/.gemini/skills
    path = shared.get_target_path("agy", "skills")
    assert path is not None
    assert path.name == "skills"
    assert path.parent.name == ".gemini"


def test_gemini_is_no_longer_a_target():
    assert "gemini" not in shared.COPY_TARGETS
    assert "gemini" not in VALID_TARGETS
    assert shared.get_target_path("gemini", "skills") is None


def test_retired_gemini_npm_package_removed():
    assert "@google/gemini-cli" not in shared.NPM_PACKAGES
