"""管理 .git/info/exclude 中的 AI 文件排除規則（標記區塊）。"""

from pathlib import Path

from rich.console import Console

console = Console()

MARKER_START = "# >>> ai-dev (managed by ai-dev, DO NOT EDIT)"
MARKER_END = "# <<< ai-dev"

DEFAULT_KEEP_TRACKED = [".editorconfig", ".gitattributes", ".gitignore"]

# .github/ 下需要特別處理的 AI 子路徑
GITHUB_AI_PATHS = ["skills", "prompts", "copilot-instructions.md"]

# 永遠加入排除的項目（即使模板中沒有）
ALWAYS_EXCLUDE = [".ai-dev-project.yaml"]


def _get_exclude_path(project_dir: Path) -> Path | None:
    """取得 .git/info/exclude 路徑，非 git repo 回傳 None。"""
    git_dir = project_dir / ".git"
    if not git_dir.is_dir():
        return None
    info_dir = git_dir / "info"
    info_dir.mkdir(parents=True, exist_ok=True)
    return info_dir / "exclude"


def _find_block(lines: list[str]) -> tuple[int | None, int | None]:
    """尋找管理區塊的起止行號。"""
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        stripped = line.rstrip("\n\r")
        if stripped == MARKER_START:
            start_idx = i
        elif stripped == MARKER_END and start_idx is not None:
            end_idx = i
            break
    return start_idx, end_idx


def _collect_existing_patterns(lines: list[str], start_idx: int | None, end_idx: int | None) -> set[str]:
    """收集區塊外已存在的 patterns（去除註釋和空行）。"""
    existing = set()
    for i, line in enumerate(lines):
        if start_idx is not None and end_idx is not None and start_idx <= i <= end_idx:
            continue
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            existing.add(stripped)
    return existing


def ensure_ai_exclude(
    project_dir: Path,
    patterns: list[str],
    dry_run: bool = False,
) -> tuple[bool, list[str], list[str]]:
    """確保 .git/info/exclude 包含 AI 文件排除規則。

    Args:
        project_dir: 專案根目錄
        patterns: 要排除的 pattern 清單
        dry_run: 只檢查不寫入

    Returns:
        (was_modified, added_patterns, skipped_patterns)
    """
    exclude_path = _get_exclude_path(project_dir)
    if exclude_path is None:
        return False, [], []

    # 讀取現有內容
    if exclude_path.is_file():
        existing = exclude_path.read_text(encoding="utf-8")
    else:
        existing = ""

    lines = existing.splitlines(keepends=True)
    start_idx, end_idx = _find_block(lines)
    has_block = start_idx is not None and end_idx is not None

    # 收集區塊外已有的 patterns
    outside_patterns = _collect_existing_patterns(lines, start_idx, end_idx)

    # 分類：要加入的 vs 跳過的
    added = []
    skipped = []
    for p in patterns:
        if p.strip() in outside_patterns:
            skipped.append(p)
        else:
            added.append(p)

    if dry_run:
        return False, added, skipped

    # 建構區塊內容
    block_lines = [MARKER_START + "\n"]
    for p in added:
        block_lines.append(p + "\n")
    block_lines.append(MARKER_END + "\n")

    if has_block:
        # 替換既有區塊
        lines[start_idx : end_idx + 1] = block_lines
        result = "".join(lines)
    else:
        # 附加到尾部
        result = existing
        if result and not result.endswith("\n"):
            result += "\n"
        if result:
            result += "\n"
        result += "".join(block_lines)

    if result and not result.endswith("\n"):
        result += "\n"

    exclude_path.write_text(result, encoding="utf-8")
    return True, added, skipped


def remove_ai_exclude(project_dir: Path) -> bool:
    """移除 .git/info/exclude 中的 ai-dev 管理區塊。

    Returns:
        bool: 是否有修改
    """
    exclude_path = _get_exclude_path(project_dir)
    if exclude_path is None or not exclude_path.is_file():
        return False

    existing = exclude_path.read_text(encoding="utf-8")
    lines = existing.splitlines(keepends=True)
    start_idx, end_idx = _find_block(lines)

    if start_idx is None or end_idx is None:
        return False

    del lines[start_idx : end_idx + 1]
    # 移除區塊前的空行
    if start_idx > 0 and start_idx <= len(lines) and lines[start_idx - 1].strip() == "":
        del lines[start_idx - 1]

    result = "".join(lines)
    if result and not result.endswith("\n"):
        result += "\n"

    exclude_path.write_text(result, encoding="utf-8")
    return True


def get_current_patterns(project_dir: Path) -> list[str] | None:
    """讀取目前管理區塊中的 patterns。

    Returns:
        None 如果沒有管理區塊，否則 pattern 清單
    """
    exclude_path = _get_exclude_path(project_dir)
    if exclude_path is None or not exclude_path.is_file():
        return None

    existing = exclude_path.read_text(encoding="utf-8")
    lines = existing.splitlines()
    start_idx, end_idx = _find_block([l + "\n" for l in lines])

    if start_idx is None or end_idx is None:
        return None

    patterns = []
    for line in lines[start_idx + 1 : end_idx]:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            patterns.append(stripped)
    return patterns


def derive_exclude_patterns(
    template_dir: Path,
    keep_tracked: list[str] | None = None,
) -> list[str]:
    """從模板目錄內容推導排除 patterns。

    掃描 template_dir 的第一層內容，排除 keep_tracked 中的項目。
    .github/ 特殊處理：只排除 AI 相關子路徑。

    Args:
        template_dir: 模板目錄
        keep_tracked: 不排除的項目清單（預設：.editorconfig, .gitattributes, .gitignore）

    Returns:
        排除 pattern 清單
    """
    if keep_tracked is None:
        keep_tracked = DEFAULT_KEEP_TRACKED

    keep_set = set(keep_tracked)
    patterns = []

    for item in sorted(template_dir.iterdir()):
        name = item.name

        # 跳過 .git 目錄和保留項
        if name == ".git" or name in keep_set:
            continue

        # .github/ 特殊處理
        if name == ".github" and item.is_dir():
            for sub in sorted(item.iterdir()):
                if sub.name in GITHUB_AI_PATHS:
                    if sub.is_dir():
                        patterns.append(f".github/{sub.name}/")
                    else:
                        patterns.append(f".github/{sub.name}")
            continue

        # 一般項目
        if item.is_dir():
            patterns.append(f"{name}/")
        else:
            patterns.append(name)

    # 永遠加入的項目
    for always in ALWAYS_EXCLUDE:
        if always not in patterns:
            patterns.append(always)

    return patterns


def prompt_exclude_choice(patterns: list[str]) -> str:
    """詢問使用者是否加入本地排除。

    Returns:
        "yes" | "no"
    """
    import typer

    console.print()
    console.print("[bold]? 是否將 AI 文件加入本地排除？(.git/info/exclude)[/bold]")
    console.print("[dim]  這些檔案在本地正常運作，AI 工具可正常讀取[/dim]")
    console.print("[dim]  但不會出現在 git status、commit 或 PR 中[/dim]")
    console.print()

    choice = typer.prompt(
        "  [1] 是，加入排除（推薦）\n"
        "  [2] 否，保持 git 追蹤\n"
        "  [3] 檢視排除清單\n\n"
        "請選擇",
        default="1",
    )

    if choice == "3":
        console.print()
        console.print(f"[bold]將排除以下 {len(patterns)} 個項目：[/bold]")
        for p in patterns:
            console.print(f"  [dim]{p}[/dim]")
        console.print()
        choice = typer.prompt(
            "  [1] 是，加入排除（推薦）\n"
            "  [2] 否，保持 git 追蹤\n\n"
            "請選擇",
            default="1",
        )

    return "yes" if choice == "1" else "no"


def print_exclude_result(added: list[str], skipped: list[str]) -> None:
    """顯示排除結果。"""
    console.print(
        f"[green]✓ 已將 {len(added)} 個 AI 相關項目加入 .git/info/exclude[/green]"
    )
    if skipped:
        console.print(
            f"[dim]  （{len(skipped)} 個項目已存在，跳過重複）[/dim]"
        )
    console.print("[dim]ℹ 此設定記錄於 .ai-dev-project.yaml，更新時自動同步[/dim]")
