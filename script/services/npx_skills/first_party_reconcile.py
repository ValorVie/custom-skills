from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Callable, ContextManager
from difflib import unified_diff

import yaml

from script.services.npx_skills.config import SkillEntry
from script.services.npx_skills.first_party_overlay import (
    FilePlan,
    FileState,
    FirstPartyState,
    FirstPartyStateStore,
    OverlayEntry,
    PlannedFile,
    SkillState,
    TransactionJournalStore,
    TransactionStatus,
    TreeFile,
    plan_skill,
    snapshot_tree,
)
from script.services.npx_skills.first_party_transaction import SkillTransaction
from script.services.npx_skills.migration import (
    MigrationRecord,
    MigrationState,
    classify_legacy_skill,
    legacy_name_for,
    read_npx_lock,
)
from script.utils.manifest import FileEntry


class Decision(str, Enum):
    KEEP_LOCAL = "keep-local"
    USE_UPSTREAM = "use-upstream"


FileConflict = PlannedFile


@dataclass(frozen=True)
class DecisionResolution:
    decisions: dict[str, Decision]
    unresolved: tuple[str, ...] = ()
    aborted: bool = False


class DecisionResolver:
    def __init__(
        self,
        *,
        interactive: bool,
        input_func: Callable[[str], str] = input,
        output_func: Callable[[str], None] = print,
    ):
        self.interactive = interactive
        self.input_func = input_func
        self.output_func = output_func

    @staticmethod
    def _text(content: bytes | None) -> list[str] | None:
        if content is None:
            return []
        if b"\x00" in content:
            return None
        try:
            return content.decode("utf-8").splitlines(keepends=True)
        except UnicodeDecodeError:
            return None

    def _show_diff(
        self,
        conflict: FileConflict,
        left: bytes | None,
        right: bytes | None,
        left_label: str,
        right_label: str,
    ) -> None:
        left_text = self._text(left)
        right_text = self._text(right)
        path = conflict.plan.path
        if left_text is None or right_text is None:
            self.output_func(
                f"binary: {path} {left_label}={len(left or b'')} bytes "
                f"{right_label}={len(right or b'')} bytes"
            )
            return
        rendered = "".join(
            unified_diff(
                left_text,
                right_text,
                fromfile=f"{left_label}/{path}",
                tofile=f"{right_label}/{path}",
            )
        )
        self.output_func(rendered or f"{path}: no content difference")

    def _show_menu(self, conflict: FileConflict) -> None:
        plan = conflict.plan
        status = {
            "both-changed": "上游與本機都已修改（both-changed）",
            "no-base": "沒有可信的共同基準（no-base）",
        }[plan.classification]
        self.output_func(f"衝突：{plan.path}")
        self.output_func(f"狀態：{status}")
        self.output_func("")
        self.output_func("查看差異：")
        if plan.classification == "no-base":
            self.output_func("  [Ds] 無法使用：沒有可信的共同基準")
            self.output_func("  [Dl] 無法使用：沒有可信的共同基準")
        else:
            self.output_func("  [Ds] 比較上游版本與上次共同基準")
            self.output_func("  [Dl] 比較本機版本與上次共同基準")
        self.output_func("  [Dc] 比較上游版本與本機版本")
        self.output_func("")
        self.output_func("處理方式：")
        self.output_func(
            "  [K] 保留本機內容／刪除狀態，存成持久覆寫層；後續更新仍會套用"
        )
        self.output_func(
            "  [O] 採用上游內容／刪除狀態；系統會先備份目前本機內容，再覆蓋"
        )
        self.output_func("  [A] 中止本次第一方 skills 更新；目前尚未寫入任何變更")

    @staticmethod
    def _prompt(plan: FilePlan) -> str:
        choices = "Dc/K/O/A" if plan.classification == "no-base" else "Ds/Dl/Dc/K/O/A"
        return f"請選擇 [{choices}]: "

    def resolve(self, conflicts: Sequence[FileConflict]) -> DecisionResolution:
        decisions: dict[str, Decision] = {}
        unresolved: list[str] = []
        for conflict in conflicts:
            plan = conflict.plan
            if plan.classification == "clean":
                decisions[plan.path] = Decision.USE_UPSTREAM
                continue
            if plan.classification == "local-only":
                decisions[plan.path] = Decision.KEEP_LOCAL
                continue
            if not self.interactive:
                unresolved.append(plan.path)
                continue

            self._show_menu(conflict)
            while True:
                answer = self.input_func(self._prompt(plan)).strip().upper()
                if answer == "DS":
                    if plan.classification == "no-base":
                        self.output_func("無法使用：沒有可信的共同基準。請改用 [Dc]。")
                    else:
                        self._show_diff(
                            conflict,
                            conflict.base_content,
                            conflict.source_content,
                            "base",
                            "upstream",
                        )
                elif answer == "DL":
                    if plan.classification == "no-base":
                        self.output_func("無法使用：沒有可信的共同基準。請改用 [Dc]。")
                    else:
                        self._show_diff(
                            conflict,
                            conflict.base_content,
                            conflict.local_content,
                            "base",
                            "local",
                        )
                elif answer == "DC":
                    self._show_diff(
                        conflict,
                        conflict.source_content,
                        conflict.local_content,
                        "upstream",
                        "local",
                    )
                elif answer == "K":
                    decisions[plan.path] = Decision.KEEP_LOCAL
                    break
                elif answer == "O":
                    decisions[plan.path] = Decision.USE_UPSTREAM
                    break
                elif answer == "A":
                    return DecisionResolution({}, aborted=True)
                else:
                    self.output_func(f"無效選項：{answer or '(空白)'}")

        return DecisionResolution(decisions, tuple(unresolved))


@dataclass(frozen=True)
class SourceSnapshot:
    skills_root: Path
    commit: str
    repo_root: Path | None = None


@dataclass(frozen=True)
class ReconcileResult:
    successful_names: tuple[str, ...]
    failed_names: tuple[str, ...]
    backup_paths: tuple[Path, ...] = ()
    aborted: bool = False


@dataclass(frozen=True)
class _SkillWork:
    entry: SkillEntry
    source: dict[str, TreeFile]
    conflicts: tuple[PlannedFile, ...]
    decisions: dict[str, Decision]
    roots: dict[str, Path]
    transaction_roots: dict[str, Path]
    legacy_aliases: tuple[Path, ...]


def get_first_party_local_roots(
    agents: Sequence[str], *, home: Path | None = None
) -> dict[str, Path]:
    """Resolve the verified npx 1.5.x global paths for ai-dev's agent IDs."""
    root = home or Path.home()
    canonical = root / ".agents" / "skills"
    mapping = {
        "claude-code": root / ".claude" / "skills",
        "codex": canonical,
        "gemini-cli": canonical,
        "opencode": canonical,
        "antigravity": canonical,
    }
    roots = {"canonical": canonical}
    for agent in agents:
        if agent not in mapping:
            raise ValueError(f"第一方 npx agent path 尚未驗證: {agent}")
        roots[agent] = mapping[agent]
    return roots


def read_guard_entries(path: Path) -> dict[str, FileEntry]:
    if not path.exists():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"第一方 guard manifest 無法讀取: {path}: {exc}") from exc
    if (
        not isinstance(payload, dict)
        or payload.get("managed_by") != "ai-dev-first-party-guard"
    ):
        raise ValueError(f"第一方 guard manifest 格式無效: {path}")
    skills = payload.get("skills", {})
    if not isinstance(skills, dict):
        raise ValueError(f"第一方 guard manifest skills 必須是 mapping: {path}")
    entries: dict[str, FileEntry] = {}
    for name, raw in skills.items():
        if not isinstance(name, str) or not isinstance(raw, dict):
            raise ValueError(f"第一方 guard manifest entry 格式無效: {path}")
        entry = FileEntry.from_dict(raw)
        if entry is None:
            raise ValueError(f"第一方 guard manifest entry 缺少 base: {name}")
        entries[name] = entry
    return entries


@contextmanager
def checkout_first_party_source(repo: str) -> Iterator[SourceSnapshot]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError(f"第一方 repository 格式無效: {repo}")
    with tempfile.TemporaryDirectory(prefix="ai-dev-first-party-") as temporary:
        checkout = Path(temporary) / "source"
        result = subprocess.run(
            [
                "git",
                "clone",
                "--quiet",
                f"https://github.com/{repo}.git",
                str(checkout),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"無法取得第一方 source snapshot: {repo}")
        commit = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
        if commit.returncode != 0 or not commit.stdout.strip():
            raise RuntimeError(f"無法解析第一方 source commit: {repo}")
        yield SourceSnapshot(
            skills_root=checkout / "skills",
            commit=commit.stdout.strip(),
            repo_root=checkout,
        )


def _git_skill_snapshot(
    snapshot: SourceSnapshot, commit: str, skill: str
) -> dict[str, TreeFile] | None:
    if snapshot.repo_root is None:
        if commit == snapshot.commit:
            path = snapshot.skills_root / skill
            return snapshot_tree(path) if path.is_dir() else None
        return None
    if not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
        return None
    prefix = f"skills/{skill}/"
    listed = subprocess.run(
        [
            "git",
            "-C",
            str(snapshot.repo_root),
            "ls-tree",
            "-rz",
            "--full-tree",
            commit,
            "--",
            f"skills/{skill}",
        ],
        check=False,
        capture_output=True,
    )
    if listed.returncode != 0:
        return None
    files: dict[str, TreeFile] = {}
    for record in listed.stdout.split(b"\0"):
        if not record:
            continue
        header, separator, raw_path = record.partition(b"\t")
        fields = header.split()
        if not separator or len(fields) != 3:
            raise ValueError(f"invalid git tree entry: {skill}")
        mode, kind, _object_id = (field.decode("ascii") for field in fields)
        path = raw_path.decode("utf-8")
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError(f"unsupported file type in source: {path}")
        if not path.startswith(prefix):
            raise ValueError(f"invalid source path: {path}")
        relative = path[len(prefix) :]
        content = subprocess.run(
            [
                "git",
                "-C",
                str(snapshot.repo_root),
                "show",
                f"{commit}:{path}",
            ],
            check=False,
            capture_output=True,
        )
        if content.returncode != 0:
            return None
        files[relative] = TreeFile.from_content(content.stdout)
    return files or None


def _same_tree(left: Mapping[str, TreeFile], right: Mapping[str, TreeFile]) -> bool:
    return {path: item.hash for path, item in left.items()} == {
        path: item.hash for path, item in right.items()
    }


def _remove_tree(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


class FirstPartyReconciler:
    """Own first-party base, local overlay, verification, and rollback."""

    def __init__(
        self,
        *,
        state_store: FirstPartyStateStore | None = None,
        local_roots: Mapping[str, Path] | None = None,
        backup_root: Path | None = None,
        transaction_root: Path | None = None,
        source_checkout: Callable[[str], ContextManager[SourceSnapshot]] = (
            checkout_first_party_source
        ),
        base_provider: Callable[
            [SourceSnapshot, str, str], dict[str, TreeFile] | None
        ] = _git_skill_snapshot,
        command_runner: Callable[..., object] | None = None,
        lock_reader: Callable[[], Mapping[str, object]] = read_npx_lock,
        interactive: bool | None = None,
        input_func: Callable[[str], str] = input,
        output_func: Callable[[str], None] = print,
        migration_loader: (
            Callable[[Sequence[SkillEntry]], Sequence[MigrationRecord]] | None
        ) = None,
        home: Path | None = None,
    ):
        root = home or Path.home()
        config = root / ".config" / "ai-dev"
        self.state_store = state_store or FirstPartyStateStore(
            config / "manifests" / "npx-first-party.yaml",
            config / "overlays" / "npx-first-party",
        )
        self.local_roots = dict(local_roots) if local_roots is not None else None
        self.backup_root = backup_root or config / "backups" / "npx-first-party"
        self.transaction_root = (
            transaction_root or config / "transactions" / "npx-first-party"
        )
        self.source_checkout = source_checkout
        self.base_provider = base_provider
        if command_runner is None:
            from script.utils.system import run_command

            command_runner = run_command
        self.command_runner = command_runner
        self.lock_reader = lock_reader
        self.interactive = sys.stdin.isatty() if interactive is None else interactive
        self.input_func = input_func
        self.output_func = output_func
        self.home = root
        self.migration_loader = migration_loader

    def _parents(self, defaults: object) -> dict[str, Path]:
        if self.local_roots is not None:
            return dict(self.local_roots)
        agents = getattr(defaults, "agents")
        return get_first_party_local_roots(agents, home=self.home)

    def _migration_records(
        self, entries: Sequence[SkillEntry]
    ) -> tuple[MigrationRecord, ...]:
        if self.migration_loader is not None:
            return tuple(self.migration_loader(entries))
        if self.local_roots is not None:
            return ()
        from script.utils.manifest import read_manifest
        from script.utils.shared import get_target_path

        lock = self.lock_reader()
        records: list[MigrationRecord] = []
        for target in ("claude", "antigravity", "opencode", "codex", "agy"):
            target_root = get_target_path(target, "skills")
            if target_root is None:
                continue
            manifest = read_manifest(target)
            for entry in entries:
                records.append(
                    classify_legacy_skill(
                        target=target,
                        canonical_id=entry.skill,
                        legacy_name=legacy_name_for(entry.skill),
                        target_root=target_root,
                        manifest=manifest,
                        npx_lock=lock,
                        expected_repo=entry.repo,
                    )
                )
        return tuple(records)

    @staticmethod
    def _skill_roots(parents: Mapping[str, Path], skill: str) -> dict[str, Path]:
        roots: dict[str, Path] = {}
        seen: set[Path] = set()
        for label, parent in parents.items():
            path = parent / skill
            resolved = path.resolve(strict=False)
            if resolved in seen:
                continue
            seen.add(resolved)
            roots[label] = resolved if path.is_symlink() else path
        return roots

    def _load_state(self) -> tuple[FirstPartyState, dict[str, FileEntry]]:
        path = self.state_store.manifest_path
        if not path.exists():
            return FirstPartyState(), {}
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as exc:
            raise ValueError(f"first-party state unreadable: {path}") from exc
        if isinstance(payload, dict) and payload.get("managed_by") == (
            "ai-dev-first-party-guard"
        ):
            return FirstPartyState(), read_guard_entries(path)
        return self.state_store.read(), {}

    def _base_for(
        self,
        snapshot: SourceSnapshot,
        entry: SkillEntry,
        skill_state: SkillState | None,
        legacy: FileEntry | None,
    ) -> dict[str, TreeFile] | None:
        commit = (
            skill_state.source_commit
            if skill_state is not None
            else legacy.src_commit if legacy is not None else None
        )
        if commit is None:
            return None
        base = self.base_provider(snapshot, commit, entry.skill)
        if base is None:
            return None
        if skill_state is not None:
            missing = TreeFile.missing()
            for path, state in skill_state.files.items():
                if base.get(path, missing).hash != state.src_hash:
                    return None
        elif legacy is not None:
            # The directory guard is trusted only when the retrieved commit
            # reproduces the recorded source hash.
            digest = hashlib.sha256()
            for path, file in sorted(base.items()):
                digest.update(path.encode("utf-8"))
                digest.update(file.hash.encode("utf-8"))
            if f"sha256:{digest.hexdigest()}" != legacy.src_hash:
                return None
        return base

    def _overlays(self, skill_state: SkillState | None) -> dict[str, TreeFile]:
        overlays: dict[str, TreeFile] = {}
        if skill_state is None:
            return overlays
        for path, state in skill_state.files.items():
            if state.overlay is None:
                continue
            content = self.state_store.read_overlay(state.overlay)
            overlays[path] = (
                TreeFile.missing()
                if content is None
                else TreeFile.from_content(content)
            )
        return overlays

    @staticmethod
    def _local_tree(
        roots: Mapping[str, Path],
        *,
        base: Mapping[str, TreeFile] | None,
        source: Mapping[str, TreeFile],
    ) -> dict[str, TreeFile] | None:
        trees = [snapshot_tree(path) for path in roots.values() if path.is_dir()]
        if not trees:
            return None
        first = trees[0]
        if all(_same_tree(first, other) for other in trees[1:]):
            return first

        modified = [
            tree
            for tree in trees
            if not _same_tree(tree, source)
            and (base is None or not _same_tree(tree, base))
        ]
        unique_modified: list[dict[str, TreeFile]] = []
        for tree in modified:
            if not any(_same_tree(tree, known) for known in unique_modified):
                unique_modified.append(tree)
        if len(unique_modified) > 1:
            raise ValueError("agent-visible roots have different local modifications")
        if unique_modified:
            return unique_modified[0]
        if any(_same_tree(tree, source) for tree in trees):
            return dict(source)
        return dict(base or first)

    def _plan(
        self,
        entries: Sequence[SkillEntry],
        defaults: object,
        snapshot: SourceSnapshot,
        state: FirstPartyState,
        legacy: Mapping[str, FileEntry],
        migration_records: Sequence[MigrationRecord],
    ) -> tuple[list[_SkillWork], list[str], bool]:
        parents = self._parents(defaults)
        resolver = DecisionResolver(
            interactive=self.interactive,
            input_func=self.input_func,
            output_func=self.output_func,
        )
        work: list[_SkillWork] = []
        failed: list[str] = []
        for entry in entries:
            try:
                source = snapshot_tree(snapshot.skills_root / entry.skill)
                roots = self._skill_roots(parents, entry.skill)
                records = tuple(
                    record
                    for record in migration_records
                    if record.canonical_id == entry.skill
                    and record.state is not MigrationState.MISSING
                    and record.path.exists()
                )
                transaction_roots = dict(roots)
                candidate_roots = dict(roots)
                legacy_aliases: list[Path] = []
                seen = {path.resolve(strict=False) for path in roots.values()}
                for index, record in enumerate(records):
                    resolved = record.path.resolve(strict=False)
                    if record.path.is_symlink():
                        if resolved in seen:
                            continue
                        raise ValueError("unsupported symlink in legacy target copy")
                    if resolved not in seen:
                        label = f"legacy-{index:03d}"
                        candidate_roots[label] = record.path
                        transaction_roots[label] = record.path
                        seen.add(resolved)
                    if record.legacy_name != entry.skill:
                        legacy_aliases.append(record.path)
                transaction = SkillTransaction(
                    entry.skill,
                    roots=transaction_roots,
                    state_store=self.state_store,
                    journal_store=TransactionJournalStore(self.transaction_root),
                    backup_root=self.backup_root,
                )
                transaction.recover_if_needed()
                skill_state = state.skills.get(entry.skill)
                base = self._base_for(
                    snapshot, entry, skill_state, legacy.get(entry.skill)
                )
                local = self._local_tree(
                    candidate_roots,
                    base=base,
                    source=source,
                )
                if local is None:
                    local = dict(base or {})
                conflicts = plan_skill(
                    base=base,
                    source=source,
                    local=local,
                    overlays=self._overlays(skill_state),
                )
                resolution = resolver.resolve(conflicts)
                if resolution.aborted:
                    return [], failed, True
                if resolution.unresolved:
                    failed.append(entry.skill)
                    continue
                work.append(
                    _SkillWork(
                        entry=entry,
                        source=source,
                        conflicts=conflicts,
                        decisions=resolution.decisions,
                        roots=roots,
                        transaction_roots=transaction_roots,
                        legacy_aliases=tuple(legacy_aliases),
                    )
                )
            except (OSError, RuntimeError, ValueError) as exc:
                self.output_func(f"{entry.skill}: {exc}")
                failed.append(entry.skill)
        return work, failed, False

    @staticmethod
    def _command(entry: SkillEntry, defaults: object) -> list[str]:
        command = [
            "npx",
            "skills",
            "add",
            entry.repo,
            "--skill",
            entry.skill,
        ]
        if getattr(defaults, "scope") == "global":
            command.append("-g")
        command.extend(["-a", *getattr(defaults, "agents")])
        if getattr(defaults, "yes"):
            command.append("--yes")
        return command

    def _verify_base(self, item: _SkillWork) -> None:
        verified: set[Path] = set()
        for root in item.roots.values():
            if not root.is_dir():
                raise RuntimeError(f"installed root missing: {root}")
            resolved = root.resolve()
            if resolved in verified:
                continue
            verified.add(resolved)
            if not _same_tree(snapshot_tree(resolved), item.source):
                raise RuntimeError(f"pure base mismatch: {item.entry.skill}")
        lock = self.lock_reader()
        skills = lock.get("skills", {}) if isinstance(lock, Mapping) else {}
        lock_entry = (
            skills.get(item.entry.skill) if isinstance(skills, Mapping) else None
        )
        lock_source = (
            lock_entry.get("source") if isinstance(lock_entry, Mapping) else None
        )
        if lock_source != item.entry.repo:
            raise RuntimeError(f"lock source mismatch: {item.entry.skill}")

    @staticmethod
    def _expected(item: _SkillWork) -> dict[str, TreeFile]:
        expected = dict(item.source)
        for conflict in item.conflicts:
            if item.decisions[conflict.plan.path] is not Decision.KEEP_LOCAL:
                continue
            if conflict.local_content is None:
                expected.pop(conflict.plan.path, None)
            else:
                expected[conflict.plan.path] = TreeFile.from_content(
                    conflict.local_content
                )
        return expected

    def _materialize(
        self, item: _SkillWork
    ) -> tuple[dict[str, OverlayEntry], dict[str, TreeFile]]:
        expected = self._expected(item)
        active = self.state_store.overlay_root / item.entry.skill
        _remove_tree(active)
        overlays: dict[str, OverlayEntry] = {}
        for conflict in item.conflicts:
            path = conflict.plan.path
            if item.decisions[path] is not Decision.KEEP_LOCAL:
                continue
            content = conflict.local_content
            overlays[path] = self.state_store.write_overlay(
                item.entry.skill, path, content
            )

        seen: set[Path] = set()
        for root in item.roots.values():
            resolved = root.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            for conflict in item.conflicts:
                path = resolved.joinpath(*PurePosixPath(conflict.plan.path).parts)
                if item.decisions[conflict.plan.path] is Decision.KEEP_LOCAL:
                    content = conflict.local_content
                    if content is None:
                        path.unlink(missing_ok=True)
                    else:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(content)
        return overlays, expected

    @staticmethod
    def _skill_state(
        item: _SkillWork,
        overlays: Mapping[str, OverlayEntry],
        source_commit: str,
        expected: Mapping[str, TreeFile],
    ) -> SkillState:
        missing = TreeFile.missing()
        files = {
            conflict.plan.path: FileState(
                src_hash=item.source.get(conflict.plan.path, missing).hash,
                src_commit=source_commit,
                src_source=item.entry.repo,
                dst_hash_at_sync=expected.get(conflict.plan.path, missing).hash,
                decision=item.decisions[conflict.plan.path].value,
                decided_at=datetime.now(timezone.utc).isoformat(),
                overlay=overlays.get(conflict.plan.path),
            )
            for conflict in item.conflicts
        }
        return SkillState(item.entry.repo, source_commit, files)

    def _apply(
        self,
        item: _SkillWork,
        defaults: object,
        source_commit: str,
        state: FirstPartyState,
    ) -> tuple[bool, Path | None, FirstPartyState]:
        transaction = SkillTransaction(
            item.entry.skill,
            roots=item.transaction_roots,
            state_store=self.state_store,
            journal_store=TransactionJournalStore(self.transaction_root),
            backup_root=self.backup_root,
        )
        retained: Path | None = None
        try:
            journal = transaction.begin()
            result = self.command_runner(
                self._command(item.entry, defaults), check=False
            )
            if getattr(result, "returncode", 1) != 0:
                raise RuntimeError(f"npx returned {getattr(result, 'returncode', 1)}")
            self._verify_base(item)
            transaction.mark(TransactionStatus.BASE_APPLIED)
            overlays, expected = self._materialize(item)
            transaction.mark(TransactionStatus.OVERLAY_APPLIED)
            for root in item.roots.values():
                if not _same_tree(snapshot_tree(root.resolve()), expected):
                    raise RuntimeError(f"effective tree mismatch: {item.entry.skill}")
            transaction.mark(TransactionStatus.VERIFIED)
            updated_skills = dict(state.skills)
            updated_skills[item.entry.skill] = self._skill_state(
                item, overlays, source_commit, expected
            )
            updated = FirstPartyState(updated_skills)
            self.state_store.write(updated)
            for legacy_alias in item.legacy_aliases:
                _remove_tree(legacy_alias)
            retain = any(
                conflict.plan.classification in {"both-changed", "no-base"}
                and item.decisions[conflict.plan.path] is Decision.USE_UPSTREAM
                for conflict in item.conflicts
            )
            if retain:
                retained = self.backup_root / journal.backup_dir
            transaction.commit(retain_backup=retain)
            return True, retained, updated
        except Exception as exc:
            self.output_func(f"{item.entry.skill}: {exc}")
            try:
                transaction.rollback()
            except RuntimeError as rollback_error:
                self.output_func(str(rollback_error))
            return False, None, state

    def reconcile(
        self,
        entries: Sequence[SkillEntry],
        defaults: object,
        *,
        dry_run: bool = False,
    ) -> ReconcileResult:
        if not entries:
            return ReconcileResult((), ())
        repositories = {entry.repo for entry in entries}
        if len(repositories) != 1:
            raise ValueError("first-party reconcile requires one repository")
        state, legacy = self._load_state()
        migration_records = self._migration_records(entries)
        with self.source_checkout(entries[0].repo) as snapshot:
            work, failed, aborted = self._plan(
                entries,
                defaults,
                snapshot,
                state,
                legacy,
                migration_records,
            )
            if aborted:
                return ReconcileResult((), tuple(failed), aborted=True)
            if dry_run:
                return ReconcileResult((), tuple(failed))
            successful: list[str] = []
            backups: list[Path] = []
            current_state = state
            for item in work:
                success, backup, current_state = self._apply(
                    item, defaults, snapshot.commit, current_state
                )
                if success:
                    successful.append(item.entry.skill)
                    if backup is not None:
                        backups.append(backup)
                else:
                    failed.append(item.entry.skill)
            return ReconcileResult(
                tuple(successful), tuple(failed), tuple(backups), aborted=False
            )
