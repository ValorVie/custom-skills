## Why

工具重疊性分析報告指出專案中存在兩處可優化的工具設計問題：

1. `coverage.md` 與 `test-coverage.md` 兩個命令功能高度重疊（60% overlap score），造成使用者選擇困惑
2. 相關 Skills 之間缺乏明確的互補關係標註，使用者難以理解工具間的關係

這些優化將提升工具可用性並降低認知負擔。

## What Changes

### 命令整合

- **合併** `commands/claude/coverage.md` 與 `commands/claude/test-coverage.md` 為單一 `coverage.md`
- 使用參數 `--generate` 區分「分析模式」與「分析+生成測試模式」
- **移除** 獨立的 `test-coverage.md`（**BREAKING**：使用者需改用 `/coverage --generate`）

### Skill 標註機制

- 在 Skills 的 YAML frontmatter 中新增 `related` 欄位
- 標註互補工具的名稱與關係說明
- 根據分析報告，以下三個群組共 8 個 Skills 需要標註：

**群組 1：Git 提交相關**
- `commit-standards` - 標準參考
- `git-commit-custom` - 實作模組
- `git-workflow-guide` - 策略指南

**群組 2：代碼審查相關**
- `code-review-assistant` - PR 審查清單
- `checkin-assistant` - 提交前檢查

**群組 3：測試相關**
- `testing-guide` - 測試理論
- `tdd-workflow` - 方法論實踐
- `test-coverage-assistant` - 評估工具

## Capabilities

### New Capabilities

- `skill-related-annotation`: 在 Skill frontmatter 中標註互補工具的能力，包含欄位定義與驗證規則

### Modified Capabilities

- `coverage-command`: 現有的覆蓋率分析命令將整合測試生成功能，新增 `--generate` 參數支援

## Impact

### 受影響的檔案

**Commands（2 個）**
- `commands/claude/coverage.md` - 修改（整合 test-coverage 功能）
- `commands/claude/test-coverage.md` - 移除

**Skills - Git 提交群組（3 個）**
- `skills/commit-standards/SKILL.md` - 修改（新增 related 欄位）
- `skills/git-commit-custom/SKILL.md` - 修改（新增 related 欄位）
- `skills/git-workflow-guide/SKILL.md` - 修改（新增 related 欄位）

**Skills - 代碼審查群組（2 個）**
- `skills/code-review-assistant/SKILL.md` - 修改（新增 related 欄位）
- `skills/checkin-assistant/SKILL.md` - 修改（新增 related 欄位）

**Skills - 測試群組（3 個）**
- `skills/testing-guide/SKILL.md` - 修改（新增 related 欄位）
- `skills/tdd-workflow/SKILL.md` - 修改（新增 related 欄位）
- `skills/test-coverage-assistant/SKILL.md` - 修改（新增 related 欄位）

### Breaking Changes

- `/test-coverage` 命令將被移除，使用者需改用 `/coverage --generate`

### 遷移指引

| 舊用法 | 新用法 |
|--------|--------|
| `/test-coverage` | `/coverage --generate` |
| `/coverage` | `/coverage`（不變） |
