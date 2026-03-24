from pathlib import Path

from script.utils import paths


def test_codex_superpowers_dir(monkeypatch):
    fake_home = Path("/tmp/fake-home")
    monkeypatch.setattr(paths, "get_home_dir", lambda: fake_home)
    assert paths.get_codex_superpowers_dir() == fake_home / ".codex" / "superpowers"


def test_agents_skills_dir(monkeypatch):
    fake_home = Path("/tmp/fake-home")
    monkeypatch.setattr(paths, "get_home_dir", lambda: fake_home)
    assert paths.get_agents_skills_dir() == fake_home / ".agents" / "skills"
