from pathlib import Path

from script.utils import paths


def test_auto_skill_paths_use_ai_dev_namespace(monkeypatch):
    fake_home = Path("/tmp/fake-home")
    monkeypatch.setattr(paths, "get_home_dir", lambda: fake_home)

    assert paths.get_auto_skill_dir() == fake_home / ".config" / "ai-dev" / "skills" / "auto-skill"
    assert paths.get_auto_skill_repo_dir() == fake_home / ".config" / "auto-skill"
    assert paths.get_auto_skill_projection_root() == fake_home / ".config" / "ai-dev" / "projections"
    assert (
        paths.get_auto_skill_shadow_dir("claude")
        == fake_home / ".config" / "ai-dev" / "projections" / "claude" / "auto-skill"
    )
    assert (
        paths.get_auto_skill_shadow_state_path("claude")
        == fake_home / ".config" / "ai-dev" / "projections" / "claude" / "auto-skill.state.json"
    )
    assert (
        paths.get_auto_skill_backup_dir("claude")
        == fake_home / ".config" / "ai-dev" / "backups" / "auto-skill" / "claude"
    )


def test_codex_skills_use_shared_agents_directory(monkeypatch):
    from script.utils import shared

    fake_home = Path("/tmp/fake-home")
    monkeypatch.setattr(paths, "get_home_dir", lambda: fake_home)
    monkeypatch.setattr(shared, "get_agents_skills_dir", lambda: fake_home / ".agents" / "skills")

    assert paths.get_agents_skills_dir() == fake_home / ".agents" / "skills"
    assert shared.get_target_path("codex", "skills") == fake_home / ".agents" / "skills"
    assert shared.COPY_TARGETS["codex"]["skills"] == Path.home() / ".agents" / "skills"


def test_install_directory_setup_creates_agents_skills_not_legacy_codex(tmp_path, monkeypatch):
    from script.services.repos.refresh import _ensure_install_directories

    monkeypatch.setattr(paths, "get_home_dir", lambda: tmp_path)

    _ensure_install_directories()

    assert (tmp_path / ".agents" / "skills").is_dir()
    assert not (tmp_path / ".codex" / "skills").exists()
