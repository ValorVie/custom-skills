from typer.testing import CliRunner

from script.main import app
from script.commands import list as list_cmd


runner = CliRunner()


def test_list_invalid_target_then_exit_1():
    result = runner.invoke(app, ["list", "--target", "bad-target"])

    assert result.exit_code == 1
    assert "無效的目標" in result.stdout


def test_list_invalid_type_then_exit_1():
    result = runner.invoke(app, ["list", "--type", "bad-type"])

    assert result.exit_code == 1
    assert "無效的類型" in result.stdout


def test_list_no_items_prints_notice(monkeypatch):
    monkeypatch.setattr(
        list_cmd,
        "list_installed_resources",
        lambda *_args, **_kwargs: {"claude": {"skills": []}},
    )

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "無符合結果" in result.stdout


def test_list_target_type_filters_and_hide_disabled(monkeypatch):
    monkeypatch.setattr(
        list_cmd,
        "list_installed_resources",
        lambda *_args, **_kwargs: {
            "claude": {
                "skills": [
                    {"name": "active-skill", "source": "custom", "disabled": False},
                    {"name": "disabled-skill", "source": "custom", "disabled": True},
                ]
            }
        },
    )

    result = runner.invoke(
        app,
        ["list", "--target", "claude", "--type", "skills", "--hide-disabled"],
    )

    assert result.exit_code == 0
    assert "active-skill" in result.stdout
    assert "disabled-skill" not in result.stdout
