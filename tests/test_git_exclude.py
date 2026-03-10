"""git_exclude.py 的單元測試。"""

from pathlib import Path

import pytest

from script.utils.git_exclude import (
    MARKER_END,
    MARKER_START,
    ensure_ai_exclude,
    remove_ai_exclude,
    get_current_patterns,
)


def _make_git_repo(tmp_path: Path) -> Path:
    """建立模擬 git repo（含 .git/info/ 目錄）。"""
    git_dir = tmp_path / ".git" / "info"
    git_dir.mkdir(parents=True)
    return tmp_path


class TestEnsureAiExclude:
    """ensure_ai_exclude 測試。"""

    def test_creates_exclude_file_if_missing(self, tmp_path: Path) -> None:
        """exclude 檔案不存在時建立並寫入區塊。"""
        project = _make_git_repo(tmp_path)
        patterns = [".claude/", "CLAUDE.md"]

        modified, added, skipped = ensure_ai_exclude(project, patterns)

        assert modified is True
        assert added == [".claude/", "CLAUDE.md"]
        assert skipped == []

        content = (project / ".git" / "info" / "exclude").read_text()
        assert MARKER_START in content
        assert ".claude/" in content
        assert "CLAUDE.md" in content
        assert MARKER_END in content

    def test_creates_info_directory_if_missing(self, tmp_path: Path) -> None:
        """.git/info/ 不存在時建立。"""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        # 不建立 info/

        patterns = [".claude/"]
        modified, added, skipped = ensure_ai_exclude(tmp_path, patterns)

        assert modified is True
        assert (tmp_path / ".git" / "info" / "exclude").exists()

    def test_skips_non_git_repo(self, tmp_path: Path) -> None:
        """非 git repo 時跳過。"""
        patterns = [".claude/"]
        modified, added, skipped = ensure_ai_exclude(tmp_path, patterns)

        assert modified is False
        assert added == []

    def test_preserves_existing_entries(self, tmp_path: Path) -> None:
        """不動使用者手動項目。"""
        project = _make_git_repo(tmp_path)
        exclude = project / ".git" / "info" / "exclude"
        exclude.write_text(".env\nnode_modules/\n", encoding="utf-8")

        patterns = [".claude/", "CLAUDE.md"]
        ensure_ai_exclude(project, patterns)

        content = exclude.read_text()
        assert ".env" in content
        assert "node_modules/" in content
        assert ".claude/" in content

    def test_skips_patterns_already_outside_block(self, tmp_path: Path) -> None:
        """使用者已手動加的 pattern 不重複。"""
        project = _make_git_repo(tmp_path)
        exclude = project / ".git" / "info" / "exclude"
        exclude.write_text(".claude/\n", encoding="utf-8")

        patterns = [".claude/", ".gemini/", "CLAUDE.md"]
        modified, added, skipped = ensure_ai_exclude(project, patterns)

        assert modified is True
        assert ".claude/" in skipped
        assert ".gemini/" in added
        content = exclude.read_text()
        # .claude/ 只出現一次（區塊外的那個）
        lines = [l.strip() for l in content.splitlines() if l.strip() == ".claude/"]
        assert len(lines) == 1

    def test_updates_existing_block(self, tmp_path: Path) -> None:
        """已有管理區塊時更新內容。"""
        project = _make_git_repo(tmp_path)
        exclude = project / ".git" / "info" / "exclude"
        old_content = (
            ".env\n"
            f"{MARKER_START}\n"
            ".claude/\n"
            f"{MARKER_END}\n"
        )
        exclude.write_text(old_content, encoding="utf-8")

        patterns = [".claude/", ".gemini/", "CLAUDE.md"]
        modified, added, skipped = ensure_ai_exclude(project, patterns)

        assert modified is True
        content = exclude.read_text()
        assert ".gemini/" in content
        assert "CLAUDE.md" in content
        assert content.count(MARKER_START) == 1

    def test_idempotent(self, tmp_path: Path) -> None:
        """多次呼叫結果一致。"""
        project = _make_git_repo(tmp_path)
        patterns = [".claude/", "CLAUDE.md"]

        ensure_ai_exclude(project, patterns)
        content1 = (project / ".git" / "info" / "exclude").read_text()

        modified, _, _ = ensure_ai_exclude(project, patterns)
        content2 = (project / ".git" / "info" / "exclude").read_text()

        assert modified is False
        assert content1 == content2

    def test_dry_run_does_not_write(self, tmp_path: Path) -> None:
        """dry_run 模式不寫入。"""
        project = _make_git_repo(tmp_path)
        patterns = [".claude/"]

        modified, added, skipped = ensure_ai_exclude(project, patterns, dry_run=True)

        assert modified is False
        assert added == [".claude/"]
        assert not (project / ".git" / "info" / "exclude").exists()


class TestRemoveAiExclude:
    """remove_ai_exclude 測試。"""

    def test_removes_block(self, tmp_path: Path) -> None:
        """移除管理區塊。"""
        project = _make_git_repo(tmp_path)
        exclude = project / ".git" / "info" / "exclude"
        content = (
            ".env\n\n"
            f"{MARKER_START}\n"
            ".claude/\n"
            f"{MARKER_END}\n"
        )
        exclude.write_text(content, encoding="utf-8")

        result = remove_ai_exclude(project)

        assert result is True
        new_content = exclude.read_text()
        assert MARKER_START not in new_content
        assert ".claude/" not in new_content
        assert ".env" in new_content

    def test_no_block_returns_false(self, tmp_path: Path) -> None:
        """無區塊時回傳 False。"""
        project = _make_git_repo(tmp_path)
        exclude = project / ".git" / "info" / "exclude"
        exclude.write_text(".env\n", encoding="utf-8")

        result = remove_ai_exclude(project)
        assert result is False


class TestGetCurrentPatterns:
    """get_current_patterns 測試。"""

    def test_returns_patterns(self, tmp_path: Path) -> None:
        """回傳目前區塊內的 patterns。"""
        project = _make_git_repo(tmp_path)
        exclude = project / ".git" / "info" / "exclude"
        content = (
            f"{MARKER_START}\n"
            ".claude/\n"
            "CLAUDE.md\n"
            f"{MARKER_END}\n"
        )
        exclude.write_text(content, encoding="utf-8")

        patterns = get_current_patterns(project)
        assert patterns == [".claude/", "CLAUDE.md"]

    def test_returns_none_when_no_block(self, tmp_path: Path) -> None:
        """無區塊時回傳 None。"""
        project = _make_git_repo(tmp_path)
        exclude = project / ".git" / "info" / "exclude"
        exclude.write_text(".env\n", encoding="utf-8")

        assert get_current_patterns(project) is None


from script.utils.git_exclude import derive_exclude_patterns


class TestDeriveExcludePatterns:
    """derive_exclude_patterns 測試。"""

    def test_derives_from_template(self, tmp_path: Path) -> None:
        """從模板內容推導排除清單。"""
        template = tmp_path / "template"
        template.mkdir()
        (template / ".claude").mkdir()
        (template / ".standards").mkdir()
        (template / "CLAUDE.md").touch()
        (template / ".editorconfig").touch()
        (template / ".gitattributes").touch()
        (template / ".gitignore").touch()

        patterns = derive_exclude_patterns(template)

        assert ".claude/" in patterns
        assert ".standards/" in patterns
        assert "CLAUDE.md" in patterns
        # 保留項不在排除清單
        assert ".editorconfig" not in patterns
        assert ".gitattributes" not in patterns
        assert ".gitignore" not in patterns

    def test_github_specific_paths(self, tmp_path: Path) -> None:
        """.github/ 只排除 AI 相關子路徑。"""
        template = tmp_path / "template"
        template.mkdir()
        github = template / ".github"
        github.mkdir()
        (github / "skills").mkdir()
        (github / "prompts").mkdir()
        (github / "copilot-instructions.md").touch()

        patterns = derive_exclude_patterns(template)

        assert ".github/skills/" in patterns
        assert ".github/prompts/" in patterns
        assert ".github/copilot-instructions.md" in patterns
        assert ".github/" not in patterns  # 整個 .github/ 不在

    def test_excludes_git_directory(self, tmp_path: Path) -> None:
        """.git 目錄不出現在排除清單。"""
        template = tmp_path / "template"
        template.mkdir()
        (template / ".git").mkdir()
        (template / "CLAUDE.md").touch()

        patterns = derive_exclude_patterns(template)

        assert ".git" not in patterns
        assert ".git/" not in patterns

    def test_custom_keep_tracked(self, tmp_path: Path) -> None:
        """自訂保留項。"""
        template = tmp_path / "template"
        template.mkdir()
        (template / "CLAUDE.md").touch()
        (template / "custom-keep.txt").touch()

        patterns = derive_exclude_patterns(
            template, keep_tracked=[".editorconfig", ".gitattributes", ".gitignore", "custom-keep.txt"]
        )

        assert "CLAUDE.md" in patterns
        assert "custom-keep.txt" not in patterns

    def test_adds_ai_dev_project_yaml(self, tmp_path: Path) -> None:
        """.ai-dev-project.yaml 永遠包含在排除清單。"""
        template = tmp_path / "template"
        template.mkdir()
        (template / "CLAUDE.md").touch()

        patterns = derive_exclude_patterns(template)

        assert ".ai-dev-project.yaml" in patterns


from script.utils.project_tracking import (
    load_tracking_file,
    save_tracking_file,
)


class TestProjectTrackingGitExclude:
    """project_tracking git_exclude 擴展測試。"""

    def test_save_and_load_git_exclude(self, tmp_path: Path) -> None:
        """git_exclude 欄位可正常存取。"""
        data = {
            "template": {"name": "test"},
            "managed_files": ["CLAUDE.md"],
            "git_exclude": {
                "enabled": True,
                "version": "1",
                "patterns": [".claude/", "CLAUDE.md"],
                "keep_tracked": [".editorconfig"],
            },
        }
        save_tracking_file(data, tmp_path)
        loaded = load_tracking_file(tmp_path)

        assert loaded is not None
        assert loaded["git_exclude"]["enabled"] is True
        assert loaded["git_exclude"]["patterns"] == [".claude/", "CLAUDE.md"]

    def test_backward_compatible_without_git_exclude(self, tmp_path: Path) -> None:
        """無 git_exclude 欄位時不影響既有功能。"""
        data = {
            "template": {"name": "test"},
            "managed_files": ["CLAUDE.md"],
        }
        save_tracking_file(data, tmp_path)
        loaded = load_tracking_file(tmp_path)

        assert loaded is not None
        assert "git_exclude" not in loaded


from script.utils.project_tracking import (
    get_git_exclude_config,
    update_git_exclude_config,
)


class TestGitExcludeHelpers:

    def test_update_and_get(self, tmp_path: Path) -> None:
        save_tracking_file({"template": {"name": "test"}, "managed_files": []}, tmp_path)
        update_git_exclude_config(
            enabled=True,
            patterns=[".claude/", "CLAUDE.md"],
            keep_tracked=[".editorconfig"],
            project_dir=tmp_path,
        )
        config = get_git_exclude_config(tmp_path)
        assert config is not None
        assert config["enabled"] is True
        assert ".claude/" in config["patterns"]

    def test_get_returns_none_when_missing(self, tmp_path: Path) -> None:
        save_tracking_file({"template": {"name": "test"}, "managed_files": []}, tmp_path)
        assert get_git_exclude_config(tmp_path) is None
