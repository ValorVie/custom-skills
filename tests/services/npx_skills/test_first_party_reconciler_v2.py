import shutil
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

from script.services.npx_skills.config import NpxDefaults, SkillEntry
from script.services.npx_skills.first_party_overlay import (
    FileState,
    FirstPartyState,
    FirstPartyStateStore,
    SkillState,
    TreeFile,
)
from script.services.npx_skills.first_party_reconcile import (
    FirstPartyReconciler,
    SourceSnapshot,
)
from script.services.npx_skills.migration import MigrationRecord, MigrationState
from script.utils.manifest import compute_dir_hash

REPO = "ValorVie/ai-dev-skills"


def _write_skill(root: Path, content: bytes) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "SKILL.md").write_bytes(content)


def _runtime(
    tmp_path: Path,
    *,
    base: bytes,
    source: bytes,
    local: bytes | None,
    interactive: bool = False,
    answers: tuple[str, ...] = (),
    runner_status: int = 0,
    runner_writes_source: bool = True,
):
    source_root = tmp_path / "source" / "skills" / "demo"
    _write_skill(source_root, source)
    installed = tmp_path / "home" / ".agents" / "skills" / "demo"
    if local is not None:
        _write_skill(installed, local)
    state_store = FirstPartyStateStore(
        tmp_path / "config" / "manifests" / "npx-first-party.yaml",
        tmp_path / "config" / "overlays" / "npx-first-party",
    )
    base_file = TreeFile.from_content(base)
    source_file = TreeFile.from_content(source)
    state_store.write(
        FirstPartyState(
            skills={
                "demo": SkillState(
                    source=REPO,
                    source_commit="base-commit",
                    files={
                        "SKILL.md": FileState(
                            src_hash=base_file.hash,
                            src_commit="base-commit",
                            src_source=REPO,
                            dst_hash_at_sync=base_file.hash,
                            decision="accepted",
                            decided_at="before",
                        )
                    },
                )
            }
        )
    )

    @contextmanager
    def checkout(_repo: str):
        yield SourceSnapshot(source_root.parent, "source-commit")

    commands: list[list[str]] = []

    def runner(command, **_kwargs):
        commands.append(command)
        if runner_status == 0 and runner_writes_source:
            shutil.rmtree(installed, ignore_errors=True)
            shutil.copytree(source_root, installed)
        return SimpleNamespace(returncode=runner_status)

    answer_iter = iter(answers)
    reconciler = FirstPartyReconciler(
        state_store=state_store,
        local_roots={"canonical": installed.parent},
        backup_root=tmp_path / "config" / "backups",
        transaction_root=tmp_path / "config" / "transactions",
        source_checkout=checkout,
        base_provider=lambda _snapshot, commit, _skill: (
            {"SKILL.md": base_file}
            if commit == "base-commit"
            else {"SKILL.md": source_file} if commit == "source-commit" else None
        ),
        command_runner=runner,
        lock_reader=lambda: {"skills": {"demo": {"source": REPO}}},
        interactive=interactive,
        input_func=lambda _prompt: next(answer_iter),
        output_func=lambda _line: None,
    )
    return reconciler, state_store, installed, commands


def _run(reconciler: FirstPartyReconciler):
    return reconciler.reconcile(
        (SkillEntry(REPO, "demo", "ai-dev-first-party"),),
        NpxDefaults(agents=("codex",), scope="global", yes=True),
    )


def test_local_only_is_saved_and_rematerialized_as_overlay(tmp_path: Path):
    reconciler, state_store, installed, commands = _runtime(
        tmp_path, base=b"base\n", source=b"base\n", local=b"local\n"
    )

    result = _run(reconciler)

    assert result.successful_names == ("demo",)
    assert result.failed_names == ()
    assert (installed / "SKILL.md").read_bytes() == b"local\n"
    file_state = state_store.read().skills["demo"].files["SKILL.md"]
    assert file_state.decision == "keep-local"
    assert file_state.overlay is not None
    assert state_store.read_overlay(file_state.overlay) == b"local\n"
    assert len(commands) == 1


def test_noninteractive_both_changed_skips_without_mutation(tmp_path: Path):
    reconciler, state_store, installed, commands = _runtime(
        tmp_path, base=b"base\n", source=b"source\n", local=b"local\n"
    )
    before = state_store.manifest_path.read_bytes()

    result = _run(reconciler)

    assert result.successful_names == ()
    assert result.failed_names == ("demo",)
    assert commands == []
    assert (installed / "SKILL.md").read_bytes() == b"local\n"
    assert state_store.manifest_path.read_bytes() == before


def test_interactive_keep_local_uses_current_source_as_new_base(tmp_path: Path):
    reconciler, state_store, installed, _commands = _runtime(
        tmp_path,
        base=b"base\n",
        source=b"source\n",
        local=b"local\n",
        interactive=True,
        answers=("K",),
    )

    result = _run(reconciler)

    assert result.successful_names == ("demo",)
    assert (installed / "SKILL.md").read_bytes() == b"local\n"
    state = state_store.read().skills["demo"]
    assert state.source_commit == "source-commit"
    assert state.files["SKILL.md"].src_hash == TreeFile.from_content(b"source\n").hash


def test_interactive_use_upstream_removes_overlay_and_retains_backup(tmp_path: Path):
    reconciler, state_store, installed, _commands = _runtime(
        tmp_path,
        base=b"base\n",
        source=b"source\n",
        local=b"local\n",
        interactive=True,
        answers=("O",),
    )

    result = _run(reconciler)

    assert (installed / "SKILL.md").read_bytes() == b"source\n"
    assert state_store.read().skills["demo"].files["SKILL.md"].overlay is None
    assert result.backup_paths
    assert result.backup_paths[0].is_dir()


def test_npx_failure_rolls_back_installed_content_and_state(tmp_path: Path):
    reconciler, state_store, installed, _commands = _runtime(
        tmp_path,
        base=b"base\n",
        source=b"source\n",
        local=b"base\n",
        runner_status=9,
    )
    before = state_store.manifest_path.read_bytes()

    result = _run(reconciler)

    assert result.failed_names == ("demo",)
    assert (installed / "SKILL.md").read_bytes() == b"base\n"
    assert state_store.manifest_path.read_bytes() == before


def test_return_zero_with_wrong_base_rolls_back(tmp_path: Path):
    reconciler, state_store, installed, _commands = _runtime(
        tmp_path,
        base=b"base\n",
        source=b"source\n",
        local=b"base\n",
        runner_writes_source=False,
    )
    before = state_store.manifest_path.read_bytes()

    result = _run(reconciler)

    assert result.failed_names == ("demo",)
    assert (installed / "SKILL.md").read_bytes() == b"base\n"
    assert state_store.manifest_path.read_bytes() == before


def test_identical_legacy_copies_merge_into_one_overlay(tmp_path: Path):
    reconciler, state_store, installed, _commands = _runtime(
        tmp_path, base=b"base\n", source=b"base\n", local=b"base\n"
    )
    first = tmp_path / "legacy-a"
    second = tmp_path / "legacy-b"
    _write_skill(first, b"local\n")
    _write_skill(second, b"local\n")
    reconciler.migration_loader = lambda _entries: (
        MigrationRecord("a", "demo", "legacy-demo", first, MigrationState.MODIFIED),
        MigrationRecord("b", "demo", "legacy-demo", second, MigrationState.MODIFIED),
    )

    result = _run(reconciler)

    assert result.successful_names == ("demo",)
    assert (installed / "SKILL.md").read_bytes() == b"local\n"
    assert not first.exists()
    assert not second.exists()
    overlay = state_store.read().skills["demo"].files["SKILL.md"].overlay
    assert overlay is not None
    assert state_store.read_overlay(overlay) == b"local\n"


def test_different_legacy_copies_fail_closed_without_per_agent_overlay(
    tmp_path: Path,
):
    reconciler, state_store, _installed, commands = _runtime(
        tmp_path, base=b"base\n", source=b"base\n", local=None
    )
    first = tmp_path / "legacy-a"
    second = tmp_path / "legacy-b"
    _write_skill(first, b"local-a\n")
    _write_skill(second, b"local-b\n")
    before = state_store.manifest_path.read_bytes()
    reconciler.migration_loader = lambda _entries: (
        MigrationRecord("a", "demo", "legacy-demo", first, MigrationState.MODIFIED),
        MigrationRecord("b", "demo", "legacy-demo", second, MigrationState.MODIFIED),
    )

    result = _run(reconciler)

    assert result.failed_names == ("demo",)
    assert commands == []
    assert first.exists() and second.exists()
    assert state_store.manifest_path.read_bytes() == before


def test_npx_projection_symlink_to_active_root_is_deduplicated(tmp_path: Path):
    reconciler, _state_store, installed, commands = _runtime(
        tmp_path, base=b"base\n", source=b"base\n", local=b"base\n"
    )
    projection = tmp_path / "home" / ".claude" / "skills" / "demo"
    projection.parent.mkdir(parents=True)
    projection.symlink_to(installed, target_is_directory=True)
    reconciler.local_roots = {
        "canonical": installed.parent,
        "claude": projection.parent,
    }
    reconciler.migration_loader = lambda _entries: (
        MigrationRecord(
            "claude",
            "demo",
            "demo",
            projection,
            MigrationState.ALREADY_MIGRATED,
        ),
    )

    result = _run(reconciler)

    assert result.successful_names == ("demo",)
    assert result.failed_names == ()
    assert projection.is_symlink()
    assert projection.resolve() == installed.resolve()
    assert len(commands) == 1


def test_legacy_symlink_to_unknown_root_still_fails_closed(tmp_path: Path):
    reconciler, state_store, installed, commands = _runtime(
        tmp_path, base=b"base\n", source=b"base\n", local=b"base\n"
    )
    outside = tmp_path / "outside"
    _write_skill(outside, b"base\n")
    legacy = tmp_path / "legacy"
    legacy.symlink_to(outside, target_is_directory=True)
    before = state_store.manifest_path.read_bytes()
    reconciler.migration_loader = lambda _entries: (
        MigrationRecord("legacy", "demo", "demo", legacy, MigrationState.UNKNOWN),
    )

    result = _run(reconciler)

    assert result.failed_names == ("demo",)
    assert commands == []
    assert legacy.is_symlink()
    assert (installed / "SKILL.md").read_bytes() == b"base\n"
    assert state_store.manifest_path.read_bytes() == before


def test_ds_store_does_not_make_agent_roots_diverge(tmp_path: Path):
    reconciler, _state_store, installed, commands = _runtime(
        tmp_path, base=b"base\n", source=b"base\n", local=b"base\n"
    )
    claude = tmp_path / "home" / ".claude" / "skills" / "demo"
    shutil.copytree(installed, claude)
    (claude / ".DS_Store").write_bytes(b"Finder metadata")
    reconciler.local_roots = {
        "canonical": installed.parent,
        "claude": claude.parent,
    }

    result = _run(reconciler)

    assert result.successful_names == ("demo",)
    assert result.failed_names == ()
    assert len(commands) == 1


def test_raw_npx_wipe_does_not_erase_persistent_local_intent(tmp_path: Path):
    reconciler, _state_store, installed, commands = _runtime(
        tmp_path, base=b"base\n", source=b"base\n", local=b"local\n"
    )
    assert _run(reconciler).successful_names == ("demo",)
    (installed / "SKILL.md").write_bytes(b"base\n")

    result = _run(reconciler)

    assert result.successful_names == ("demo",)
    assert (installed / "SKILL.md").read_bytes() == b"local\n"
    assert len(commands) == 2


def test_overlay_write_failure_rolls_back_everything(tmp_path: Path, monkeypatch):
    reconciler, state_store, installed, _commands = _runtime(
        tmp_path, base=b"base\n", source=b"base\n", local=b"local\n"
    )
    before = state_store.manifest_path.read_bytes()
    monkeypatch.setattr(
        state_store,
        "write_overlay",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("overlay failed")),
    )

    result = _run(reconciler)

    assert result.failed_names == ("demo",)
    assert (installed / "SKILL.md").read_bytes() == b"local\n"
    assert state_store.manifest_path.read_bytes() == before


def test_state_write_failure_rolls_back_everything(tmp_path: Path, monkeypatch):
    reconciler, state_store, installed, _commands = _runtime(
        tmp_path, base=b"base\n", source=b"source\n", local=b"base\n"
    )
    before = state_store.manifest_path.read_bytes()
    monkeypatch.setattr(
        state_store,
        "write",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("state failed")),
    )

    result = _run(reconciler)

    assert result.failed_names == ("demo",)
    assert (installed / "SKILL.md").read_bytes() == b"base\n"
    assert state_store.manifest_path.read_bytes() == before


def test_multiple_skills_continue_after_one_transaction_fails(tmp_path: Path):
    source_skills = tmp_path / "source" / "skills"
    installed_parent = tmp_path / "home" / ".agents" / "skills"
    for name in ("good", "bad"):
        _write_skill(source_skills / name, f"{name}-source\n".encode())
        _write_skill(installed_parent / name, f"{name}-base\n".encode())
    state_store = FirstPartyStateStore(
        tmp_path / "config" / "manifest.yaml",
        tmp_path / "config" / "overlays",
    )
    skills = {}
    for name in ("good", "bad"):
        base = TreeFile.from_content(f"{name}-base\n".encode())
        skills[name] = SkillState(
            REPO,
            "base-commit",
            {
                "SKILL.md": FileState(
                    base.hash,
                    "base-commit",
                    REPO,
                    base.hash,
                    "accepted",
                    "before",
                )
            },
        )
    state_store.write(FirstPartyState(skills))

    @contextmanager
    def checkout(_repo: str):
        yield SourceSnapshot(source_skills, "source-commit")

    def base_provider(_snapshot, _commit, skill):
        return {"SKILL.md": TreeFile.from_content(f"{skill}-base\n".encode())}

    def runner(command, **_kwargs):
        name = command[command.index("--skill") + 1]
        if name == "bad":
            return SimpleNamespace(returncode=7)
        shutil.rmtree(installed_parent / name)
        shutil.copytree(source_skills / name, installed_parent / name)
        return SimpleNamespace(returncode=0)

    reconciler = FirstPartyReconciler(
        state_store=state_store,
        local_roots={"canonical": installed_parent},
        backup_root=tmp_path / "config" / "backups",
        transaction_root=tmp_path / "config" / "transactions",
        source_checkout=checkout,
        base_provider=base_provider,
        command_runner=runner,
        lock_reader=lambda: {
            "skills": {
                "good": {"source": REPO},
                "bad": {"source": REPO},
            }
        },
        interactive=False,
        output_func=lambda _line: None,
    )

    result = reconciler.reconcile(
        (
            SkillEntry(REPO, "good", "ai-dev-first-party"),
            SkillEntry(REPO, "bad", "ai-dev-first-party"),
        ),
        NpxDefaults(agents=("codex",)),
    )

    assert result.successful_names == ("good",)
    assert result.failed_names == ("bad",)
    assert (installed_parent / "good" / "SKILL.md").read_bytes() == b"good-source\n"
    assert (installed_parent / "bad" / "SKILL.md").read_bytes() == b"bad-base\n"
    updated = state_store.read()
    assert updated.skills["good"].source_commit == "source-commit"
    assert updated.skills["bad"].source_commit == "base-commit"


def test_v1_directory_guard_with_local_drift_migrates_to_schema_v2(tmp_path: Path):
    reconciler, state_store, installed, _commands = _runtime(
        tmp_path, base=b"base\n", source=b"base\n", local=b"local\n"
    )
    source_skill = tmp_path / "source" / "skills" / "demo"
    state_store.manifest_path.write_text(
        f"""schema_version: 1
managed_by: ai-dev-first-party-guard
skills:
  demo:
    src_hash: {compute_dir_hash(source_skill)}
    src_commit: base-commit
    src_source: {REPO}
    dst_hash_at_sync: {compute_dir_hash(source_skill)}
    decision: accepted
    decided_at: before
""",
        encoding="utf-8",
    )

    result = _run(reconciler)

    assert result.successful_names == ("demo",)
    assert (installed / "SKILL.md").read_bytes() == b"local\n"
    assert state_store.read().skills["demo"].files["SKILL.md"].overlay is not None
