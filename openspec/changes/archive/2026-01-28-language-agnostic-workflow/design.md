## Context

目前專案的測試工作流程命令（`custom-skills-test`、`custom-skills-coverage`、`custom-skills-derive-tests`）是為 Python/pytest 設計的。隨著可能需要支援 PHP 專案，需要重構命令結構以支援多語言。

現有架構：
- `commands/claude/custom-skills-*.md` - Claude Code 命令定義
- `script/commands/*.py` - CLI 實作（`ai-dev` CLI）
- `docs/dev-guide/DEVELOPMENT-WORKFLOW.md` - 開發流程文件

## Goals / Non-Goals

**Goals:**

- 建立語言無關的命令命名結構：`/custom-skills-{lang}-{action}`
- 為 Python 和 PHP 分別建立獨立的測試命令
- 更新 DEVELOPMENT-WORKFLOW.md 支援多語言工作流程
- 保持 `custom-skills-report` 通用（自動偵測語言）

**Non-Goals:**

- 不建立通用的 CLI wrapper（各語言直接呼叫原生工具）
- 不在此階段支援其他語言（如 JavaScript/TypeScript）
- 不修改 OpenSpec 核心功能

## Decisions

### Decision 1: 命令命名規則

**選擇**: `custom-skills-{lang}-{action}` 格式

```
/custom-skills-python-test
/custom-skills-python-coverage
/custom-skills-python-derive-tests

/custom-skills-php-test
/custom-skills-php-coverage
/custom-skills-php-derive-tests
```

**替代方案**:
- `custom-skills-test-python` - action 在前，但與現有命名風格不一致
- `test-python` / `test-php` - 太簡短，可能與其他命令衝突

**理由**: 保持 `custom-skills-` 前綴一致性，語言標識在 action 之前便於分組。

### Decision 2: PHP 測試工具

**選擇**: PHPUnit + PCOV

| 功能 | 工具 |
|------|------|
| 測試框架 | PHPUnit |
| 覆蓋率 | PCOV（或 Xdebug） |
| 執行方式 | `./vendor/bin/phpunit` |

**理由**: PHPUnit 是 PHP 生態系的標準測試框架，PCOV 效能優於 Xdebug。

### Decision 3: CLI 實作策略

**選擇**: Claude Code 命令直接呼叫原生工具

- Python: `uv run ai-dev test` / `uv run pytest`
- PHP: `./vendor/bin/phpunit`

**替代方案**:
- 建立統一的 `ai-dev test --lang python` wrapper

**理由**:
- 各語言工具差異大，統一 wrapper 會增加複雜度
- Claude Code 命令本身就是 AI 理解的介面，不需要額外抽象層
- AI 可根據命令內容理解如何執行和分析結果

### Decision 4: DEVELOPMENT-WORKFLOW.md 結構

**選擇**: 通用流程 + 語言區塊

```markdown
## Phase 5: 測試

### 通用流程
1. 從 specs 生成測試
2. 執行測試（Red Phase）
3. 實作功能
4. 執行測試（Green Phase）
5. 檢查覆蓋率

### Python
| 步驟 | 命令 |
|------|------|
| 生成測試 | `/custom-skills-python-derive-tests` |
| 執行測試 | `/custom-skills-python-test` |
| 覆蓋率 | `/custom-skills-python-coverage` |

### PHP
| 步驟 | 命令 |
|------|------|
| 生成測試 | `/custom-skills-php-derive-tests` |
| 執行測試 | `/custom-skills-php-test` |
| 覆蓋率 | `/custom-skills-php-coverage` |
```

**理由**: 保持工作流程的語言無關性，具體命令按語言分類。

### Decision 5: Report 命令處理

**選擇**: `custom-skills-report` 保持通用

AI 自動偵測專案語言：
1. 檢查 `composer.json` → PHP
2. 檢查 `pyproject.toml` / `requirements.txt` → Python
3. 根據語言執行對應的測試和覆蓋率命令

**理由**: Report 是整合性命令，應該智能處理多語言專案。

## Risks / Trade-offs

### Risk 1: Breaking Change

**風險**: 使用者需要更新命令名稱

**緩解**:
- 在文件中清楚說明變更
- 考慮提供 symlink 或 alias 過渡期

### Risk 2: PHP 環境差異

**風險**: PHP 環境設定比 Python 更分散（Composer、PHPUnit 版本等）

**緩解**:
- 命令中提供清楚的環境要求
- AI 分析結果時處理常見錯誤訊息

### Risk 3: 測試生成品質

**風險**: AI 生成的 PHPUnit 測試可能不如 pytest 測試準確（較少訓練資料）

**緩解**:
- 提供詳細的 PHPUnit 測試模板和範例
- 命令中加入 PHPUnit 最佳實踐指引
