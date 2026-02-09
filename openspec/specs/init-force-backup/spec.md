# init-force-backup Specification

## Purpose
init --force 執行時的差異檔案備份機制，在覆蓋前精準備份有差異的檔案到專案根目錄。

## Requirements

### Requirement: 差異檔案收集 (Diff File Collection)

系統 SHALL 提供 `_collect_diff_files(src_dir, dst_dir)` 函式，遞迴比對兩個目錄並回傳需要備份的檔案清單。

#### Scenario: 目標有但模板沒有的檔案

- **WHEN** 目標目錄包含 `workflows/deploy.yml` 但模板目錄不包含此檔案
- **THEN** 該檔案 MUST 被列入備份清單

#### Scenario: 兩邊都有但內容不同的檔案

- **WHEN** 目標目錄和模板目錄都包含 `workflows/claude.yml` 但內容不同
- **THEN** 目標版本的檔案 MUST 被列入備份清單

#### Scenario: 兩邊都有且內容相同的檔案

- **WHEN** 目標目錄和模板目錄都包含 `workflows/claude.yml` 且內容相同
- **THEN** 該檔案 MUST NOT 被列入備份清單

#### Scenario: 目標有但模板沒有的子目錄

- **WHEN** 目標目錄包含子目錄 `workflows/custom/` 但模板目錄不包含此子目錄
- **THEN** 該子目錄及其所有內容 MUST 被遞迴列入備份清單

### Requirement: 備份目錄結構 (Backup Directory Structure)

備份 SHALL 存放在目標專案根目錄的 `_backup_after_init_force/<YYYYMMDD_HHMMSS>/` 下，保留原始的相對路徑結構。

#### Scenario: 備份目錄命名

- **WHEN** 執行 init --force 且有檔案需要備份
- **THEN** 系統 MUST 在目標專案根目錄建立 `_backup_after_init_force/<timestamp>/` 目錄，timestamp 格式為 `YYYYMMDD_HHMMSS`

#### Scenario: 保留相對路徑

- **WHEN** 備份 `.github/workflows/deploy.yml`
- **THEN** 備份檔案路徑 MUST 為 `_backup_after_init_force/<timestamp>/.github/workflows/deploy.yml`

#### Scenario: 多次 force 不互相覆蓋

- **WHEN** 連續執行兩次 init --force
- **THEN** 每次 MUST 使用不同的 timestamp 子目錄，前次備份不受影響

### Requirement: 備份觸發條件 (Backup Trigger Conditions)

備份 SHALL 僅在正向 init --force 流程中觸發，且僅在有差異檔案時才建立備份目錄。

#### Scenario: 正向 init --force 時觸發

- **WHEN** 在一般專案中執行 `ai-dev project init --force` 且目標目錄存在需覆蓋的內容
- **THEN** 系統 MUST 在覆蓋前執行差異比對和備份

#### Scenario: 反向同步不觸發

- **WHEN** 在 custom-skills 專案中執行 `ai-dev project init --force`（反向同步模式）
- **THEN** 系統 MUST NOT 執行備份邏輯

#### Scenario: 非 force 模式不觸發

- **WHEN** 執行 `ai-dev project init`（不帶 --force）
- **THEN** 系統 MUST NOT 執行備份邏輯（因為已存在的檔案會被跳過）

#### Scenario: 無差異時不建立備份目錄

- **WHEN** 執行 init --force 但所有目標檔案與模板完全相同
- **THEN** 系統 MUST NOT 建立 `_backup_after_init_force/` 目錄

### Requirement: 備份摘要顯示 (Backup Summary Display)

系統 SHALL 在備份完成後顯示摘要資訊。

#### Scenario: 有檔案被備份時顯示摘要

- **WHEN** init --force 過程中有檔案被備份
- **THEN** 系統 MUST 顯示備份目錄路徑和被備份的檔案清單

#### Scenario: 無檔案需要備份時不顯示

- **WHEN** init --force 過程中無檔案需要備份
- **THEN** 系統 MUST NOT 顯示備份相關訊息

### Requirement: 單一檔案備份 (Single File Backup)

對於模板中的單一檔案（非目錄）覆蓋，系統 SHALL 同樣執行差異比對和備份。

#### Scenario: 檔案內容不同時備份

- **WHEN** init --force 要覆蓋的單一檔案（如 `CLAUDE.md`）與模板版本內容不同
- **THEN** 系統 MUST 備份目標版本到 `_backup_after_init_force/<timestamp>/CLAUDE.md`

#### Scenario: 檔案內容相同時不備份

- **WHEN** init --force 要覆蓋的單一檔案與模板版本內容相同
- **THEN** 系統 MUST NOT 備份該檔案

### Requirement: Gitignore 排除 (Gitignore Exclusion)

`project-template/.gitignore` SHALL 包含 `_backup_after_init_force/` 排除規則。

#### Scenario: gitignore 包含備份目錄排除

- **WHEN** 使用者透過 init 初始化專案
- **THEN** 專案的 `.gitignore` MUST 包含 `_backup_after_init_force/` 條目
