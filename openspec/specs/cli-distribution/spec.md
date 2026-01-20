# cli-distribution Specification

## Purpose
TBD - created by archiving change add-global-cli-distribution. Update Purpose after archive.
## Requirements
### Requirement: Entry Point Configuration (進入點配置)

CLI 工具 MUST (必須) 透過 `pyproject.toml` 配置 entry point，使其可透過標準 Python 工具鏈安裝。

#### Scenario: pyproject.toml 配置 entry point

給定 `pyproject.toml` 檔案
當配置 `[project.scripts]` 區段時
則應該包含：
```toml
[project.scripts]
ai-dev = "script.main:app"
```
使得安裝後可執行 `ai-dev` 命令。

#### Scenario: 使用 uv tool install 安裝

給定已配置 entry point 的專案
當執行 `uv tool install .` 於專案目錄時
則應該：
1. 安裝 CLI 到使用者的 tool 環境
2. `ai-dev` 命令可在任意目錄下執行
3. 所有子命令（`install`、`maintain`、`project` 等）皆可使用

#### Scenario: 使用 pipx install 安裝

給定已配置 entry point 的專案
當執行 `pipx install .` 於專案目錄時
則應該：
1. 安裝 CLI 到隔離的虛擬環境
2. `ai-dev` 命令可在任意目錄下執行

#### Scenario: 從 GitHub 私有倉庫安裝

給定 GitHub 私有倉庫已配置正確的 entry point
當執行 `uv tool install git+https://github.com/ValorVie/custom-skills.git` 時
則應該：
1. 從 GitHub 下載並安裝套件
2. `ai-dev` 命令可在任意目錄下執行
3. 所有子命令皆可使用

#### Scenario: 使用 token 安裝私有倉庫

給定使用者沒有 GitHub SSH 金鑰設定
當執行 `uv tool install git+https://<TOKEN>@github.com/ValorVie/custom-skills.git` 時
則應該透過 Personal Access Token 驗證並完成安裝

### Requirement: Package Metadata (套件元資料)

`pyproject.toml` MUST (必須) 包含完整的套件元資料以支援發布。

#### Scenario: 必要元資料欄位

給定 `pyproject.toml` 檔案
則應該包含：
- `name`：套件名稱（建議 `ai-dev-cli` 或 `custom-skills-cli`）
- `version`：語意化版本號
- `description`：簡短描述
- `authors`：作者資訊
- `license`：授權條款
- `readme`：README 檔案路徑
- `requires-python`：Python 版本需求

### Requirement: Dependency Declaration (依賴宣告)

`pyproject.toml` MUST (必須) 宣告所有執行時期依賴。

#### Scenario: 核心依賴

給定 `pyproject.toml` 的 `[project.dependencies]` 區段
則應該包含：
- `typer>=0.9.0`：CLI 框架
- `rich>=13.0.0`：終端機美化輸出
- `pyyaml>=6.0.0`：YAML 解析
- `textual>=0.89.0`：TUI 框架

