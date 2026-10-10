from pathlib import Path

from typer.testing import CliRunner

from script.main import app


runner = CliRunner()


def test_standards_is_retired_and_does_nothing(monkeypatch, tmp_path: Path):
    disabled = tmp_path / ".claude" / "disabled.yaml"
    disabled.parent.mkdir(parents=True)
    disabled.write_text("_profile: all\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    for args in (
        ["standards"],
        ["standards", "status"],
        ["standards", "switch", "ecc", "--dry-run"],
    ):
        result = runner.invoke(app, args)

        assert result.exit_code == 0, result.output
        assert "已隨 UDS 退役" in result.output

    assert disabled.read_text(encoding="utf-8") == "_profile: all\n"


def test_standards_is_hidden_from_help():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "standards" not in result.output
