## ADDED Requirements

### Requirement: SessionStart 知識索引注入

系統 SHALL 在 Claude Code SessionStart 事件時自動注入 auto-skill 的知識庫與經驗索引摘要到對話 context。

#### Scenario: 正常注入知識庫索引

- **WHEN** Claude Code 新 Session 開始
- **AND** auto-skill 目錄存在（`skills/auto-skill/` 或 `~/.claude/skills/auto-skill/`）
- **AND** `knowledge-base/_index.json` 存在且包含 count > 0 的分類
- **THEN** hook 輸出 `[Auto-Skill Knowledge Base]` 標題
- **AND** 每個有內容的分類輸出一行：分類名、檔案名、條目數、keywords

#### Scenario: 正常注入經驗索引

- **WHEN** Claude Code 新 Session 開始
- **AND** `experience/_index.json` 存在且包含有效的 skill 條目（skillId 非空）
- **THEN** hook 輸出 `[Auto-Skill Experience]` 標題
- **AND** 每個有效 skill 輸出一行：skillId、檔案名、條目數

#### Scenario: 空知識庫靜默跳過

- **WHEN** Claude Code 新 Session 開始
- **AND** 所有知識庫分類的 count 均為 0
- **THEN** hook 不輸出 `[Auto-Skill Knowledge Base]` 區塊

#### Scenario: 無效經驗條目過濾

- **WHEN** `experience/_index.json` 包含 skillId 或 file 為空字串的條目
- **THEN** hook 過濾掉這些無效條目
- **AND** 若過濾後無有效條目，不輸出 `[Auto-Skill Experience]` 區塊

#### Scenario: auto-skill 未安裝

- **WHEN** Claude Code 新 Session 開始
- **AND** auto-skill 目錄不存在
- **THEN** hook 靜默退出，不輸出任何內容
- **AND** 不產生錯誤訊息

#### Scenario: JSON 解析失敗

- **WHEN** `_index.json` 檔案格式錯誤（非合法 JSON）
- **THEN** hook 靜默跳過該索引
- **AND** 不產生錯誤訊息
- **AND** 不影響其他 SessionStart hooks 的執行

### Requirement: 知識索引注入腳本

注入腳本 SHALL 為 Python 3 腳本，位於獨立的 `auto-skill-hooks` 插件中。

#### Scenario: 腳本位置

- **WHEN** 部署知識注入腳本
- **THEN** 腳本位於 `plugins/auto-skill-hooks/scripts/inject-knowledge-index.py`

#### Scenario: 插件結構

- **WHEN** 建立 auto-skill-hooks 插件
- **THEN** 插件目錄為 `plugins/auto-skill-hooks/`
- **AND** 包含 `.claude-plugin/plugin.json` 插件定義
- **AND** 包含 `hooks/hooks.json` hook 配置
- **AND** 包含 `scripts/inject-knowledge-index.py` 注入腳本
- **AND** 插件名稱為 `auto-skill-hooks`，獨立於 ecc-hooks

#### Scenario: skill 目錄搜尋順序

- **WHEN** 腳本搜尋 auto-skill 目錄
- **THEN** 優先檢查 `~/.claude/skills/auto-skill/`
- **AND** 其次檢查當前工作目錄下的 `skills/auto-skill/`
- **AND** 使用第一個找到的目錄

#### Scenario: 跨平台相容

- **WHEN** 腳本在 macOS、Linux 或 Windows 上執行
- **THEN** 使用 `os.path` 或 `pathlib` 處理路徑
- **AND** 使用 Python 標準庫，不依賴第三方套件

### Requirement: CLAUDE.md 知識庫行為指令

系統 SHALL 在 `~/.claude/CLAUDE.md` 中提供知識庫使用與經驗記錄的行為指令。

#### Scenario: 指令內容涵蓋讀取規則

- **WHEN** Claude 在對話中看到 `[Auto-Skill Knowledge Base]` 或 `[Auto-Skill Experience]` 標記
- **THEN** CLAUDE.md 指令告訴 Claude 根據任務相關性決定是否讀取對應 `.md` 檔案
- **AND** 提供知識庫路徑（`skills/auto-skill/knowledge-base/{file}`）
- **AND** 提供經驗路徑（`skills/auto-skill/experience/{file}`）

#### Scenario: 指令內容涵蓋記錄規則

- **WHEN** Claude 完成一個任務
- **THEN** CLAUDE.md 指令告訴 Claude 在產生可重用經驗時主動詢問使用者是否記錄
- **AND** 指引 Claude 參考 `skills/auto-skill/SKILL.md` 的條目格式
- **AND** 指引 Claude 更新對應的 `_index.json`

#### Scenario: 指令以獨立區塊存在

- **WHEN** 寫入 `~/.claude/CLAUDE.md`
- **THEN** 使用 `## 知識庫與經驗協議` 作為區塊標題
- **AND** 區塊內容自包含，不依賴 CLAUDE.md 中的其他區塊

### Requirement: SKILL.md 精簡

`skills/auto-skill/SKILL.md` SHALL 移除無法在 Claude Code 中運作的機制，保留有價值的參考內容。

#### Scenario: 移除的內容

- **WHEN** 精簡 SKILL.md
- **THEN** 移除 Step 0.5（自動加固全局規則）
- **AND** 移除 Step 1（逐回合關鍵詞抽取）
- **AND** 移除 Step 2（話題切換偵測）
- **AND** 移除 Step 0 的對話內快取定義
- **AND** 移除 QMD 升級章節

#### Scenario: 保留的內容

- **WHEN** 精簡 SKILL.md
- **THEN** 保留知識庫條目格式規範（knowledge-base 條目格式）
- **AND** 保留經驗條目格式規範（experience 條目格式）
- **AND** 保留記錄判斷準則（應該記錄/不應記錄）
- **AND** 保留存儲路徑說明
- **AND** 保留動態分類說明
