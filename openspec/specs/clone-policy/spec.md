# clone-policy Specification

## Purpose
TBD

## Requirements

### Requirement: .clonepolicy.json 配置格式

Skill 目錄 MAY 包含 `.clonepolicy.json` 檔案，宣告檔案層級的複製策略。系統 SHALL 支援以下 JSON 格式：

```json
{
  "rules": [
    { "pattern": "<glob-pattern>", "strategy": "<strategy-name>" }
  ]
}
```

支援的 strategy：
- `key-merge`：JSON 按 key 合併
- `skip-if-exists`：目標存在則跳過

未匹配任何 rule 的檔案 SHALL 使用 default 策略（hash 比對 + 互動提示）。

#### Scenario: 合法的 .clonepolicy.json

- **WHEN** skill 目錄包含以下 `.clonepolicy.json`：
  ```json
  {
    "rules": [
      { "pattern": "*/_index.json", "strategy": "key-merge" },
      { "pattern": "knowledge-base/*.md", "strategy": "skip-if-exists" },
      { "pattern": "experience/*.md", "strategy": "skip-if-exists" }
    ]
  }
  ```
- **THEN** 系統 SHALL 解析並套用對應策略

#### Scenario: 無 .clonepolicy.json

- **WHEN** skill 目錄不包含 `.clonepolicy.json`
- **THEN** 系統 SHALL 使用原有的 `shutil.copytree` 複製邏輯，行為完全不變

#### Scenario: .clonepolicy.json 格式錯誤

- **WHEN** `.clonepolicy.json` 內容非合法 JSON 或缺少 `rules` 欄位
- **THEN** 系統 SHALL 顯示警告訊息
- **THEN** 系統 SHALL fallback 為原有的 copytree 複製邏輯

### Requirement: skip-if-exists 策略

當檔案匹配 `skip-if-exists` 策略時，系統 SHALL 在目標檔案已存在的情況下跳過複製。

#### Scenario: 目標檔案已存在

- **WHEN** 來源檔案匹配 `skip-if-exists` 規則
- **AND** 目標路徑已存在同名檔案
- **THEN** 系統 SHALL 跳過此檔案，不覆蓋目標內容

#### Scenario: 目標檔案不存在（首次 clone）

- **WHEN** 來源檔案匹配 `skip-if-exists` 規則
- **AND** 目標路徑不存在同名檔案
- **THEN** 系統 SHALL 複製來源檔案到目標路徑

### Requirement: key-merge 策略

當 JSON 檔案匹配 `key-merge` 策略時，系統 SHALL 合併來源與目標的 JSON 內容，以陣列元素的 identifier key 為合併依據。

#### Scenario: 來源有新條目、目標無

- **WHEN** 來源 `_index.json` 的 `categories` 陣列包含 id 為 `devops` 的條目
- **AND** 目標 `_index.json` 的 `categories` 陣列無 id 為 `devops` 的條目
- **THEN** 系統 SHALL 將 `devops` 條目新增到目標的 `categories` 陣列

#### Scenario: 目標有使用者修改的條目

- **WHEN** 目標 `_index.json` 的 `categories` 陣列包含 id 為 `workflow` 且 `count` 為 2 的條目
- **AND** 來源 `_index.json` 的同一條目 `count` 為 0
- **THEN** 系統 SHALL 保留目標的版本（`count` 為 2），不以來源覆蓋

#### Scenario: 陣列 key 偵測

- **WHEN** JSON 陣列中的物件包含 `id` 欄位
- **THEN** 系統 SHALL 以 `id` 為合併 key
- **WHEN** JSON 陣列中的物件包含 `skillId` 欄位（但無 `id`）
- **THEN** 系統 SHALL 以 `skillId` 為合併 key

#### Scenario: 目標不存在（首次 clone）

- **WHEN** 目標 JSON 檔案不存在
- **THEN** 系統 SHALL 直接複製來源檔案

#### Scenario: 目標 JSON 解析失敗

- **WHEN** 目標 JSON 檔案存在但非合法 JSON
- **THEN** 系統 SHALL 顯示警告
- **THEN** 系統 SHALL 跳過此檔案，不覆蓋損壞的目標

### Requirement: Default 策略（hash 比對 + 互動提示）

未匹配任何 rule 的檔案 SHALL 使用 default 策略：比對來源與目標的 hash，若不同則互動提示使用者。

#### Scenario: 來源與目標相同

- **WHEN** 來源檔案的 SHA-256 hash 與目標檔案相同
- **THEN** 系統 SHALL 跳過此檔案（已是最新）

#### Scenario: 來源與目標不同

- **WHEN** 來源檔案的 SHA-256 hash 與目標檔案不同
- **THEN** 系統 SHALL 顯示檔案名稱與變更提示
- **THEN** 系統 SHALL 提供選項：覆蓋 / 跳過 / 備份後覆蓋 / 查看差異

#### Scenario: 目標不存在

- **WHEN** 目標檔案不存在
- **THEN** 系統 SHALL 直接複製來源檔案，不需提示

#### Scenario: --force flag

- **WHEN** 使用者執行 clone 時帶有 `--force` flag
- **AND** 來源與目標 hash 不同
- **THEN** 系統 SHALL 直接覆蓋，不互動提示

#### Scenario: --skip-conflicts flag

- **WHEN** 使用者執行 clone 時帶有 `--skip-conflicts` flag
- **AND** 來源與目標 hash 不同
- **THEN** 系統 SHALL 跳過此檔案，不互動提示

### Requirement: .clonepolicy.json 不複製到目標

`.clonepolicy.json` 檔案 SHALL NOT 被複製到目標目錄。

#### Scenario: 排除 .clonepolicy.json

- **WHEN** 系統逐檔複製 skill 目錄內容
- **THEN** `.clonepolicy.json` SHALL 被自動排除，不出現在目標目錄
