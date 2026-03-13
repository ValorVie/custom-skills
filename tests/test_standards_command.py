from pathlib import Path

from typer.testing import CliRunner

from script.main import app
from script.commands import standards as standards_cmd


runner = CliRunner()


def test_standards_switch_does_not_sync_target_by_default(monkeypatch, tmp_path: Path):
    sync_calls = []

    monkeypatch.setattr(standards_cmd, "load_overlaps", lambda: {"groups": {}, "exclusive": {}, "shared": {}})
    monkeypatch.setattr(standards_cmd, "load_profile", lambda _name: {"display_name": "UDS"})
    monkeypatch.setattr(standards_cmd, "load_disabled_yaml", lambda: {})
    monkeypatch.setattr(standards_cmd, "compute_disabled_items", lambda *_args, **_kwargs: set())
    monkeypatch.setattr(standards_cmd, "save_disabled_yaml", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(standards_cmd, "get_items_by_type", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(standards_cmd, "get_active_profile_path", lambda: tmp_path / "active-profile.yaml")
    monkeypatch.setattr(standards_cmd, "load_yaml", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(standards_cmd, "save_yaml", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        standards_cmd,
        "sync_resources",
        lambda *_args, **_kwargs: sync_calls.append(True) or {"success": True},
    )

    result = standards_cmd.switch_profile("uds")

    assert result["success"] is True
    assert sync_calls == []


def test_standards_sync_requires_target(monkeypatch):
    monkeypatch.setattr(standards_cmd, "load_disabled_yaml", lambda: {"_profile": "uds"})

    result = runner.invoke(app, ["standards", "sync"])

    assert result.exit_code == 1
    assert "請指定目標工具" in result.output


def test_standards_sync_invalid_target_then_exit_1(monkeypatch):
    monkeypatch.setattr(standards_cmd, "load_disabled_yaml", lambda: {"_profile": "uds"})

    result = runner.invoke(app, ["standards", "sync", "--target", "bad"])

    assert result.exit_code == 1
    assert "無效的目標工具" in result.output
