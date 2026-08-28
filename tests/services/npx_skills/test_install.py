from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
import typer

from script.services.npx_skills import install as install_mod
from script.services.npx_skills import manifest_sync
from script.services.npx_skills.config import (
    NpxDefaults,
    SkillEntry,
)
from script.services.npx_skills.first_party_reconcile import SourceSnapshot
from script.services.npx_skills.install import (
    build_add_command,
    build_update_command,
    group_entries_by_repo,
    run_npx_skills_phase,
)
from script.services.npx_skills.migration import (
    MigrationRecord,
    MigrationState,
    VerificationResult,
)


def _mock_first_party_runtime(
    monkeypatch,
    tmp_path: Path,
    skill_names: tuple[str, ...],
) -> Path:
    source_skills = tmp_path / "source" / "skills"
    for name in skill_names:
        skill = source_skills / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\n---\n",
            encoding="utf-8",
        )

    @contextmanager
    def fake_checkout(_repo):
        yield SourceSnapshot(source_skills, "source-commit")

    monkeypatch.setattr(install_mod, "checkout_first_party_source", fake_checkout)
    monkeypatch.setattr(
        install_mod,
        "get_first_party_local_roots",
        lambda _agents: {"canonical": tmp_path / "installed"},
    )
    monkeypatch.setattr(install_mod, "read_npx_lock", lambda: {"skills": {}})
    monkeypatch.setattr(
        manifest_sync,
        "cleanup_skills_from_manifests",
        lambda _names: {},
    )
    monkeypatch.setattr(
        install_mod,
        "verify_first_party_paths",
        lambda entries, **_kwargs: VerificationResult(
            tuple(entry.skill for entry in entries), ()
        ),
    )
    return tmp_path / "guard.yaml"


def test_build_add_command_includes_global_and_agents():
    entries = (
        SkillEntry(repo="anthropics/skills", skill="claude-api", source="anthropic"),
        SkillEntry(repo="anthropics/skills", skill="skill-creator", source="anthropic"),
    )
    defaults = NpxDefaults(agents=("*",), scope="global", yes=True)

    cmd = build_add_command(entries, defaults)

    assert cmd == [
        "npx", "skills", "add",
        "anthropics/skills",
        "--skill", "claude-api",
        "--skill", "skill-creator",
        "-g", "-a", "*", "--yes",
    ]


def test_build_add_command_expands_explicit_agents_without_project_only_targets():
    entries = (SkillEntry(repo="x/y", skill="z", source="x"),)
    defaults = NpxDefaults(
        agents=(
            "claude-code",
            "codex",
            "gemini-cli",
            "opencode",
            "antigravity",
        ),
        scope="global",
        yes=True,
    )

    cmd = build_add_command(entries, defaults)

    assert cmd == [
        "npx",
        "skills",
        "add",
        "x/y",
        "--skill",
        "z",
        "-g",
        "-a",
        "claude-code",
        "codex",
        "gemini-cli",
        "opencode",
        "antigravity",
        "--yes",
    ]
    assert "eve" not in cmd
    assert "promptscript" not in cmd


def test_build_add_command_project_scope_omits_global():
    entries = (SkillEntry(repo="x/y", skill="z", source="x"),)
    defaults = NpxDefaults(agents=("claude",), scope="project", yes=False)

    cmd = build_add_command(entries, defaults)

    assert "-g" not in cmd
    assert "--yes" not in cmd
    assert cmd == [
        "npx", "skills", "add",
        "x/y", "--skill", "z",
        "-a", "claude",
    ]


def test_build_update_command_global_scope_includes_g():
    entries = (
        SkillEntry(repo="anthropics/skills", skill="claude-api", source="anthropic"),
        SkillEntry(repo="anthropics/skills", skill="skill-creator", source="anthropic"),
    )
    defaults = NpxDefaults()  # default scope=global, yes=True

    cmd = build_update_command(entries, defaults)

    assert cmd == [
        "npx", "skills", "update", "claude-api", "skill-creator", "-g", "-y"
    ]


def test_build_update_command_project_scope_omits_g():
    entries = (SkillEntry(repo="x/y", skill="z", source="x"),)
    defaults = NpxDefaults(agents=("claude",), scope="project", yes=False)

    cmd = build_update_command(entries, defaults)

    assert "-g" not in cmd
    assert "-y" not in cmd
    assert cmd == ["npx", "skills", "update", "z"]


def test_group_entries_by_repo_preserves_manifest_order():
    entries = (
        SkillEntry(repo="a/repo", skill="one", source="a"),
        SkillEntry(repo="b/repo", skill="two", source="b"),
        SkillEntry(repo="a/repo", skill="three", source="a"),
    )

    groups = group_entries_by_repo(entries)

    assert [[entry.skill for entry in group] for group in groups] == [
        ["one", "three"],
        ["two"],
    ]


def test_build_command_rejects_mixed_repositories():
    entries = (
        SkillEntry(repo="a/repo", skill="one", source="a"),
        SkillEntry(repo="b/repo", skill="two", source="b"),
    )

    with pytest.raises(ValueError, match="同一個 repository"):
        build_add_command(entries, NpxDefaults())


def test_phase_skips_when_project_yaml_missing(tmp_path: Path, monkeypatch):
    """過時 clone 缺少 project yaml 時，應警告並跳過，不得拋例外中斷 install。"""
    monkeypatch.setattr(install_mod, "check_command_exists", lambda _: True)
    missing = tmp_path / "custom-skills" / "upstream" / "npx-skills.yaml"
    user = tmp_path / "ai-dev" / "npx-skills.yaml"

    run_npx_skills_phase(mode="add", project_yaml=missing, user_yaml=user)

    # 未建立 user yaml、未拋例外即代表已優雅跳過
    assert not user.exists()


def test_add_phase_cleans_only_successful_packages_and_exits_nonzero(
    tmp_path: Path, monkeypatch
):
    project = tmp_path / "npx-skills.yaml"
    project.write_text(
        """version: 1
defaults:
  agents: "*"
  scope: global
  yes: true
packages:
  - repo: ok/repo
    skills: [one, two]
  - repo: bad/repo
    skills: [three]
""",
        encoding="utf-8",
    )
    user = tmp_path / "user" / "npx-skills.yaml"
    commands: list[list[str]] = []
    cleaned: list[str] = []

    monkeypatch.setattr(install_mod, "check_command_exists", lambda _: True)

    def fake_run(cmd, **_):
        commands.append(cmd)
        return SimpleNamespace(returncode=0 if "ok/repo" in cmd else 9)

    monkeypatch.setattr(install_mod, "run_command", fake_run)
    monkeypatch.setattr(
        manifest_sync,
        "cleanup_skills_from_manifests",
        lambda names: cleaned.extend(names) or {},
    )

    with pytest.raises(typer.Exit) as error:
        run_npx_skills_phase(
            mode="add", project_yaml=project, user_yaml=user, dry_run=False
        )

    assert error.value.exit_code == 1
    assert len(commands) == 2
    assert cleaned == ["one", "two"]


def test_dry_run_does_not_execute_or_cleanup(tmp_path: Path, monkeypatch):
    project = tmp_path / "npx-skills.yaml"
    project.write_text(
        """version: 1
packages:
  - repo: a/repo
    skills: [one, two]
""",
        encoding="utf-8",
    )
    user = tmp_path / "user" / "npx-skills.yaml"

    monkeypatch.setattr(install_mod, "check_command_exists", lambda _: True)
    monkeypatch.setattr(
        install_mod,
        "run_command",
        lambda *_args, **_kwargs: pytest.fail("dry-run executed npx"),
    )
    monkeypatch.setattr(
        manifest_sync,
        "cleanup_skills_from_manifests",
        lambda _names: pytest.fail("dry-run cleaned manifests"),
    )

    run_npx_skills_phase(
        mode="add", project_yaml=project, user_yaml=user, dry_run=True
    )
    assert not user.exists()


def test_first_party_add_requires_safe_preflight_and_verified_readback(
    tmp_path: Path, monkeypatch
):
    project = tmp_path / "npx-skills.yaml"
    project.write_text(
        """version: 1
packages:
  - repo: ValorVie/ai-dev-skills
    source: ai-dev-first-party
    skills: [simplify]
""",
        encoding="utf-8",
    )
    user = tmp_path / "user" / "npx-skills.yaml"
    cleaned: list[str] = []

    monkeypatch.setattr(install_mod, "check_command_exists", lambda _: True)
    monkeypatch.setattr(
        install_mod,
        "run_command",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(install_mod, "_preview_first_party_group", lambda _group: ())
    guard_path = _mock_first_party_runtime(
        monkeypatch, tmp_path, ("simplify",)
    )
    monkeypatch.setattr(
        install_mod,
        "backup_and_remove_legacy_paths",
        lambda _records, verified_names: (),
    )
    monkeypatch.setattr(
        manifest_sync,
        "cleanup_skills_from_manifests",
        lambda names: cleaned.extend(sorted(names)) or {},
    )

    run_npx_skills_phase(
        mode="add",
        project_yaml=project,
        user_yaml=user,
        dry_run=False,
        first_party_guard_path=guard_path,
    )

    assert cleaned == ["custom-simplify", "simplify"]
    assert guard_path.exists()


def test_first_party_add_stops_before_npx_when_preflight_is_unsafe(
    tmp_path: Path, monkeypatch
):
    project = tmp_path / "npx-skills.yaml"
    project.write_text(
        """version: 1
packages:
  - repo: ValorVie/ai-dev-skills
    source: ai-dev-first-party
    skills: [simplify]
""",
        encoding="utf-8",
    )
    user = tmp_path / "user" / "npx-skills.yaml"
    record = MigrationRecord(
        target="codex",
        canonical_id="simplify",
        legacy_name="custom-simplify",
        path=tmp_path / "custom-simplify",
        state=MigrationState.MODIFIED,
        changed_files=("SKILL.md",),
    )

    monkeypatch.setattr(install_mod, "check_command_exists", lambda _: True)
    monkeypatch.setattr(
        install_mod,
        "_preview_first_party_group",
        lambda _group: (record,),
    )
    monkeypatch.setattr(
        install_mod,
        "run_command",
        lambda *_args, **_kwargs: pytest.fail("unsafe preflight executed npx"),
    )
    guard_path = _mock_first_party_runtime(
        monkeypatch, tmp_path, ("simplify",)
    )

    with pytest.raises(typer.Exit) as error:
        run_npx_skills_phase(
            mode="add",
            project_yaml=project,
            user_yaml=user,
            dry_run=False,
            first_party_guard_path=guard_path,
        )

    assert error.value.exit_code == 1


def test_first_party_add_installs_safe_skills_and_preserves_unsafe_skill(
    tmp_path: Path, monkeypatch
):
    project = tmp_path / "npx-skills.yaml"
    project.write_text(
        """version: 1
packages:
  - repo: ValorVie/ai-dev-skills
    source: ai-dev-first-party
    skills: [safe, blocked]
""",
        encoding="utf-8",
    )
    user = tmp_path / "user" / "npx-skills.yaml"
    blocked = MigrationRecord(
        target="codex",
        canonical_id="blocked",
        legacy_name="blocked",
        path=tmp_path / "blocked",
        state=MigrationState.MODIFIED,
    )
    commands: list[list[str]] = []
    cleaned: list[str] = []

    monkeypatch.setattr(install_mod, "check_command_exists", lambda _: True)
    monkeypatch.setattr(
        install_mod, "_preview_first_party_group", lambda _group: (blocked,)
    )

    def fake_run(cmd, **_kwargs):
        commands.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(install_mod, "run_command", fake_run)
    guard_path = _mock_first_party_runtime(
        monkeypatch, tmp_path, ("safe", "blocked")
    )
    monkeypatch.setattr(
        install_mod,
        "backup_and_remove_legacy_paths",
        lambda _records, verified_names: (),
    )
    monkeypatch.setattr(
        manifest_sync,
        "cleanup_skills_from_manifests",
        lambda names: cleaned.extend(sorted(names)) or {},
    )

    with pytest.raises(typer.Exit) as error:
        run_npx_skills_phase(
            mode="add",
            project_yaml=project,
            user_yaml=user,
            dry_run=False,
            first_party_guard_path=guard_path,
        )

    assert error.value.exit_code == 1
    assert commands == [
        [
            "npx",
            "skills",
            "add",
            "ValorVie/ai-dev-skills",
            "--skill",
            "safe",
            "-g",
            "-a",
            "claude-code",
            "codex",
            "gemini-cli",
            "opencode",
            "antigravity",
            "--yes",
        ]
    ]
    assert cleaned == ["safe"]


def test_first_party_update_uses_guarded_add_for_missing_skill(
    tmp_path: Path, monkeypatch
):
    project = tmp_path / "npx-skills.yaml"
    project.write_text(
        """version: 1
packages:
  - repo: ValorVie/ai-dev-skills
    source: ai-dev-first-party
    skills: [new-skill]
""",
        encoding="utf-8",
    )
    user = tmp_path / "user" / "npx-skills.yaml"
    commands: list[list[str]] = []
    cleaned: list[str] = []
    monkeypatch.setattr(install_mod, "check_command_exists", lambda _: True)
    monkeypatch.setattr(install_mod, "_preview_first_party_group", lambda _group: ())
    guard_path = _mock_first_party_runtime(
        monkeypatch, tmp_path, ("new-skill",)
    )
    monkeypatch.setattr(
        manifest_sync,
        "cleanup_skills_from_manifests",
        lambda names: cleaned.extend(names) or {},
    )

    def fake_run(cmd, **_kwargs):
        commands.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(install_mod, "run_command", fake_run)

    run_npx_skills_phase(
        mode="update",
        project_yaml=project,
        user_yaml=user,
        first_party_guard_path=guard_path,
    )

    assert commands[0][:4] == [
        "npx",
        "skills",
        "add",
        "ValorVie/ai-dev-skills",
    ]
    assert "update" not in commands[0]
    assert cleaned == ["new-skill"]


def test_third_party_update_remains_native_passthrough(tmp_path: Path, monkeypatch):
    project = tmp_path / "npx-skills.yaml"
    project.write_text(
        """version: 1
packages:
  - repo: example/skills
    source: third-party
    skills: [one]
""",
        encoding="utf-8",
    )
    user = tmp_path / "user" / "npx-skills.yaml"
    commands: list[list[str]] = []
    monkeypatch.setattr(install_mod, "check_command_exists", lambda _: True)
    monkeypatch.setattr(
        install_mod,
        "checkout_first_party_source",
        lambda _repo: pytest.fail("third-party update entered first-party guard"),
    )

    def fake_run(cmd, **_kwargs):
        commands.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(install_mod, "run_command", fake_run)

    run_npx_skills_phase(mode="update", project_yaml=project, user_yaml=user)

    assert commands == [["npx", "skills", "update", "one", "-g", "-y"]]


def test_first_party_verification_failure_keeps_guard_and_manifest(
    tmp_path: Path, monkeypatch
):
    project = tmp_path / "npx-skills.yaml"
    project.write_text(
        """version: 1
packages:
  - repo: ValorVie/ai-dev-skills
    source: ai-dev-first-party
    skills: [one]
""",
        encoding="utf-8",
    )
    user = tmp_path / "user" / "npx-skills.yaml"
    cleaned: list[str] = []
    monkeypatch.setattr(install_mod, "check_command_exists", lambda _: True)
    monkeypatch.setattr(install_mod, "_preview_first_party_group", lambda _group: ())
    guard_path = _mock_first_party_runtime(monkeypatch, tmp_path, ("one",))
    monkeypatch.setattr(
        install_mod,
        "run_command",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(
        install_mod,
        "verify_first_party_paths",
        lambda *_args, **_kwargs: VerificationResult((), ("one: codex hash mismatch",)),
    )
    monkeypatch.setattr(
        manifest_sync,
        "cleanup_skills_from_manifests",
        lambda names: cleaned.extend(names) or {},
    )

    with pytest.raises(typer.Exit) as error:
        run_npx_skills_phase(
            mode="update",
            project_yaml=project,
            user_yaml=user,
            first_party_guard_path=guard_path,
        )

    assert error.value.exit_code == 1
    assert not guard_path.exists()
    assert cleaned == []


def test_first_party_dry_run_does_not_write_or_execute(tmp_path: Path, monkeypatch):
    project = tmp_path / "npx-skills.yaml"
    project.write_text(
        """version: 1
packages:
  - repo: ValorVie/ai-dev-skills
    source: ai-dev-first-party
    skills: [one]
""",
        encoding="utf-8",
    )
    user = tmp_path / "user" / "npx-skills.yaml"
    monkeypatch.setattr(install_mod, "check_command_exists", lambda _: True)
    monkeypatch.setattr(install_mod, "_preview_first_party_group", lambda _group: ())
    guard_path = _mock_first_party_runtime(monkeypatch, tmp_path, ("one",))
    monkeypatch.setattr(
        install_mod,
        "run_command",
        lambda *_args, **_kwargs: pytest.fail("dry-run executed npx"),
    )

    run_npx_skills_phase(
        mode="update",
        project_yaml=project,
        user_yaml=user,
        dry_run=True,
        first_party_guard_path=guard_path,
    )

    assert not guard_path.exists()
    assert not user.exists()
