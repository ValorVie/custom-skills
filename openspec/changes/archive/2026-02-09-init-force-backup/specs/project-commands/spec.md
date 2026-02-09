## MODIFIED Requirements

### Requirement: Project Init Command (專案初始化指令)

`ai-dev project init` MUST (必須) 整合呼叫 openspec 和 uds 的初始化命令。

使用 `--force` 時，系統 SHALL 在覆蓋檔案前執行差異比對，並將有差異的檔案備份到 `_backup_after_init_force/<YYYYMMDD_HHMMSS>/`。

#### Scenario: 預設初始化流程

給定一個尚未初始化的專案目錄
當執行 `ai-dev project init` 時
則應該依序執行：
1. `uds init`（建立 `.standards/` 目錄）
2. `openspec init`（建立 `openspec/` 目錄）
並顯示每個步驟的執行結果。

#### Scenario: 強制初始化時備份差異檔案

- **WHEN** 執行 `ai-dev project init --force` 且目標專案已有自定義的 `.github/workflows/deploy.yml`
- **THEN** 系統 MUST 先將該檔案備份到 `_backup_after_init_force/<timestamp>/.github/workflows/deploy.yml`，再用模板覆蓋 `.github/` 目錄

#### Scenario: 強制初始化後顯示備份摘要

- **WHEN** init --force 過程中有檔案被備份
- **THEN** 系統 MUST 在初始化完成後顯示備份路徑和檔案清單
