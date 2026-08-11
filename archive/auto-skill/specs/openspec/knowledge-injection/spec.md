# knowledge-injection Specification

## Purpose
TBD

## Requirements

### Requirement: SessionStart 知識索引注入

系統 SHALL 在 Claude Code SessionStart 事件時自動注入 auto-skill 的知識庫與經驗索引摘要到對話 context。

#### Scenario: 正常注入知識庫索引

- **WHEN** Claude Code 新 Session 開始
- **AND** auto-skill 目錄存在（`~/.claude/skills/auto-skill/` 或 `./skills/auto-skill/`，或兩者皆存在）
- **AND** 至少一個層級的 `knowledge-base/_index.json` 存在且包含 count > 0 的分類
- **THEN** hook 輸出 `[Auto-Skill Knowledge Base]` 標題
- **AND** 每個有內容的分類輸出一行：分類名、檔案名、條目數（含來源標註）、keywords

#### Scenario: 正常注入經驗索引

- **WHEN** Claude Code 新 Session 開始
- **AND** 至少一個層級的 `experience/_index.json` 存在且包含有效的 skill 條目（skillId 非空）
- **THEN** hook 輸出 `[Auto-Skill Experience]` 標題
- **AND** 每個有效 skill 輸出一行：skillId、檔案名、條目數（含來源標註）

#### Scenario: 空知識庫靜默跳過

- **WHEN** Claude Code 新 Session 開始
- **AND** 所有層級的知識庫分類 count 均為 0
- **THEN** hook 不輸出 `[Auto-Skill Knowledge Base]` 區塊

#### Scenario: 無效經驗條目過濾

- **WHEN** `experience/_index.json` 包含 skillId 或 file 為空字串的條目
- **THEN** hook 過濾掉這些無效條目
- **AND** 若過濾後無有效條目，不輸出 `[Auto-Skill Experience]` 區塊

#### Scenario: auto-skill 未安裝

- **WHEN** Claude Code 新 Session 開始
- **AND** 兩個層級的 auto-skill 目錄都不存在
- **THEN** hook 靜默退出，不輸出任何內容
- **AND** 不產生錯誤訊息

#### Scenario: JSON 解析失敗

- **WHEN** 某一層級的 `_index.json` 檔案格式錯誤（非合法 JSON）
- **THEN** hook 靜默跳過該層級的索引
- **AND** 不產生錯誤訊息
- **AND** 不影響另一層級的載入

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
- **THEN** 檢查 `~/.claude/skills/auto-skill/`（使用者層級）
- **AND** 檢查當前工作目錄下的 `skills/auto-skill/`（專案層級）
- **AND** 將所有找到的目錄都納入載入範圍

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

### Requirement: SKILL.md 雙層級存儲路徑

SKILL.md SHALL 記載雙層級的存儲路徑與層級選擇建議。

#### Scenario: 存儲路徑文件

- **WHEN** 使用者或 Claude 查看 SKILL.md 的存儲路徑
- **THEN** 包含使用者層級路徑（`~/.claude/skills/auto-skill/`）
- **AND** 包含專案層級路徑（`./skills/auto-skill/`）
- **AND** 包含層級選擇建議（使用者層級適合個人偏好，專案層級適合團隊規範）

### Requirement: 雙層級知識索引合併

系統 SHALL 同時載入使用者層級和專案層級的 auto-skill 索引，合併後輸出並標註來源。

#### Scenario: 雙層都存在時合併輸出

- **WHEN** Claude Code 新 Session 開始
- **AND** 使用者層級 `~/.claude/skills/auto-skill/` 存在
- **AND** 專案層級 `./skills/auto-skill/` 存在
- **THEN** hook 載入兩個層級的 `knowledge-base/_index.json` 和 `experience/_index.json`
- **AND** 以 `id`（knowledge-base）或 `skillId`（experience）為鍵合併

#### Scenario: 來源標註 — 單層有內容

- **WHEN** 某分類僅在使用者層級有 count > 0
- **THEN** 輸出格式為 `{name} ({file}): N entries [使用者] | keywords: ...`

#### Scenario: 來源標註 — 雙層有內容

- **WHEN** 某分類在使用者層級有 count X > 0
- **AND** 同一分類在專案層級有 count Y > 0
- **THEN** 輸出格式為 `{name} ({file}): {X+Y} entries (X [使用者] + Y [專案]) | keywords: ...`

#### Scenario: 雙層 count 都為 0 則跳過

- **WHEN** 某分類在兩個層級的 count 都為 0
- **THEN** 不輸出該分類

#### Scenario: 僅一個層級存在

- **WHEN** 僅使用者層級存在（或僅專案層級存在）
- **THEN** 行為等同現有單層模式，但輸出加上對應層級標註

### Requirement: SKILL.md 雙層讀取指令

SKILL.md SHALL 指引 Claude 在讀取知識庫和經驗時，同時讀取使用者層級和專案層級的內容。

#### Scenario: 經驗讀取（Step 3）合併雙層

- **WHEN** Claude 需要讀取某 skill 的經驗
- **THEN** 先讀取使用者層級 `{user}/experience/skill-{id}.md`（若存在）
- **AND** 再讀取專案層級 `{project}/experience/skill-{id}.md`（若存在）
- **AND** 回覆中標註來源：`我已讀取經驗：skill-xxx.md [使用者] + [專案]`

#### Scenario: 知識庫讀取（Step 4）合併雙層

- **WHEN** Claude 需要讀取某分類的知識庫
- **THEN** 先讀取使用者層級 `{user}/knowledge-base/{category}.md`（若存在）
- **AND** 再讀取專案層級 `{project}/knowledge-base/{category}.md`（若存在）
- **AND** 回覆中標註來源

#### Scenario: 經驗缺失判斷改為雙層

- **WHEN** 某 skill 的經驗在使用者層級和專案層級的索引中都不存在
- **THEN** 記錄到 `missing_experience_skills`
- **AND** 任務結束時觸發詢問

### Requirement: 記錄層級選擇

SKILL.md SHALL 指引 Claude 在記錄經驗或知識時，詢問使用者要存到哪一層。

#### Scenario: 記錄時詢問層級

- **WHEN** Claude 決定記錄經驗或知識
- **THEN** 詢問使用者選擇：「使用者層級（僅個人使用）」或「專案層級（團隊共享，提交到 git）」
- **AND** 根據選擇寫入對應層級的目錄

#### Scenario: 記錄後確認

- **WHEN** 記錄完成
- **THEN** 回覆確認：`已記錄至 [使用者] 層級` 或 `已記錄至 [專案] 層級`

### Requirement: 專案層級目錄初始化

系統 SHALL 在使用者選擇記錄到專案層級但目錄不存在時，提供初始化流程。

#### Scenario: 專案層級不存在時詢問初始化

- **WHEN** 使用者選擇記錄到專案層級
- **AND** `./skills/auto-skill/` 不存在
- **THEN** 詢問使用者：「專案中尚未建立 auto-skill 目錄，是否要從模板初始化？」

#### Scenario: 同意初始化

- **WHEN** 使用者同意初始化
- **THEN** 從 `~/.config/custom-skills/skills/auto-skill/` 複製完整模板結構到 `./skills/auto-skill/`
- **AND** 完成後執行原本的記錄操作

#### Scenario: 拒絕初始化

- **WHEN** 使用者拒絕初始化
- **THEN** 改為記錄到使用者層級
- **AND** 告知使用者：`已改為記錄至 [使用者] 層級`

#### Scenario: 模板來源不存在

- **WHEN** `~/.config/custom-skills/skills/auto-skill/` 不存在
- **THEN** 告知使用者模板來源不可用
- **AND** 改為記錄到使用者層級
