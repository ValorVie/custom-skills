# status-upstream-sync Specification

## Purpose
TBD

## Requirements

### Requirement: 上游同步狀態表顯示

`ai-dev status` SHALL 在設定儲存庫表之後顯示「上游同步狀態」表，列出 `upstream/last-sync.yaml` 中所有追蹤的 repo 的同步狀態。

#### Scenario: 正常顯示同步狀態
- **WHEN** 使用者執行 `ai-dev status` 且 `upstream/last-sync.yaml` 存在
- **THEN** 系統 MUST 顯示一張「上游同步狀態」Rich Table，包含欄位：名稱、同步時間、狀態

#### Scenario: repo 已同步
- **WHEN** `last-sync.yaml` 記錄的 commit 等於對應 repo `~/.config/<name>/` 的 HEAD
- **THEN** 狀態欄顯示「✓ 同步」

#### Scenario: repo 落後
- **WHEN** `last-sync.yaml` 記錄的 commit 落後於對應 repo 的 HEAD
- **THEN** 狀態欄顯示「⚠ 落後 N」，其中 N 為落後的 commit 數量

#### Scenario: commit 無法比對
- **WHEN** `last-sync.yaml` 記錄的 commit 在本地 repo 中不存在（例如未 fetch）
- **THEN** 狀態欄顯示「? 無法比對」

#### Scenario: repo 目錄不存在
- **WHEN** `last-sync.yaml` 記錄了某 repo 但對應的本地目錄不存在
- **THEN** 狀態欄顯示「未安裝」

### Requirement: last-sync.yaml 不存在時的處理

`ai-dev status` SHALL 在 `upstream/last-sync.yaml` 不存在時優雅降級。

#### Scenario: yaml 檔案不存在
- **WHEN** `upstream/last-sync.yaml` 不存在
- **THEN** 不顯示「上游同步狀態」表，不產生錯誤

### Requirement: 同步時間顯示格式

同步時間 SHALL 以簡潔格式顯示。

#### Scenario: 顯示日期
- **WHEN** 渲染同步時間欄位
- **THEN** 格式為 MM-DD（例如 `01-26`、`02-02`）
