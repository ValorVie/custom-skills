import typer
from rich.console import Console
from utils.system import run_command, check_command_exists
from utils.paths import (
    get_config_dir,
    get_custom_skills_dir,
    get_claude_config_dir,
    get_antigravity_config_dir,
    get_opencode_config_dir,
    get_superpowers_dir,
    get_uds_dir,
    get_project_root,
)
import shutil


app = typer.Typer()
console = Console()


@app.command()
def install():
    """首次安裝 AI 開發環境。"""
    console.print("[bold blue]開始安裝...[/bold blue]")

    # 1. 檢查前置需求
    if not check_command_exists("node"):
        console.print("[bold red]找不到 Node.js，請先安裝 Node.js。[/bold red]")
        raise typer.Exit(code=1)

    if not check_command_exists("git"):
        console.print("[bold red]找不到 Git，請先安裝 Git。[/bold red]")
        raise typer.Exit(code=1)

    # 2. 安裝全域 NPM 套件
    console.print("[green]正在安裝全域 NPM 套件...[/green]")
    npm_packages = [
        "@anthropic-ai/claude-code",
        "@fission-ai/openspec@latest",
        "@google/gemini-cli",
        "universal-dev-standards",
        "opencode-ai@latest",
    ]
    total = len(npm_packages)
    for i, package in enumerate(npm_packages, 1):
        console.print(f"[bold cyan][{i}/{total}] 正在安裝 {package}...[/bold cyan]")
        run_command(["npm", "install", "-g", package])

    # 3. 建立目錄
    console.print("[green]正在建立目錄...[/green]")
    dirs = [
        get_config_dir(),
        get_custom_skills_dir(),
        get_superpowers_dir(),
        get_uds_dir(),
        get_claude_config_dir() / "skills",
        get_claude_config_dir() / "commands",
        get_antigravity_config_dir() / "skills",
        get_antigravity_config_dir() / "global_workflows",
        get_opencode_config_dir() / "agent",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # 4. Clone 儲存庫
    console.print("[green]正在 Clone 儲存庫...[/green]")

    repos = {
        get_custom_skills_dir(): "https://github.com/ValorVie/custom-skills.git",
        get_superpowers_dir(): "https://github.com/obra/superpowers.git",
        get_uds_dir(): "https://github.com/AsiaOstrich/universal-dev-standards.git",
    }

    for path, url in repos.items():
        if not (path / ".git").exists():
            console.print(f"正在 Clone {url} 到 {path}...")
            run_command(["git", "clone", url, str(path)])
        else:
            console.print(f"{path} 已存在，跳過 Clone。")

    # 5. 複製 Skills 與設定
    console.print("[green]正在複製 Skills 與設定...[/green]")
    copy_skills()

    console.print("[bold green]安裝完成！[/bold green]")


def copy_skills():
    """複製 Skills 從來源到目標目錄。"""
    # 邏輯改編自指南的腳本

    # Universal Dev Standards 到 Custom Skills (統一)
    src_uds_claude = get_uds_dir() / "skills" / "claude-code"
    dst_custom_skills = get_custom_skills_dir() / "skills"

    if src_uds_claude.exists():
        console.print(f"正在複製從 {src_uds_claude} 到 {dst_custom_skills}...")
        if dst_custom_skills.exists():
            shutil.rmtree(dst_custom_skills)
        shutil.copytree(src_uds_claude, dst_custom_skills)

    # 清理 Custom Skills 中不需要的 UDS 檔案
    unwanted = [
        "tdd-assistant",
        "CONTRIBUTING.template.md",
        "install.ps1",
        "install.sh",
        "README.md",
    ]
    for item in unwanted:
        path = dst_custom_skills / item
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

    # 複製到 Claude Code
    dst_claude_skills = get_claude_config_dir() / "skills"
    if src_uds_claude.exists():
        console.print(f"正在複製從 {src_uds_claude} 到 {dst_claude_skills}...")
        if dst_claude_skills.exists():
            shutil.rmtree(dst_claude_skills)
        shutil.copytree(src_uds_claude, dst_claude_skills)

    # 清理 Claude 中不需要的 UDS 檔案
    for item in unwanted:
        path = dst_claude_skills / item
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

    # 複製 Custom Skills (統一) 到 Antigravity
    src_custom_skills = get_custom_skills_dir() / "skills"
    dst_antigravity_skills = get_antigravity_config_dir() / "skills"

    if src_custom_skills.exists():
        console.print(f"正在複製從 {src_custom_skills} 到 {dst_antigravity_skills}...")
        if dst_antigravity_skills.exists():
            shutil.rmtree(dst_antigravity_skills)
        shutil.copytree(src_custom_skills, dst_antigravity_skills)

    # 複製 Commands
    src_cmd_claude = get_custom_skills_dir() / "command" / "claude"
    dst_cmd_claude = get_claude_config_dir() / "commands"
    if src_cmd_claude.exists():
        console.print(f"正在複製 Commands 到 {dst_cmd_claude}...")
        # 複製內容而非取代目錄，以免遺失使用者自行新增的指令
        if dst_cmd_claude.exists():
            shutil.copytree(src_cmd_claude, dst_cmd_claude, dirs_exist_ok=True)

    src_cmd_antigravity = get_custom_skills_dir() / "command" / "antigravity"
    dst_cmd_antigravity = get_antigravity_config_dir() / "global_workflows"
    if src_cmd_antigravity.exists():
        console.print(f"正在複製 Workflows 到 {dst_cmd_antigravity}...")
        shutil.copytree(src_cmd_antigravity, dst_cmd_antigravity, dirs_exist_ok=True)

    # 複製 Agents
    src_agent_opencode = get_custom_skills_dir() / "agent" / "opencode"
    dst_agent_opencode = get_opencode_config_dir() / "agent"
    if src_agent_opencode.exists():
        console.print(f"正在複製 Agents 到 {dst_agent_opencode}...")
        shutil.copytree(src_agent_opencode, dst_agent_opencode, dirs_exist_ok=True)

    # 複製到目前專案 (如果是在開發環境執行)
    project_root = get_project_root()
    # 簡單判斷：如果看到 .git 和 pyproject.toml
    if (project_root / ".git").exists() and (project_root / "pyproject.toml").exists():
        console.print(f"[bold yellow]偵測到專案目錄：{project_root}[/bold yellow]")

        # 1. UDS -> Project/skills
        dst_project_skills = project_root / "skills"
        if src_uds_claude.exists():
            console.print(f"正在複製從 {src_uds_claude} 到 {dst_project_skills}...")
            # 這裡覆蓋使用者 local 的 skills 修改，以確保更新資料
            if dst_project_skills.exists():
                shutil.rmtree(dst_project_skills)
            shutil.copytree(src_uds_claude, dst_project_skills)

        # 清理 Project/skills 中不需要的檔案
        unwanted = [
            "tdd-assistant",
            "CONTRIBUTING.template.md",
            "install.ps1",
            "install.sh",
            "README.md",
        ]
        for item in unwanted:
            path = dst_project_skills / item
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
        # 2. Config -> Project/command
        src_msg_command = get_custom_skills_dir() / "command"
        dst_project_command = project_root / "command"
        if src_msg_command.exists():
            console.print(f"正在複製從 {src_msg_command} 到 {dst_project_command}...")
            # 使用 dirs_exist_ok=True 來合併/更新
            shutil.copytree(src_msg_command, dst_project_command, dirs_exist_ok=True)

        # 3. Config -> Project/agent
        src_msg_agent = get_custom_skills_dir() / "agent"
        dst_project_agent = project_root / "agent"
        if src_msg_agent.exists():
            console.print(f"正在複製從 {src_msg_agent} 到 {dst_project_agent}...")
            shutil.copytree(src_msg_agent, dst_project_agent, dirs_exist_ok=True)
