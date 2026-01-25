## ADDED Requirements

### Requirement: custom-skills-dev Skill

系統 SHALL 提供 custom-skills-dev skill 指導此專案的開發流程與最佳實踐。

#### Scenario: Skill 觸發

- **GIVEN** 開發者在 custom-skills 專案中工作
- **WHEN** 執行以下任務：新增 skill、修改 CLI、更新複製邏輯、發布版本
- **THEN** custom-skills-dev skill 自動觸發
- **AND** 提供專案特定的開發指南

#### Scenario: 三階段複製架構指南

- **WHEN** 開發者需要理解或修改複製流程
- **THEN** skill 提供三階段架構說明（Clone → 整合 → 分發）
- **AND** 提供 `references/copy-architecture.md` 詳細參考

#### Scenario: CLI 開發指南

- **WHEN** 開發者需要修改或新增 CLI 功能
- **THEN** skill 提供 Python + uv 開發流程
- **AND** 提供 `references/cli-development.md` 詳細參考

#### Scenario: 版本發布流程

- **WHEN** 開發者需要發布新版本
- **THEN** skill 提供版本發布 checklist
- **AND** 提供 `references/release-workflow.md` 詳細參考
