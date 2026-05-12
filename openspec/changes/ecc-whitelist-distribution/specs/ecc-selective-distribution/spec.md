## MODIFIED Requirements

### Requirement: ECC 選擇性分發邏輯

`ai-dev clone` SHALL 根據 `upstream/distribution.yaml` 的白名單從 ECC 來源目錄選擇性分發 skills 到各平台目標。commands 與 agents 維持原有黑名單邏輯。

#### Scenario: skills 採白名單分發

- **WHEN** 執行 `ai-dev clone` 且 ECC 來源目錄存在
- **THEN** SHALL 僅分發名稱出現在 `distribute.skills.enabled` 中的 skill 目錄
- **THEN** ECC 中其他未列入 `enabled` 的 skill 目錄 SHALL 不被分發
- **THEN** ECC 上游新增的 skill 預設 SHALL 不被分發（直到被加入 `enabled`）

#### Scenario: enabled 清單為空

- **WHEN** `distribute.skills.enabled` 為空陣列或不存在
- **THEN** SHALL 不分發任何 ECC skill
- **THEN** SHALL 不視為錯誤（明確的「全部停用」意圖）

#### Scenario: enabled 列出但 ECC 沒有

- **WHEN** `distribute.skills.enabled` 列出的名稱在 ECC 來源中不存在
- **THEN** SHALL 跳過該項目（不報錯）
- **THEN** SHALL 在 stderr 印出黃色警告：「enabled 中的 X 個 skill 在 ECC 中找不到，建議檢查名稱或執行 `ai-dev ecc audit`」

#### Scenario: Claude Code 平台完整分發

- **WHEN** 執行 `ai-dev clone` 且 `~/.config/everything-claude-code/` 存在
- **THEN** SHALL 分發符合白名單的 skills 到 `~/.claude/skills/`
- **THEN** SHALL 分發 commands 與 agents（依現有黑名單邏輯）

#### Scenario: 其他平台分發

- **WHEN** 執行 `ai-dev clone` 對 OpenCode / Gemini / Codex / Antigravity 平台
- **THEN** SHALL 依各平台 `targets` 設定，採白名單分發 skills
- **THEN** commands / agents 維持各平台既有邏輯（OpenCode 用 `.opencode/`、Gemini 不分發 commands、Codex 僅分發 skills 等）

#### Scenario: ECC 來源目錄不存在

- **WHEN** 執行 `ai-dev clone` 且 `~/.config/everything-claude-code/` 不存在
- **THEN** SHALL 跳過 ECC 分發
- **THEN** SHALL 顯示警告訊息提示先執行 `ai-dev update`

#### Scenario: 跳過 skip_directories 定義的目錄

- **WHEN** 分發 ECC skills 時遇到 `skip_directories` 中定義的目錄名
- **THEN** SHALL 不複製該目錄及其內容（即使該名稱出現在 `enabled` 中）

### Requirement: distribution.yaml 設定檔格式

系統 SHALL 支援 `upstream/distribution.yaml` 設定檔，定義 ECC 的白名單分發規則。

#### Scenario: 基本結構

- **WHEN** 讀取 `upstream/distribution.yaml`
- **THEN** SHALL 包含以下頂層欄位：`version`（整數）、`source`（來源名稱）、`source_path`（本地路徑）、`distribute`（分發規則）、`skip_directories`（跳過目錄）、`exclude`（commands / agents 排除清單）

#### Scenario: distribute.skills 區塊

- **WHEN** 解析 `distribute.skills` 區塊
- **THEN** SHALL 包含 `source_path`、`targets`、`enabled` 三個欄位
- **THEN** `enabled` SHALL 為字串陣列，每個元素是 ECC skill 目錄名稱

#### Scenario: distribute.commands 與 distribute.agents 區塊

- **WHEN** 解析 `distribute.commands` 或 `distribute.agents`
- **THEN** SHALL 支援按平台定義不同的 `source_path`
- **THEN** SHALL 不包含 `enabled` 欄位（commands / agents 維持黑名單）

#### Scenario: source_path 展開

- **WHEN** `source_path` 包含 `~`
- **THEN** SHALL 展開為使用者家目錄的絕對路徑

### Requirement: ECC 分發 Manifest 追蹤

ECC 分發的檔案 SHALL 納入現有 ManifestTracker 系統追蹤，支援衝突偵測和孤兒清理。

#### Scenario: 記錄分發檔案 hash

- **WHEN** ECC 檔案被分發到目標平台
- **THEN** ManifestTracker SHALL 記錄檔案路徑和 hash 值
- **THEN** source 欄位 SHALL 標記為 `ecc`

#### Scenario: 偵測衝突

- **WHEN** ECC 分發的檔案與 custom-skills 或 custom repo 的檔案同名
- **THEN** SHALL 按衝突處理策略處理（force/skip/backup/interactive）

#### Scenario: 從白名單移除 skill 後的孤兒清理

- **WHEN** 使用者從 `distribute.skills.enabled` 移除某個 skill
- **THEN** 下次 clone 時 ManifestTracker SHALL 偵測到該 skill 在目標目錄為孤兒並清理
- **THEN** 不影響其他 skill 或非 ECC 來源的檔案

#### Scenario: ECC 上游移除 skill 時的孤兒清理

- **WHEN** ECC 上游移除了某個 skill
- **THEN** 下次 clone 時 ManifestTracker SHALL 偵測孤兒並清理（與既有行為一致）

### Requirement: commands 與 agents 排除清單

`exclude.commands.<target>` 與 `exclude.agents.<target>` SHALL 繼續支援按平台排除特定項目。

#### Scenario: 排除特定平台的 command

- **WHEN** `exclude.commands.claude` 包含 `["example-cmd"]`
- **THEN** Claude Code 平台 SHALL 不分發名為 `example-cmd` 的 command
- **THEN** 其他平台不受影響

#### Scenario: 空排除清單

- **WHEN** `exclude.commands.<target>` 或 `exclude.agents.<target>` 為空陣列
- **THEN** SHALL 分發該平台該類型的所有資源（無排除）

## REMOVED Requirements

### Requirement: exclude.skills 黑名單

**Reason:** 已被白名單機制 `distribute.skills.enabled` 取代。黑名單導致 ECC 上游新增 skill 預設被動分發，與「可控性優先」目標衝突。

**Migration:** 既有 `exclude.skills` 不再被讀取。改採白名單後，使用者需在 `distribute.skills.enabled` 顯式列出要分發的 skill 名稱。初始遷移時將目前實際被分發的 133 個 skill 全部加入 `enabled` 以保持行為兼容。

### Requirement: ecc-profile.yaml 使用者層級覆寫

**Reason:** 白名單已在 repo 內可直接編輯，跨機器需求由 git branch / fork 處理。user-level include_skills / exclude_skills 是黑名單時代的補丁，白名單化後冗餘。

**Migration:** `_load_distribution_config()` 移除 `ecc-profile.yaml` 合併邏輯。若使用者本機有 `~/.config/ai-dev/ecc-profile.yaml`，SHALL 印出一次性警告告知該檔案已不再生效，建議改為直接編輯 `upstream/distribution.yaml`。檔案本身不主動刪除。
