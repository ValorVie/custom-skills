"""Tests for the tools-phase update helpers."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from script.services.tools.update import (
    _NPX_PROJECT_AGENTS,
    _update_project_npx_skills_from_lock,
)


def _write_lock(project_dir: Path, payload: dict) -> Path:
    lock = project_dir / "skills-lock.json"
    lock.write_text(json.dumps(payload), encoding="utf-8")
    return lock


def test_no_lock_file_is_silent_noop(tmp_path):
    with patch("script.services.tools.update.run_command") as run:
        _update_project_npx_skills_from_lock(tmp_path)
    run.assert_not_called()


def test_empty_skills_section_is_noop(tmp_path):
    _write_lock(tmp_path, {"version": 1, "skills": {}})
    with patch("script.services.tools.update.run_command") as run:
        _update_project_npx_skills_from_lock(tmp_path)
    run.assert_not_called()


def test_each_eligible_skill_invokes_add_with_skill_filter(tmp_path):
    _write_lock(
        tmp_path,
        {
            "version": 1,
            "skills": {
                "javascript-testing-patterns": {
                    "source": "wshobson/agents",
                    "sourceType": "github",
                    "computedHash": "abc",
                },
                "hook-development": {
                    "source": "anthropics/claude-plugins-official",
                    "sourceType": "github",
                    "computedHash": "def",
                },
            },
        },
    )

    with patch("script.services.tools.update.run_command") as run:
        _update_project_npx_skills_from_lock(tmp_path)

    assert run.call_count == 2
    issued = [call.args[0] for call in run.call_args_list]
    assert [
        "npx",
        "skills",
        "add",
        "wshobson/agents",
        "--skill",
        "javascript-testing-patterns",
        "-a",
        *_NPX_PROJECT_AGENTS,
        "-y",
    ] in issued
    assert [
        "npx",
        "skills",
        "add",
        "anthropics/claude-plugins-official",
        "--skill",
        "hook-development",
        "-a",
        *_NPX_PROJECT_AGENTS,
        "-y",
    ] in issued
    for call in run.call_args_list:
        assert call.kwargs.get("check") is False


def test_ref_is_appended_with_fragment(tmp_path):
    _write_lock(
        tmp_path,
        {
            "version": 1,
            "skills": {
                "pinned-skill": {
                    "source": "owner/repo",
                    "sourceType": "github",
                    "ref": "v1.2.3",
                },
            },
        },
    )

    with patch("script.services.tools.update.run_command") as run:
        _update_project_npx_skills_from_lock(tmp_path)

    run.assert_called_once()
    cmd = run.call_args.args[0]
    assert cmd[3] == "owner/repo#v1.2.3"
    expected_tail = ["--skill", "pinned-skill", "-a", *_NPX_PROJECT_AGENTS, "-y"]
    assert cmd[4:] == expected_tail


def test_local_and_node_modules_sources_skipped(tmp_path):
    _write_lock(
        tmp_path,
        {
            "version": 1,
            "skills": {
                "from-node-modules": {
                    "source": "x/y",
                    "sourceType": "node_modules",
                },
                "from-local": {
                    "source": "/abs/path",
                    "sourceType": "local",
                },
                "missing-source": {
                    "sourceType": "github",
                },
                "ok": {
                    "source": "good/repo",
                    "sourceType": "github",
                },
            },
        },
    )

    with patch("script.services.tools.update.run_command") as run:
        _update_project_npx_skills_from_lock(tmp_path)

    run.assert_called_once()
    cmd = run.call_args.args[0]
    assert cmd[3] == "good/repo"
    assert cmd[5] == "ok"
    assert cmd[6:] == ["-a", *_NPX_PROJECT_AGENTS, "-y"]


def test_malformed_json_is_warned_not_raised(tmp_path, capsys):
    (tmp_path / "skills-lock.json").write_text("{not json", encoding="utf-8")

    with patch("script.services.tools.update.run_command") as run:
        _update_project_npx_skills_from_lock(tmp_path)

    run.assert_not_called()
