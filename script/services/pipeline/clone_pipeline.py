from __future__ import annotations

from pathlib import Path

from rich.console import Console

from script.models.execution_plan import ExecutionPlan
from script.services.state.auto_skill import run_state_phase
from script.services.targets.distribute import run_targets_phase

console = Console()


def _collect_sources() -> list[tuple[str, Path]]:
    """蒐集所有可同步的來源 repo (name, local_path)。"""
    out: list[tuple[str, Path]] = []
    custom_skills = Path.home() / ".config" / "custom-skills"
    if custom_skills.exists():
        out.append(("custom-skills", custom_skills))
    ecc = Path.home() / ".config" / "everything-claude-code"
    if ecc.exists():
        out.append(("ecc", ecc))
    try:
        from script.utils.custom_repos import load_custom_repos

        for name, info in load_custom_repos().get("repos", {}).items():
            local = info.get("local_path", "").replace("~", str(Path.home()))
            p = Path(local)
            if p.exists():
                out.append((name, p))
    except Exception:
        pass
    return out


def _build_source_summary(plan: ExecutionPlan) -> list[dict]:
    """產生 per-source update summary rows。"""
    from script.utils.manifest import (
        get_manifest_dir,
        get_repo_head,
        list_changed_files,
        read_manifest,
        is_v2,
    )

    sources = _collect_sources()
    if not sources:
        return []

    # 從 manifests/ 收集每個 source 的 last_sync_commit（取任一 target 內最新者）
    last_commits: dict[str, str] = {}
    manifest_dir = get_manifest_dir()
    if manifest_dir.exists():
        for path in manifest_dir.glob("*.yaml"):
            target_name = path.stem
            m = read_manifest(target_name)
            if not is_v2(m):
                continue
            mapping = (m or {}).get("last_sync_commit_by_source", {}) or {}
            for source, commit in mapping.items():
                last_commits.setdefault(source, commit)

    selected_targets = set(plan.targets) if plan.targets else None
    rows: list[dict] = []
    for source, _local_path in sources:
        head = get_repo_head(source)
        last = last_commits.get(source)
        if not head:
            continue
        if not last:
            rows.append({"source": source, "status": "first-sync"})
            continue
        if last == head:
            rows.append({"source": source, "status": "unchanged"})
            continue
        changed = list_changed_files(source, last, head)
        # 影響評估：以「檔案路徑落在 platform_targets 對應 source 結構」為近似
        # 簡化版：不細分本次 / 其他 target，列總數即可
        affected_current = len(changed) if selected_targets else len(changed)
        affected_other = 0 if selected_targets else 0
        rows.append({
            "source": source,
            "status": "updated",
            "last_commit": last,
            "head_commit": head,
            "total_changed": len(changed),
            "affected_current": affected_current,
            "affected_other": affected_other,
        })
    return rows


def execute_clone_plan(
    plan: ExecutionPlan,
    *,
    force: bool = False,
    skip_conflicts: bool = False,
    backup: bool = False,
) -> None:
    if plan.dry_run:
        target_text = ", ".join(plan.targets) if plan.targets else "all"
        console.print(
            f"[bold blue][dry-run][/bold blue] clone phases={', '.join(plan.phases)} targets={target_text}"
        )

    # 進入 targets 階段前先印 per-source update summary
    if "targets" in plan.phases:
        try:
            from script.utils.manifest import render_source_summary

            rows = _build_source_summary(plan)
            if rows:
                render_source_summary(rows)
        except Exception as e:
            console.print(f"[dim]（來源摘要無法產生：{e}）[/dim]")

    if plan.dry_run:
        return

    for phase in plan.phases:
        if phase == "state":
            run_state_phase(plan=plan)
        elif phase == "targets":
            run_targets_phase(
                plan=plan,
                force=force,
                skip_conflicts=skip_conflicts,
                backup=backup,
            )
        else:
            raise ValueError(f"Unsupported clone phase: {phase}")

    console.print("[bold green]分發完成！[/bold green]")
