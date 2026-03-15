from __future__ import annotations

from dataclasses import dataclass, field
import filecmp
from pathlib import Path
import shutil


@dataclass
class ProjectTemplateSyncResult:
    copied: int = 0
    updated: int = 0
    skipped: int = 0
    missing: list[str] = field(default_factory=list)


def _normalize_entry(entry: str) -> str:
    return entry[:-1] if entry.endswith("/") else entry


def _build_ignore(repo_root: Path, exclude: set[str]):
    def _ignore(current_dir: str, contents: list[str]) -> set[str]:
        base = Path(current_dir).relative_to(repo_root)
        ignored: set[str] = set()
        for name in contents:
            rel = (base / name).as_posix()
            if rel in exclude:
                ignored.add(name)
        return ignored

    return _ignore


def _replace_path(src: Path, dst: Path, ignore_callback) -> None:
    if dst.exists():
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
            dst.unlink()

    if src.is_dir():
        shutil.copytree(src, dst, ignore=ignore_callback)
        return

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _is_excluded_path(path: Path, repo_root: Path, exclude: set[str]) -> bool:
    try:
        rel = path.relative_to(repo_root).as_posix()
    except ValueError:
        return False
    return rel in exclude


def _paths_match(src: Path, dst: Path, repo_root: Path, exclude: set[str]) -> bool:
    if src.is_dir():
        if not dst.exists() or not dst.is_dir():
            return False

        src_names = {
            child.name
            for child in src.iterdir()
            if not _is_excluded_path(child, repo_root, exclude)
        }
        dst_names = {
            child.name
            for child in dst.iterdir()
            if not _is_excluded_path(src / child.name, repo_root, exclude)
        }
        if src_names != dst_names:
            return False

        return all(
            _paths_match(src / name, dst / name, repo_root, exclude)
            for name in src_names
        )

    if not dst.exists() or not dst.is_file():
        return False

    try:
        return filecmp.cmp(src, dst, shallow=False)
    except OSError:
        return False


def sync_project_template(
    *,
    repo_root: Path,
    template_dir: Path,
    manifest: dict,
    check: bool = False,
) -> ProjectTemplateSyncResult:
    repo_root = Path(repo_root).resolve()
    template_dir = Path(template_dir).resolve()
    result = ProjectTemplateSyncResult()
    exclude = {_normalize_entry(item) for item in manifest.get("exclude", [])}
    ignore_callback = _build_ignore(repo_root, exclude)

    for raw_entry in manifest.get("include", []):
        entry = _normalize_entry(raw_entry)
        src = repo_root / entry
        dst = template_dir / entry

        if entry in exclude:
            result.skipped += 1
            continue

        if not src.exists():
            result.missing.append(entry)
            continue

        existed = dst.exists()
        if check:
            if not existed:
                result.copied += 1
            elif not _paths_match(src, dst, repo_root, exclude):
                result.updated += 1
            continue

        _replace_path(src, dst, ignore_callback)
        if existed:
            result.updated += 1
        else:
            result.copied += 1

    return result
