## MODIFIED Requirements

### Requirement: MP slice work

`mp-to-issues` SHALL convert a plan, PRD, OpenSpec proposal, or conversation summary into vertical slices and select an output supported by the repository's canonical tracker rules.

#### Scenario: Vertical slice output

- **GIVEN** source material describes a larger change
- **WHEN** `mp-to-issues` drafts work items
- **THEN** each item SHALL describe a narrow but complete path through the affected system
- **AND** each item SHALL include verification criteria
- **AND** each item SHALL be marked `AFK` or `HITL`

#### Scenario: Beads issue graph output

- **GIVEN** 儲存庫以 Beads 作為 canonical 執行追蹤器
- **WHEN** `mp-to-issues` outputs work items
- **THEN** it SHALL support Beads issue 或 command draft 輸出
- **AND** 可獨立認領的切片 SHALL 成為 Beads 工作項目
- **AND** 切片依賴 SHALL 以 `bd dep add <blocked> <blocker>` 表示
- **AND** 未取得寫入授權時 SHALL 只輸出指令草稿

#### Scenario: OpenSpec task output

- **GIVEN** 來源素材是 OpenSpec change
- **WHEN** `mp-to-issues` outputs work items
- **THEN** it SHALL support writing or drafting OpenSpec `tasks.md` format
- **AND** it SHALL preserve dependency order between slices
- **AND** 需要獨立認領或跨 session 交接的切片 SHALL 同時支援 Beads 追蹤

#### Scenario: Multiple output modes

- **GIVEN** 儲存庫使用不同的工作追蹤方式
- **WHEN** 使用者或儲存庫規則選擇輸出模式
- **THEN** `mp-to-issues` SHALL support Beads、OpenSpec tasks、GitHub issue draft 與 local Markdown output
- **AND** 使用者明確指定 SHALL 優先於自動偵測

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

### Requirement: MP triage work

`mp-triage` SHALL classify work items by readiness for agent execution without binding the model to a single issue tracker, and SHALL map the result to the repository's canonical tracker when available.

#### Scenario: Shared states

- **GIVEN** a work item needs classification
- **WHEN** `mp-triage` evaluates it
- **THEN** it SHALL choose one of `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, or `wontfix`
- **AND** the selected state SHALL be independent from external label names

#### Scenario: Agent-ready item

- **GIVEN** a work item has clear scope, verification criteria, and no unresolved human decision
- **WHEN** `mp-triage` evaluates it
- **THEN** it SHALL classify the item as `ready-for-agent`

#### Scenario: Human-ready item

- **GIVEN** a work item requires product judgment, external access, or manual approval
- **WHEN** `mp-triage` evaluates it
- **THEN** it SHALL classify the item as `ready-for-human`
- **AND** it SHALL explain why the item cannot be delegated safely

#### Scenario: Beads mapping

- **GIVEN** 儲存庫以 Beads 作為 canonical 執行追蹤器
- **WHEN** `mp-triage` 產生分流結果
- **THEN** 結果 SHALL 包含唯一 triage label 與對應 Beads status
- **AND** `ready-for-agent` SHALL map to `open`
- **AND** `needs-triage`、`needs-info`、`ready-for-human` SHALL map to `blocked`
- **AND** `wontfix` SHALL map to `closed` 並附原因

### Requirement: MP wayfinder 規劃

`mp-wayfinder` SHALL 把「大到單一 session 裝不下、尚無法撰寫 OpenSpec proposal」的模糊工作，規劃為 canonical tracker 上的地圖與子工作項目，且只做決策不做交付。

#### Scenario: 地圖式規劃輸出

- **GIVEN** 使用者帶著模糊的大型想法啟動 `mp-wayfinder`
- **WHEN** 完成目的地釐清與初次展開
- **THEN** it SHALL create 一張地圖工作項目（含目的地、已決事項索引、尚未成形區、範圍外清單）
- **AND** 可明確提問的決策點 SHALL 成為地圖的子工作項目並宣告阻擋關係
- **AND** 尚無法精確提問的內容 SHALL 留在「尚未成形」區，不預先切票

#### Scenario: Beads 地圖

- **GIVEN** 儲存庫以 Beads 作為 canonical 執行追蹤器
- **WHEN** `mp-wayfinder` 建立地圖
- **THEN** 地圖 SHALL 使用 Beads epic
- **AND** 決策點 SHALL 使用 child issue
- **AND** frontier SHALL 由 open、無 blocking dependency 且 triage label 為 `ready-for-agent` 或 `ready-for-human` 的子工作組成

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
