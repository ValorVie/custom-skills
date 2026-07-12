# mp-workflow-entry-layer Delta

## ADDED Requirements

### Requirement: MP 第二批技能存在

系統 SHALL 提供第二批 `mp-*` 技能，覆蓋探索期規劃與設計驗證。

#### Scenario: 第二批技能存在

- **GIVEN** 使用者需要探索期規劃或設計驗證
- **WHEN** 檢查本專案 skills
- **THEN** `skills/mp-wayfinder/SKILL.md` SHALL exist
- **AND** `skills/mp-prototype/SKILL.md` SHALL exist

#### Scenario: 第二批技能命名沿用上游對映規則

- **GIVEN** 第二批技能已建立
- **WHEN** 檢查技能命名
- **THEN** `wayfinder` SHALL map to `mp-wayfinder`
- **AND** `prototype` SHALL map to `mp-prototype`

#### Scenario: 第二批技能隨既有管線分發

- **GIVEN** `skills/mp-wayfinder/` 與 `skills/mp-prototype/` 位於分發來源目錄
- **WHEN** 變更合併推送後執行 `ai-dev clone`
- **THEN** 兩技能 SHALL 隨既有三階段複製分發至 Claude Code 與 Codex
- **AND** 分發 SHALL NOT 需要額外的 registry 登記
- **AND** 專案 repo SHALL NOT 保留 `.claude/skills/` 或 `.codex/skills/` 投影副本

### Requirement: MP wayfinder 規劃

`mp-wayfinder` SHALL 把「大到單一 session 裝不下、尚無法撰寫 OpenSpec proposal」的模糊工作，規劃為 issue tracker 上的地圖與子工作項目，且只做決策不做交付。

#### Scenario: 地圖式規劃輸出

- **GIVEN** 使用者帶著模糊的大型想法啟動 `mp-wayfinder`
- **WHEN** 完成目的地釐清與初次展開
- **THEN** it SHALL create 一張地圖 issue（含目的地、已決事項索引、尚未成形區、範圍外清單）
- **AND** 可明確提問的決策點 SHALL 成為地圖的子工作項目並宣告阻擋關係
- **AND** 尚無法精確提問的內容 SHALL 留在「尚未成形」區，不預先切票

#### Scenario: 每 session 只解一張

- **GIVEN** 地圖已存在且使用者帶著地圖啟動工作模式
- **WHEN** 選定一張無阻擋的子工作項目
- **THEN** the session SHALL 先認領再開工
- **AND** 解決後 SHALL 把結論記回該項目並更新地圖索引
- **AND** the session SHALL NOT 於同一 session 內解第二張

#### Scenario: 結晶成果轉入 OpenSpec

- **GIVEN** 地圖上的決策已足以撰寫 OpenSpec proposal
- **WHEN** 該部分工作要進入正式變更
- **THEN** it SHALL 轉入 OpenSpec change 流程
- **AND** 地圖 SHALL 只保留指向該 change 的連結，不重複維護內容

### Requirement: MP prototype 驗證

`mp-prototype` SHALL 以丟棄式原型回答單一設計問題，且原型程式碼不得進入 main 分支。

#### Scenario: 依問題選擇分支

- **GIVEN** 使用者提出一個設計問題
- **WHEN** `mp-prototype` 判斷問題型態
- **THEN** 狀態或邏輯問題 SHALL 產出可互動的終端原型
- **AND** 外觀或介面問題 SHALL 產出可切換的多變體 UI 原型

#### Scenario: 丟棄式紀律

- **GIVEN** 原型建立中
- **WHEN** 檢查原型內容
- **THEN** 原型 SHALL 可用單一指令執行
- **AND** 原型 SHALL NOT 引入持久化、測試或錯誤處理等打磨項目
- **AND** 原型檔案 SHALL 以名稱清楚標示為原型

#### Scenario: 完成即捕捉

- **GIVEN** 原型已回答設計問題
- **WHEN** 收尾
- **THEN** 驗證後的決策 SHALL 寫回實作、spec 或對應工作項目
- **AND** 原型程式碼 SHALL commit 到 `experiment/` 開頭的分支並於對應工作項目留下連結
- **AND** main 分支 SHALL NOT 包含原型程式碼

### Requirement: 上游對照表有效性

`upstream/mattpocock-skills/` 追蹤檔 SHALL 指向存在於參考快照中的上游路徑。

#### Scenario: 對照表路徑修正

- **GIVEN** 上游已將 `to-issues`、`to-prd`、`diagnose` 改名
- **WHEN** 檢查 `upstream/mattpocock-skills/mapping.yaml`
- **THEN** `mp-to-issues` 的 upstream_path SHALL 指向 `skills/engineering/to-tickets/`
- **AND** `mp-to-prd` 的 upstream_path SHALL 指向 `skills/engineering/to-spec/`
- **AND** excluded 區的除錯技能 SHALL 指向 `skills/engineering/diagnosing-bugs/`

#### Scenario: 參考快照更新

- **GIVEN** 本次審核基於上游 commit `391a270`
- **WHEN** 檢查 `upstream/mattpocock-skills/last-sync.yaml`
- **THEN** 參考快照 SHALL 更新為該 commit
- **AND** rename 歷史 SHALL 記錄於 notes

## MODIFIED Requirements

### Requirement: Claude Code 與 Codex 共同支援

MP 工作入口層 SHALL 同時支援 Claude Code 與 Codex，投影由 `ai-dev` 分發機制產生，專案 repo 不保留投影副本。

#### Scenario: 分發來源與管線

- **GIVEN** mp-* 技能位於專案 `skills/` 目錄（分發來源）
- **WHEN** 變更合併推送後執行 `ai-dev clone`
- **THEN** mp-* 技能 SHALL 隨三階段複製分發至 Claude Code 與 Codex 的 skills 目錄
- **AND** 專案 repo SHALL NOT 保留 `.claude/skills/mp-*` 或 `.codex/skills/mp-*` 投影副本

#### Scenario: Shared workflow source

- **GIVEN** `CLAUDE.md` 與 `AGENTS.md` 都存在
- **WHEN** MP 工作入口層設定完成
- **THEN** `CLAUDE.md` 與 `AGENTS.md` SHALL reference `docs/agents/`
- **AND** MP 工作流細節 SHALL be maintained in `docs/agents/`
- **AND** `CLAUDE.md` and `AGENTS.md` SHALL NOT define divergent MP workflow rules

### Requirement: MP slice work

`mp-to-issues` SHALL convert a plan, PRD, OpenSpec proposal, or conversation summary into vertical slices.

#### Scenario: Vertical slice output

- **GIVEN** source material describes a larger change
- **WHEN** `mp-to-issues` drafts work items
- **THEN** each item SHALL describe a narrow but complete path through the affected system
- **AND** each item SHALL include verification criteria
- **AND** each item SHALL be marked `AFK` or `HITL`

#### Scenario: OpenSpec task output

- **GIVEN** 來源素材是 OpenSpec change
- **WHEN** `mp-to-issues` outputs work items
- **THEN** it SHALL support writing or drafting OpenSpec `tasks.md` format
- **AND** it SHALL preserve dependency order between slices

#### Scenario: Multiple output modes

- **GIVEN** 儲存庫在 OpenSpec 之外追蹤工作項目
- **WHEN** 使用者選擇另一種輸出模式
- **THEN** `mp-to-issues` SHALL support GitHub issue draft output
- **AND** it SHALL support local Markdown output

#### Scenario: Blocking edges declared

- **GIVEN** 切片之間存在先後依賴
- **WHEN** `mp-to-issues` drafts work items
- **THEN** each item SHALL 宣告阻擋它的其他切片（無阻擋者標示可立即開工）
- **AND** 輸出順序 SHALL 使被依賴的切片排在前面
- **AND** 無阻擋的切片集合 SHALL 可平行認領

#### Scenario: Wide refactor uses expand-contract

- **GIVEN** 單一機械性變更的影響面橫跨大量呼叫點，無法以垂直切片保持綠燈
- **WHEN** `mp-to-issues` 切分該工作
- **THEN** it SHALL 依 expand–contract 順序切分：先新增新形式、再分批遷移呼叫點、最後移除舊形式
- **AND** 每個遷移批次 SHALL 宣告被 expand 切片阻擋
- **AND** 移除切片 SHALL 宣告被所有遷移批次阻擋

### Requirement: MP intake brief

`mp-to-prd` SHALL 將既有對話與儲存庫脈絡整理成精簡的實作入口文件。

#### Scenario: No re-interview

- **GIVEN** sufficient conversation context already exists
- **WHEN** `mp-to-prd` runs
- **THEN** it SHALL synthesize from existing context
- **AND** it SHALL NOT restart a full interview

#### Scenario: OpenSpec-ready output

- **GIVEN** the user wants to proceed toward OpenSpec
- **WHEN** `mp-to-prd` outputs a brief
- **THEN** the brief SHALL include problem, intended outcome, known decisions, open questions, out-of-scope items, and verification direction

#### Scenario: Seam confirmed before brief

- **GIVEN** 變更涉及可測試的程式邏輯
- **WHEN** `mp-to-prd` 整理 brief
- **THEN** it SHALL 先提出建議的測試 seam（優先沿用既有 seam、位置越高越好）
- **AND** it SHALL 與使用者核對 seam 後才輸出 brief
- **AND** brief 的驗證方向 SHALL 引用已確認的 seam
