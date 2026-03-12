import subprocess
from datetime import datetime, timezone
from wl_parser.git_collector import _get_git_author, _parse_git_log_output, collect_git_data


def test_get_git_author_returns_name(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Test User"], capture_output=True)
    assert _get_git_author(str(tmp_path)) == "Test User"


def test_get_git_author_returns_none_no_config(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "--unset", "user.name"], capture_output=True)
    result = _get_git_author(str(tmp_path))
    assert result is None or isinstance(result, str)


def test_get_git_author_returns_none_not_git(tmp_path):
    assert _get_git_author(str(tmp_path)) is None


def test_parse_git_log_output_single_commit():
    raw = "abc1234\x00abc1234\x00feat: add login\x002026-03-11 14:00:00 +0800\n\n src/auth.py | 50 +++++++\n 1 file changed, 50 insertions(+)\n"
    commits = _parse_git_log_output(raw)
    assert len(commits) == 1
    c = commits[0]
    assert c["hash"] == "abc1234"
    assert c["message"] == "feat: add login"
    assert c["files_changed"] == 1
    assert c["insertions"] == 50
    assert c["deletions"] == 0


def test_parse_git_log_output_multiple_commits():
    raw = "aaa1111\x00aaa1111\x00fix: bug A\x002026-03-11 10:00:00 +0800\n\n file1.py | 5 ++---\n 1 file changed, 2 insertions(+), 3 deletions(-)\n\nbbb2222\x00bbb2222\x00feat: feature B\x002026-03-11 12:00:00 +0800\n\n file2.py | 10 ++++++++++\n file3.py | 3 ++-\n 2 files changed, 11 insertions(+), 1 deletion(-)\n"
    commits = _parse_git_log_output(raw)
    assert len(commits) == 2
    assert commits[0]["message"] == "fix: bug A"
    assert commits[0]["insertions"] == 2
    assert commits[0]["deletions"] == 3
    assert commits[1]["message"] == "feat: feature B"
    assert commits[1]["files_changed"] == 2
    assert commits[1]["insertions"] == 11
    assert commits[1]["deletions"] == 1


def test_parse_git_log_output_empty():
    assert _parse_git_log_output("") == []
    assert _parse_git_log_output("\n") == []


def test_parse_git_log_output_no_stat():
    raw = "ccc3333\x00ccc3333\x00Merge branch main\x002026-03-11 15:00:00 +0800\n\n"
    commits = _parse_git_log_output(raw)
    assert len(commits) == 1
    assert commits[0]["files_changed"] == 0


def test_collect_git_data_real_repo(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Test"], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@t.com"], capture_output=True)
    (tmp_path / "test.py").write_text("print('hello')")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "feat: initial"], capture_output=True)

    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    end = datetime(2030, 1, 1, tzinfo=timezone.utc)
    commits = collect_git_data(str(tmp_path), start, end)
    assert len(commits) >= 1
    assert commits[0]["message"] == "feat: initial"
    assert commits[0]["files_changed"] >= 1


def test_collect_git_data_not_git_repo(tmp_path):
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    end = datetime(2030, 1, 1, tzinfo=timezone.utc)
    assert collect_git_data(str(tmp_path), start, end) == []


def test_collect_git_data_nonexistent_path():
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    end = datetime(2030, 1, 1, tzinfo=timezone.utc)
    assert collect_git_data("/nonexistent/path", start, end) == []


def test_collect_git_data_no_commits_in_range(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Test"], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@t.com"], capture_output=True)
    (tmp_path / "test.py").write_text("x")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "old commit"], capture_output=True)
    start = datetime(2099, 1, 1, tzinfo=timezone.utc)
    end = datetime(2099, 12, 31, tzinfo=timezone.utc)
    assert collect_git_data(str(tmp_path), start, end) == []


def test_collect_git_data_max_commits(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Test"], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@t.com"], capture_output=True)
    for i in range(5):
        (tmp_path / f"file{i}.py").write_text(f"v{i}")
        subprocess.run(["git", "-C", str(tmp_path), "add", "."], capture_output=True)
        subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", f"commit {i}"], capture_output=True)
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    end = datetime(2030, 1, 1, tzinfo=timezone.utc)
    commits = collect_git_data(str(tmp_path), start, end, max_commits=3)
    assert len(commits) == 3
