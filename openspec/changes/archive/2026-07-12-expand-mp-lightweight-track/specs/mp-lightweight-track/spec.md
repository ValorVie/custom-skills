# mp-lightweight-track Specification

## ADDED Requirements

### Requirement: 輕量軌工作流文件

`docs/dev-guide/workflow/DEVELOPMENT-WORKFLOW.md` SHALL 定義輕量開發軌：適用準則、流程路徑、以及與重量軌（OpenSpec）和探索軌（wayfinder）的分界。

#### Scenario: 輕量軌章節存在

- **GIVEN** 開發者查閱開發工作流程指南
- **WHEN** 尋找小型變更的處理方式
- **THEN** 文件 SHALL 包含輕量軌章節
- **AND** 章節 SHALL 描述路徑：`mp-grill-with-docs`（必要時）→ `mp-to-issues`（GitHub issue 出口）→ 直接實作（superpowers TDD）→ code review
- **AND** 快速參考表 SHALL 包含 `mp-wayfinder` 與 `mp-prototype` 條目

#### Scenario: 三軌分界明確

- **GIVEN** 開發者不確定該走哪條軌
- **WHEN** 查閱輕量軌章節
- **THEN** 文件 SHALL 提供三軌對照：正式變更走 OpenSpec、小變更走輕量軌、模糊大工作先走 `mp-wayfinder`
- **AND** 每軌 SHALL 附至少一個本專案情境的範例

### Requirement: 輕量軌準入條件

輕量軌 SHALL 僅在三項條件同時成立時允許不開 OpenSpec change，任一不成立 SHALL 走 OpenSpec 流程。

#### Scenario: 準入條件列舉

- **GIVEN** 開發者評估某變更是否可走輕量軌
- **WHEN** 查閱準入條件
- **THEN** 條件 SHALL 包含：變更範圍在單一模組或文件群且不影響 `openspec/specs/` 既有規格行為
- **AND** 條件 SHALL 包含：單一 session 內可完成實作與驗證
- **AND** 條件 SHALL 包含：不屬於 `docs/agents/issue-tracker.md` 定義的正式變更（功能、重構、規格修改）

#### Scenario: canonical 出口不受影響

- **GIVEN** 輕量軌已納入工作流文件
- **WHEN** 檢查 `docs/agents/issue-tracker.md`
- **THEN** OpenSpec `tasks.md` SHALL 仍為正式變更的 canonical 出口
- **AND** 輕量軌工作項目 SHALL 使用 GitHub issues 輔出口追蹤

#### Scenario: 分流時檢查準入

- **GIVEN** `mp-triage` 分流一個工作項目
- **WHEN** 該項目被建議走輕量軌
- **THEN** 分流結果 SHALL 說明三項準入條件的判斷依據
- **AND** 任一條件不成立時 SHALL 改建議 OpenSpec 流程
