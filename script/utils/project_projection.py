"""專案 AI 設定投影與重整流程。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
from pathlib import Path
import shutil

from .git_exclude import ALWAYS_EXCLUDE, ensure_ai_exclude
from .manifest import compute_dir_hash, compute_file_hash
from .paths import get_custom_skills_dir
from .project_blocks import read_managed_block, remove_managed_block, upsert_managed_block
from .project_projection_manifest import read_project_manifest, write_project_manifest
from .project_tracking import load_tracking_file, update_tracking_file

PROJECT_PROJECTION_SCHEMA_VERSION = "1"
PROJECT_MANAGED_BLOCK_ID = "ai-dev-project"
MANAGED_BLOCK_FILES = {
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "INSTRUCTIONS.md",
}
FULLY_MANAGED_TOP_LEVEL_ITEMS = {
    ".agent",
    ".agents",
    ".claude",
    ".codex",
    ".gemini",
    ".opencode",
    *MANAGED_BLOCK_FILES,
}
PARTIALLY_MANAGED_PROJECT_PATHS = {
    ".github/copilot-instructions.md",
    ".github/prompts",
    ".github/skills",
}


@dataclass(frozen=True)
class ProjectionEntry:
    """單一專案投影來源。"""

    relative_path: str
    source_path: Path
    kind: str


@dataclass
class HydrateResult:
    """hydrate/reconcile 結果摘要。"""

    generated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    manifest_path: Path | None = None


def get_project_template_dir() -> Path:
    """回傳內建 project-template 目錄。"""
    custom_skills_dir = get_custom_skills_dir()
    template_dir = custom_skills_dir / "project-template"
    if template_dir.exists():
        return template_dir

    script_dir = Path(__file__).resolve().parent.parent.parent
    return script_dir / "project-template"


def compute_text_hash(text: str) -> str:
    """計算文字內容的 SHA-256 hash。"""
    normalized = text.rstrip("\n")
    return f"sha256:{hashlib.sha256(normalized.encode('utf-8')).hexdigest()}"


def _pattern_to_relative_path(pattern: str) -> str:
    return pattern[:-1] if pattern.endswith("/") else pattern


def get_project_projection_patterns(template_dir: Path) -> list[str]:
    """只回傳 project projection 需要排除的 AI 生成路徑。"""
    patterns: list[str] = []

    for relative_path in sorted(FULLY_MANAGED_TOP_LEVEL_ITEMS | PARTIALLY_MANAGED_PROJECT_PATHS):
        source_path = template_dir / relative_path
        if not source_path.exists():
            continue
        if source_path.is_dir():
            patterns.append(f"{relative_path}/")
        else:
            patterns.append(relative_path)

    for always in ALWAYS_EXCLUDE:
        if always not in patterns:
            patterns.append(always)

    return patterns


def _collect_projection_entries(template_dir: Path) -> list[ProjectionEntry]:
    """依排除清單收集專案 AI 投影來源。"""
    entries: list[ProjectionEntry] = []

    for pattern in get_project_projection_patterns(template_dir):
        relative_path = _pattern_to_relative_path(pattern)
        if relative_path == ".ai-dev-project.yaml":
            continue

        source_path = template_dir / relative_path
        if not source_path.exists():
            continue

        if relative_path in MANAGED_BLOCK_FILES:
            kind = "managed_block"
        elif source_path.is_dir():
            kind = "dir"
        else:
            kind = "file"

        entries.append(
            ProjectionEntry(
                relative_path=relative_path,
                source_path=source_path,
                kind=kind,
            )
        )

    return sorted(entries, key=lambda entry: entry.relative_path)


def _get_expected_hash(entry: ProjectionEntry) -> str:
    if entry.kind == "managed_block":
        return compute_text_hash(entry.source_path.read_text(encoding="utf-8"))
    if entry.kind == "dir":
        return compute_dir_hash(entry.source_path)
    return compute_file_hash(entry.source_path)


def _get_current_hash(target_path: Path, kind: str) -> str | None:
    if not target_path.exists():
        return None

    if kind == "managed_block":
        content = read_managed_block(target_path, PROJECT_MANAGED_BLOCK_ID)
        if content is None:
            return None
        return compute_text_hash(content)

    if kind == "dir":
        if not target_path.is_dir():
            return None
        return compute_dir_hash(target_path)

    if not target_path.is_file():
        return None
    return compute_file_hash(target_path)


def _backup_path(project_root: Path, relative_path: str, backup_root: Path) -> None:
    """備份衝突或待刪除的投影路徑。"""
    source_path = project_root / relative_path
    backup_path = backup_root / relative_path
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    if source_path.is_dir():
        shutil.copytree(source_path, backup_path, dirs_exist_ok=True)
    else:
        shutil.copy2(source_path, backup_path)


def _remove_path(project_root: Path, relative_path: str, kind: str) -> None:
    target_path = project_root / relative_path

    if kind == "managed_block":
        remove_managed_block(target_path, PROJECT_MANAGED_BLOCK_ID)
        return

    if target_path.is_dir():
        shutil.rmtree(target_path)
    elif target_path.exists():
        target_path.unlink()


def _apply_projection_entry(project_root: Path, entry: ProjectionEntry) -> None:
    target_path = project_root / entry.relative_path

    if entry.kind == "managed_block":
        upsert_managed_block(
            target_path,
            PROJECT_MANAGED_BLOCK_ID,
            entry.source_path.read_text(encoding="utf-8"),
        )
        return

    target_path.parent.mkdir(parents=True, exist_ok=True)
    if entry.kind == "dir":
        shutil.copytree(entry.source_path, target_path, dirs_exist_ok=True)
        return

    shutil.copy2(entry.source_path, target_path)


def hydrate_project(
    project_root: Path,
    template_dir: Path | None = None,
    on_conflict: str = "skip",
) -> HydrateResult:
    """依 project intent 將 AI 設定投影到專案內。"""
    project_root = Path(project_root).resolve()
    intent = load_tracking_file(project_root)
    if intent is None:
        raise FileNotFoundError(".ai-dev-project.yaml 不存在，請先初始化專案意圖")

    template_dir = (template_dir or get_project_template_dir()).resolve()
    if not template_dir.exists():
        raise FileNotFoundError(f"找不到 project-template 目錄：{template_dir}")

    if on_conflict not in {"skip", "force", "backup"}:
        raise ValueError("on_conflict 必須是 skip、force 或 backup")

    project_id = intent["project_id"]
    patterns = get_project_projection_patterns(template_dir)
    ensure_ai_exclude(project_root, patterns)

    old_manifest = read_project_manifest(project_id) or {}
    old_files = old_manifest.get("files", {})
    entries = _collect_projection_entries(template_dir)
    desired_paths = {entry.relative_path for entry in entries}

    result = HydrateResult()
    backup_root: Path | None = None
    if on_conflict == "backup":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_root = project_root / "_backup_project_projection" / timestamp

    new_files: dict[str, dict] = {}

    for entry in entries:
        target_path = project_root / entry.relative_path
        expected_hash = _get_expected_hash(entry)
        previous_record = old_files.get(entry.relative_path)

        conflict = False
        if previous_record is not None:
            current_hash = _get_current_hash(target_path, entry.kind)
            if current_hash is not None and current_hash != previous_record.get("hash"):
                conflict = True
        elif entry.kind != "managed_block" and target_path.exists():
            conflict = True

        if conflict and on_conflict == "skip":
            result.conflicts.append(entry.relative_path)
            result.skipped.append(entry.relative_path)
            if previous_record is not None:
                new_files[entry.relative_path] = previous_record
            continue

        if conflict and on_conflict == "backup" and backup_root is not None and target_path.exists():
            _backup_path(project_root, entry.relative_path, backup_root)

        _apply_projection_entry(project_root, entry)
        result.generated.append(entry.relative_path)
        new_files[entry.relative_path] = {
            "kind": entry.kind,
            "hash": expected_hash,
            "source": entry.relative_path,
        }

    for relative_path, previous_record in sorted(old_files.items()):
        if relative_path in desired_paths:
            continue

        target_path = project_root / relative_path
        if not target_path.exists():
            continue

        kind = previous_record.get("kind", "file")
        current_hash = _get_current_hash(target_path, kind)
        conflict = current_hash is not None and current_hash != previous_record.get("hash")

        if conflict and on_conflict == "skip":
            result.conflicts.append(relative_path)
            result.skipped.append(relative_path)
            new_files[relative_path] = previous_record
            continue

        if conflict and on_conflict == "backup" and backup_root is not None:
            _backup_path(project_root, relative_path, backup_root)

        _remove_path(project_root, relative_path, kind)
        result.removed.append(relative_path)

    manifest_payload = {
        "managed_by": "ai-dev",
        "schema_version": PROJECT_PROJECTION_SCHEMA_VERSION,
        "project_id": project_id,
        "project_root": str(project_root),
        "exclude": {
            "version": "1",
            "patterns": patterns,
        },
        "files": dict(sorted(new_files.items())),
    }
    result.manifest_path = write_project_manifest(project_id, manifest_payload)
    update_tracking_file(managed_files=sorted(manifest_payload["files"]), project_dir=project_root)
    return result


def reconcile_project(
    project_root: Path,
    template_dir: Path | None = None,
    on_conflict: str = "skip",
) -> HydrateResult:
    """收斂 project intent、projection manifest 與實際生成檔。"""
    return hydrate_project(project_root, template_dir=template_dir, on_conflict=on_conflict)
