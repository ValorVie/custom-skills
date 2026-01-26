import typer
import subprocess
from pathlib import Path
from rich.console import Console

import yaml

console = Console()


def get_sources_yaml_path() -> Path:
    """取得 sources.yaml 路徑。"""
    # 從安裝位置找到專案根目錄
    current = Path(__file__).resolve().parent
    while current != current.parent:
        sources_path = current / "upstream" / "sources.yaml"
        if sources_path.exists():
            return sources_path
        current = current.parent

    # 如果找不到，嘗試從 cwd 找
    cwd = Path.cwd()
    while cwd != cwd.parent:
        sources_path = cwd / "upstream" / "sources.yaml"
        if sources_path.exists():
            return sources_path
        cwd = cwd.parent

    raise FileNotFoundError("找不到 upstream/sources.yaml")


def parse_repo_url(remote_path: str) -> tuple[str, str, str]:
    """解析遠端 URL，回傳 (repo_name, owner/repo, branch)。

    支援格式：
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - git@github.com:owner/repo.git
    - owner/repo (簡寫)
    """
    # 移除尾端 .git
    remote_path = remote_path.rstrip("/")
    if remote_path.endswith(".git"):
        remote_path = remote_path[:-4]

    # 解析不同格式
    if remote_path.startswith("https://github.com/"):
        # https://github.com/owner/repo
        parts = remote_path.replace("https://github.com/", "").split("/")
        if len(parts) >= 2:
            owner, repo = parts[0], parts[1]
            return repo, f"{owner}/{repo}", "main"

    elif remote_path.startswith("git@github.com:"):
        # git@github.com:owner/repo.git
        parts = remote_path.replace("git@github.com:", "").split("/")
        if len(parts) >= 2:
            owner, repo = parts[0], parts[1]
            return repo, f"{owner}/{repo}", "main"

    elif "/" in remote_path and not remote_path.startswith(("http", "git@")):
        # owner/repo 簡寫格式
        parts = remote_path.split("/")
        if len(parts) == 2:
            owner, repo = parts[0], parts[1]
            return repo, f"{owner}/{repo}", "main"

    raise ValueError(f"無法解析 URL: {remote_path}")


def clone_repo(repo_path: str, target_dir: Path) -> bool:
    """Clone repo 到指定目錄。"""
    url = f"https://github.com/{repo_path}.git"

    console.print(f"[cyan]正在 clone {url}...[/cyan]")

    result = subprocess.run(
        ["git", "clone", url, str(target_dir)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        console.print(f"[red]Clone 失敗: {result.stderr}[/red]")
        return False

    console.print(f"[green]✓ Clone 完成: {target_dir}[/green]")
    return True


def detect_repo_format(repo_dir: Path) -> str:
    """偵測 repo 的格式。"""
    # 檢查是否有 UDS 格式的特徵
    if (repo_dir / ".standards").exists():
        return "uds"

    # 檢查 skills 目錄中的檔案格式
    skills_dir = repo_dir / "skills"
    if skills_dir.exists():
        for skill_file in skills_dir.rglob("*.md"):
            content = skill_file.read_text(encoding="utf-8", errors="ignore")
            # 檢查是否有 YAML frontmatter
            if content.startswith("---"):
                lines = content.split("\n")
                for i, line in enumerate(lines[1:], 1):
                    if line.strip() == "---":
                        # 有 frontmatter，檢查是否有 UDS 特徵
                        frontmatter = "\n".join(lines[1:i])
                        if "triggers:" in frontmatter or "category:" in frontmatter:
                            return "uds"
                        break
            break

    return "claude-code-native"


def add_to_sources_yaml(
    sources_path: Path,
    name: str,
    repo: str,
    local_path: str,
    branch: str,
    format: str,
) -> bool:
    """將新 repo 加入 sources.yaml。"""
    try:
        with open(sources_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        console.print(f"[red]讀取 sources.yaml 失敗: {e}[/red]")
        return False

    if "sources" not in data:
        data["sources"] = {}

    # 檢查是否已存在
    if name in data["sources"]:
        console.print(f"[yellow]⚠ {name} 已存在於 sources.yaml[/yellow]")
        return True

    # 新增條目
    data["sources"][name] = {
        "repo": repo,
        "branch": branch,
        "local_path": local_path,
        "format": format,
    }

    # 寫回檔案
    try:
        with open(sources_path, "w", encoding="utf-8") as f:
            # 保留註解，手動寫入
            f.write("# Upstream Sources Registry\n")
            f.write("# 上游來源註冊表 - 記錄所有第三方 repo 的來源資訊\n")
            f.write("#\n")
            f.write("# 用途：\n")
            f.write("# - custom-skills-upstream-sync 分析上游 commit 差異\n")
            f.write("# - 記錄 repo 位置與分支資訊\n")
            f.write("#\n")
            f.write("# 注意：\n")
            f.write("# - ai-dev update 會拉取這些 repo 到 ~/.config/\n")
            f.write("# - ai-dev clone 會從 ~/.config/ 整合內容到各工具目錄\n")
            f.write("\n")
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        console.print(f"[green]✓ 已加入 sources.yaml[/green]")
        return True
    except Exception as e:
        console.print(f"[red]寫入 sources.yaml 失敗: {e}[/red]")
        return False


def add_repo(
    remote_path: str = typer.Argument(..., help="遠端 repo 路徑 (例如: owner/repo 或完整 URL)"),
    name: str = typer.Option(None, "--name", "-n", help="自訂名稱（預設使用 repo 名稱）"),
    branch: str = typer.Option("main", "--branch", "-b", help="追蹤的分支"),
    skip_clone: bool = typer.Option(False, "--skip-clone", help="跳過 clone（僅加入 sources.yaml）"),
    analyze: bool = typer.Option(False, "--analyze", "-a", help="加入後立即執行分析"),
):
    """新增上游 repo 並開始追蹤。

    此指令會：
    1. Clone repo 到 ~/.config/<repo-name>/
    2. 將 repo 資訊加入 upstream/sources.yaml
    3. [可選] 執行 custom-skills-upstream-sync 分析

    範例：
        ai-dev add-repo owner/repo
        ai-dev add-repo https://github.com/owner/repo
        ai-dev add-repo owner/repo --name my-custom-name
        ai-dev add-repo owner/repo --analyze
    """
    console.print("[bold blue]新增上游 Repo[/bold blue]")

    # 解析 URL
    try:
        repo_name, repo_path, default_branch = parse_repo_url(remote_path)
    except ValueError as e:
        console.print(f"[red]錯誤: {e}[/red]")
        raise typer.Exit(1)

    # 使用自訂名稱或 repo 名稱
    name = name or repo_name
    branch = branch or default_branch

    # 目標目錄
    target_dir = Path.home() / ".config" / name
    local_path = f"~/.config/{name}/"

    console.print(f"  Repo: {repo_path}")
    console.print(f"  名稱: {name}")
    console.print(f"  分支: {branch}")
    console.print(f"  目錄: {target_dir}")

    # Clone repo
    if not skip_clone:
        if target_dir.exists():
            console.print(f"[yellow]⚠ 目錄已存在: {target_dir}[/yellow]")
            console.print("[yellow]  跳過 clone，僅更新 sources.yaml[/yellow]")
        else:
            if not clone_repo(repo_path, target_dir):
                raise typer.Exit(1)

    # 偵測格式
    if target_dir.exists():
        format = detect_repo_format(target_dir)
        console.print(f"  格式: {format}")
    else:
        format = "claude-code-native"
        console.print(f"  格式: {format} (預設)")

    # 加入 sources.yaml
    try:
        sources_path = get_sources_yaml_path()
    except FileNotFoundError as e:
        console.print(f"[red]錯誤: {e}[/red]")
        raise typer.Exit(1)

    if not add_to_sources_yaml(sources_path, name, repo_path, local_path, branch, format):
        raise typer.Exit(1)

    console.print()
    console.print("[bold green]✓ 完成！[/bold green]")
    console.print()
    console.print("[dim]下一步：[/dim]")
    console.print(f"[dim]  1. 分析 repo: python skills/custom-skills-upstream-sync/scripts/analyze_upstream.py --new-repo {target_dir}[/dim]")
    console.print(f"[dim]  2. AI 評估: /upstream-compare --new-repo[/dim]")

    # 可選：執行分析
    if analyze and target_dir.exists():
        console.print()
        console.print("[cyan]正在執行分析...[/cyan]")
        # 找到分析腳本
        script_path = sources_path.parent.parent / "skills" / "custom-skills-upstream-sync" / "scripts" / "analyze_upstream.py"
        if script_path.exists():
            subprocess.run(
                ["python", str(script_path), "--new-repo", str(target_dir)],
                check=False,
            )
