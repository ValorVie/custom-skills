# Tool Overlap Analysis Report

**Generated**: 2026-01-26
**Project**: custom-skills
**Analyzer**: custom-skills-tool-overlap-analyzer v1.0.0

---

## Executive Summary

本報告針對 custom-skills 專案進行工具重疊性分析，涵蓋 Agents、Skills、Commands、Workflows 和 Hooks 五種工具類型。

**重要說明**：本專案採用多平台分發架構，相同內容的檔案會複製到不同位置（如 `agents/claude/`、`agents/opencode/`、`skills/agents/`）以支援不同 AI 平台。這些跨平台副本不視為重疊問題，分析時已先行去重，僅分析唯一版本。

### 統計摘要

| 指標 | 數量 |
|------|------|
| 工具總數（去重後） | 96 |
| 中等重疊問題 (50-69%) | 4 |
| 低重疊/需釐清邊界 | 3 |
| 優化建議 | 6 |

### 各類型工具數量（去重後）

| 類型 | 原始數量 | 去重後 | 重疊問題數 |
|------|----------|--------|-----------|
| Agents | 17 | 11 | 0 |
| Skills | 41 | 41 | 2 組 |
| Commands | 48 | 44 | 3 組 |
| Workflows | 5 | 5 | 0 |
| Hooks | 0 | 0 | N/A |

---

## Analysis by Tool Type

### Agents (11 unique, analyzed)

去重後的唯一 Agents：

| Agent | 用途 |
|-------|------|
| `build-error-resolver` | 構建錯誤快速修復 |
| `code-architect` | 系統架構設計 |
| `code-simplifier` | 代碼簡化與重構 |
| `database-reviewer` | PostgreSQL 優化與安全 |
| `doc-updater` | 文件與 Codemap 更新 |
| `doc-writer` | 技術文件撰寫 |
| `e2e-runner` | Playwright E2E 測試 |
| `reviewer` | 代碼審查與品質評估 |
| `security-reviewer` | 安全漏洞檢測 |
| `spec-analyst` | 需求分析與規格生成 |
| `test-specialist` | 測試策略與覆蓋率 |

**分析結果**：11 個 Agents 各有明確且不重疊的職責，設計良好。

---

### Skills (41 analyzed)

#### 潛在重疊群組

##### 群組 1：Git 提交相關 (Overlap Score: 55%)

| Skill | 用途 | 定位 |
|-------|------|------|
| `commit-standards` | 提交訊息格式標準 | 📚 標準參考 |
| `custom-skills-git-commit` | 完整 Git 工作流模組 | 🔧 實作模組 |
| `git-workflow-guide` | Git 分支策略指南 | 📖 策略指南 |

**分析**：
三者定位不同：
- `commit-standards` 是格式規範的參考文件
- `custom-skills-git-commit` 是供 Command 調用的實作模組
- `git-workflow-guide` 是分支策略的指導方針

**結論**：功能互補，非重疊。但建議在各自的 description 中明確說明與其他工具的關係。

##### 群組 2：代碼審查相關 (Overlap Score: 50%)

| Skill | 用途 | 定位 |
|-------|------|------|
| `code-review-assistant` | PR 審查清單與標準 | 📋 審查清單 |
| `checkin-assistant` | 提交前品質關卡 | ✅ 提交前檢查 |

**分析**：
`checkin-assistant` 已在檔案中明確聲明：
> "This skill focuses on **when and how to commit**. For code review during PR, see [Code Review Assistant]."

**結論**：定位清晰，互補關係。無需調整。

##### 群組 3：測試相關 (Overlap Score: 45%)

| Skill | 用途 | 定位 |
|-------|------|------|
| `testing-guide` | 測試金字塔與標準 | 📚 測試理論 |
| `tdd-workflow` | TDD 工作流實踐 | 🔄 方法論實踐 |
| `test-coverage-assistant` | 測試完整性評估 | 📊 評估工具 |

**結論**：三者分別處理「理論標準」、「實踐方法」、「評估分析」，定位清晰。

---

### Commands (44 unique, analyzed)

去重說明：
- `commands/claude/custom-skills-git-commit.md` 與 `commands/antigravity/custom-skills-git-commit.md` 內容相似，僅分析 claude 版本
- `commands/antigravity/code-simplifier-antigravity.md` 是 antigravity 專屬，保留

#### 潛在重疊群組

##### 群組 1：提交訊息命令 (Overlap Score: 65%)

| Command | 用途 | 功能範圍 |
|---------|------|----------|
| `commit.md` | 生成提交訊息 | 訊息生成 |
| `custom-skills-git-commit.md` | 完整提交工作流 | 同步 + 分析 + 提交 + 推送 + PR |

**分析**：
- `commit.md` 的功能是 `custom-skills-git-commit.md` 的子集
- 兩者觸發詞相近（"commit"）

**建議**：
考慮以下方案之一：
1. **整合方案**：`/commit` 作為 `/custom-skills-git-commit --message-only` 的別名
2. **保留方案**：明確區分使用場景
   - `/commit` → 只需要訊息，不執行 git 操作
   - `/custom-skills-git-commit` → 完整工作流

##### 群組 2：測試覆蓋率命令 (Overlap Score: 60%)

| Command | 用途 |
|---------|------|
| `coverage.md` | 分析覆蓋率並提供建議 |
| `test-coverage.md` | 分析覆蓋率並生成缺失測試 |

**分析**：
- 核心功能相同（分析覆蓋率）
- `test-coverage.md` 多了「生成測試」功能

**建議**：
合併為單一命令，使用參數區分：
```bash
/coverage              # 分析模式（預設）
/coverage --generate   # 分析 + 生成測試
```

##### 群組 3：BDD 命令族群 (Overlap Score: 40%)

| Command | 用途 | 方向 |
|---------|------|------|
| `bdd.md` | BDD 工作流引導 | 通用引導 |
| `derive-bdd.md` | 從 SDD 推導 BDD | SDD → BDD |
| `reverse-bdd.md` | SDD 轉 BDD 場景 | SDD → BDD |

**分析**：
`derive-bdd.md` 與 `reverse-bdd.md` 命名易混淆，但檢視內容後：
- `derive-bdd.md` - 從 SDD 規格「推導」新的 BDD 場景
- `reverse-bdd.md` - 將 SDD 驗收條件「轉換」為 Gherkin 格式

**結論**：功能有細微差異，但命名確實容易混淆。建議改善命名或加強文件說明。

##### 群組 4：TDD 命令族群 (Overlap Score: 40%)

與 BDD 群組類似的結構，同樣建議改善命名或文件。

---

### Workflows (5 analyzed)

| Workflow | 用途 |
|----------|------|
| `code-review.workflow.yaml` | PR 審查流程 |
| `feature-dev.workflow.yaml` | 功能開發流程 |
| `integrated-flow.workflow.yaml` | 整合 ATDD/SDD/BDD/TDD |
| `large-codebase-analysis.workflow.yaml` | 大型代碼庫分析 |
| `release.workflow.yaml` | 發布流程 |

**分析結果**：五個 Workflow 各有明確且不重疊的用途，設計良好，無需調整。

---

### Hooks (0 analyzed)

專案未配置任何 Hook。

---

## Optimization Recommendations

### 1. ~~合併 coverage.md 與 test-coverage.md~~ ✅ 已完成

**狀態**：✅ 已實作（2026-01-26）

**實作內容**：
- `test-coverage.md` 已移除
- `coverage.md` 新增 `--generate` / `-g` 參數
- `/coverage` 為分析模式，`/coverage --generate` 為生成模式

---

### 2. 釐清 commit.md 與 git-commit.md 的關係

**優先級**：🟢 低

**選項 A - 整合**：
```bash
/commit          # 別名，等同 /custom-skills-git-commit --message-only
/custom-skills-git-commit      # 完整工作流
```

**選項 B - 保留並文件化**：
在兩者的 description 中明確說明：
- `/commit` - "Quick commit message generation. For full workflow, use /custom-skills-git-commit"
- `/custom-skills-git-commit` - "Complete Git workflow. For message-only, use /commit"

---

### 3. 改善 BDD/TDD derive/reverse 命令命名

**優先級**：🟢 低

**現狀**：
- `derive-bdd.md` vs `reverse-bdd.md` 語意相近
- `derive-tdd.md` vs `reverse-tdd.md` 語意相近

**建議**：
考慮重新命名以更清晰區分：
- `derive-*` → `spec-to-*`（從規格推導）
- `reverse-*` → `*-coverage-check`（覆蓋率檢查）

或在 COMMAND-FAMILY-OVERVIEW.md 中加強說明區別。

---

### 4. 建立工具選擇指南

**優先級**：🟢 低

建議在專案文件中加入工具選擇快速參考：

```markdown
## 工具選擇指南

### Git 提交相關
| 我想要... | 使用 |
|----------|------|
| 快速生成提交訊息 | `/commit` |
| 完整的提交工作流（同步、提交、推送） | `/custom-skills-git-commit` |
| 了解提交訊息規範 | `commit-standards` Skill |
| 了解分支策略 | `git-workflow-guide` Skill |

### 測試相關
| 我想要... | 使用 |
|----------|------|
| 分析測試覆蓋率 | `/coverage` |
| 執行 TDD 工作流 | `/tdd` |
| 從規格推導測試 | `/derive-all` |
| 了解測試標準 | `testing-guide` Skill |
```

---

### 5. ~~在 Skill 中標註互補工具~~ ❌ 已取消

**狀態**：❌ 已取消（2026-01-26）

**取消原因**：
經評估，Claude Code 的 Skill 選擇機制是基於 `description` 的語意理解，不會讀取 `related` 欄位做推薦。因此 `related` 欄位的實際效益有限，僅具文檔價值。

**結論**：改善 `description` 內容比新增 `related` 欄位更有效

---

### 6. 更新 custom-skills-tool-overlap-analyzer Skill

**優先級**：🟢 低

更新 Skill 邏輯，加入「跨平台分發去重」的處理步驟：

```markdown
## Step 0: Deduplication

Before analysis, identify and deduplicate cross-platform copies:
- Same filename in different platform directories
- Content hash matching

Treat identical copies as single tool for analysis.
```

---

## Summary

經過修正後的分析顯示，custom-skills 專案的工具生態系統設計良好：

### 無重疊問題 ✅
- **Agents** (11 個)：各有明確職責
- **Workflows** (5 個)：各有明確用途
- **大部分 Skills 和 Commands**：定位清晰

### 可優化項目 🔧
| 項目 | 類型 | 優先級 | 狀態 |
|------|------|--------|------|
| coverage + test-coverage | Commands | 🟡 中 | ✅ 已合併 |
| Skill related 標註 | Skills | 🟢 低 | ❌ 已取消（效益有限） |
| commit vs git-commit | Commands | 🟢 低 | 待處理 |
| derive-* vs reverse-* 命名 | Commands | 🟢 低 | 待處理 |

### 整體評估

專案工具架構設計合理，採用了清晰的分層結構（Standards → Skills → Commands → Workflows）。跨平台分發機制（claude/opencode/agents）是有意為之的設計，不是問題。建議的優化項目屬於「錦上添花」性質，現有架構已可良好運作。

---

## Appendix: Tool Inventory (Deduplicated)

### A. Unique Agents (11)

| Name | Primary Function |
|------|------------------|
| build-error-resolver | 構建錯誤修復 |
| code-architect | 架構設計 |
| code-simplifier | 代碼簡化 |
| database-reviewer | 資料庫審查 |
| doc-updater | 文件更新 |
| doc-writer | 文件撰寫 |
| e2e-runner | E2E 測試 |
| reviewer | 代碼審查 |
| security-reviewer | 安全審查 |
| spec-analyst | 規格分析 |
| test-specialist | 測試策略 |

### B. Skills by Category (41)

| Category | Count | Skills |
|----------|-------|--------|
| OpenSpec | 10 | openspec-* 系列 |
| 開發方法論 | 8 | spec-driven-dev, bdd-assistant, tdd-workflow, atdd-assistant, forward-derivation, methodology-system, continuous-learning, eval-harness |
| 程式碼品質 | 7 | code-review-assistant, checkin-assistant, testing-guide, test-coverage-assistant, security-review, coding-standards, error-code-guide |
| 文檔 | 6 | documentation-guide, changelog-guide, docs-generator, commit-standards, requirement-assistant, logging-guide |
| 架構 | 5 | ai-friendly-architecture, ai-instruction-standards, ai-collaboration-standards, project-structure-guide, refactoring-assistant |
| 專案管理 | 4 | custom-skills-dev, custom-skills-doc-updater, custom-skills-upstream-sync, custom-skills-upstream-compare |
| 其他 | 1 | cloud-infrastructure-security, obsidian-markdown, obsidian-bases, json-canvas, strategic-compact, skill-creator, reverse-engineer, release-standards, custom-skills-git-commit, git-workflow-guide, custom-skills-tool-overlap-analyzer |

### C. Commands by Category (44 unique)

| Category | Commands |
|----------|----------|
| OpenSpec | apply, archive, bulk-archive, continue, explore, ff, new, onboard, sync, verify |
| 測試驅動 | tdd, bdd, atdd, derive-all, derive-tdd, derive-bdd, derive-atdd, reverse-tdd, reverse-bdd |
| Git | commit, git-commit, changelog, release |
| 品質 | review, refactor, coverage, build-fix |
| 文件 | docs, generate-docs |
| 標準 | init, config, check, update |
| 其他 | spec, reverse-spec, requirement, methodology, checkpoint, e2e, eval, learn, custom-skills-upstream-sync |

### D. Workflows (5)

| Workflow | Purpose |
|----------|---------|
| code-review | PR 審查 |
| feature-dev | 功能開發 |
| integrated-flow | 整合流程 |
| large-codebase-analysis | 大型代碼庫 |
| release | 發布流程 |

---

*Report generated by custom-skills-tool-overlap-analyzer skill*
*Analysis method: Cross-platform duplicates deduplicated before comparison*
