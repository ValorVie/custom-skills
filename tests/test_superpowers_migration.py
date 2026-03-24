"""Tests for superpowers migration functions in script.utils.shared."""

import json
import os
from pathlib import Path

from script.utils.shared import (
    _ensure_opencode_superpowers_plugin,
    migrate_opencode_superpowers,
    refresh_codex_superpowers_symlinks,
    SUPERPOWERS_GIT_URL,
)


# ============================================================
# _ensure_opencode_superpowers_plugin
# ============================================================


class TestEnsureOpencodeSuperpowersPlugin:
    """Tests for _ensure_opencode_superpowers_plugin."""

    def test_plugin_inject_to_empty_array(self, tmp_path):
        """opencode.json with empty plugin array -> should add superpowers entry."""
        config = {"mcpServers": {}, "plugin": []}
        opencode_json = tmp_path / "opencode.json"
        opencode_json.write_text(json.dumps(config, indent=2), encoding="utf-8")

        result = _ensure_opencode_superpowers_plugin(opencode_json)

        assert result is True
        written = json.loads(opencode_json.read_text(encoding="utf-8"))
        assert len(written["plugin"]) == 1
        assert "superpowers" in written["plugin"][0]
        assert SUPERPOWERS_GIT_URL in written["plugin"][0]

    def test_plugin_already_exists(self, tmp_path):
        """opencode.json already has superpowers -> should return True without writing."""
        plugin_entry = f"superpowers@git+{SUPERPOWERS_GIT_URL}"
        config = {"plugin": [plugin_entry]}
        opencode_json = tmp_path / "opencode.json"
        original_content = json.dumps(config, indent=2)
        opencode_json.write_text(original_content, encoding="utf-8")

        result = _ensure_opencode_superpowers_plugin(opencode_json)

        assert result is True
        # File should not have been rewritten (content unchanged)
        assert opencode_json.read_text(encoding="utf-8") == original_content

    def test_missing_opencode_json(self, tmp_path):
        """File doesn't exist -> return False, no crash."""
        opencode_json = tmp_path / "opencode.json"

        result = _ensure_opencode_superpowers_plugin(opencode_json)

        assert result is False

    def test_invalid_json(self, tmp_path):
        """Broken JSON -> return False with warning."""
        opencode_json = tmp_path / "opencode.json"
        opencode_json.write_text("{broken json content", encoding="utf-8")

        result = _ensure_opencode_superpowers_plugin(opencode_json)

        assert result is False

    def test_jsonc_trailing_commas(self, tmp_path):
        """opencode.json with trailing commas (JSONC) -> should parse successfully."""
        jsonc_content = '{\n  "plugin": ["existing-plugin",],\n  "key": "value",\n}'
        opencode_json = tmp_path / "opencode.json"
        opencode_json.write_text(jsonc_content, encoding="utf-8")

        result = _ensure_opencode_superpowers_plugin(opencode_json)

        assert result is True
        written = json.loads(opencode_json.read_text(encoding="utf-8"))
        assert len(written["plugin"]) == 2
        assert written["plugin"][0] == "existing-plugin"
        assert "superpowers" in written["plugin"][1]

    def test_preserves_existing_config(self, tmp_path):
        """Write back should preserve all existing keys."""
        config = {
            "mcpServers": {"server1": {"url": "http://localhost"}},
            "plugin": [],
            "theme": "dark",
            "customKey": [1, 2, 3],
        }
        opencode_json = tmp_path / "opencode.json"
        opencode_json.write_text(json.dumps(config, indent=2), encoding="utf-8")

        result = _ensure_opencode_superpowers_plugin(opencode_json)

        assert result is True
        written = json.loads(opencode_json.read_text(encoding="utf-8"))
        assert written["mcpServers"] == {"server1": {"url": "http://localhost"}}
        assert written["theme"] == "dark"
        assert written["customKey"] == [1, 2, 3]
        assert len(written["plugin"]) == 1


# ============================================================
# migrate_opencode_superpowers
# ============================================================


class TestMigrateOpencodeSuperpowers:
    """Tests for migrate_opencode_superpowers."""

    def _setup_paths(self, monkeypatch, tmp_path):
        """Helper to set up all mocked paths under tmp_path."""
        opencode_dir = tmp_path / "opencode"
        opencode_dir.mkdir(parents=True)

        superpowers_dir = opencode_dir / "superpowers"
        plugin_dir = opencode_dir / "plugins"
        plugin_dir.mkdir(parents=True)
        skills_dir = opencode_dir / "skills"
        skills_dir.mkdir(parents=True)

        monkeypatch.setattr(
            "script.utils.shared.get_opencode_superpowers_dir",
            lambda: superpowers_dir,
        )
        monkeypatch.setattr(
            "script.utils.shared.get_opencode_plugin_dir",
            lambda: plugin_dir,
        )
        monkeypatch.setattr(
            "script.utils.shared.get_opencode_config_dir",
            lambda: opencode_dir,
        )

        return opencode_dir, superpowers_dir, plugin_dir, skills_dir

    def test_no_old_setup_no_opencode_json(self, monkeypatch, tmp_path):
        """Nothing exists -> no-op."""
        opencode_dir, superpowers_dir, plugin_dir, skills_dir = self._setup_paths(
            monkeypatch, tmp_path
        )

        # No old setup, no opencode.json — should just return without error
        migrate_opencode_superpowers()

    def test_no_old_setup_with_opencode_json(self, monkeypatch, tmp_path):
        """Only opencode.json exists -> ensure plugin is called."""
        opencode_dir, superpowers_dir, plugin_dir, skills_dir = self._setup_paths(
            monkeypatch, tmp_path
        )

        # Create opencode.json with empty plugin array
        opencode_json = opencode_dir / "opencode.json"
        opencode_json.write_text(json.dumps({"plugin": []}, indent=2), encoding="utf-8")

        migrate_opencode_superpowers()

        # Should have injected the plugin
        written = json.loads(opencode_json.read_text(encoding="utf-8"))
        assert any("superpowers" in p for p in written["plugin"])

    def test_old_symlinks_detected_and_removed(self, monkeypatch, tmp_path):
        """Create symlinks at old locations, verify they get removed."""
        opencode_dir, superpowers_dir, plugin_dir, skills_dir = self._setup_paths(
            monkeypatch, tmp_path
        )

        # Create a real target for symlinks
        real_target = tmp_path / "real_target"
        real_target.mkdir()
        real_file = tmp_path / "real_file.js"
        real_file.write_text("// plugin", encoding="utf-8")

        # Create old symlinks
        old_plugin_link = plugin_dir / "superpowers.js"
        os.symlink(real_file, old_plugin_link)

        old_skills_link = skills_dir / "superpowers"
        os.symlink(real_target, old_skills_link)

        # Create opencode.json so plugin injection works
        opencode_json = opencode_dir / "opencode.json"
        opencode_json.write_text(json.dumps({"plugin": []}, indent=2), encoding="utf-8")

        assert old_plugin_link.is_symlink()
        assert old_skills_link.is_symlink()

        migrate_opencode_superpowers()

        assert not old_plugin_link.is_symlink()
        assert not old_skills_link.is_symlink()

    def test_old_repo_detected_and_removed(self, monkeypatch, tmp_path):
        """Create a fake .git dir in superpowers, verify rmtree removes it."""
        opencode_dir, superpowers_dir, plugin_dir, skills_dir = self._setup_paths(
            monkeypatch, tmp_path
        )

        # Create fake repo with .git directory
        superpowers_dir.mkdir(parents=True, exist_ok=True)
        (superpowers_dir / ".git").mkdir()
        (superpowers_dir / "some_file.txt").write_text("content", encoding="utf-8")

        # Create opencode.json
        opencode_json = opencode_dir / "opencode.json"
        opencode_json.write_text(json.dumps({"plugin": []}, indent=2), encoding="utf-8")

        assert (superpowers_dir / ".git").exists()

        migrate_opencode_superpowers()

        assert not superpowers_dir.exists()

    def test_real_directory_not_deleted(self, monkeypatch, tmp_path):
        """Real (non-symlink) directory at old skills path -> should NOT be deleted."""
        opencode_dir, superpowers_dir, plugin_dir, skills_dir = self._setup_paths(
            monkeypatch, tmp_path
        )

        # Create a real (non-symlink) directory at the old skills path
        old_skills_path = skills_dir / "superpowers"
        old_skills_path.mkdir(parents=True)
        (old_skills_path / "user_file.txt").write_text("important", encoding="utf-8")

        # Also create a real plugin file (not symlink)
        old_plugin_file = plugin_dir / "superpowers.js"
        old_plugin_file.write_text("// real file", encoding="utf-8")

        # Create opencode.json
        opencode_json = opencode_dir / "opencode.json"
        opencode_json.write_text(json.dumps({"plugin": []}, indent=2), encoding="utf-8")

        migrate_opencode_superpowers()

        # Real directories/files should NOT be deleted (safety check)
        assert old_skills_path.exists()
        assert old_plugin_file.exists()
        assert (old_skills_path / "user_file.txt").read_text(encoding="utf-8") == "important"


# ============================================================
# refresh_codex_superpowers_symlinks
# ============================================================


class TestRefreshCodexSuperpowersSymlinks:
    """Tests for refresh_codex_superpowers_symlinks."""

    def test_creates_symlink(self, monkeypatch, tmp_path):
        """Repo with skills/ dir -> symlink created."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / "skills").mkdir()

        agents_skills = tmp_path / "agents_skills"
        monkeypatch.setattr(
            "script.utils.shared.get_agents_skills_dir",
            lambda: agents_skills,
        )

        result = refresh_codex_superpowers_symlinks(repo_path)

        assert result is True
        symlink_path = agents_skills / "superpowers"
        assert symlink_path.is_symlink()
        assert symlink_path.resolve() == (repo_path / "skills").resolve()

    def test_skips_if_no_git(self, monkeypatch, tmp_path):
        """Repo path has no .git -> returns False."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / "skills").mkdir()

        agents_skills = tmp_path / "agents_skills"
        monkeypatch.setattr(
            "script.utils.shared.get_agents_skills_dir",
            lambda: agents_skills,
        )

        result = refresh_codex_superpowers_symlinks(repo_path)

        assert result is False

    def test_skips_if_no_skills_dir(self, monkeypatch, tmp_path):
        """Repo path/.git exists but skills/ doesn't -> returns False."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        agents_skills = tmp_path / "agents_skills"
        monkeypatch.setattr(
            "script.utils.shared.get_agents_skills_dir",
            lambda: agents_skills,
        )

        result = refresh_codex_superpowers_symlinks(repo_path)

        assert result is False

    def test_idempotent_when_correct(self, monkeypatch, tmp_path):
        """Symlink already points to correct target -> returns True without recreating."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / "skills").mkdir()

        agents_skills = tmp_path / "agents_skills"
        agents_skills.mkdir(parents=True)
        monkeypatch.setattr(
            "script.utils.shared.get_agents_skills_dir",
            lambda: agents_skills,
        )

        # Pre-create correct symlink
        symlink_path = agents_skills / "superpowers"
        os.symlink(repo_path / "skills", symlink_path)

        result = refresh_codex_superpowers_symlinks(repo_path)

        assert result is True
        assert symlink_path.is_symlink()
        assert symlink_path.resolve() == (repo_path / "skills").resolve()

    def test_replaces_wrong_symlink(self, monkeypatch, tmp_path):
        """Symlink points to wrong target -> replaced."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / "skills").mkdir()

        wrong_target = tmp_path / "wrong_target"
        wrong_target.mkdir()

        agents_skills = tmp_path / "agents_skills"
        agents_skills.mkdir(parents=True)
        monkeypatch.setattr(
            "script.utils.shared.get_agents_skills_dir",
            lambda: agents_skills,
        )

        # Pre-create wrong symlink
        symlink_path = agents_skills / "superpowers"
        os.symlink(wrong_target, symlink_path)
        assert symlink_path.resolve() == wrong_target.resolve()

        result = refresh_codex_superpowers_symlinks(repo_path)

        assert result is True
        assert symlink_path.is_symlink()
        assert symlink_path.resolve() == (repo_path / "skills").resolve()
