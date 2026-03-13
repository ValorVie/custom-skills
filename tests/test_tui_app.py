from types import SimpleNamespace

from script.tui.app import SkillManagerApp


def test_install_button_no_longer_passes_sync_project_args(monkeypatch):
    app = SkillManagerApp()
    calls = []

    def fake_run_cli_command(command: str, extra_args=None):
        calls.append((command, extra_args))

    monkeypatch.setattr(app, "run_cli_command", fake_run_cli_command)

    app.on_button_pressed(SimpleNamespace(button=SimpleNamespace(id="btn-install")))

    assert calls == [("install", None)]


def test_clone_button_no_longer_passes_sync_project_args(monkeypatch):
    app = SkillManagerApp()
    calls = []

    def fake_run_cli_command(command: str, extra_args=None):
        calls.append((command, extra_args))

    monkeypatch.setattr(app, "run_cli_command", fake_run_cli_command)

    app.on_button_pressed(SimpleNamespace(button=SimpleNamespace(id="btn-clone")))

    assert calls == [("clone", None)]
