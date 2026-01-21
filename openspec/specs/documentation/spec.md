# documentation Specification

## Purpose
TBD - created by archiving change add-ai-setup-script. Update Purpose after archive.
## Requirements
### Requirement: Dependency Management (依賴管理)
專案 MUST (必須) 使用 `uv` 與 `pyproject.toml` 進行依賴管理。

#### 場景：專案定義
給定 `script/pyproject.toml`
它應該定義諸如 `typer`、`rich` 等依賴。
並且應該支援 `requires-python`。

### Requirement: Usage Documentation (使用說明文件)
`script/README.md` MUST (必須) 提供關於如何使用腳本的清晰說明。

#### 場景：README 內容
當使用者閱讀 README 時
則它應該說明：
1. 如何安裝 CLI 工具（透過 `uv tool install` 或 `pipx`）。
2. 如何執行安裝 (`ai-dev install`)。
3. 如何執行更新 (`ai-dev update`)。

