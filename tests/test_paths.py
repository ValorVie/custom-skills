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
