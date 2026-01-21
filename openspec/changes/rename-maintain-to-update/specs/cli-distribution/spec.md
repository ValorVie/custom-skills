# cli-distribution Spec Delta

## MODIFIED Requirements

### Requirement: Entry Point Configuration (進入點配置)

CLI 工具 MUST (必須) 透過 `pyproject.toml` 配置 entry point，使其可透過標準 Python 工具鏈安裝。

> **變更說明**：更新子命令列表，將 `maintain` 改為 `update`。

#### Scenario: 使用 uv tool install 安裝

給定已配置 entry point 的專案
當執行 `uv tool install .` 於專案目錄時
則應該：
1. 安裝 CLI 到使用者的 tool 環境
2. `ai-dev` 命令可在任意目錄下執行
3. 所有子命令（`install`、`update`、`project` 等）皆可使用
