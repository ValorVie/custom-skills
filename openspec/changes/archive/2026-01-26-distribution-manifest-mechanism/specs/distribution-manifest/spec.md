## ADDED Requirements

### Requirement: Manifest 檔案格式

系統 SHALL 使用 YAML 格式的 manifest 檔案追蹤已分發的資源。

Manifest 檔案 SHALL 包含以下欄位：
- `managed_by`: 固定值 `"ai-dev"`
- `version`: 分發時的 custom-skills 版本號
- `last_sync`: ISO 8601 格式的同步時間戳
- `target`: 目標平台名稱
- `files`: 按資源類型分組的已分發檔案清單，每個檔案包含 `hash` 欄位
  - `skills`: skill 目錄名稱與其 hash
  - `commands`: command 檔案名稱與其 hash
  - `agents`: agent 檔案名稱與其 hash
  - `workflows`: workflow 檔案名稱與其 hash

#### Scenario: Manifest 檔案結構

- **WHEN** 分發完成後讀取 manifest 檔案
- **THEN** manifest 檔案 SHALL 符合以下結構：
  ```yaml
  managed_by: ai-dev
  version: "2.1.0"
  last_sync: "2026-01-26T10:00:00+08:00"
  target: claude
  files:
    skills:
      commit-standards:
        hash: "sha256:a1b2c3d4..."
      custom-skills-git-commit:
        hash: "sha256:e5f6g7h8..."
    commands:
      commit.md:
        hash: "sha256:i9j0k1l2..."
    agents:
      reviewer.md:
        hash: "sha256:q7r8s9t0..."
    workflows:
      code-review.workflow.yaml:
        hash: "sha256:u1v2w3x4..."
  ```

---

### Requirement: Manifest 統一存放位置

系統 SHALL 將所有平台的 manifest 檔案統一存放在 `~/.config/ai-dev/manifests/` 目錄。

Manifest 檔案命名 SHALL 為 `<target>.yaml`：
- Claude Code: `~/.config/ai-dev/manifests/claude.yaml`
- OpenCode: `~/.config/ai-dev/manifests/opencode.yaml`
- Antigravity: `~/.config/ai-dev/manifests/antigravity.yaml`
- Codex: `~/.config/ai-dev/manifests/codex.yaml`
- Gemini CLI: `~/.config/ai-dev/manifests/gemini.yaml`

#### Scenario: 分發到 Claude Code

- **WHEN** 執行 `ai-dev clone` 分發到 Claude Code
- **THEN** 系統 SHALL 在 `~/.config/ai-dev/manifests/claude.yaml` 寫入該平台的 manifest

#### Scenario: 分發到多個平台

- **WHEN** 執行 `ai-dev clone` 分發到所有平台
- **THEN** `~/.config/ai-dev/manifests/` 目錄 SHALL 包含各平台獨立的 manifest 檔案

---

### Requirement: Hash 計算

系統 SHALL 計算每個分發檔案的 SHA-256 hash。

#### Scenario: 單檔案 hash 計算

- **WHEN** 分發單一檔案（commands/agents/workflows）
- **THEN** 系統 SHALL 計算該檔案內容的 SHA-256 hash
- **AND** hash 格式 SHALL 為 `sha256:<hex_digest>`

#### Scenario: 目錄 hash 計算（Skills）

- **WHEN** 分發 skill 目錄
- **THEN** 系統 SHALL 遞迴遍歷目錄內所有檔案
- **AND** 計算每個檔案的 SHA-256 hash
- **AND** 按檔案相對路徑排序後組合成總 hash
- **AND** 總 hash 格式 SHALL 為 `sha256:<hex_digest>`

---

### Requirement: 分發時記錄已複製檔案與 Hash

系統 SHALL 在分發過程中追蹤所有已複製的檔案及其 hash，並在分發完成後寫入 manifest。

#### Scenario: 記錄 skills

- **WHEN** 分發 skills 目錄到目標平台
- **THEN** 系統 SHALL 記錄每個已複製的 skill 目錄名稱及其 hash 到 manifest

#### Scenario: 記錄 commands

- **WHEN** 分發 commands 檔案到目標平台
- **THEN** 系統 SHALL 記錄每個已複製的 command 檔案名稱及其 hash 到 manifest

#### Scenario: 記錄 agents

- **WHEN** 分發 agents 檔案到目標平台
- **THEN** 系統 SHALL 記錄每個已複製的 agent 檔案名稱及其 hash 到 manifest

#### Scenario: 記錄 workflows

- **WHEN** 分發 workflows 檔案到目標平台
- **THEN** 系統 SHALL 記錄每個已複製的 workflow 檔案名稱及其 hash 到 manifest

---

### Requirement: 衝突檢測

系統 SHALL 在分發前檢測目標檔案是否被用戶修改。

衝突定義：目標檔案的當前 hash 與 manifest 記錄的 hash 不一致。

#### Scenario: 檔案未修改

- **WHEN** 目標檔案存在
- **AND** 目標檔案 hash 等於 manifest 記錄的 hash
- **THEN** 系統 SHALL 判定為「未修改」，允許安全覆蓋

#### Scenario: 檔案已被用戶修改

- **WHEN** 目標檔案存在
- **AND** 目標檔案 hash 不等於 manifest 記錄的 hash
- **THEN** 系統 SHALL 判定為「衝突」，提醒用戶

#### Scenario: 新檔案

- **WHEN** 目標檔案不存在
- **THEN** 系統 SHALL 判定為「新檔案」，直接複製

#### Scenario: 用戶自訂檔案

- **WHEN** 目標檔案存在
- **AND** manifest 無該檔案的記錄
- **THEN** 系統 SHALL 判定為「用戶自訂」，不處理該檔案

---

### Requirement: 衝突處理選項

系統 SHALL 提供多種衝突處理方式。

#### Scenario: 強制覆蓋

- **WHEN** 用戶使用 `--force` 選項
- **THEN** 系統 SHALL 覆蓋所有衝突檔案，不提示

#### Scenario: 跳過衝突

- **WHEN** 用戶使用 `--skip-conflicts` 選項
- **THEN** 系統 SHALL 跳過所有衝突檔案，僅分發無衝突的檔案

#### Scenario: 備份後覆蓋

- **WHEN** 用戶使用 `--backup` 選項
- **THEN** 系統 SHALL 將衝突檔案備份到 `.backup/` 目錄
- **AND** 備份檔名 SHALL 包含時間戳以避免覆蓋
- **AND** 備份完成後覆蓋原檔案

#### Scenario: 預設行為（互動式）

- **WHEN** 偵測到衝突且用戶未指定處理選項
- **THEN** 系統 SHALL 顯示衝突清單
- **AND** 詢問用戶如何處理

---

### Requirement: 比對新舊 Manifest 識別孤兒檔案

系統 SHALL 在分發前讀取舊 manifest，分發後比對新舊清單，識別需要清理的孤兒檔案。

孤兒檔案定義：存在於舊 manifest 但不存在於新 manifest 的檔案。

#### Scenario: 識別被重命名的 skill

- **WHEN** 舊 manifest 包含 `git-commit-custom`，新 manifest 包含 `custom-skills-git-commit`
- **THEN** 系統 SHALL 識別 `git-commit-custom` 為孤兒檔案

#### Scenario: 識別被移除的 command

- **WHEN** 舊 manifest 包含 `deprecated-command.md`，新 manifest 不包含
- **THEN** 系統 SHALL 識別 `deprecated-command.md` 為孤兒檔案

#### Scenario: 無舊 Manifest 時不產生孤兒清單

- **WHEN** 目標目錄不存在舊 manifest（首次分發）
- **THEN** 系統 SHALL 返回空的孤兒清單，不刪除任何檔案

---

### Requirement: 清理孤兒檔案

系統 SHALL 在分發完成後刪除已識別的孤兒檔案。

#### Scenario: 清理孤兒 skill 目錄

- **WHEN** `git-commit-custom` 被識別為孤兒
- **THEN** 系統 SHALL 刪除目標平台的 `skills/git-commit-custom/` 目錄及其所有內容

#### Scenario: 清理孤兒 command 檔案

- **WHEN** `git-commit.md` 被識別為孤兒
- **THEN** 系統 SHALL 刪除目標平台的 `commands/git-commit.md` 檔案

#### Scenario: 清理時輸出日誌

- **WHEN** 系統清理孤兒檔案
- **THEN** 系統 SHALL 輸出清理日誌，顯示已刪除的檔案路徑

---

### Requirement: 不影響用戶自訂資源

系統 SHALL NOT 刪除不在 manifest 中的檔案，以保護用戶自訂的資源。

#### Scenario: 保護用戶自訂 skill

- **WHEN** 目標目錄存在 `my-custom-skill/`，且該名稱不在任何 manifest 中
- **THEN** 系統 SHALL NOT 刪除 `my-custom-skill/`

#### Scenario: 保護用戶自訂 command

- **WHEN** 目標目錄存在 `my-command.md`，且該名稱不在任何 manifest 中
- **THEN** 系統 SHALL NOT 刪除 `my-command.md`

---

### Requirement: 向後相容性

系統 SHALL 在無舊 manifest 的情況下安全運作，不破壞現有環境。

#### Scenario: 首次分發

- **WHEN** `~/.config/ai-dev/manifests/` 目錄不存在或為空
- **THEN** 系統 SHALL 建立目錄和新的 manifest 檔案
- **AND** 系統 SHALL NOT 刪除任何現有檔案
- **AND** 系統 SHALL NOT 報告任何衝突（因無基準可比）

#### Scenario: 升級現有環境

- **WHEN** 用戶從無 manifest 版本升級
- **THEN** 系統 SHALL 建立 manifest 並記錄當前分發的檔案
- **AND** 舊有孤兒檔案 SHALL 保留（因無舊 manifest 可比對）

#### Scenario: Manifest 損壞

- **WHEN** manifest 檔案存在但無法解析（格式錯誤）
- **THEN** 系統 SHALL 視為無舊 manifest
- **AND** 系統 SHALL 輸出警告訊息
- **AND** 系統 SHALL 繼續分發並建立新的 manifest
