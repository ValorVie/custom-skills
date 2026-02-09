"""
project 指令群組：專案級別的初始化與更新操作。

採用模板複製模式：
- init: 從 project-template/ 複製到目標專案
- init --force（在 custom-skills 專案中）: 反向同步，從專案複製到 project-template/
- update: 執行 openspec update 和 uds update
"""

import filecmp
import os
import shutil
import stat
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

from ..utils.paths import get_custom_skills_dir

app = typer.Typer(help="專案級別的初始化與更新操作")
console = Console()

# 需要合併而非覆蓋的檔案（保留目標設定並加入來源新增的內容）
MERGE_FILES = {".gitattributes", ".gitignore"}

# 複製到 project-template 時要排除的檔案名稱（個人設定，不屬於共享範本）
EXCLUDE_FROM_TEMPLATE = {"settings.local.json"}


def _template_ignore(directory: str, contents: list[str]) -> set[str]:
    """返回 shutil.copytree 的 ignore 回調，排除不屬於共享範本的檔案。"""
    return {name for name in contents if name in EXCLUDE_FROM_TEMPLATE}


def _remove_readonly(path: Path) -> None:
    """移除檔案或目錄的唯讀屬性（遞迴處理目錄）。"""
    path = Path(path)
    if path.is_file():
        os.chmod(path, stat.S_IWUSR | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)  # 644
    elif path.is_dir():
        for item in path.rglob("*"):
            try:
                if item.is_dir():
                    # 目錄需要 execute 權限才能進入和刪除內容
                    os.chmod(
                        item,
                        stat.S_IRWXU
                        | stat.S_IRGRP
                        | stat.S_IXGRP
                        | stat.S_IROTH
                        | stat.S_IXOTH,
                    )  # 755
                else:
                    os.chmod(
                        item, stat.S_IWUSR | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
                    )  # 644
            except (OSError, PermissionError):
                pass
        try:
            os.chmod(
                path,
                stat.S_IRWXU
                | stat.S_IRGRP
                | stat.S_IXGRP
                | stat.S_IROTH
                | stat.S_IXOTH,
            )  # 755
        except (OSError, PermissionError):
            pass


def _safe_rmtree(path: Path) -> None:
    """安全刪除目錄，處理 Windows 唯讀檔案問題。

    先遞迴移除所有檔案的唯讀屬性，再執行刪除。
    """
    path = Path(path)
    if not path.exists():
        return

    # 先移除唯讀屬性
    _remove_readonly(path)

    # 再執行刪除
    shutil.rmtree(path)


def _collect_diff_files(src_dir: Path, dst_dir: Path) -> list[Path]:
    """遞迴比對來源與目標目錄，回傳需要備份的相對檔案路徑。"""
    src_dir = Path(src_dir)
    dst_dir = Path(dst_dir)
    diff_files: list[Path] = []

    if not dst_dir.exists() or not dst_dir.is_dir():
        return diff_files

    def _collect_all_files(base_dir: Path) -> None:
        for file_path in base_dir.rglob("*"):
            if file_path.is_file():
                diff_files.append(file_path.relative_to(dst_dir))

    if not src_dir.exists() or not src_dir.is_dir():
        _collect_all_files(dst_dir)
        return sorted(diff_files)

    def _walk(src_base: Path, dst_base: Path) -> None:
        for dst_item in dst_base.iterdir():
            src_item = src_base / dst_item.name

            if dst_item.is_dir():
                if not src_item.exists() or not src_item.is_dir():
                    _collect_all_files(dst_item)
                else:
                    _walk(src_item, dst_item)
                continue

            if not dst_item.is_file():
                continue

            if not src_item.exists() or not src_item.is_file():
                diff_files.append(dst_item.relative_to(dst_dir))
                continue

            try:
                if not filecmp.cmp(src_item, dst_item, shallow=False):
                    diff_files.append(dst_item.relative_to(dst_dir))
            except OSError:
                diff_files.append(dst_item.relative_to(dst_dir))

    _walk(src_dir, dst_dir)
    return sorted(diff_files)


def _backup_diff_files(
    target_dir: Path, diff_files: list[Path], item_name: str, backup_dir: Path
) -> list[Path]:
    """將差異檔案從目標目錄備份到指定備份路徑。"""
    target_dir = Path(target_dir)
    backup_dir = Path(backup_dir)
    backed_up_files: list[Path] = []

    for relative_path in diff_files:
        source_file = target_dir / item_name / relative_path
        if not source_file.exists() or not source_file.is_file():
            continue

        backup_file = backup_dir / item_name / relative_path
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, backup_file)
        backed_up_files.append(Path(item_name) / relative_path)

    return backed_up_files


def _merge_text_file(src: Path, dst: Path) -> tuple[int, int]:
    """合併文字檔案內容，保留目標設定並加入來源新增的行。

    適用於 .gitignore、.gitattributes 等逐行設定的檔案。
    以行為單位進行去重，保留目標原有順序，將來源的新行附加在尾部。

    Args:
        src: 來源檔案路徑
        dst: 目標檔案路徑

    Returns:
        tuple[int, int]: (新增行數, 總行數)
    """
    # 讀取來源內容
    src_lines = src.read_text(encoding="utf-8").splitlines()

    # 若目標不存在，直接複製
    if not dst.exists():
        dst.write_text("\n".join(src_lines) + "\n", encoding="utf-8")
        return len(src_lines), len(src_lines)

    # 讀取目標內容
    dst_lines = dst.read_text(encoding="utf-8").splitlines()

    # 建立目標行的集合（用於快速查重，忽略空白差異）
    dst_lines_normalized = {line.strip() for line in dst_lines if line.strip()}

    # 找出來源中目標沒有的行
    new_lines = []
    for line in src_lines:
        normalized = line.strip()
        if normalized and normalized not in dst_lines_normalized:
            new_lines.append(line)
            dst_lines_normalized.add(normalized)  # 避免來源內的重複

    # 若有新行，附加到目標檔案尾部
    if new_lines:
        # 確保目標檔案最後有換行
        content = dst.read_text(encoding="utf-8")
        if content and not content.endswith("\n"):
            content += "\n"
        # 附加新行
        content += "\n".join(new_lines) + "\n"
        dst.write_text(content, encoding="utf-8")

    return len(new_lines), len(dst_lines) + len(new_lines)


def _is_custom_skills_project(project_root: Path) -> bool:
    """檢查是否在 custom-skills 專案目錄中。

    透過檢查 pyproject.toml 中的 name = "ai-dev" 來判斷。
    """
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        return False

    try:
        content = pyproject_path.read_text(encoding="utf-8")
        return 'name = "ai-dev"' in content
    except Exception:
        return False


# 支援的工具（用於 update 指令）
TOOLS = {
    "openspec": {
        "check_dir": "openspec",
        "install_hint": "npm install -g @fission-ai/openspec@latest",
    },
    "uds": {
        "check_dir": ".standards",
        "install_hint": "npm install -g universal-dev-standards",
    },
}


def get_project_template_dir() -> Path:
    """取得 project-template 目錄的路徑。"""
    # 優先使用 custom-skills 目錄下的模板
    custom_skills_dir = get_custom_skills_dir()
    template_dir = custom_skills_dir / "project-template"
    if template_dir.exists():
        return template_dir

    # 備用：使用腳本相對路徑
    script_dir = Path(__file__).resolve().parent.parent.parent
    return script_dir / "project-template"


def check_tool_installed(tool: str) -> bool:
    """檢查工具是否已安裝。"""
    return shutil.which(tool) is not None


def run_tool_command(tool: str, command: str) -> bool:
    """執行工具命令，即時顯示輸出。返回是否成功。"""
    console.print(f"[bold cyan]執行 {tool} {command}...[/bold cyan]")
    try:
        result = subprocess.run(
            [tool, command],
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        console.print(f"[bold red]找不到 {tool} 命令[/bold red]")
        return False


def check_project_initialized(tool: str) -> bool:
    """檢查專案是否已初始化特定工具。"""
    check_dir = TOOLS[tool]["check_dir"]
    return Path(check_dir).exists()


def get_missing_tools(tools: List[str]) -> List[str]:
    """取得未安裝的工具列表。"""
    return [t for t in tools if not check_tool_installed(t)]


def _sync_to_project_template(project_root: Path, template_dir: Path) -> None:
    """反向同步：從專案複製到 project-template（開發者模式）。

    當在 custom-skills 專案中執行 `ai-dev project init --force` 時，
    會將專案根目錄的模板檔案同步回 project-template/ 目錄。

    同步的檔案清單由 template_dir 中現有的檔案決定，包含隱藏檔案和目錄。
    """
    console.print(
        "[bold yellow]偵測到 custom-skills 專案：啟用反向同步模式[/bold yellow]"
    )
    console.print(f"[dim]專案根目錄：{project_root}[/dim]")
    console.print(f"[dim]模板目錄：{template_dir}[/dim]")
    console.print()
    console.print("[bold cyan]同步方向：專案 → project-template/[/bold cyan]")
    console.print()

    copied_count = 0
    skipped_count = 0

    # 根據 template_dir 中現有的檔案來決定要同步哪些項目
    for item in template_dir.iterdir():
        item_name = item.name
        src = project_root / item_name
        dst = template_dir / item_name

        # 合併檔案（保留目標設定並加入來源新增的內容）
        if item_name in MERGE_FILES:
            if not src.exists():
                console.print(f"  [yellow]跳過[/yellow] {item_name}（來源不存在）")
                skipped_count += 1
                continue
            try:
                added, total = _merge_text_file(src, dst)
                if added > 0:
                    console.print(
                        f"  [blue]合併[/blue] {item_name}（+{added} 行，共 {total} 行）"
                    )
                else:
                    console.print(f"  [dim]無變更[/dim] {item_name}（內容相同）")
                copied_count += 1
            except Exception as e:
                console.print(f"  [red]✗[/red] {item_name}：{e}")
            continue

        if not src.exists():
            console.print(f"  [yellow]跳過[/yellow] {item_name}（來源不存在）")
            skipped_count += 1
            continue

        try:
            if src.is_dir():
                if dst.exists():
                    _safe_rmtree(dst)
                shutil.copytree(src, dst, ignore=_template_ignore)
                console.print(f"  [green]✓[/green] {item_name}/ → project-template/")
            else:
                if src.name in EXCLUDE_FROM_TEMPLATE:
                    console.print(
                        f"  [yellow]排除[/yellow] {item_name}（不屬於共享範本）"
                    )
                    skipped_count += 1
                    continue
                shutil.copy2(src, dst)
                console.print(f"  [green]✓[/green] {item_name} → project-template/")
            copied_count += 1
        except Exception as e:
            console.print(f"  [red]✗[/red] {item_name}：{e}")

    console.print()
    console.print(f"[green]同步完成：{copied_count} 個項目[/green]")
    if skipped_count > 0:
        console.print(f"[yellow]跳過：{skipped_count} 個項目[/yellow]")

    console.print()
    console.print("[bold green]模板更新完成！[/bold green]")
    console.print()
    console.print("[dim]提示：記得提交 project-template/ 的變更[/dim]")


@app.command()
def init(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="強制重新初始化（覆蓋現有檔案）；在 custom-skills 專案中會反向同步到 project-template",
    ),
    target: Optional[str] = typer.Argument(
        None,
        help="目標目錄（預設為當前目錄）",
    ),
):
    """初始化專案（從 project-template 複製模板）。

    此指令會將 custom-skills/project-template 中的檔案複製到目標專案，
    包含 .standards、CLAUDE.md、AGENTS.md 等配置目錄和標準文件模板。

    特殊行為：
    - 在 custom-skills 專案中使用 --force 時，會反向同步（專案 → project-template/）
    - 這允許開發者更新模板後同步回 project-template/ 目錄
    """
    # 決定目標目錄
    target_dir = Path(target) if target else Path.cwd()
    target_dir = target_dir.resolve()

    # 取得模板目錄
    template_dir = get_project_template_dir()
    if not template_dir.exists():
        console.print("[bold red]找不到 project-template 目錄[/bold red]")
        console.print(f"[dim]預期路徑：{template_dir}[/dim]")
        console.print("[yellow]請先執行 `ai-dev install` 確保環境已安裝[/yellow]")
        raise typer.Exit(code=1)

    # 特殊處理：在 custom-skills 專案中使用 --force 時反向同步
    # 反向同步目標固定為 repo 內的 project-template/，不使用 get_project_template_dir()
    if force and _is_custom_skills_project(target_dir):
        local_template_dir = target_dir / "project-template"
        _sync_to_project_template(target_dir, local_template_dir)
        return

    # 檢查是否已初始化
    standards_dir = target_dir / ".standards"
    if standards_dir.exists() and not force:
        console.print("[yellow]專案已初始化（.standards 目錄已存在）[/yellow]")
        console.print("[dim]使用 --force 強制重新初始化[/dim]")
        return

    console.print("[bold blue]開始初始化專案...[/bold blue]")
    console.print(f"[dim]模板目錄：{template_dir}[/dim]")
    console.print(f"[dim]目標目錄：{target_dir}[/dim]")
    console.print()

    # 複製模板
    copied_count = 0
    skipped_count = 0
    backup_base_dir: Optional[Path] = None
    backed_up_files: list[Path] = []

    if force:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_base_dir = target_dir / "_backup_after_init_force" / timestamp

    for item in template_dir.iterdir():
        src = item
        dst = target_dir / item.name

        # 合併檔案（保留目標設定並加入來源新增的內容）
        if item.name in MERGE_FILES:
            try:
                dst_existed = dst.exists()
                added, total = _merge_text_file(src, dst)
                if dst_existed and added > 0:
                    console.print(
                        f"  [blue]合併[/blue] {item.name}（+{added} 行，共 {total} 行）"
                    )
                elif dst_existed:
                    console.print(f"  [dim]無變更[/dim] {item.name}（內容相同）")
                else:
                    console.print(f"  [green]✓[/green] {item.name}")
                copied_count += 1
            except Exception as e:
                console.print(f"  [red]✗[/red] {item.name}：{e}")
            continue

        # 檢查是否需要跳過
        if dst.exists() and not force:
            console.print(f"  [yellow]跳過[/yellow] {item.name}（已存在）")
            skipped_count += 1
            continue

        # 複製檔案或目錄
        try:
            if src.is_dir():
                if dst.exists():
                    if force and backup_base_dir is not None:
                        if dst.is_dir():
                            diff_files = _collect_diff_files(src, dst)
                            if diff_files:
                                backed_up_files.extend(
                                    _backup_diff_files(
                                        target_dir=target_dir,
                                        diff_files=diff_files,
                                        item_name=item.name,
                                        backup_dir=backup_base_dir,
                                    )
                                )
                        elif dst.is_file():
                            backup_file = backup_base_dir / item.name
                            backup_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(dst, backup_file)
                            backed_up_files.append(Path(item.name))

                    if dst.is_dir():
                        _safe_rmtree(dst)
                    else:
                        dst.unlink()
                shutil.copytree(src, dst, ignore=_template_ignore)
                console.print(f"  [green]✓[/green] {item.name}/")
            else:
                if force and backup_base_dir is not None and dst.exists():
                    if dst.is_file():
                        try:
                            files_differ = not filecmp.cmp(src, dst, shallow=False)
                        except OSError:
                            files_differ = True

                        if files_differ:
                            backup_file = backup_base_dir / item.name
                            backup_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(dst, backup_file)
                            backed_up_files.append(Path(item.name))
                    elif dst.is_dir():
                        diff_files = _collect_diff_files(src, dst)
                        if diff_files:
                            backed_up_files.extend(
                                _backup_diff_files(
                                    target_dir=target_dir,
                                    diff_files=diff_files,
                                    item_name=item.name,
                                    backup_dir=backup_base_dir,
                                )
                            )

                if dst.exists() and dst.is_dir():
                    _safe_rmtree(dst)

                shutil.copy2(src, dst)
                console.print(f"  [green]✓[/green] {item.name}")
            copied_count += 1
        except Exception as e:
            console.print(f"  [red]✗[/red] {item.name}：{e}")

    console.print()
    console.print(f"[green]複製完成：{copied_count} 個項目[/green]")
    if skipped_count > 0:
        console.print(
            f"[yellow]跳過：{skipped_count} 個項目（使用 --force 覆蓋）[/yellow]"
        )

    if backed_up_files and backup_base_dir is not None:
        backup_files_display = sorted({path.as_posix() for path in backed_up_files})
        console.print()
        console.print("[bold cyan]差異檔案備份摘要[/bold cyan]")
        console.print(f"[dim]備份目錄：{backup_base_dir}[/dim]")
        for backup_file in backup_files_display:
            console.print(f"  [blue]-[/blue] {backup_file}")
        console.print(f"[dim]備份檔案數量：{len(backup_files_display)}[/dim]")

    console.print()
    console.print("[bold green]專案初始化完成！[/bold green]")
    console.print()
    console.print("[dim]下一步：[/dim]")
    console.print("[dim]  1. 檢視並客製化 CLAUDE.md 專案指引[/dim]")
    console.print("[dim]  2. 檢視並調整 .standards/ 中的開發規範[/dim]")


@app.command()
def update(
    only: Optional[str] = typer.Option(
        None,
        "--only",
        "-o",
        help="只更新特定工具：openspec, uds",
    ),
):
    """更新專案配置（整合 openspec update + uds update）。"""
    # 決定要更新的工具
    if only:
        if only not in TOOLS:
            console.print(f"[red]無效的工具：{only}[/red]")
            console.print(f"有效選項：{', '.join(TOOLS.keys())}")
            raise typer.Exit(code=1)
        tools_to_update = [only]
    else:
        tools_to_update = list(TOOLS.keys())

    # 檢查工具是否已安裝
    missing = get_missing_tools(tools_to_update)
    if missing:
        console.print("[bold red]以下工具尚未安裝：[/bold red]")
        for tool in missing:
            hint = TOOLS[tool]["install_hint"]
            console.print(f"  - {tool}: [dim]{hint}[/dim]")
        console.print()
        console.print("[yellow]請先安裝所需工具後再執行此命令。[/yellow]")
        raise typer.Exit(code=1)

    # 檢查是否已初始化
    not_init = [t for t in tools_to_update if not check_project_initialized(t)]
    if not_init:
        if len(not_init) == len(tools_to_update):
            # 全部都沒初始化
            console.print("[bold red]專案尚未初始化。[/bold red]")
            console.print("[yellow]請先執行 `ai-dev project init`[/yellow]")
            raise typer.Exit(code=1)
        else:
            # 部分初始化
            console.print("[yellow]以下工具尚未初始化：[/yellow]")
            for tool in not_init:
                check_dir = TOOLS[tool]["check_dir"]
                console.print(f"  - {tool}: {check_dir}/ 不存在")
            console.print()
            console.print(
                f"[dim]建議執行 `ai-dev project init --only {not_init[0]}`[/dim]"
            )
            console.print()

            # 只更新已初始化的工具
            tools_to_update = [t for t in tools_to_update if t not in not_init]

    console.print("[bold blue]開始更新專案配置...[/bold blue]")
    console.print()

    # 執行更新（uds 先，openspec 後）
    update_order = ["uds", "openspec"]
    success = True

    for tool in update_order:
        if tool not in tools_to_update:
            continue

        if not run_tool_command(tool, "update"):
            console.print(f"[bold red]{tool} update 失敗[/bold red]")
            success = False
            break

        console.print(f"[green]✓ {tool} update 完成[/green]")
        console.print()

    if success:
        console.print("[bold green]專案配置更新完成！[/bold green]")
    else:
        raise typer.Exit(code=1)
