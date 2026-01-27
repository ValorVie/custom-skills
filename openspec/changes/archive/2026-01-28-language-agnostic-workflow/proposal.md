## Why

目前的開發工作流程文件（DEVELOPMENT-WORKFLOW.md）和測試相關命令（derive-tests、test、coverage、report）僅支援 Python。隨著專案可能需要支援多語言（如 PHP），需要將工作流程和命令抽象化，使其語言無關，並為各語言建立獨立的命令。

## What Changes

- **BREAKING**: 重新命名現有 Python 測試命令
  - `custom-skills-test` → `custom-skills-python-test`
  - `custom-skills-coverage` → `custom-skills-python-coverage`
  - `custom-skills-derive-tests` → `custom-skills-python-derive-tests`
- 新增 PHP 測試命令
  - `custom-skills-php-test` - PHPUnit 測試執行與分析
  - `custom-skills-php-coverage` - PHPUnit 覆蓋率分析
  - `custom-skills-php-derive-tests` - 從 specs 生成 PHPUnit 測試
- 修改 DEVELOPMENT-WORKFLOW.md
  - 將 Phase 5 測試部分拆分為通用流程 + 各語言區塊
  - 更新命令速查表為多語言版本
- `custom-skills-report` 保持通用（整合各語言測試結果）

## Capabilities

### New Capabilities

- `php-test-execution`: PHPUnit 測試執行與 AI 分析結果
- `php-coverage`: PHPUnit 覆蓋率分析與 AI 改善建議
- `php-test-generation`: 從 OpenSpec specs 生成 PHPUnit 測試程式碼

### Modified Capabilities

- `test-execution`: 將現有 Python 測試執行規格調整為語言無關結構，具體實作移至 Python 專用 spec
- `coverage`: 將現有覆蓋率規格調整為語言無關結構，具體實作移至 Python 專用 spec
- `test-generation`: 將現有測試生成規格調整為語言無關結構，具體實作移至 Python 專用 spec

## Impact

### 命令檔案

| 現有 | 新名稱 |
|------|--------|
| `commands/claude/custom-skills-test.md` | `commands/claude/custom-skills-python-test.md` |
| `commands/claude/custom-skills-coverage.md` | `commands/claude/custom-skills-python-coverage.md` |
| `commands/claude/custom-skills-derive-tests.md` | `commands/claude/custom-skills-python-derive-tests.md` |

### 新增命令檔案

- `commands/claude/custom-skills-php-test.md`
- `commands/claude/custom-skills-php-coverage.md`
- `commands/claude/custom-skills-php-derive-tests.md`

### 文件

- `docs/dev-guide/DEVELOPMENT-WORKFLOW.md` - 更新為多語言版本

### 相依性

- PHP 環境需要 PHPUnit 和 php-code-coverage
- 現有 Python 環境不受影響

### 使用者影響

- 使用者需更新命令名稱（`/custom-skills-test` → `/custom-skills-python-test`）
- 可考慮提供別名以保持向後相容
