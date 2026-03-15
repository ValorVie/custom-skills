"""
Smart Merge：智慧合併流程，比較來源與目標檔案，依內容差異提供互動選項。
"""

import difflib
import hashlib
import shutil
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt
from rich.syntax import Syntax

console = Console()

# 排除不複製的檔案/目錄（相對於模板根目錄）
EXCLUDE_PATHS = {".git", ".gitkeep", ".gitignore-downstream", "README.md", "LICENSE"}

# 5 個標準工具目錄（若模板包含這些目錄會發出警告）
STANDARD_TOOL_DIRS = {"agents", "commands", "hooks", "plugins", "skills"}


class MergeStats:
    """合併結果統計。"""

    def __init__(self) -> None:
        self.new: int = 0
        self.identical: int = 0
        self.overwritten: int = 0
        self.appended: int = 0
        self.incremental: int = 0
        self.skipped: int = 0

    def total_managed(self) -> int:
        """回傳實際被管理的檔案數（排除跳過的）。"""
        return self.new + self.overwritten + self.appended + self.incremental

    def print_summary(self) -> None:
        """顯示合併摘要。"""
        console.print()
        console.print("[bold]合併結果摘要：[/bold]")
        if self.new:
            console.print(f"  [green]+ {self.new} 個新檔案已複製[/green]")
        if self.identical:
            console.print(f"  [dim]= {self.identical} 個相同檔案已跳過[/dim]")
        if self.overwritten:
            console.print(f"  [cyan]O {self.overwritten} 個檔案已覆蓋[/cyan]")
        if self.appended:
            console.print(f"  [blue]A {self.appended} 個檔案已附加[/blue]")
        if self.incremental:
            console.print(f"  [magenta]I {self.incremental} 個檔案已增量附加[/magenta]")
        if self.skipped:
            console.print(f"  [yellow]S {self.skipped} 個衝突檔案已由使用者跳過[/yellow]")


def _sha256(path: Path) -> str:
    """計算檔案的 SHA-256 雜湊值。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _show_diff(src: Path, dst: Path) -> None:
    """顯示兩個檔案的 unified diff。"""
    try:
        src_text = src.read_text(encoding="utf-8", errors="replace").splitlines(
            keepends=True
        )
        dst_text = dst.read_text(encoding="utf-8", errors="replace").splitlines(
            keepends=True
        )
    except Exception:
        console.print("[yellow]  無法顯示 diff（非文字檔案）[/yellow]")
        return

    diff = list(
        difflib.unified_diff(
            dst_text,
            src_text,
            fromfile=f"目前：{dst.name}",
            tofile=f"模板：{src.name}",
            n=3,
        )
    )

    if not diff:
        console.print("[dim]  （兩個檔案內容相同）[/dim]")
        return

    diff_text = "".join(diff)
    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
    console.print(syntax)


def _compute_incremental_lines(src: Path, dst: Path) -> list[str]:
    """計算來源檔案中有、但目標檔案中沒有的行（增量差異）。

    以行為單位比對，忽略空白行。回傳來源中存在但目標中不存在的非空白行。
    """
    try:
        src_lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
        dst_lines = dst.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []

    dst_set = {line.rstrip() for line in dst_lines if line.strip()}
    new_lines = []
    for line in src_lines:
        stripped = line.rstrip()
        if stripped and stripped not in dst_set:
            new_lines.append(line)
    return new_lines


def _prompt_conflict(
    src: Path,
    dst: Path,
    relative_path: str,
    *,
    show_prompt_hint: bool = False,
) -> str:
    """提示使用者選擇衝突檔案的處理方式。

    Returns:
        str: "append" | "overwrite" | "skip" | "incremental"
    """
    while True:
        if show_prompt_hint:
            _prompt_hint()
        console.print(
            f"  [yellow]? 衝突：{relative_path}[/yellow] "
            f"[dim]（目標檔案已存在且內容不同）[/dim]"
        )
        choice = Prompt.ask(
            "    選擇",
            choices=["A", "I", "O", "S", "D", "a", "i", "o", "s", "d"],
            default="S",
            show_choices=False,
            show_default=False,
        )
        choice = choice.upper()

        if choice == "D":
            _show_diff(src, dst)
            continue  # 顯示 diff 後重新提示
        elif choice == "A":
            return "append"
        elif choice == "I":
            return "incremental"
        elif choice == "O":
            return "overwrite"
        else:
            return "skip"


def _prompt_hint() -> None:
    """顯示互動提示說明。"""
    console.print(
        "  [dim]  [A] 附加到尾部  [I] 增量附加  [O] 覆蓋整份  [S] 跳過  [D] 顯示差異[/dim]"
    )


def merge_file(
    src: Path,
    dst: Path,
    relative_path: str,
    force: bool = False,
    skip_conflicts: bool = False,
    stats: MergeStats | None = None,
    show_prompt_hint: bool = False,
    src_hash: str | None = None,
    dst_hash: str | None = None,
) -> str:
    """合併單一檔案。

    Args:
        src: 來源（模板）檔案路徑
        dst: 目標檔案路徑
        relative_path: 相對路徑（用於顯示）
        force: 強制覆蓋，不提示
        skip_conflicts: 跳過所有衝突，不提示
        stats: 統計物件（若提供則更新）
        show_prompt_hint: 是否顯示互動提示說明
        src_hash: 預先計算的來源檔案 hash
        dst_hash: 預先計算的目標檔案 hash

    Returns:
        str: "new" | "identical" | "overwritten" | "appended" | "incremental" | "skipped"
    """
    if stats is None:
        stats = MergeStats()

    if not dst.exists():
        # 新檔案——直接複製
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        console.print(f"  [green]+[/green] {relative_path} [dim](新)[/dim]")
        stats.new += 1
        return "new"

    # 檔案已存在——比較內容
    effective_src_hash = src_hash or _sha256(src)
    effective_dst_hash = dst_hash or _sha256(dst)
    if effective_src_hash == effective_dst_hash:
        console.print(f"  [dim]= {relative_path} (相同)[/dim]")
        stats.identical += 1
        return "identical"

    # 內容不同——依模式決定
    if force:
        shutil.copy2(src, dst)
        console.print(f"  [cyan]O[/cyan] {relative_path} [dim](已覆蓋)[/dim]")
        stats.overwritten += 1
        return "overwritten"

    if skip_conflicts:
        console.print(f"  [yellow]S[/yellow] {relative_path} [dim](跳過衝突)[/dim]")
        stats.skipped += 1
        return "skipped"

    # 互動模式
    action = _prompt_conflict(
        src,
        dst,
        relative_path,
        show_prompt_hint=show_prompt_hint,
    )

    if action == "overwrite":
        shutil.copy2(src, dst)
        console.print(f"  [cyan]O[/cyan] {relative_path} [dim](已覆蓋)[/dim]")
        stats.overwritten += 1
        return "overwritten"
    elif action == "append":
        existing = dst.read_text(encoding="utf-8", errors="replace")
        new_content = src.read_text(encoding="utf-8", errors="replace")
        with open(dst, "w", encoding="utf-8") as f:
            f.write(existing)
            if not existing.endswith("\n"):
                f.write("\n")
            f.write(new_content)
        console.print(f"  [blue]A[/blue] {relative_path} [dim](已附加)[/dim]")
        stats.appended += 1
        return "appended"
    elif action == "incremental":
        new_lines = _compute_incremental_lines(src, dst)
        if not new_lines:
            console.print(
                f"  [dim]=[/dim] {relative_path} [dim](增量比對後無新內容)[/dim]"
            )
            stats.identical += 1
            return "identical"
        existing = dst.read_text(encoding="utf-8", errors="replace")
        with open(dst, "w", encoding="utf-8") as f:
            f.write(existing)
            if not existing.endswith("\n"):
                f.write("\n")
            f.write("\n".join(new_lines))
            f.write("\n")
        console.print(
            f"  [magenta]I[/magenta] {relative_path} "
            f"[dim](增量附加 {len(new_lines)} 行)[/dim]"
        )
        stats.incremental += 1
        return "incremental"
    else:
        console.print(f"  [yellow]S[/yellow] {relative_path} [dim](使用者跳過)[/dim]")
        stats.skipped += 1
        return "skipped"


def merge_template(
    template_dir: Path,
    target_dir: Path,
    force: bool = False,
    skip_conflicts: bool = False,
    only_files: list[str] | None = None,
) -> tuple[list[str], MergeStats]:
    """將模板目錄內容合併到目標目錄。

    Args:
        template_dir: 模板本地目錄
        target_dir: 目標目錄（通常為 CWD）
        force: 強制覆蓋所有衝突
        skip_conflicts: 跳過所有衝突
        only_files: 若提供，只合併這些相對路徑（用於 --update 模式）

    Returns:
        tuple:
            - list[str]: 被管理的相對路徑清單（new/overwrite/append，不含 skip）
            - MergeStats: 統計結果
    """
    stats = MergeStats()
    managed_files: list[str] = []
    hint_shown = False

    # 警告：模板包含標準工具目錄
    for tool_dir in STANDARD_TOOL_DIRS:
        if (template_dir / tool_dir).is_dir():
            console.print(
                f"[yellow]⚠ 模板包含標準工具目錄 '{tool_dir}'。"
                f"工具分發請考慮使用 `add-custom-repo`。[/yellow]"
            )

    if only_files is not None:
        # --update 模式：只處理指定檔案
        file_list = [Path(f) for f in only_files]
    else:
        # 全量模式：遍歷模板目錄
        file_list = []
        for src_path in sorted(template_dir.rglob("*")):
            if not src_path.is_file():
                continue

            # 計算相對路徑
            rel = src_path.relative_to(template_dir)
            rel_parts = rel.parts

            # 排除清單檢查：.git 目錄（任意位置）
            if rel_parts[0] in {".git"}:
                continue
            # .gitkeep 排除（任意位置）
            if src_path.name == ".gitkeep":
                continue
            # 根層 README.md 和 LICENSE
            if len(rel_parts) == 1 and src_path.name in {"README.md", "LICENSE"}:
                continue
            file_list.append(rel)

    for rel in file_list:
        if isinstance(rel, str):
            rel = Path(rel)

        src = template_dir / rel
        if not src.exists():
            continue

        dst = target_dir / rel
        relative_str = str(rel)

        result = merge_file(
            src=src,
            dst=dst,
            relative_path=relative_str,
            force=force,
            skip_conflicts=skip_conflicts,
            stats=stats,
            show_prompt_hint=not hint_shown and not force and not skip_conflicts,
        )
        if not hint_shown and result in ("overwritten", "appended", "incremental", "skipped"):
            hint_shown = True

        if result in ("new", "overwritten", "appended", "incremental"):
            managed_files.append(relative_str)

    return managed_files, stats
