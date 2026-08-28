from typer.testing import CliRunner

from script.main import app
from script.commands import toggle as toggle_cmd


runner = CliRunner()


def test_toggle_requires_target():
    result = runner.invoke(app, ["toggle", "--type", "skills", "--name", "demo", "--disable"])

    assert result.exit_code == 1
    assert "請指定目標工具" in result.stdout


def test_toggle_dry_run_does_not_mutate_state(monkeypatch):
    monkeypatch.setattr(toggle_cmd, "load_toggle_config", lambda: {})
    monkeypatch.setattr(
        toggle_cmd,
        "disable_resource",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not disable")),
    )
    monkeypatch.setattr(
        toggle_cmd,
        "enable_resource",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not enable")),
    )

    result = runner.invoke(
        app,
        [
            "toggle",
            "--target",
            "claude",
            "--type",
            "skills",
            "--name",
            "demo",
            "--disable",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "dry-run" in result.stdout.lower()


def test_codex_skill_toggle_warns_about_shared_agents_directory(monkeypatch):
    monkeypatch.setattr(toggle_cmd, "load_toggle_config", lambda: {})

    result = runner.invoke(
        app,
        [
            "toggle",
            "--target",
            "codex",
            "--type",
            "skills",
            "--name",
            "demo",
            "--disable",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "~/.agents/skills" in result.stdout
    assert "其他工具" in result.stdout


def test_npx_managed_skill_toggle_fails_without_mutation(monkeypatch):
    monkeypatch.setattr(toggle_cmd, "load_toggle_config", lambda: {})
    monkeypatch.setattr(
        toggle_cmd, "get_npx_managed_skill_names", lambda: {"managed"}
    )
    monkeypatch.setattr(
        toggle_cmd,
        "get_npx_managed_skill_entry",
        lambda _name: type("Entry", (), {"repo": "owner/repo"})(),
    )
    monkeypatch.setattr(
        toggle_cmd,
        "disable_resource",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("must not move npx skill")
        ),
    )

    result = runner.invoke(
        app,
        [
            "toggle",
            "--target",
            "claude",
            "--type",
            "skills",
            "--name",
            "managed",
            "--disable",
        ],
    )

    assert result.exit_code == 1
    assert "npx skills remove --global --agent claude-code managed" in result.stdout


def test_npx_managed_skill_without_verified_agent_mapping_fails_closed(monkeypatch):
    monkeypatch.setattr(toggle_cmd, "load_toggle_config", lambda: {})
    monkeypatch.setattr(
        toggle_cmd, "get_npx_managed_skill_names", lambda: {"managed"}
    )
    monkeypatch.setattr(
        toggle_cmd,
        "get_npx_managed_skill_entry",
        lambda _name: type("Entry", (), {"repo": "owner/repo"})(),
    )

    result = runner.invoke(
        app,
        [
            "toggle",
            "--target",
            "antigravity",
            "--type",
            "skills",
            "--name",
            "managed",
            "--enable",
        ],
    )

    assert result.exit_code == 1
    assert "尚未驗證 npx agent mapping" in result.stdout
