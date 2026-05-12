## MODIFIED Requirements

### Requirement: ECC 選擇性分發邏輯

`ai-dev clone` SHALL 根據 `upstream/distribution.yaml` 的白名單與使用者層級 `~/.config/ai-dev/ecc-profile.yaml` 覆寫合併後的有效白名單，從 ECC 來源目錄選擇性分發 skills 到各平台目標。commands 與 agents 維持原有黑名單邏輯。

#### Scenario: skills 採合併後的白名單分發

- **WHEN** 執行 `ai-dev clone` 且 ECC 來源目錄存在
- **THEN** SHALL 計算有效白名單 `final_enabled = (repo.enabled ∪ user.enabled_extra) \ user.enabled_remove`
- **THEN** SHALL 僅分發名稱出現在 `final_enabled` 中的 skill 目錄
- **THEN** ECC 中其他未列入 `final_enabled` 的 skill 目錄 SHALL 不被分發
- **THEN** ECC 上游新增的 skill 預設 SHALL 不被分發（直到被加入 `repo.enabled` 或 `user.enabled_extra`）

#### Scenario: 合併後 enabled 為空

- **WHEN** `final_enabled` 經合併後為空集合（repo.enabled 與 enabled_extra 皆空，或被 enabled_remove 完全消去）
- **THEN** SHALL 不分發任何 ECC skill
- **THEN** SHALL 不視為錯誤（明確的「全部停用」意圖）

#### Scenario: enabled 列出但 ECC 沒有

- **WHEN** `final_enabled` 列出的名稱在 ECC 來源中不存在
- **THEN** SHALL 跳過該項目（不報錯）
- **THEN** SHALL 在 stderr 印出黃色警告：「enabled 中的 X 個 skill 在 ECC 中找不到，建議檢查名稱或執行 `ai-dev ecc audit`」
- **THEN** 警告 SHALL 不區分名稱來自 repo.enabled 或 user.enabled_extra

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

- **WHEN** 使用者從 `distribute.skills.enabled` 移除某個 skill 且該 skill 也不在 `user.enabled_extra`
- **THEN** 下次 clone 時 ManifestTracker SHALL 偵測到該 skill 在目標目錄為孤兒並清理
- **THEN** 不影響其他 skill 或非 ECC 來源的檔案

#### Scenario: 使用者透過 enabled_extra 保留將被移除的 skill

- **WHEN** maintainer 從 `repo.enabled` 移除某個 skill，但使用者於 `~/.config/ai-dev/ecc-profile.yaml` 將該 skill 加入 `enabled_extra`
- **THEN** `final_enabled` SHALL 仍包含該 skill
- **THEN** ManifestTracker SHALL 不視該 skill 為孤兒，分發行為與保留前一致

#### Scenario: 升級時通知本地 ECC skill 將被移除

- **WHEN** `ai-dev clone` 執行時偵測到舊 manifest 中有 ECC 來源 skill 將因 `final_enabled` 變動而被孤兒清理
- **THEN** SHALL 在分發前印出黃色非阻塞提示，列出受影響的 skill 名稱與保留辦法（加入 `enabled_extra`）
- **THEN** SHALL 繼續執行（不阻塞、不需要使用者確認）

#### Scenario: ECC 上游移除 skill 時的孤兒清理

- **WHEN** ECC 上游移除了某個 skill
- **THEN** 下次 clone 時 ManifestTracker SHALL 偵測孤兒並清理（與既有行為一致）

### Requirement: ecc-profile.yaml 使用者層級覆寫（whitelist 語意）

系統 SHALL 支援 `~/.config/ai-dev/ecc-profile.yaml` 作為使用者層級覆寫，使用 `enabled_extra` / `enabled_remove` 兩個欄位。runtime 將其與 `repo.distribute.skills.enabled` 合併後再進行白名單判斷。

#### Scenario: ecc-profile.yaml 不存在

- **WHEN** `~/.config/ai-dev/ecc-profile.yaml` 不存在
- **THEN** `final_enabled` SHALL 等於 `repo.distribute.skills.enabled`
- **THEN** SHALL 不視為錯誤、不印警告

#### Scenario: 使用者新增 skill

- **WHEN** `ecc-profile.yaml.enabled_extra` 列出 skill X，且 X 不在 `repo.enabled`
- **THEN** `final_enabled` SHALL 包含 X
- **THEN** 若 X 存在於 ECC 來源，SHALL 分發

#### Scenario: 使用者移除 skill

- **WHEN** `ecc-profile.yaml.enabled_remove` 列出 skill Y，且 Y 在 `repo.enabled`
- **THEN** `final_enabled` SHALL 不包含 Y
- **THEN** 若 Y 先前已分發，下次 clone 時 ManifestTracker SHALL 偵測孤兒並清理

#### Scenario: extra 與 remove 同名衝突

- **WHEN** 同一個 skill 同時出現在 `enabled_extra` 與 `enabled_remove`
- **THEN** `enabled_remove` SHALL 勝出（subtraction 在 union 之後）
- **THEN** `final_enabled` SHALL 不包含該 skill

#### Scenario: remove 列出不在 repo.enabled 的名稱

- **WHEN** `enabled_remove` 列出的 skill 不在 `repo.enabled`
- **THEN** SHALL 靜默忽略
- **THEN** SHALL 不視為錯誤、不印警告

#### Scenario: extra 列出 ECC 不存在的名稱

- **WHEN** `enabled_extra` 列出的 skill 在 ECC 來源中不存在
- **THEN** SHALL 與 repo.enabled 列出不存在 skill 同等處理（黃色警告、非阻塞）

#### Scenario: Legacy v1 鍵自動相容

- **WHEN** 偵測到 `~/.config/ai-dev/ecc-profile.yaml` 含 `include_skills` 或 `exclude_skills`（且對應新鍵未設定）
- **THEN** SHALL 視 `include_skills` 為 `enabled_extra`、`exclude_skills` 為 `enabled_remove`
- **THEN** SHALL 印出一次性 deprecation hint 引導使用者改名
- **THEN** SHALL 不阻塞、不自動寫檔

#### Scenario: 新舊鍵同時存在

- **WHEN** `enabled_extra` 與 `include_skills`（或 `enabled_remove` 與 `exclude_skills`）同時存在
- **THEN** 新鍵 SHALL 優先，legacy 鍵 SHALL 被忽略
- **THEN** SHALL 印出一次性警告告知 legacy 鍵不生效

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

