# 提案：ai-dev 自動安裝 Codex CLI

## 背景與動機

OpenAI Codex CLI 是官方推薦的 AI 開發工具之一。根據最新文件，Codex 的安裝方式已從 `npm install -g @openai/codex` 變更為 `bun install -g @openai/codex`。

為了提供統一的開發環境設定體驗，ai-dev 應該在 `install` 和 `update` 指令中自動處理 Codex 的安裝與更新，類似於目前處理其他 NPM 套件的方式。

## 目標

1. 在 `ai-dev install` 時自動安裝 Codex CLI（如果尚未安裝）
2. 在 `ai-dev update` 時自動更新 Codex CLI
3. 檢查並提示 Bun 的安裝狀態（類似 Claude Code 的處理方式）
4. 維持向後相容，允許使用者透過 `--skip-bun` 跳過 Bun 套件安裝

## 非目標

- 不自動安裝 Bun（僅提供安裝指引，類似 Claude Code 的處理方式）
- 不改變現有的 NPM 套件安裝邏輯
- 不處理 Codex 的設定或配置（僅安裝套件本身）

## 預期行為

### Install 流程

```
$ ai-dev install

[bold blue]開始安裝...[/bold blue]
...
[green]正在檢查 Bun...[/green]
✓ Bun 已安裝 (v1.x.x)

[green]正在安裝 Bun 套件...[/green]
[bold cyan][1/1][/bold cyan] 正在安裝 @openai/codex...
...
```

### Bun 未安裝時的提示

```
[green]正在檢查 Bun...[/green]
[yellow]⚠️  未檢測到 Bun。[/yellow]

Codex CLI 需要 Bun 才能安裝。請選擇以下方式之一安裝：

**macOS / Linux：**
  curl -fsSL https://bun.sh/install | bash

**Windows (PowerShell)：**
  powershell -c "irm bun.sh/install.ps1 | iex"

安裝完成後，請重新執行 `ai-dev install`

[yellow]跳過 Codex 安裝[/yellow]
```

### Update 流程

```
$ ai-dev update

[bold blue]開始更新...[/bold blue]
...
[green]正在更新 Bun 套件...[/green]
[bold cyan][1/1][/bold cyan] 正在更新 @openai/codex...
...
```

## 實作方案

### 1. 新增配置常數

在 `script/utils/shared.py` 中新增：

```python
BUN_PACKAGES = [
    "@openai/codex",
]
```

### 2. 新增 Bun 檢查函式

在 `script/utils/system.py` 中新增：

```python
def check_bun_installed() -> bool:
    """檢查 Bun 是否已安裝。"""
    return check_command_exists("bun")

def get_bun_version() -> str | None:
    """取得 Bun 版本號。"""
    try:
        result = subprocess.run(
            ["bun", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None

def get_bun_package_version(package: str) -> str | None:
    """檢查 Bun 全域套件是否已安裝，並回傳版本號。"""
    try:
        result = subprocess.run(
            ["bun", "pm", "ls", "-g"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # 解析輸出找尋套件版本
            for line in result.stdout.split("\n"):
                if package in line:
                    # 解析版本號邏輯...
                    return version
    except Exception:
        pass
    return None
```

### 3. 修改 install.py

新增 `--skip-bun` 參數和相關邏輯：

```python
@app.command()
def install(
    skip_npm: bool = typer.Option(False, "--skip-npm", help="跳過 NPM 套件安裝"),
    skip_bun: bool = typer.Option(False, "--skip-bun", help="跳過 Bun 套件安裝"),  # 新增
    # ... 其他參數
):
    # ... 現有邏輯 ...
    
    # 新增：安裝 Bun 套件
    if skip_bun:
        console.print("[yellow]跳過 Bun 套件安裝[/yellow]")
    else:
        console.print("[green]正在檢查 Bun...[/green]")
        if not check_bun_installed():
            console.print("[yellow]⚠️  未檢測到 Bun。[/yellow]")
            console.print()
            console.print("Codex CLI 需要 Bun 才能安裝。請選擇以下方式之一安裝：")
            console.print()
            console.print("[bold]macOS / Linux：[/bold]")
            console.print("  curl -fsSL https://bun.sh/install | bash")
            console.print()
            console.print("[bold]Windows (PowerShell)：[/bold]")
            console.print('  powershell -c "irm bun.sh/install.ps1 | iex"')
            console.print()
            console.print("安裝完成後，請重新執行 `ai-dev install`")
            console.print()
            console.print("[yellow]跳過 Codex 安裝[/yellow]")
        else:
            bun_version = get_bun_version()
            console.print(f"[dim]✓ Bun 已安裝 ({bun_version})[/dim]")
            console.print("[green]正在安裝 Bun 套件...[/green]")
            total = len(BUN_PACKAGES)
            for i, package in enumerate(BUN_PACKAGES, 1):
                existing_version = get_bun_package_version(package)
                if existing_version:
                    console.print(
                        f"[bold cyan][{i}/{total}][/bold cyan] {package} "
                        f"[dim](已安裝 v{existing_version}，檢查更新...)[/dim]"
                    )
                else:
                    console.print(f"[bold cyan][{i}/{total}] 正在安裝 {package}...[/bold cyan]")
                run_command(["bun", "install", "-g", package])
```

### 4. 修改 update.py

```python
@app.command()
def update(
    skip_npm: bool = typer.Option(False, "--skip-npm", help="跳過 NPM 套件更新"),
    skip_bun: bool = typer.Option(False, "--skip-bun", help="跳過 Bun 套件更新"),  # 新增
    # ... 其他參數
):
    # ... 現有邏輯 ...
    
    # 新增：更新 Bun 套件
    if skip_bun:
        console.print("[yellow]跳過 Bun 套件更新[/yellow]")
    else:
        console.print("[green]正在更新 Bun 套件...[/green]")
        if check_bun_installed():
            total = len(BUN_PACKAGES)
            for i, package in enumerate(BUN_PACKAGES, 1):
                console.print(f"[bold cyan][{i}/{total}] 正在更新 {package}...[/bold cyan]")
                run_command(["bun", "install", "-g", package])
        else:
            console.print("[yellow]⚠️  Bun 未安裝，跳過 Bun 套件更新[/yellow]")
```

## 相依性

- Bun 必須由使用者手動安裝（我們只提供指引）
- 所有現有的 NPM 套件安裝邏輯保持不變

## 風險與緩解措施

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| Bun 未安裝 | 中 | 提供清晰的安裝指引，不強制中斷流程 |
| Bun 指令不存在 | 低 | 使用 `check_command_exists` 預先檢查 |
| 與現有 Codex 安裝衝突 | 低 | Bun 會覆蓋/更新現有安裝，行為與 npm 類似 |
| 網路問題導致安裝失敗 | 低 | 使用現有的 `run_command` 錯誤處理 |

## 測試策略

1. **單元測試**：測試 Bun 檢查函式的各種回傳值
2. **整合測試**：
   - 測試 `ai-dev install` 在 Bun 已安裝/未安裝時的行為
   - 測試 `ai-dev update` 的更新流程
   - 測試 `--skip-bun` 參數

## 文件更新

- 更新 `README.md` 中的安裝說明
- 更新 `docs/AI開發環境設定指南.md` 中的 Codex 章節
- 更新 `ai-dev install --help` 和 `ai-dev update --help` 輸出

## 驗收標準

- [ ] `ai-dev install` 會檢查 Bun 並在安裝時自動安裝 Codex
- [ ] `ai-dev update` 會自動更新 Codex
- [ ] Bun 未安裝時顯示清晰的安裝指引
- [ ] `--skip-bun` 參數可以正確跳過 Bun 套件安裝
- [ ] 現有的 NPM 套件安裝不受影響
- [ ] 文件已更新

## 預估工作量

- 實作：2-3 小時
- 測試：1-2 小時
- 文件更新：30 分鐘
- **總計：約 4-6 小時**
