## ADDED Requirements

### Requirement: MP 工作入口層技能組

系統 SHALL 提供一組 `mp-*` 技能，作為 `openspec` 與 `superpowers` 之前的工作入口層。

#### Scenario: P0 技能存在

- **GIVEN** 使用者需要從模糊需求進入正式工程流程
- **WHEN** 檢查本專案 skills
- **THEN** `skills/mp-setup-matt-pocock-skills/SKILL.md` SHALL exist
- **AND** `skills/mp-grill-with-docs/SKILL.md` SHALL exist
- **AND** `skills/mp-to-issues/SKILL.md` SHALL exist

#### Scenario: P1 技能存在

- **GIVEN** 使用者需要任務分流或架構回看
- **WHEN** 檢查本專案 skills
- **THEN** `skills/mp-triage/SKILL.md` SHALL exist
- **AND** `skills/mp-improve-codebase-architecture/SKILL.md` SHALL exist

#### Scenario: P2 技能存在

- **GIVEN** 使用者需要把既有討論整理成需求摘要
- **WHEN** 檢查本專案 skills
- **THEN** `skills/mp-to-prd/SKILL.md` SHALL exist

#### Scenario: Skill names preserve upstream identity

- **GIVEN** MP 工作入口層技能已建立
- **WHEN** 檢查技能命名
- **THEN** 本地技能名稱 SHALL use `mp-<來源技能名>`
- **AND** `setup-matt-pocock-skills` SHALL map to `mp-setup-matt-pocock-skills`
- **AND** `to-issues` SHALL map to `mp-to-issues`
- **AND** `improve-codebase-architecture` SHALL map to `mp-improve-codebase-architecture`

### Requirement: Claude Code 與 Codex 共同支援

MP 工作入口層 SHALL 同時支援 Claude Code 與 Codex。

#### Scenario: Claude Code projection

- **GIVEN** 已執行 skill 分發
- **WHEN** 檢查 Claude Code 投影
- **THEN** `.claude/skills/mp-setup-matt-pocock-skills/SKILL.md` SHALL exist
- **AND** `.claude/skills/mp-grill-with-docs/SKILL.md` SHALL exist
- **AND** `.claude/skills/mp-to-issues/SKILL.md` SHALL exist

#### Scenario: Codex projection

- **GIVEN** 已執行 skill 分發
- **WHEN** 檢查 Codex 投影
- **THEN** `.codex/skills/mp-setup-matt-pocock-skills/SKILL.md` SHALL exist
- **AND** `.codex/skills/mp-grill-with-docs/SKILL.md` SHALL exist
- **AND** `.codex/skills/mp-to-issues/SKILL.md` SHALL exist

#### Scenario: Shared workflow source

- **GIVEN** `CLAUDE.md` 與 `AGENTS.md` 都存在
- **WHEN** MP 工作入口層設定完成
- **THEN** `CLAUDE.md` 與 `AGENTS.md` SHALL reference `docs/agents/`
- **AND** MP 工作流細節 SHALL be maintained in `docs/agents/`
- **AND** `CLAUDE.md` and `AGENTS.md` SHALL NOT define divergent MP workflow rules

### Requirement: MP setup workflow

`mp-setup-matt-pocock-skills` SHALL 建立儲存庫層級的共同工作入口文件。

#### Scenario: Shared docs created

- **GIVEN** 使用者執行 `mp-setup-matt-pocock-skills`
- **WHEN** 使用者確認寫入設定
- **THEN** `docs/agents/issue-tracker.md` SHALL exist
- **AND** `docs/agents/triage-states.md` SHALL exist
- **AND** `docs/agents/domain.md` SHALL exist
- **AND** `docs/agents/mp-workflow.md` SHALL exist

#### Scenario: Existing entrypoints updated

- **GIVEN** both `CLAUDE.md` and `AGENTS.md` exist
- **WHEN** `mp-setup-matt-pocock-skills` writes entrypoint rules
- **THEN** 兩個檔案 SHALL 被更新
- **AND** 更新內容 SHALL 指向 `docs/agents/`

### Requirement: MP grill with docs

`mp-grill-with-docs` SHALL turn vague requirements into project language and durable decisions before implementation starts.

#### Scenario: Project language captured

- **GIVEN** a domain term is clarified during a grilling session
- **WHEN** 該術語不只對單一實作細節有意義
- **THEN** `CONTEXT.md` SHALL be updated or created
- **AND** 該術語 SHALL 使用儲存庫的標準語言

#### Scenario: ADR creation is constrained

- **GIVEN** a design decision is reached during a grilling session
- **WHEN** the decision is hard to reverse, surprising without context, and based on a real trade-off
- **THEN** an ADR MAY be created under `docs/adr/`
- **AND** if any condition is missing, an ADR SHALL NOT be created

#### Scenario: Code can answer the question

- **GIVEN** a grilling question can be answered by inspecting local code or docs
- **WHEN** the skill runs
- **THEN** 它 SHALL 檢查儲存庫，而不是要求使用者憑記憶回答

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

### Requirement: MP triage work

`mp-triage` SHALL classify work items by readiness for agent execution without binding the model to a single issue tracker.

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

### Requirement: MP architecture review

`mp-improve-codebase-architecture` SHALL 找出架構改善候選，且不修改實作程式碼。

#### Scenario: Candidate-only output

- **GIVEN** user asks for architecture review
- **WHEN** `mp-improve-codebase-architecture` completes exploration
- **THEN** it SHALL output candidates with files, problem, proposed direction, benefit, and testing implication
- **AND** it SHALL NOT edit 實作程式碼

#### Scenario: Context-aware review

- **GIVEN** `CONTEXT.md`, `CONTEXT-MAP.md`, or `docs/adr/` exists
- **WHEN** `mp-improve-codebase-architecture` starts
- **THEN** it SHALL read relevant domain docs and ADRs before proposing candidates

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

### Requirement: Existing workflow preservation

MP 工作入口層 SHALL preserve existing `superpowers` and `openspec` responsibilities.

#### Scenario: No TDD replacement

- **GIVEN** user asks for TDD or red-green-refactor implementation
- **WHEN** skill selection occurs
- **THEN** existing `superpowers` TDD workflow SHALL remain the implementation workflow
- **AND** MP skills SHALL NOT replace it

#### Scenario: No OpenSpec replacement

- **GIVEN** a change is ready for formal proposal, design, tasks, or verification
- **WHEN** 使用者選擇 OpenSpec
- **THEN** existing `openspec-*` skills SHALL remain the formal lifecycle workflow
- **AND** MP skills SHALL only provide upstream intake, slicing, triage, or architecture candidate input

#### Scenario: No upstream bundle install

- **GIVEN** MP workflow entry layer is implemented
- **WHEN** checking implementation artifacts
- **THEN** the project SHALL NOT require `npx skills add mattpocock/skills`
- **AND** it SHALL NOT install upstream `tdd` or `diagnose` as first-class MP skills

### Requirement: Upstream update tracking

MP 工作入口層 SHALL 保留 `mattpocock/skills` 上游更新的可追蹤性。

#### Scenario: Upstream source registered

- **GIVEN** MP 工作入口層實作完成
- **WHEN** 檢查上游來源註冊
- **THEN** `upstream/sources.yaml` SHALL include `mattpocock-skills`
- **AND** 來源 SHALL 指向 `mattpocock/skills`
- **AND** 來源 SHALL 使用 `install_method: manual`
- **AND** 來源 SHALL 使用人工審核語意，而不是自動覆蓋

#### Scenario: Last sync records adapted upstream commit

- **GIVEN** MP 工作入口層實作完成
- **WHEN** 檢查上游同步紀錄
- **THEN** `upstream/mattpocock-skills/last-sync.yaml` SHALL exist
- **AND** it SHALL 記錄採用的上游 commit
- **AND** it SHALL 標記本地狀態為 manually adapted

#### Scenario: Mapping file records adapted skills

- **GIVEN** MP 工作入口層實作完成
- **WHEN** 檢查上游 mapping
- **THEN** `upstream/mattpocock-skills/mapping.yaml` SHALL exist
- **AND** it SHALL 將每個採用的上游技能對應到本地 `mp-*` 技能
- **AND** 每個採用技能的 mapping SHALL 記錄 `local_skill`, `priority`, and `adaptation`
- **AND** it SHALL 記錄已排除的上游技能與原因

#### Scenario: Upstream audit does not overwrite local adaptations

- **GIVEN** 上游 `mattpocock/skills` 有新 commit
- **WHEN** 執行上游審核流程
- **THEN** 審核流程 SHALL 產出可檢視的 diff 或 report
- **AND** it SHALL NOT 在沒有明確實作任務時覆蓋本地 `skills/mp-*` 檔案
