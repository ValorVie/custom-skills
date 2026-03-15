from pathlib import Path

from typer.testing import CliRunner

from script.main import app
from script.commands import coverage as coverage_cmd
from script.utils.test_runner import PythonTestRunner, CommandResult


runner = CliRunner()


class DummyPythonRunner(PythonTestRunner):
    def __init__(self) -> None:
        self.calls: list[tuple[str | None, str | None]] = []

    def is_available(self) -> bool:
        return True

    def is_coverage_available(self) -> bool:
        return True

    def run(self, path: str | None = None, verbose: bool = False, fail_fast: bool = False, keyword: str | None = None) -> CommandResult:
        raise AssertionError("run() should not be called in coverage command tests")

    def run_with_coverage(
        self,
        path: str | None = None,
        source: str | None = None,
    ) -> CommandResult:
        self.calls.append((path, source))
        return CommandResult(output="coverage ok", exit_code=0)


def test_coverage_normalizes_file_source_to_parent_dir(monkeypatch, tmp_path: Path):
    source_file = tmp_path / "script" / "commands" / "install.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("print('ok')\n", encoding="utf-8")

    runner_impl = DummyPythonRunner()
    monkeypatch.setattr(coverage_cmd, "detect_test_runner", lambda _project_path: runner_impl)

    result = runner.invoke(app, ["coverage", "--source", str(source_file)])

    assert result.exit_code == 0
    assert runner_impl.calls == [(None, str(source_file.parent))]
    assert "單一檔案路徑" in result.output
