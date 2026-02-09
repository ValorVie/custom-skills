# project-commands Specification

## Purpose
TBD - created by archiving change add-global-cli-distribution. Update Purpose after archive.
## Requirements
### Requirement: Project Command Group (專案指令群組)

CLI MUST (必須) 提供 `project` 子命令群組，包含專案級別的操作。

#### Scenario: project 指令群組結構

給定 `ai-dev` CLI
當執行 `ai-dev project --help` 時
則應該顯示可用的子命令：
- `init`：初始化專案
- `update`：更新專案配置

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

#### Scenario: 選擇性初始化

給定 `ai-dev project init` 指令
當使用 `--only` 參數時
則應該只執行指定的工具：
- `ai-dev project init --only uds`：只執行 `uds init`
- `ai-dev project init --only openspec`：只執行 `openspec init`

#### Scenario: 工具未安裝時的錯誤處理

給定 openspec 或 uds 未安裝
當執行 `ai-dev project init` 時
則應該：
1. 顯示清楚的錯誤訊息，指出缺少哪個工具
2. 提供安裝指引（如 `npm install -g @fission-ai/openspec`）
3. 不執行任何初始化步驟（避免部分初始化）

#### Scenario: 已初始化的專案

給定專案已有 `openspec/` 或 `.standards/` 目錄
當執行 `ai-dev project init` 時
則應該：
1. 提示使用者該專案已部分或完全初始化
2. 詢問是否要重新初始化（或跳過已存在的部分）

### Requirement: Project Update Command (專案更新指令)

`ai-dev project update` MUST (必須) 整合呼叫 openspec 和 uds 的更新命令。

#### Scenario: 預設更新流程

給定一個已初始化的專案目錄
當執行 `ai-dev project update` 時
則應該依序執行：
1. `uds update`（更新 `.standards/` 配置）
2. `openspec update`（更新 `openspec/` 配置）
並顯示每個步驟的執行結果。

#### Scenario: 選擇性更新

給定 `ai-dev project update` 指令
當使用 `--only` 參數時
則應該只執行指定的工具：
- `ai-dev project update --only uds`：只執行 `uds update`
- `ai-dev project update --only openspec`：只執行 `openspec update`

#### Scenario: 未初始化的專案

給定專案尚未初始化（沒有 `openspec/` 和 `.standards/`）
當執行 `ai-dev project update` 時
則應該：
1. 顯示錯誤訊息，指出專案尚未初始化
2. 建議先執行 `ai-dev project init`

#### Scenario: 部分初始化的專案

給定專案只有 `.standards/` 但沒有 `openspec/`
當執行 `ai-dev project update` 時
則應該：
1. 只更新已存在的配置（`.standards/`）
2. 警告缺少 `openspec/` 目錄，建議執行 `openspec init`

### Requirement: Thin Wrapper Implementation (薄包裝實作)

專案指令 MUST (必須) 採用薄包裝模式，不重新實作底層邏輯。

#### Scenario: 使用 subprocess 呼叫底層工具

給定 `ai-dev project init` 或 `ai-dev project update` 執行時
則應該透過 `subprocess.run()` 呼叫底層命令：
```python
subprocess.run(["uds", "init"], check=True)
subprocess.run(["openspec", "init"], check=True)
```
而非重新實作 uds/openspec 的邏輯。

#### Scenario: 傳遞底層工具的輸出

給定底層工具產生輸出
當 `ai-dev project init` 或 `update` 執行時
則應該將底層工具的 stdout 和 stderr 即時顯示給使用者。

#### Scenario: 傳遞退出碼

給定底層工具執行失敗（非零退出碼）
當 `ai-dev project init` 或 `update` 執行時
則應該：
1. 顯示失敗的步驟
2. 停止執行後續步驟
3. 以非零退出碼結束

### Requirement: Current Directory Context (當前目錄上下文)

專案指令 MUST (必須) 在當前工作目錄執行，與底層工具行為一致。

#### Scenario: 在專案目錄執行

給定使用者位於專案根目錄
當執行 `ai-dev project init` 時
則應該在當前目錄建立配置，與直接執行 `uds init` + `openspec init` 的行為相同。

