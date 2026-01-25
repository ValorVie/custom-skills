# Spec Delta: standards-profiles (Phase 3)

## Purpose

擴展 `standards-profiles` 規格，新增動態 Profile 載入功能，讓切換 Profile 時實際改變 `.standards/` 中的標準內容。

---

## ADDED Requirements

### Requirement: 標準檔案庫管理

系統 SHALL 在 `profiles/standards/` 目錄中維護各 Profile 的標準檔案庫。

#### Scenario: 標準檔案庫目錄結構

- **GIVEN** 專案已初始化 Profile 系統
- **THEN** 存在 `profiles/standards/` 目錄
- **AND** 存在 `profiles/standards/uds/` 子目錄（UDS 專屬標準）
- **AND** 存在 `profiles/standards/ecc/` 子目錄（ECC 專屬標準）
- **AND** 存在 `profiles/standards/minimal/` 子目錄（Minimal 專屬標準）
- **AND** 存在 `profiles/standards/shared/` 子目錄（共用標準，可選）

#### Scenario: UDS 標準檔案庫內容

- **GIVEN** `profiles/standards/uds/` 目錄
- **THEN** 包含 `profiles/uds.yaml` 的 `includes` 清單中所有檔案
- **AND** 至少包含 10 個標準檔案

#### Scenario: Minimal 標準檔案庫內容

- **GIVEN** `profiles/standards/minimal/` 目錄
- **THEN** 包含 `profiles/minimal.yaml` 的 `includes` 清單中所有檔案
- **AND** 僅包含 3-5 個核心標準檔案

#### Scenario: ECC 標準檔案庫內容

- **GIVEN** `profiles/standards/ecc/` 目錄
- **THEN** 包含 ECC 專屬版本的標準檔案
- **AND** `commit-message.ai.yaml` 為 ECC 版本（使用英文類型）

### Requirement: 動態 Profile 啟用

系統 SHALL 提供 `activate_profile()` 函式，實際複製標準檔案到 `.standards/` 目錄。

#### Scenario: 啟用 UDS Profile

- **GIVEN** 使用者執行 `ai-dev standards switch uds`
- **WHEN** 系統呼叫 `activate_profile("uds")`
- **THEN** 清除 `.standards/` 中由 Profile 管理的舊檔案
- **AND** 從 `profiles/standards/uds/` 複製標準檔案到 `.standards/`
- **AND** 更新 `profiles/active.yaml` 的 `active` 欄位為 `uds`
- **AND** 更新 `profiles/active.yaml` 的 `managed_files` 清單
- **AND** `.standards/` 包含 UDS 的所有標準（10+ 個檔案）

#### Scenario: 啟用 Minimal Profile

- **GIVEN** 使用者執行 `ai-dev standards switch minimal`
- **WHEN** 系統呼叫 `activate_profile("minimal")`
- **THEN** 清除 `.standards/` 中由 Profile 管理的舊檔案
- **AND** 從 `profiles/standards/minimal/` 複製標準檔案到 `.standards/`
- **AND** `.standards/` 僅包含 Minimal 的核心標準（3-5 個檔案）

#### Scenario: 啟用 ECC Profile（含繼承）

- **GIVEN** 使用者執行 `ai-dev standards switch ecc`
- **AND** `profiles/ecc.yaml` 定義 `inherits: minimal`
- **WHEN** 系統呼叫 `activate_profile("ecc")`
- **THEN** 解析繼承關係，合併 minimal 與 ecc 的 `includes`
- **AND** 優先使用 ECC 專屬版本的標準檔案
- **AND** 套用 `overrides` 覆寫設定
- **AND** `.standards/commit-message.ai.yaml` 為 ECC 版本（英文類型）

#### Scenario: 標準檔案來源解析優先順序

- **GIVEN** 啟用 Profile `X`，需要標準檔案 `foo.ai.yaml`
- **WHEN** 系統呼叫 `resolve_standard_source("X", "foo.ai.yaml")`
- **THEN** 優先查找 `profiles/standards/X/foo.ai.yaml`
- **AND** 若不存在，查找繼承的父 Profile 目錄
- **AND** 若不存在，查找 `profiles/standards/shared/foo.ai.yaml`
- **AND** 若都不存在，拋出 `FileNotFoundError`

### Requirement: 使用者自訂標準保護

系統 SHALL 保護使用者自訂的標準檔案，不在 Profile 切換時刪除。

#### Scenario: 保護非 managed 檔案

- **GIVEN** `.standards/` 中存在 `custom.ai.yaml`（使用者自訂）
- **AND** `profiles/active.yaml` 的 `managed_files` 不包含 `custom.ai.yaml`
- **WHEN** 使用者執行 `ai-dev standards switch minimal`
- **THEN** `custom.ai.yaml` 不被刪除
- **AND** 顯示警告「保留了 1 個使用者自訂檔案」

#### Scenario: 僅清除 managed 檔案

- **GIVEN** `profiles/active.yaml` 的 `managed_files` 為 `["a.yaml", "b.yaml"]`
- **AND** `.standards/` 包含 `a.yaml`, `b.yaml`, `user.yaml`
- **WHEN** 系統呼叫 `clear_managed_standards()`
- **THEN** 僅刪除 `a.yaml`, `b.yaml`
- **AND** `user.yaml` 保留

### Requirement: 標準同步功能

系統 SHALL 提供 `sync` 命令，重新同步當前 Profile 的標準檔案。

#### Scenario: 執行 sync 命令

- **GIVEN** 目前啟用的 Profile 為 `uds`
- **WHEN** 使用者執行 `ai-dev standards sync`
- **THEN** 系統呼叫 `activate_profile("uds")`
- **AND** 重新複製 UDS 的所有標準檔案到 `.standards/`
- **AND** 顯示「同步完成」訊息

#### Scenario: 無啟用 Profile 時執行 sync

- **GIVEN** `profiles/active.yaml` 的 `active` 欄位為空或不存在
- **WHEN** 使用者執行 `ai-dev standards sync`
- **THEN** 顯示警告「沒有啟用的 Profile」
- **AND** 建議執行 `ai-dev standards switch <profile>`

### Requirement: 狀態追蹤

系統 SHALL 在 `profiles/active.yaml` 中追蹤 Profile 啟用狀態。

#### Scenario: active.yaml 包含 managed_files

- **GIVEN** 執行 `activate_profile("uds")` 後
- **THEN** `profiles/active.yaml` 包含 `managed_files` 欄位
- **AND** `managed_files` 列出所有複製到 `.standards/` 的檔案名稱

#### Scenario: active.yaml 包含 last_activated

- **GIVEN** 執行 `activate_profile("uds")` 後
- **THEN** `profiles/active.yaml` 包含 `last_activated` 欄位
- **AND** `last_activated` 為 ISO 8601 格式的時間戳

---

## MODIFIED Requirements

### Requirement: 標準切換 CLI（更新）

系統 SHALL 更新 `switch` 命令，在切換 Profile 時觸發動態標準載入。

#### Scenario: switch 命令觸發動態載入

- **WHEN** 使用者執行 `ai-dev standards switch ecc`
- **THEN** 驗證 `profiles/ecc.yaml` 存在
- **AND** 呼叫 `activate_profile("ecc")`
- **AND** 顯示啟用結果（複製檔案數、移除檔案數、耗時）
- **AND** `.standards/` 實際發生變化

#### Scenario: status 命令顯示 managed_files 資訊

- **WHEN** 使用者執行 `ai-dev standards status`
- **THEN** 顯示目前啟用的 Profile
- **AND** 顯示 `managed_files` 的數量
- **AND** 顯示 `last_activated` 時間

---

## Notes

- 此 spec delta 建立在 `implement-profile-system` 的基礎上
- 動態載入使用檔案複製（非符號連結），確保跨平台相容
- `managed_files` 機制確保使用者自訂標準不被覆蓋
- `sync` 命令用於 UDS 更新後重新同步標準檔案

---

## Relationships

- **前置依賴**：`implement-profile-system`（Phase 2）
- **相關規格**：`tui-standards-profile`（TUI 需呼叫 `activate_profile()`）
