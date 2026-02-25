## MODIFIED Requirements

### Requirement: 安裝方式
安裝 ai-dev CLI SHALL 改為透過 npm/bun 全域安裝，取代 Python `pip install -e .`。

#### Scenario: Bun 安裝
- **WHEN** 使用者執行 `bun add -g @valorvie/ai-dev`
- **THEN** ai-dev CLI 安裝完成，可在終端使用 `ai-dev` 指令

#### Scenario: npm 安裝
- **WHEN** 使用者執行 `npm install -g @valorvie/ai-dev`
- **THEN** ai-dev CLI 安裝完成，可在終端使用 `ai-dev` 指令

#### Scenario: 前置條件變更
- **WHEN** 使用者尚未安裝 Bun
- **THEN** `ai-dev install` SHALL 提示安裝 Bun runtime

## REMOVED Requirements

### Requirement: Python 安裝方式
**Reason**: 以 npm/bun 全域安裝取代
**Migration**: 執行 `pip uninstall ai-dev`，改用 `bun add -g @valorvie/ai-dev`
